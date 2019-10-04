import logging

import requests

import config
from . import model


logger = logging.getLogger('PenguinReporter')

stages = model.StageModel(())
items = model.ItemModel(())
constraints = model.ValidationModel(())

session = requests.Session()

def load_from_service():
    global stages, items, constraints

    resp = session.get('https://penguin-stats.io/PenguinStats/api/items')
    resp.raise_for_status()
    items = model.ItemModel(resp.json())

    resp = session.get('https://penguin-stats.io/PenguinStats/api/stages')
    resp.raise_for_status()
    stages = model.StageModel(resp.json())

    resp = session.get('https://penguin-stats.io/PenguinStats/api/limitations')
    resp.raise_for_status()
    constraints = model.ValidationModel(resp.json())

def user_login():
    uid = config.get('reporting/penguin_stats_uid', None)
    if uid is None:
        return
    resp = session.post('https://penguin-stats.io/PenguinStats/api/users',
                        headers={'Content-Type': 'text/plain'},
                        data=str(uid).encode())
    # now we have cookie stored in session
    return bool(resp)
