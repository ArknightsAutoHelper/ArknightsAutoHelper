import json

globals().update(json.load(
    open("./config/default_setting.json"), encoding="utf8",
))
