from . import resources
from PIL import ImageCms
p3_profile = ImageCms.ImageCmsProfile(resources.open_file('DisplayP3.icm'))
srgb_profile = ImageCms.createProfile('sRGB')


# numpy is slower than ImageCms (LittleCMS)


# import numpy as np

# denorm8 = np.arange(256, dtype=np.float32) / 255
# denorm_degamma8 = np.piecewise(denorm8, [denorm8 <= 0.04045, denorm8 > 0.04045], [lambda x: x / 12.92, lambda x: ((x + 0.055) / 1.055) ** 2.4])
# norm10 = np.arange(1024, dtype=np.float32) / 1023
# regamma10 = np.piecewise(norm10, [norm10 <= 0.0031308, norm10 > 0.0031308], [lambda x: x * 12.92, lambda x: 1.055 * (x ** (1.0 / 2.4)) - 0.055])
# regamma10_norm8 = np.round(regamma10 * 255).astype(np.uint8)

# def matrix_for_primaries(red, green, blue, white):
#     Yxy = np.array([(1, *red), (1, *green), (1, *blue), (1, *white)], dtype=np.float32)
#     x = Yxy[:, 1]
#     y = Yxy[:, 2]
#     X = x / y
#     Z = (1 - x - y) / y
#     XYZ = np.array([X, Yxy[:, 0], Z])
#     S = np.linalg.inv(XYZ[..., :3]) @ XYZ[..., 3]
#     M = S * XYZ[..., :3]
#     return M

# M_srgb_to_xyz = matrix_for_primaries((0.64, 0.33), (0.3, 0.6), (0.15, 0.06), (0.3127, 0.3290))
# M_xyz_to_srgb = np.linalg.inv(M_srgb_to_xyz)
# M_p3_to_xyz = matrix_for_primaries((0.680, 0.320), (0.265, 0.690), (0.150, 0.060), (0.3127, 0.3290))
# M_p3_to_srgb = M_xyz_to_srgb @ M_p3_to_xyz

# def p3_to_srgb(img):
#     if img.dtype == np.uint8:
#         gamma_p3 = None  # flag to use fast denorm&degamma LUT
#     elif np.issubdtype(img.dtype, np.integer):
#         gamma_p3 = img / np.float32(np.iinfo(img.dtype).max)
#     elif np.issubdtype(img.dtype, np.floating):
#         gamma_p3 = img
#     if gamma_p3 is None:
#         linear_p3 = denorm_degamma8[img]
#     else:
#         linear_p3 = np.piecewise(gamma_p3, [gamma_p3 <= 0.04045, gamma_p3 > 0.04045], [lambda x: x / 12.92, lambda x: ((x + 0.055) / 1.055) ** 2.4])
#     linear_srgb = np.asarray(M_p3_to_srgb @ linear_p3.reshape(-1, 3, 1)).reshape(img.shape)
#     # normalize to uint10 and apply gamma LUT
#     linear_srgb_uint10 = np.round(np.clip(linear_srgb, 0, 1, out=linear_srgb) * 1023).astype(np.uint16)
#     # uint8_srgb = np.round(np.clip(gamma_srgb, 0, 1, out=gamma_srgb) * 255).astype(np.uint8)
#     gamma_srgb_uint8 = regamma10_norm8[linear_srgb_uint10]
#     return gamma_srgb_uint8


# def _test():
#     print(repr(M_p3_to_srgb))
#     import cv2
#     import time
#     im = cv2.imread(r"D:\staging\p3screen.png", cv2.IMREAD_COLOR)  # opencv will discard icc profile
#     im = cv2.cvtColor(im, cv2.COLOR_RGBA2BGR)
#     t0 = time.perf_counter()
#     im = p3_to_srgb(im)
#     t1 = time.perf_counter()
#     print('numpy:', t1 - t0)
#     # im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
#     # cv2.imshow('srgb', im)
#     # cv2.waitKey()
#     # cv2.destroyAllWindows()
#     from PIL import Image, ImageCms
#     from io import BytesIO
#     img = Image.open(r"D:\staging\p3screen.png")
#     if icc := img.info.get('icc_profile', ''):
#         iccio = BytesIO(icc)
#         src_profile = ImageCms.ImageCmsProfile(iccio)
#         dst_profile = ImageCms.createProfile('sRGB')
#         t0 = time.perf_counter()
#         img = ImageCms.profileToProfile(img, src_profile, dst_profile, ImageCms.INTENT_RELATIVE_COLORIMETRIC)
#         t1 = time.perf_counter()
#         print('PIL.ImageCms:', t1 - t0)
#     img.show()


# if __name__ == '__main__':
#     _test()