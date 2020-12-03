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

from matplotlib import pyplot as plt
from matplotlib import colorbar, colors
import numpy as np
from types import SimpleNamespace


config = SimpleNamespace(
    cmap=None
)


def get_cmap():
    """
    get the currenly used color map
    :return: a pyplot colormap
    """
    if config.cmap is None:
        return plt.cm.gist_rainbow
    else:
        return config.cmap


def set_cmap(cmap):
    """
    set the default color map used by all the functions in this module
    :param cmap:
    :return:
    """
    config.cmap = cmap


def color_code(stack, threshold=0):
    """
    Color code the pages of a multipage grayscale tiff image
    :param stack:
    :param threshold: intensity values below the threshold are set to zero
    :return: a rgb multipage image (numpy array)
    """
    cmap = get_cmap()
    selection = stack.pages[stack.start_frame:stack.end_frame+1]
    rgb = np.zeros((*selection.shape, 3))
    for i, img in enumerate(selection):
        img_min = img.min()
        img_max = img.max()
        img_c = img_max - img_min
        if (img_c != 0):
            img = (img-img_min)/img_c
        img[img < threshold] = 0
        j = i/(stack.selection_length-1)
        rgb[i,:,:,0] = img*cmap(j)[0]
        rgb[i,:,:,1] = img*cmap(j)[1]
        rgb[i,:,:,2] = img*cmap(j)[2]

    return rgb


def flatten(stack, threshold=0):
    """
    generate the max projection of a stack.
    The color map is defied in the cmap setting variable.
    The color map limits are defined by the stack start_frame, ketframe and end_frame property.
    :param stack:
    :param threshold: intensity values below the threshold are set to zero
    :return: a numpy array
    """
    idx = np.argmax(stack.pages[stack.start_frame:stack.end_frame + 1], axis=0)
    out = np.zeros((*stack.pages.shape[1:], 3))
    rgb = color_code(stack, threshold=threshold)
    for i in range(out.shape[0]):
        for j in range(out.shape[1]):
            out[i, j, :] = rgb[idx[i, j], i, j]
    return out


def plot_flatten(stack, threshold=0):
    """
    Plot the max projection and its color bar.
    The labels are taken from the stack object properties.

    :param stack:
    :param threshold: intensity values below the threshold are set to zero
    :return: None
    """
    n=10
    ax1 = plt.subplot2grid((n, n), (0, 0), colspan=n-1, rowspan=n)
    ax2 = plt.subplot2grid((n, n), (0, n-1), colspan=1, rowspan=n)

    ax1.imshow(flatten(stack, threshold=threshold))
    ax1.set_title(stack.title)
    norm = colors.Normalize(vmin=stack.range_in_units[0], vmax=stack.range_in_units[1])
    cb1 = colorbar.ColorbarBase(ax2, cmap=get_cmap(),
                                    norm=norm,
                                    orientation='vertical')
   
    if stack.z_label:
        cb1.set_label("{}".format(stack.z_label))
    if stack.units:
        cb1.set_label("{} [{}]".format(stack.z_label, stack.units))
        


def plot_frames(stack, frames=None, colorcoded=False, **kwargs):
    """
    Plot the frames of the stack.
    :param stack:
    :param colorcoded: the stack is color coded
    :param frames: list of integer indicating the frames to plot
    :return: None
    """
    if colorcoded:
        imgs = color_code(stack)
    else:
        imgs = stack.pages

    MAX_IMGS = 36 # max images to show
    
    if frames is not None:
        try:
            iter(frames)
        except TypeError:
            raise TypeError("frames must be an iterable.")
    else:
        frames = range(len(imgs))

    if len(frames) > MAX_IMGS:
        frames=frames[:MAX_IMGS]

    n_imgs = len(frames)

    cols = min(n_imgs, 6)
    rows = min(6, int(np.floor(n_imgs/cols))+1)

    for j,i in enumerate(frames):
        img=imgs[i]
        plt.subplot(rows,cols,j+1)
        plt.imshow(img, **kwargs)
        plt.axis('off')
        plt.text(0.05*img.shape[0],0.9*img.shape[1],str(i), {'bbox': dict(boxstyle="round", fc="white", ec="gray", pad=0.1)})

    plt.tight_layout()


def get_xz(stack, y, x=None, length=None, interpolation=1):
    """
    Get a slice of the stack on the XZ plane
    :param stack:
    :param y: center coodrinate y
    :param x: center coordinate x (optional)
    :param length: length of the profile line
    :param interpolation: number of z steps per x step
    :return: a numpy array
    """

    if x is None:
        x = np.floor((stack[0].shape[1]+1)//2)

    if length is None:
        length = stack[0].shape[1]
    else:
        assert length % 2 != 0, "length must be odd"

    start = max(0, x-length//2)
    end = min(x+length//2, stack[0].shape[1])

    length = end-start

    xz = np.zeros((len(stack)*interpolation, length, 3))
    for i,img in enumerate(color_code(stack)):
        for j in range(i*interpolation, (i+1)*interpolation):
            xz[j,:] = img[y,start:end]

    return xz
