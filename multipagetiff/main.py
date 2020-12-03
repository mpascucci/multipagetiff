"""

MULTIPAGETIFF

tools for multipage tiff images manipulation

author: Marco Pascucci
copyright: 2018


This file is part of MULTIPAGETIFF.

MULTIPAGETIFF is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Foobar is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Foobar.  If not, see <https://www.gnu.org/licenses/>.

"""

from collections.abc import Sequence
from PIL import Image
import numpy as np


def tiff2nparray(patj):
    """Transform a multipage tiff in numpy array
    :param path: path of the tiff file
    :return: a numpy array of shape (n,h,w) where n is the number of pages of the tiff file
    """
    im = Image.open(patj)
    i = 0
    frames = []
    try:
        while True:
            im.seek(i)
            frames.append(np.array(im))
            i += 1
    except EOFError:
        pass

    return np.array(frames)


class Stack(Sequence):
    """The multipage tiff object.
    it behaves as a list which members are the pages of the tiff.
    Each page is a numpy array.
    """

    def __init__(self, path, dx, dz, title='', z_label='depth', units=''):
        """
        :param path: path to the tiff file
        :param dx: value of one pixel in physical units, on the transverse plane (X,Y)
        :param dz: value of one pixel in physical units, on the axial direction (Z)
        :param units: physical units of the z axis
        :param z_label: label used for the color coding
        :param cmap: colormap used to repsresent the
        :param title:

        properties:
        these properties can be modified
        - crop: [x0,y0,x1,y1] defines a rectangle which crops the stack when plotting
        - start_frame, end_frame : int, defines the first and last frame to use
        - keyframe: the frame at which z=0
        """
        self._imgs = tiff2nparray(path)
        self.crop=[0,0,*self._imgs[0].shape]
        self.keyframe = len(self)//2
        self.start_frame = 0
        self.end_frame = len(self) - 1
        self.dx = dx
        self.dz = dz
        self.title = title
        self.units = units
        self.z_label = z_label

    def reverse(self):
        self._imgs = self.pages[::-1]
        self.start_frame = len(self) - self.end_frame
        self.end_frame = len(self) - self.start_frame

    def reduce(self, f=2):
        self._imgs = self.pages[::f]
        self.dz *= 2
        self.keyframe = round(self.keyframe//f)
        self.start_frame = round(self.start_frame//f)
        self.end_frame = round(self.end_frame//f)

    def __getitem__(self, i):
        return self.pages[i]

    def __len__(self):
        return self.pages.shape[0]

    def set_start_in_units(self, start):
        self.start_frame = self.keyframe + round(start//self.dz) + 1

    def set_end_in_units(self, end):
        self.end_frame = self.keyframe + round(end//self.dz)

    @property
    def pages(self):
        x,y,h,w = self.crop
        return self._imgs[:,x:x+h,y:y+w]

    @property
    def selection_length(self):
        return self.end_frame - self.start_frame + 1

    @property
    def range_in_units(self):
        return np.array([self.start_frame-self.keyframe, self.end_frame-self.keyframe])*self.dz

