import json

globals().update(json.load(
    open("location.json", encoding="utf8"))
)
