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

from multipagetiff.stack.stack import Stack
from .. import stack as _stack
from .. import image_tools as _image_tools
from .. import transform


import numpy as _np
# from types import SimpleNamespace as _SimpleNamespace


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


def unpad_stack(stack):
    """Un-pad the stack by setting an appropriate crop.
    The padding is estimated from the first page"""

    # Estimate the padding in a stack from the first non-empty image
    for i in range(len(stack._imgs)):
        try:
            pad = _image_tools.estimate_zero_padding(stack._imgs[i])
            break
        except _image_tools.EmptyImageException:
            continue
    else:
        raise ValueError("The stack seems empty")

    stack.crop = [pad['v'][0], pad['v'][1], pad['h'][0], pad['h'][1]]


def _get_orthogonal_slices(stack, z, v, h):
    """
        Get the orthogonal planes passing through the specified point.

        v = vertical axis of the page (third dimension of pages array),
        h = horizontal axis of the page (second dimension of pages array),
        z = depth of the stack, page number (first dimension of pages array),
    """

    vh = stack.pages[z, :, :]
    zv = stack.pages[:, :, h]
    zh = stack.pages[:, v, :]
    return dict(vh=vh, zv=zv, zh=zh, vz=zv.T, hz=zh.T)


def affine_transform(stack, matrix):
    """Apply a 3D affine transformation to the pages of the input stack.
    Return the result in a new stack."""

    img = stack.pages.copy()
    out = transform.affine3D(img, matrix)
    return Stack(out)
