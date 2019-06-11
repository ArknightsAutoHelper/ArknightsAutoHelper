import json

globals().update(json.load(
    open("Arknights/click_location/location.json", encoding="utf8"))
)
