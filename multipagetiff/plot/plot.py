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

import matplotlib.gridspec as _gridspec
from ..config import config as _config
from matplotlib import pyplot as _plt
from matplotlib import colorbar, colors
import numpy as _np
from ..stacktools import _get_orthogonal_slices


def plot_selection(stack, page=None, plot_axis=None, **kwargs):
    """Plot the crop region over a raw image of the stack

    if page is None the stack is z-projected"""
    plot_axis = _plt.gca if plot_axis is None else plot_axis
    if page is None:
        img = stack._imgs.max(axis=0)
    else:
        img = stack._imgs[page]
    _plt.imshow(img)
    r0, r1, c0, c1 = stack._crop[2:]
    fill = kwargs.get("fill", False)
    edgecolor = kwargs.get("edgecolor", 'red')
    r = _plt.Rectangle((c0, r0), c1-c0, r1-r0, edgecolor=edgecolor, fill=fill)
    _plt.gca().add_artist(r)


def get_cmap():
    """
    get the currenly used color map
    :return: a pyplot colormap
    """
    if _config.cmap is None:
        return _plt.cm.gist_rainbow
    else:
        return _config.cmap


def set_cmap(cmap):
    """
    set the default color map used by all the functions in this module
    :param cmap:
    :return:
    """
    _config.cmap = cmap


def color_code_ndarray(ndarray, threshold=0, axis=0):
    cmap = get_cmap()

    s = ndarray.shape[0]

    rgb = _np.zeros((*ndarray.shape, 3))
    for i, img in enumerate(ndarray):
        img_min = img.min()
        img_max = img.max()
        img_c = img_max - img_min
        if (img_c != 0):
            img = (img-img_min)/img_c
        img[img < threshold] = 0
        j = i/s
        rgb[i, :, :, 0] = img*cmap(j)[0]
        rgb[i, :, :, 1] = img*cmap(j)[1]
        rgb[i, :, :, 2] = img*cmap(j)[2]

    return rgb


def color_code(stack, threshold=0, axis=0):
    """
    Color code the pages of a multipage grayscale tiff image
    :param stack:
    :param threshold: [0,1] intensity values below the threshold are set to zero
    :return: a rgb multipage image (numpy array)
    """

    selection = stack.pages.copy()

    # rotate the array
    if axis != 0:
        selection = _np.rot90(selection, axes=(0, axis))
    if axis == 2:
        selection = _np.rot90(selection, axes=(2, 1))

    return color_code_ndarray(selection, threshold, axis)


def flatten_grayscale(stack, axis=0):
    """Return the 2D max projection of the intensity along the specified axis.
    depth = 0
    vertical = 1
    horizontal = 2
    """
    return stack[:].max(axis=axis)


def flatten(stack, threshold=0, axis=0, rotate_axis_2=False):
    """
    Return the color-coded max projection of the stack values along the specified axis
    (depth = 0, vertical = 1, horizontal = 2).

    The color map is defied in the cmap setting variable.
    The color map limits are defined by the stack start_page, keypage and end_page property.
    :param stack: a Stack
    :param threshold: [0,1] intensity values below the threshold are set to zero
    :return: a numpy array
    """
    imgs = stack.pages.copy()
    # imgs = imgs.swapaxes(axis, 0)
    if axis != 0:
        imgs = _np.rot90(imgs, axes=(0, axis))
    if (axis == 2) and rotate_axis_2:
        imgs = _np.rot90(imgs, axes=(2, 1))
    idx = _np.argmax(imgs, axis=0)
    # the output rgb image
    rgb = color_code_ndarray(imgs, threshold=threshold, axis=axis)
    out = _np.zeros((*rgb.shape[1:3], 3))

    for i in range(out.shape[0]):
        for j in range(out.shape[1]):
            out[i, j, :] = rgb[idx[i, j], i, j]
    return out


def plot_flatten(stack, threshold=0, axis=0):
    """Plot the max projection and its color bar.

    The projection is done along the specified axis.
    The color map is defied in the cmap setting variable.
    The color map limits are defined by the stack start_page, keypage and end_page property.
    The labels are taken from the stack properties.

    :param stack:
    :param threshold:
    :return: None

    Args:
        stack (Stack): a Stack
        threshold (int, optional): [0,1] intensity values below the threshold are set to zero. Defaults to 0.
        axis (int, optional): The axis of the projection (depth = 0, vertical = 1, horizontal = 2). Defaults to 0.
    """

    n = 10
    ax1 = _plt.subplot2grid((n, n), (0, 0), colspan=n-1, rowspan=n)
    ax2 = _plt.subplot2grid((n, n), (0, n-1), colspan=1, rowspan=n)

    ax1.imshow(flatten(stack, threshold=threshold,
               axis=axis, rotate_axis_2=True))
    ax1.set_title(stack.title)
    if axis == 0:
        norm = colors.Normalize(
            vmin=stack.range_in_units[0], vmax=stack.range_in_units[1])
    else:
        s = stack.pages.shape[axis]/2
        norm = colors.Normalize(
            vmin=-s*stack.dx, vmax=s*stack.dx,)
    cb1 = colorbar.ColorbarBase(ax2, cmap=get_cmap(),
                                norm=norm,
                                orientation='vertical')

    if stack.z_label:
        cb1.set_label("{}".format(stack.z_label))
    if stack.units:
        cb1.set_label("{} [{}]".format(stack.z_label, stack.units))


