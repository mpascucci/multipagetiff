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

import numpy as _np


class EmptyImageException(ValueError):
    pass


def estimate_zero_padding(img):
    """Estimate horizontal and vertical padding in an image.

    Return value: a dictionary of two touples.

    """

    if (img == 0).all():
        raise EmptyImageException("The image is empty!")

    res = dict()

    # horizontal
    th_img = img.sum(axis=0) != 0
    nonzero_indx = _np.argwhere(th_img).squeeze()
    res['h'] = (int(nonzero_indx[0]), int(nonzero_indx[-1]))

    # vertical
    th_img = img.sum(axis=1) != 0
    nonzero_indx = _np.argwhere(th_img).squeeze()
    res['v'] = (int(nonzero_indx[0]), int(nonzero_indx[-1]))

    return res


def unpad(img):
    """Remove zero-valued borders from the image

    :param img: input image 2D numpy array
    :return: a view of the image with removed borders (same type as input)

    Note: This function does not copy the image data.
    """
    pad = estimate_zero_padding(img)
    hstart, hend = pad['h']
    vstart, vend = pad['v']
    return img[vstart:vend, hstart:hend]


def normalize(ndarray, output_dtype='same'):
    output_dtype = ndarray if output_dtype == 'same' else output_dtype

    try:
        min_level = _np.iinfo(output_dtype).min
        max_level = _np.iinfo(output_dtype).max
    except ValueError:
        # the output type is not an integer type
        min_level = 0
        max_level = 1

    imgs = ndarray.astype(_np.float64)

    imgs -= ndarray.min()
    imgs /= ndarray.max() - ndarray()
    imgs *= max_level + min_level
    imgs -= min_level

    return imgs.astype(output_dtype)
