import ctypes
from rotypes import GUID, REFGUID, HRESULT
import json
from rotypes.inspectable import CoTaskMemFree

HCN_NETWORK = ctypes.c_void_p
HCN_ENDPOINT = ctypes.c_void_p

computenetwork = ctypes.windll.computenetwork

HcnEnumerateNetworks = computenetwork.HcnEnumerateNetworks
HcnEnumerateNetworks.argtypes = (ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_wchar_p), ctypes.POINTER(ctypes.c_wchar_p))
HcnEnumerateNetworks.restype = HRESULT

HcnOpenNetwork = computenetwork.HcnOpenNetwork
HcnOpenNetwork.argtypes = (REFGUID, ctypes.POINTER(HCN_NETWORK), ctypes.POINTER(ctypes.c_wchar_p))
HcnOpenNetwork.restype = HRESULT

HcnQueryNetworkProperties = computenetwork.HcnQueryNetworkProperties
HcnQueryNetworkProperties.argtypes = (HCN_NETWORK , ctypes.c_void_p, ctypes.POINTER(ctypes.c_wchar_p), ctypes.POINTER(ctypes.c_wchar_p))
HcnQueryNetworkProperties.restype = HRESULT

HcnCloseNetwork = computenetwork.HcnCloseNetwork
HcnCloseNetwork.argtypes = (HCN_NETWORK,)
HcnCloseNetwork.restype = HRESULT

HcnEnumerateEndpoints = computenetwork.HcnEnumerateEndpoints
HcnEnumerateEndpoints.argtypes = (ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_wchar_p), ctypes.POINTER(ctypes.c_wchar_p))
HcnEnumerateEndpoints.restype = HRESULT

HcnOpenEndpoint = computenetwork.HcnOpenEndpoint
HcnOpenEndpoint.argtypes = (REFGUID, ctypes.POINTER(HCN_ENDPOINT), ctypes.POINTER(ctypes.c_wchar_p))
HcnOpenEndpoint.restype = HRESULT

HcnQueryEndpointProperties = computenetwork.HcnQueryEndpointProperties
HcnQueryEndpointProperties.argtypes = (HCN_ENDPOINT , ctypes.c_void_p, ctypes.POINTER(ctypes.c_wchar_p), ctypes.POINTER(ctypes.c_wchar_p))
HcnQueryEndpointProperties.restype = HRESULT

HcnCloseEndpoint = computenetwork.HcnCloseEndpoint
HcnCloseEndpoint.argtypes = (HCN_ENDPOINT,)
HcnCloseEndpoint.restype = HRESULT

def enum_endpoints():
    response = ctypes.c_void_p()
    try:
        HcnEnumerateEndpoints(None, ctypes.byref(response), None)
        return json.loads(ctypes.wstring_at(response))
    finally:
        if response.value:
            CoTaskMemFree(response)

def query_endpoint(ep_guid: str) -> dict:
    handle = HCN_ENDPOINT()
    guid = GUID(ep_guid)
    response = ctypes.c_void_p()
    HcnOpenEndpoint(ctypes.byref(guid), ctypes.byref(handle), None)
    try:
        HcnQueryEndpointProperties(handle, "", ctypes.byref(response), None)
        jdoc = ctypes.wstring_at(response)
        return json.loads(jdoc)
    finally:
        if handle.value:
            HcnCloseEndpoint(handle)
        if response.value:
            CoTaskMemFree(response)

def dump_endpoints_state() -> dict[str, dict]:
    return {ep_guid: query_endpoint(ep_guid) for ep_guid in enum_endpoints()}
