from __future__ import annotations
import numpy as np
from PIL import Image


_ptrtypestr = np.dtype(np.uintp).str

class _ArrayInterfaceForObject:
    __slots__ = ('__array_interface__', 'owner_object')
    def __init__(self, array_intf, obj=None):
        self.__array_interface__ = array_intf
        self.owner_object = obj

class _ArrayInterfaceForPointer:
    __slots__ = ('__array_interface__', 'owner_object')
    def __init__(self, ptr, shape, typestr='|u8', strides=None, readonly=True, owner_object=None):
        self.owner_object = owner_object
        self.__array_interface__ = {
            'data': (ptr, readonly),
            'typestr': typestr,
            'shape': shape,
            'strides': strides,
        }


def asarray(im: Image.Image, padding_channel='stride', allow_copy=True) -> np.ndarray:
    """
    Return an numpy.ndarray that shares the underlying buffer with the given image (if possible).

    Parameters
    ----------
    im : PIL.Image.Image
        The image.
    padding_channel : str
        Handling of padding channel in 3-channel image. 'stride' or 'passthrough' or 'copy_remove'.
        
        'stride':      The padding channel will be hidden from the result array. NOTE: ndarray with channel stride cannot be passed to OpenCV.
        'passthrough': The padding channel will be available with undetermined values in the result array.
        'copy_remove': The result array will be a copy of the image buffer with padding channel removed.
    allow_copy : bool
        Allow copying pixels when buffer sharing is unavailable, or raise an exception instead.

    Returns
    -------
    numpy.ndarray

    """

    imdata = im.getdata()
    make_copy = False
    shape, typestr = Image._conv_type_shape(im)
    pilbuf = dict(imdata.unsafe_ptrs)
    if pilbuf.get('pixel32', 0) != 0:
        pixel_advance = 4
        if shape[-1] == 3:
            if padding_channel == 'passthrough':
                shape = (shape[0], shape[1], 4)
            elif padding_channel == 'stride':
                pass
            elif padding_channel == 'copy_remove':
                if not allow_copy:
                    raise ValueError('cannot remove padding channel without copying')
                make_copy = True
            else:
                raise ValueError('invalid padding_channel')
    elif im.mode == 'LA':
        pixel_advance = 2
    else:
        pixel_advance = 1
    # examine if we can represent the PIL-style buffer as an numpy-style buffer (fixed stride)
    line_ptrs = np.asarray(_ArrayInterfaceForPointer(pilbuf['image'], (im.height,), _ptrtypestr, owner_object=imdata))
    pil_strides = np.diff(line_ptrs)
    if np.all(pil_strides == pil_strides[0]):
        # found fixed stride, construct numpy array interface
        data = (line_ptrs[0], False)
        arr_strides = (pil_strides[0], pixel_advance, 1) if pixel_advance > 1 else (pil_strides[0], 1)
        array_intf = {
            'version': 3,
            'shape': shape,
            'typestr': typestr,
            'strides': arr_strides,
            'data': data,
        }
        result = np.asarray(_ArrayInterfaceForObject(array_intf, imdata))
        if make_copy:
            result = result.copy()
        return result
    elif allow_copy:
        # the PIL buffer cannot fit in numpy layout, so we need to copy it
        if pixel_advance == 4 and shape[-1] == 3:
            arr_strides = (4,1)
        else:
            arr_strides = None
        # use ndarray for writable buffer
        return np.concatenate([np.asarray(_ArrayInterfaceForPointer(p, shape[1:], typestr, strides=arr_strides, readonly=False, owner_object=imdata)) for p in line_ptrs])
    raise ValueError('this PIL buffer cannot be represented as a numpy array')



# def asarray(im: Image.Image, hide_padding_channel=True):
#     """
#     Return a ndarray that shares the underlying buffer with the given image.

#     NOTE: For 3-channel modes (RGB, HSV, YCbCr, LAB), the returned array has stride in pixel axis, which is not supported by OpenCV.
#     """
#     return np.asarray(_ArrayInterfaceForObject(_pil_array_interface(im), im.getdata()))


