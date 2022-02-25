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

from .. import stack as _stack
from PIL import Image as _Image
import numpy as _np
import multiprocessing as _mp
from tqdm import tqdm as _tqdm
import functools as _ft


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
    return _stack.Stack(tiff2nparray(path), dx=dx, dz=dz, title=title, z_label=z_label, units=units)


def write_stack(stack, path="untitled.tif"):
    """Write the current pages of the stack as TIFF file"""
    imlist = []
    for m in stack.pages:
        imlist.append(_Image.fromarray(m))

    imlist[0].save(path, save_all=True, append_images=imlist[1:])


def load_and_apply(path, f, **kwargs):
    """Load a tif stack and apply f to it.

    f is a function that takes as input the pages of a stack (i.e. a 3D numpy array)
    kwargs are passed to f
    """
    stack = read_stack(path, dx=1, dz=1)
    retval = f(stack.pages, **kwargs)
    return retval


def load_and_apply_batch(paths, f=_np.sum, ncpu=None, **kwargs):
    """Load tif stacks and apply function f to each of them.

    f is a function that takes as input the pages of a stack (i.e. a 3D numpy array)
    kwargs are passed to f
    """

    f = _ft.partial(load_and_apply, f=f, **kwargs)

    # chose number of used CPUs
    ncpu = _mp.cpu_count()*0.8 if ncpu is None else ncpu
    ncpu = int(ncpu)

    with _mp.Pool(ncpu) as pool:
        return list(_tqdm(pool.imap(f, paths), total=len(paths), desc=f"Using {ncpu} CPUs"))
