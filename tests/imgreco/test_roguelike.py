import unittest

from imgreco.roguelike import RoguelikeOCR
from util import cvimage as Image
import os


def load_image(file):
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, f'../resources/imgreco/roguelike/{file}')
    return filename


class RoguelikeOCRTest(unittest.TestCase):

    def setUp(self) -> None:
        self.ocr = RoguelikeOCR()

    def test_check_battle(self):
        screenshot = Image.open(load_image("battle.png")).convert('RGB')
        w, h = screenshot.width, screenshot.height
        subarea = (0, h * 0.2, w, h * 0.8)
        screenshot = screenshot.crop(subarea)
        result = self.ocr.check_current_stage(screenshot)
        self.assertEqual(result, 1)

        screenshot = Image.open(load_image("battle2.png")).convert('RGB')
        screenshot = screenshot.crop(subarea)
        result = self.ocr.check_current_stage(screenshot)
        self.assertEqual(result, 1)

    def test_check_accident(self):
        screenshot = Image.open(load_image("accident.png")).convert('RGB')
        w, h = screenshot.width, screenshot.height
        subarea = (0, h * 0.2, w, h * 0.8)
        screenshot = screenshot.crop(subarea)
        result = self.ocr.check_current_stage(screenshot)
        self.assertEqual(result, 2)

    def test_check_interlude(self):
        screenshot = Image.open(load_image("interlude.png")).convert('RGB')
        w, h = screenshot.width, screenshot.height
        subarea = (0, h * 0.2, w, h * 0.8)
        screenshot = screenshot.crop(subarea)
        result = self.ocr.check_current_stage(screenshot)
        self.assertEqual(result, 3)

    def test_troop(self):
        screenshot = Image.open(load_image("mountain_troop.png")).convert('RGB')
        self.assertFalse(self.ocr.check_mountain_exist_in_troop(screenshot))

        screenshot = Image.open(load_image("mountain_troop2.png")).convert('RGB')
        self.assertTrue(self.ocr.check_mountain_exist_in_troop(screenshot))
