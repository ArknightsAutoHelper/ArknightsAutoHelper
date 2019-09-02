# coding: utf-8

from Arknights.click_location.click_location import *

JSON_PARAMS = ['LOCATION_JSON_NAME', 'WITH_SCREEN', 'CLICK_LOCATION_INFO', 'CLICK_LOCATION', 'MAP_LOCATION',
               'SWIPE_LOCATION', 'LIZHI_CONSUME', 'BATTLE_SELECTORS', 'MAIN_TASK_CHAPTER_SWIPE',
               'MAIN_TASK_BATTLE_SWIPE', 'MAIN_TASK_SUPPORT', 'DAILY_LIST']
JSON_DATAS = {}
a = globals().copy()

for key, value in a.items():
    if key in JSON_PARAMS:
        JSON_DATAS[key] = value

name = input("please input json file name>> ")
JSON_DATAS["LOCATION_JSON_NAME"] = name.strip()
input_true = True
while input_true:
    param = input("please input screen range FORMAT('1280*720')>> ")
    try:
        assert param.split("*")[0].isnumeric() and param.split("*")[1].isnumeric()
    except Exception as e:
        print(e)
        continue
    JSON_DATAS["WITH_SCREEN"] = [param.split("*")[0], param.split("*")[1]]
    input_true = False

import json

json.dump(JSON_DATAS, open('location.json', 'w', encoding='utf8'))
