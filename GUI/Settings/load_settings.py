import json


def load_settings():
    globals().update(json.load(
        open("D:\python_box\shaobao_adb\GUI\Settings\default_setting.json"), encoding="utf8",
    ))