def plot_pages(stack, pages=None, colorcoded=False, **kwargs):
    """
    Plot the pages of the stack.
    :param stack:
    :param colorcoded: the stack is color coded
    :param pages: list of integer indicating the pages to plot
    :return: None
    """
    if colorcoded:
        imgs = color_code(stack)
    else:
        imgs = stack.pages

    if pages is not None:
        try:
            iter(pages)
        except TypeError:
            raise TypeError("pages must be an iterable.")
    else:
        pages = range(len(imgs))

    if len(pages) > _config.n_max_img_plot:
        pages = pages[:_config.n_max_img_plot]

    n_imgs = len(pages)

    cols = min(n_imgs, 6)
    rows = min(6, int(_np.floor(n_imgs/cols))+1)

    for j, i in enumerate(pages):
        img = imgs[i]
        _plt.subplot(rows, cols, j+1)
        _plt.imshow(img, **kwargs)
        _plt.axis('off')
        _plt.text(0.05*img.shape[0], 0.9*img.shape[1], str(i),
                  {'bbox': dict(boxstyle="round", fc="white", ec="gray", pad=0.1)})

    _plt.tight_layout()


def get_xz_color_coded(stack, y, x=None, length=None, interpolation=1):
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
        x = _np.floor((stack[0].shape[1]+1)//2)

    if length is None:
        length = stack[0].shape[1]
    else:
        assert length % 2 != 0, "length must be odd"

    start = max(0, x-length//2)
    end = min(x+length//2, stack[0].shape[1])
    length = end-start

    xz = _np.zeros((len(stack)*interpolation, length, 3))
    for i, img in enumerate(color_code(stack)):
        for j in range(i*interpolation, (i+1)*interpolation):
            xz[j, :] = img[y, start:end]

    return xz


def orthogonal_views(stack, v=None, h=None, z=None, **kwargs):
    """
    Plot orthogonal planes intersecting at the specified point.

    The point is specified by the following coordinates:
    v = vertical axis of the stack page (third dimension of pages array)
    h = horizontal axis of the stack page (second dimension of pages array)
    z = depth of the stack, page number (first dimension of pages array)
    **kwargs are forwarded to the pyplot.imshow function

    if a coordinate is missing, the center of that dimension is used.

    """

    fig = _plt.gcf()
    gs1 = _gridspec.GridSpec(2, 2)

    point = _np.array([z, v, h])

    # the default point is in the middle of the stack
    default_point = (_np.array(stack[:].shape)//2).astype(int)
    # set default for unspecified coordinates
    for i in range(len(point)):
        if point[i] is None:
            point[i] = default_point[i]

    orto = _get_orthogonal_slices(stack, *point)

    ax = fig.add_subplot(gs1[0])
    av = 'v'
    ah = 'h'
    ax.imshow(orto[f'{av}{ah}'], **kwargs)
    ax.scatter(h, v, facecolors='none', edgecolors='red')
    ax.set_ylabel(av)
    ax.set_xlabel(ah)

    ax = fig.add_subplot(gs1[1])
    av = 'z'
    ah = 'v'
    ax.imshow(orto[f'{av}{ah}'], **kwargs)
    ax.scatter(v, z, facecolors='none', edgecolors='red')
    ax.set_ylabel(av)
    ax.set_xlabel(ah)

    ax = fig.add_subplot(gs1[2])
    av = 'z'
    ah = 'h'
    ax.imshow(orto[f'{av}{ah}'], **kwargs)
    ax.scatter(h, z, facecolors='none', edgecolors='red')
    ax.set_ylabel(av)
    ax.set_xlabel(ah)

    _plt.tight_layout()


def orthogonal_project(stack, depth_color_coded=False, **kwargs):
    fig = _plt.gcf()
    gs1 = _gridspec.GridSpec(2, 2)

    axis_names = ('yx', 'zx', 'zy')

    for i in range(3):
        ax = fig.add_subplot(gs1[i])
        if depth_color_coded:
            img = flatten(stack, axis=i)
        else:
            img = flatten_grayscale(stack, axis=i)

        ax.imshow(img, **kwargs)
        ax.set_ylabel(axis_names[i][0])
        ax.set_xlabel(axis_names[i][1])

    _plt.tight_layout()
