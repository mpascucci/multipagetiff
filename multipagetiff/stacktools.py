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

from . import main as _stack
from . import image_tools as _image_tools

from matplotlib import pyplot as _plt
from matplotlib import colorbar, colors
import numpy as _np
from types import SimpleNamespace as _SimpleNamespace

import multiprocessing as _mp
from tqdm import tqdm as _tqdm
import functools as _ft
from PIL import Image as _Image


config = _SimpleNamespace(
    cmap=None
)


def tiff2nparray(path):
    """Transform a multipage tiff in numpy array
    :param path: path of the tiff file
    :return: a numpy array of shape (n,h,w) where n is the number of pages of the tiff file
    """
    im = _Image.open(path)
    i = 0
    frames = []
    try:
        while True:
            im.seek(i)
            frames.append(_np.array(im))
            i += 1
    except EOFError:
        pass

    return _np.array(frames)


def read_stack(path, dx=1, dz=1, title='', z_label='depth', units=''):
    """Load a stack form a tif file.

    :param path: (string) path to the tiff file
    :return: a Stack object
    """
    return _stack.Stack(tiff2nparray(path), dx=dx, dz=dz, title=title, z_label=z_label, units='')


def write_stack(stack, path="untitled.tif"):
    """Write the current pages of the stack as TIFF file"""
    imlist = []
    for m in stack.pages:
        imlist.append(_Image.fromarray(m))

    imlist[0].save(path, save_all=True, append_images=imlist[1:])


def empty_like(stack, value=0):
    """Create a new empty stack the same shape as stack

    :param stack: The reference Stack
    :type stack: multipagetiff.Stack
    :param value: the new Stack will be filled with this value, defaults to 0
    :type value: int, optional
    :return: a new Stack
    :rtype: multipagetiff.Stack
    """
    data = _np.zeros_like(stack.pages) + value
    new_stack = _stack.Stack(data)
    new_stack.copy_props_from_stack(stack)
    return new_stack


def get_cmap():
    """
    get the currenly used color map
    :return: a pyplot colormap
    """
    if config.cmap is None:
        return _plt.cm.gist_rainbow
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
    rgb = _np.zeros((*selection.shape, 3))
    for i, img in enumerate(selection):
        img_min = img.min()
        img_max = img.max()
        img_c = img_max - img_min
        if (img_c != 0):
            img = (img-img_min)/img_c
        img[img < threshold] = 0
        j = i/(stack.selection_length-1)
        rgb[i, :, :, 0] = img*cmap(j)[0]
        rgb[i, :, :, 1] = img*cmap(j)[1]
        rgb[i, :, :, 2] = img*cmap(j)[2]

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
    idx = _np.argmax(
        stack.pages[stack.start_frame:stack.end_frame + 1], axis=0)
    out = _np.zeros((*stack.pages.shape[1:], 3))
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
    n = 10
    ax1 = _plt.subplot2grid((n, n), (0, 0), colspan=n-1, rowspan=n)
    ax2 = _plt.subplot2grid((n, n), (0, n-1), colspan=1, rowspan=n)

    ax1.imshow(flatten(stack, threshold=threshold))
    ax1.set_title(stack.title)
    norm = colors.Normalize(
        vmin=stack.range_in_units[0], vmax=stack.range_in_units[1])
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

    MAX_IMGS = 36  # max images to show

    if frames is not None:
        try:
            iter(frames)
        except TypeError:
            raise TypeError("frames must be an iterable.")
    else:
        frames = range(len(imgs))

    if len(frames) > MAX_IMGS:
        frames = frames[:MAX_IMGS]

    n_imgs = len(frames)

    cols = min(n_imgs, 6)
    rows = min(6, int(_np.floor(n_imgs/cols))+1)

    for j, i in enumerate(frames):
        img = imgs[i]
        _plt.subplot(rows, cols, j+1)
        _plt.imshow(img, **kwargs)
        _plt.axis('off')
        _plt.text(0.05*img.shape[0], 0.9*img.shape[1], str(i),
                  {'bbox': dict(boxstyle="round", fc="white", ec="gray", pad=0.1)})

    _plt.tight_layout()


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


def load_and_apply(path, f=_np.sum, f_args={'axis': 0}):
    """Load a tif stack and apply f to it.

    f is a function that takes as input the pages of a stack (i.e. a 3D numpy array)
    """
    stack = read_stack(path, dx=1, dz=1)
    retval = f(stack.pages, **f_args)
    return retval


def load_and_apply_batch(paths, f=_np.sum, f_args={'axis': 0}, ncpu=None):
    """Load tif stacks and apply function f to each of them.

    f is a function that takes as input the pages of a stack (i.e. a 3D numpy array)
    """

    f = _ft.partial(load_and_apply, f=f, f_args=f_args)

    # chose number of used CPUs
    ncpu = _mp.cpu_count()*0.8 if ncpu is None else ncpu
    ncpu = int(ncpu)

    with _mp.Pool(ncpu) as pool:
        return list(_tqdm(pool.imap(f, paths), total=len(paths), desc=f"Using {ncpu} CPUs"))


def unpad_stack(stack):
    """Unpad the stack by setting an appropriate crop.
    The padding is estimated from the first page"""
    pad = _image_tools.estimate_zero_padding(stack._imgs[0])
    stack.crop = [pad['v'][0], pad['v'][1], pad['h'][0], pad['h'][1]]


def plot_crop(stack, page=0, plot_axis=None, **kwargs):
    """Plot the crop region over a raw image of the stack"""
    plot_axis = _plt.gca if plot_axis is None else plot_axis
    _plt.imshow(stack._imgs[page])
    r0, r1, c0, c1 = stack._crop[2:]
    fill = kwargs.get("fill", False)
    edgecolor = kwargs.get("edgecolor", 'red')
    r = _plt.Rectangle((c0, r0), c1-c0, r1-r0, edgecolor=edgecolor, fill=fill)
    _plt.gca().add_artist(r)
