import json

globals().update(json.load(
    open("GUI/Settings/gui_settings.json", encoding="utf8"))
)
