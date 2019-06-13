import json

globals().update(json.load(
    open("settings.json"), encoding="utf8",
))
