from imgreco import resources
import numpy as np
from util import cvimage as Image


icon_size = (36, 36)
normal_icons = {}
dark_icons = {}

def populate():
    dirs, files = resources.get_entries('riic/bskill')
    for file in files:
        if file.endswith('.png'):
            name = file[:-4]
            im = resources.load_image('riic/bskill/'+file, 'RGBA')
            if im.size != icon_size:
                im = im.resize(icon_size, Image.BILINEAR)
            background = np.full((im.height, im.width, 3), 32)
            alpha = im.array[..., 3] / 255.0
            normal_blend = (im.array[..., 0:3] * alpha[..., np.newaxis] + (1-alpha[..., np.newaxis]) * background).astype(np.uint8)
            alpha = alpha / 2.0
            dark_blend = (im.array[..., 0:3] * alpha[..., np.newaxis] + (1-alpha[..., np.newaxis]) * background).astype(np.uint8)

            normal_icons[name] = Image.fromarray(normal_blend, 'RGB')
            dark_icons[name] = Image.fromarray(dark_blend, 'RGB')

populate()
