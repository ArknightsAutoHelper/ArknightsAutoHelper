import app
import requests
import requests_cache
import json
import datetime
import time

session = requests_cache.CachedSession(str(app.cache_path / 'gamedata'), backend='filesystem', cache_control=True)

baseurl = 'https://gh.cirno.xyz/raw.githubusercontent.com/Kengxxiao/ArknightsGameData/master/zh_CN/gamedata/excel/'

_gamedata_version = ''
_last_check = time.time() - 300
_cached_tables = {}

def ensure_table_cache_version():
    global _last_check
    if time.time() - _last_check < 300:
        return
    global _gamedata_version
    resp = session.get(baseurl + 'data_version.txt', expire_after=-1)
    cache_version = None
    try:
        with open(app.cache_path / 'local_gamedata_version.txt', 'rb') as f:
            cache_version = f.read()
    except:
        pass
    if resp.content != cache_version:
        session.cache.clear()
    with open(app.cache_path / 'local_gamedata_version.txt', 'wb') as f:
        f.write(resp.content)
    _gamedata_version = resp.content.decode('utf-8')
    _cached_tables.clear()
    _last_check = time.time()


def get_version() -> str:
    ensure_table_cache_version()
    return _gamedata_version


def load_table(table_name: str):
    ensure_table_cache_version()
    cached = _cached_tables.get(table_name, None)
    if cached is not None:
        return cached
    table_url = baseurl + table_name + '.json'
    # fetch from cache only since we ensured data_version
    req = requests.Request('GET', table_url).prepare()
    key = requests_cache.cache_keys.create_key(req)
    resp = session.cache.get_response(key)
    # not cached, fetch from remote
    if resp is None:
        resp = session.send(req, expire_after=-1)
        resp.raise_for_status()
    table = json.loads(resp.content)
    _cached_tables[table_name] = table
    return table
