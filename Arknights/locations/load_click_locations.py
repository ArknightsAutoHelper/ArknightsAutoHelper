import json

globals().update(json.load(
    open("Arknights/locations/location.json", encoding="utf8"))
)
