from scipy.ndimage import affine_transform
import numpy as np


def calc_transf_image_shape(img, matrix):
    """
    Calculate the shape that whould contain entirely img after
    its transformation by matrix.

    matrix transforms the coordinate of img in the output coordnates.

    e.g. Using scipy.ndimage to transform `img` into `out`,  
    if `M` is the tranformation matrix and `M_inv` its inverse:

    d = calc_transf_image_shape(img, M)
    out = nd.affine_transform(img, M_inv, output_shape=d)

    """

    if matrix.shape != (3, 3):
        raise ValueError("ERROR: Only 3x3 matrices are supported.")

    d, h, w = img.shape
    corners = np.float32([
        [0, 0, 0], [0, h-1, 0], [0, 0, w-1], [0, h-1, w-1],
        [d-1, 0, 0], [d-1, h-1, 0], [d-1, 0, w-1], [d-1, h-1, w-1]])

    # Transformed corners

    cornersT = np.dot(matrix, corners.T)
    minT = cornersT.min(axis=1)

    # negative coordinates must be compensated by an offset
    offset = np.where(minT < 0, minT, 0).astype(int)
    offset = offset/matrix.diagonal()

    # the output shape is the distance among the furtest corners
    shapeT = np.ceil(cornersT.max(axis=1) - minT).astype(int)
    # print(minT, shapeT)

    return shapeT, offset


def affine3D(img, matrix):
    """Apply an affine transformation to a 3D image
    Matrix is the direct transformation matrix from the image to its output.
    The output image has the correct shape to hold it entirely.

    This function calls scipy.ndimage.affine_transform using the inverse of matrix.

    Args:
        img (array): 3D image to transform
        matrix (array): 3x3 affine transformation matrix

    Raises:
        ValueError: if the shape of matrix is not (3,3)

    Returns:
        array: the transformed image.
    """
    if matrix.shape != (3, 3):
        raise ValueError("ERROR: Only 3x3 matrices are supported.")

    m_inv = np.linalg.inv(matrix)
    shp, offset = calc_transf_image_shape(img, matrix)
    return affine_transform(img, m_inv, offset=offset, output_shape=shp)
