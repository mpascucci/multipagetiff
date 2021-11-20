from .config import config as _config
from matplotlib import pyplot as _plt
from matplotlib import colorbar, colors
import numpy as _np


def plot_selection(stack, page=0, plot_axis=None, **kwargs):
    """Plot the crop region over a raw image of the stack"""
    plot_axis = _plt.gca if plot_axis is None else plot_axis
    _plt.imshow(stack._imgs[page])
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


def color_code(stack, threshold=0):
    """
    Color code the pages of a multipage grayscale tiff image
    :param stack:
    :param threshold: [0,1] intensity values below the threshold are set to zero
    :return: a rgb multipage image (numpy array)
    """
    cmap = get_cmap()
    selection = stack.pages
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
    The color map limits are defined by the stack start_page, keypage and end_page property.
    :param stack:
    :param threshold: [0,1] intensity values below the threshold are set to zero
    :return: a numpy array
    """
    idx = _np.argmax(stack.pages, axis=0)
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
    :param threshold: [0,1] intensity values below the threshold are set to zero
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
