import urllib.request as _victim

_old_getproxies = _victim.getproxies

def _hook_getporxies():
    result = _old_getproxies()
    if 'https' in result and 'http' in result:
        https_proxy = result['https']
        http_proxy = result['http']
        if https_proxy.startswith('https://') and https_proxy[8:] in http_proxy:
            # if we have both http_proxy and https_proxy, and https_proxy looks
            # like http_proxy but with https scheme, we assume it can't handle 
            # inbound TLS connections and replace it with http_proxy
            result['https'] = http_proxy
    return result

_victim.getproxies = _hook_getporxies
