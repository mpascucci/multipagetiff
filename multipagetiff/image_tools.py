import numpy as _np


def estimate_zero_padding(img):
    """Estimate horizontal and vertical padding in an image.

    Return value: a dictionary of two touples.

    """
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
