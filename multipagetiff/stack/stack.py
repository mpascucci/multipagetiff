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

MULTIPAGETIFF is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with MULTIPAGETIFF.  If not, see <https://www.gnu.org/licenses/>.

"""

from collections.abc import Sequence
import numpy as _np


class Stack(Sequence):
    """The multipage tiff object.
    it behaves as a list which members are the pages of the tiff.
    Each page is a numpy array.
    """

    def __init__(self, imgs, dx=1, dz=1, title='', z_label='depth', units='units'):
        """
        :param imgs: numpy array of shape (Nz, Nx, Ny) containing the raw images of the stack
        :param dx: value of one pixel in physical units, on the transverse plane (X,Y)
        :param dz: value of one pixel in physical units, on the axial direction (Z)
        :param units: physical units of the z axis
        :param z_label: label used for the color coding
        :param title:

        properties:
        - Stack.crop: [row0,row1,col0,col1] defines a rectangle which crops the stack pages
        - Stack.start_page, end_page : (index) defines the first and last page to use
        - Stack.keypage: the page at which z=0
        - Stack.raw_images stores the raw image data.
        - Stack.pages is a view of the stack images restricted by the specified crop and start/end pages
        """

        self._set_raw_images(imgs)
        self.dx = dx
        self.dz = dz
        self.title = title
        self.units = units
        self.z_label = z_label
        # by setting this flag to TRUE the pages will be recalculated at next access
        self._update_pages = True
        self._normalize = False
        self._dtype_out = 'same'

    def reverse(self):
        self._imgs = self.pages[::-1]
        self.start_page = len(self) - self.end_page
        self.end_page = len(self) - self.start_page

    def reduce(self, f=2):
        self._imgs = self.pages[::f]
        self.dz *= 2
        self.keypage = round(self.keypage//f)
        self.start_page = round(self.start_page//f)
        self.end_page = round(self.end_page//f)

    def copy_props_from_stack(self, stack):
        self.dx = stack.dx
        self.dz = stack.dz
        self.title = stack.title
        self.units = stack.units
        self.z_label = stack.z_label
        self._crop = stack._crop.copy()
        self._normalize = stack._normalize
        self._dtype_out = stack._dtype_out

    def __getitem__(self, i):
        return self.pages[i]

    def __len__(self):
        return self._crop[1] - self._crop[0]

    def set_start_in_units(self, start):
        self.start_page = self.keypage + round(start//self.dz) + 1

    def set_end_in_units(self, end):
        self.end_page = self.keypage + round(end//self.dz)

    def _set_raw_images(self, images):
        if type(images) != _np.ndarray:
            try:
                images = _np.ndarray(images)
            except:
                raise ValueError(
                    "The images parameter is not a numpy array or is not convertible into one.")
        self._imgs = images
        self._crop = [0, len(images), 0, images[0].shape[0],
                      0, images[0].shape[1]]
        self._lazy_pages = None
        self.keypage = len(self)//2
        self._update_pages = True

    def copy(self):
        """Copy this stack into a new Stack instance"""
        new_stack = Stack(self._imgs, dx=self.dx, dz=self.dz,
                          title=self.title, z_label=self.z_label, units=self.units)

        new_stack.copy_props_from_stack(self)

        return new_stack

    def apply_to_pages(self, f, **kwargs):
        """Apply function f with the given kwargs to each page of a stack.
        f is a function that accepts 2D arrays as input.

        Return the results as a list."""
        pages = self.pages.copy()
        result = list()
        for page in pages:
            result.append(f(page, **kwargs))
        return result

    def apply(self, f, **kwargs):
        """Apply a function to the pages of the stack as a 3D array.
        f is a function accepting 3D a array as input

        Return the result"""

        return f(self.pages, **kwargs)

    def __repr__(self):
        d = dict(dx=self.dx, dz=self.dz, length=len(self),
                 title='"{}" '.format(self.title) if self.title != '' else '', unit=self.units, crop=self._crop[2:], pages=self._crop[:2])
        return "Multi-Page Stack {title}of {length} pages. (dx=dy={dx}{unit}, dz={dz}{unit}, crop={crop}], page limits={pages})".format(**d)

    def set_selection(self, start_page, end_page, vertical_start,
                      vertical_end, horizontal_start, horizontal_end):
        """Set crop and page limits for this stack.

        start and end values are indices in the raw_image spaces.
        start values are included, end values are excluded.

        if any of the region_limits is None, the current value is kept.
        """

        region_limits = [start_page, end_page, vertical_start,
                         vertical_end, horizontal_start, horizontal_end]

        assert len(region_limits) == 6

        for i, limit in enumerate(region_limits):
            if limit is not None:
                self._crop[i] = limit

        self._update_pages = True

    def set_pages_selection(self, start_page, end_page):
        """Set the limits of the current selected pages"""
        assert end_page > start_page
        self.start_page = start_page
        self.end_page = end_page

    def reset_selection(self):
        """reset the pages crop"""
        h, w = self._imgs[0].shape
        self._crop[2:] = [0, h, 0, w]

    def reset_page_limits(self):
        """reset the start/end pages"""
        self._crop[0:2] = [0, len(self._imgs)]

    def reset(self):
        """Reset the stack pages to the raw data"""
        self.reset_selection()
        self.reset_page_limits()
        self._lazy_pages = None

    def overwrite_raw_images(self):
        self._set_raw_images(self.pages)

    def revert_pages(self):
        """Revert the pages to undo direct modifications"""
        self._update_pages = True

    def _apply_normalization(self):
        """Normalize the gray levels of the stack.
        Pixel values will be rescaled between MIN and MAX.
        MIN and MAX are the limits of the output_datatype property of this stack
        (a numpy datatype specifier or 'same' (which indicates the same as input).

        NOTE: The normalization is calculated and applied on the selected pages (cropped)
        """

        output_dtype = self._imgs.dtype if self._dtype_out == 'same' else self._dtype_out

        try:
            min_level = _np.iinfo(output_dtype).min
            max_level = _np.iinfo(output_dtype).max
        except ValueError:
            # the output type is not an integer type
            min_level = 0
            max_level = 1

        imgs = self.pages.astype(_np.float64)

        imgs -= self.pages.min()
        imgs /= self.pages.max() - self.pages.min()
        imgs *= max_level + min_level
        imgs -= min_level

        self._lazy_pages = imgs.astype(output_dtype)

    @ property
    def normalize(self):
        return self._normalize

    @ normalize.setter
    def normalize(self, v):
        self._normalize = v
        self._update_pages = True

    @ property
    def dtype_out(self):
        return self._dtype_out

    @ dtype_out.setter
    def dtype_out(self, v):
        self._dtype_out = v
        self._update_pages = True

    @ property
    def pages(self):

        # if the crop region has been modified
        if self._update_pages or (self._lazy_pages is None):
            self._update_pages = False

            start, end, r0, r1, c0, c1 = self._crop
            self._lazy_pages = self._imgs[start:end, r0:r1, c0:c1]

            if self.normalize:
                self._apply_normalization()

        return self._lazy_pages

    @property
    def shape(self):
        # the shape of the stack selection
        return self.pages.shape

    def _crop_setter(self, ar_slice, value):
        """helper function for property setters.
        This function ensures that the selection regions are properly set."""

        # ensure iterability
        try:
            iter(value)
        except:
            value = [value]

        exp_len = ar_slice.stop - ar_slice.start
        assert len(value) == exp_len,\
            "Expected len({exp_len}) values".format()
        crop = self._crop.copy()
        crop[ar_slice] = value
        self.set_selection(*crop)

    def set_crop(self, vertical_start, vertical_end, horizontal_start, horizontal_end):
        """Set the crop region of this stack.

        start and end values are indeces in the raw_image spaces.
        start is included, end is excluded.
        """
        self.crop = (vertical_start, vertical_end,
                     horizontal_start, horizontal_end)

    def set_crop_vertical(self, start, end):
        self.crop_vertical = [start, end]

    def set_crop_horizontal(self, start, end):
        self.crop_horizontal = [start, end]

    def set_page_limits(self, start, end):
        self.page_limits = [start, end]

    @ property
    def crop(self):
        return self._crop[2:]

    @ crop.setter
    def crop(self, v):
        self._crop_setter(slice(2, 6), v)

    @ property
    def crop_vertical(self):
        return self._crop[2:4]

    @ crop_vertical.setter
    def crop_vertical(self, v):
        self._crop_setter(slice(2, 4), v)

    @ property
    def crop_horizontal(self):
        return self._crop[4:6]

    @ crop_horizontal.setter
    def crop_horizontal(self, v):
        self._crop_setter(slice(4, 6), v)

    @ property
    def start_page(self):
        return self._crop[0]

    @ start_page.setter
    def start_page(self, v):
        self._crop_setter(slice(0, 1), v)

    @ property
    def end_page(self):
        return self._crop[1]

    @ end_page.setter
    def end_page(self, v):
        self._crop_setter(slice(1, 2), v)

    @ property
    def page_limits(self):
        return self._crop[0:2]

    @ page_limits.setter
    def page_limits(self, v):
        self._crop_setter(slice(0, 2), v)

    @ property
    def selection_length(self):
        return self.end_page - self.start_page + 1

    @ property
    def range_in_units(self):
        return _np.array([self.start_page-self.keypage, self.end_page-self.keypage])*self.dz

    @ property
    def raw_images(self):
        return self._imgs

    @ raw_images.setter
    def raw_images(self, images):
        self._set_raw_images(images)

    @ property
    def max(self):
        return self.pages.max()

    @ property
    def mean(self):
        return self.pages.mean()

    @ property
    def min(self):
        return self.pages.min()

    @ property
    def std(self):
        return self.pages.std()
