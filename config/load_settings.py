import json
import os

globals().update(json.load(
    open("settings.json"), encoding="utf8",
))
