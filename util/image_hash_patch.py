import builtins
from PIL import Image

Image.Image.__hash__ = lambda self: builtins.id(self)
