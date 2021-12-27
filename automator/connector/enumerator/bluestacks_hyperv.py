import contextlib
import ctypes
from rotypes.types import GUID, REFGUID, check_hresult
import json
# import pprint
import logging
from ..ADBConnector import ADBConnector

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logger.addHandler(logging.StreamHandler(__import__('sys').stderr))
    logger.setLevel(logging.DEBUG)


try:
    HCS_SYSTEM = ctypes.POINTER(ctypes.c_void_p)
    HCN_NETWORK = ctypes.POINTER(ctypes.c_void_p)
    HCN_ENDPOINT = ctypes.POINTER(ctypes.c_void_p)

    vmcompute = ctypes.windll.vmcompute
    computenetwork = ctypes.windll.computenetwork

    CoTaskMemFree = ctypes.windll.ole32.CoTaskMemFree
    CoTaskMemFree.argtypes = (ctypes.c_void_p,)

    HcsEnumerateComputeSystems = vmcompute.HcsEnumerateComputeSystems
    HcsEnumerateComputeSystems.argtypes = (ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_wchar_p), ctypes.POINTER(ctypes.c_wchar_p))
    HcsEnumerateComputeSystems.restype = check_hresult

    HcsOpenComputeSystem = vmcompute.HcsOpenComputeSystem
    HcsOpenComputeSystem.argtypes = (ctypes.c_wchar_p, ctypes.POINTER(HCS_SYSTEM), ctypes.POINTER(ctypes.c_wchar_p))
    HcsOpenComputeSystem.restype = check_hresult

    HcsGetComputeSystemProperties = vmcompute.HcsGetComputeSystemProperties
    HcsGetComputeSystemProperties.argtypes = (HCS_SYSTEM , ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_wchar_p), ctypes.POINTER(ctypes.c_wchar_p))
    HcsGetComputeSystemProperties.restype = check_hresult

    HcsCloseComputeSystem = vmcompute.HcsCloseComputeSystem
    HcsCloseComputeSystem.argtypes = (HCS_SYSTEM,)
    HcsCloseComputeSystem.restype = check_hresult

    HcnEnumerateNetworks = computenetwork.HcnEnumerateNetworks
    HcnEnumerateNetworks.argtypes = (ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_wchar_p), ctypes.POINTER(ctypes.c_wchar_p))
    HcnEnumerateNetworks.restype = check_hresult

    HcnOpenNetwork = computenetwork.HcnOpenNetwork
    HcnOpenNetwork.argtypes = (REFGUID, ctypes.POINTER(HCN_NETWORK), ctypes.POINTER(ctypes.c_wchar_p))
    HcnOpenNetwork.restype = check_hresult

    HcnQueryNetworkProperties = computenetwork.HcnQueryNetworkProperties
    HcnQueryNetworkProperties.argtypes = (HCN_NETWORK , ctypes.c_void_p, ctypes.POINTER(ctypes.c_wchar_p), ctypes.POINTER(ctypes.c_wchar_p))
    HcnQueryNetworkProperties.restype = check_hresult

    HcnCloseNetwork = computenetwork.HcnCloseNetwork
    HcnCloseNetwork.argtypes = (HCN_NETWORK,)
    HcnCloseNetwork.restype = check_hresult

    HcnEnumerateEndpoints = computenetwork.HcnEnumerateEndpoints
    HcnEnumerateEndpoints.argtypes = (ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_wchar_p), ctypes.POINTER(ctypes.c_wchar_p))
    HcnEnumerateEndpoints.restype = check_hresult

    HcnOpenEndpoint = computenetwork.HcnOpenEndpoint
    HcnOpenEndpoint.argtypes = (REFGUID, ctypes.POINTER(HCN_ENDPOINT), ctypes.POINTER(ctypes.c_wchar_p))
    HcnOpenEndpoint.restype = check_hresult

    HcnQueryEndpointProperties = computenetwork.HcnQueryEndpointProperties
    HcnQueryEndpointProperties.argtypes = (HCN_ENDPOINT , ctypes.c_void_p, ctypes.POINTER(ctypes.c_wchar_p), ctypes.POINTER(ctypes.c_wchar_p))
    HcnQueryEndpointProperties.restype = check_hresult

    HcnCloseEndpoint = computenetwork.HcnCloseEndpoint
    HcnCloseEndpoint.argtypes = (HCN_ENDPOINT,)
    HcnCloseEndpoint.restype = check_hresult
    availiable = True
except Exception as e:
    logger.info("HCN API not availiable")
    availiable = False

if availiable:
    from .append import compare_adb_serial
    def enum(devices):
        with contextlib.nullcontext():
            response = ctypes.c_wchar_p()
            HcsEnumerateComputeSystems('{"State":"Running"}', ctypes.byref(response), None)
            runningsystems = json.loads(ctypes.wstring_at(response))
            CoTaskMemFree(response)
            logger.debug("running compute systems: %r", runningsystems)
            if not runningsystems:
                logger.debug("no running compute systems, skipping")
                return
            runningids = [GUID(x['RuntimeId']) for x in runningsystems]
            
            HcnEnumerateEndpoints(None, ctypes.byref(response), None)
            endpoints = json.loads(ctypes.wstring_at(response))
            CoTaskMemFree(response)
            logger.debug("endpoints: %r", endpoints)

            for guidstr in endpoints:
                logger.debug("probing endpoint %s", guidstr)
                guid = GUID(guidstr)
                nethandle = HCN_NETWORK()
                HcnOpenEndpoint(ctypes.byref(guid), ctypes.byref(nethandle), None)
                response = ctypes.c_wchar_p()
                HcnQueryEndpointProperties(nethandle, "", ctypes.byref(response), None)
                jdoc = ctypes.wstring_at(response)
                CoTaskMemFree(response)
                obj = json.loads(jdoc)
                # print(obj)
                # logger.debug("HcnQueryEndpointProperties(%r) => %r", guid, jdoc)
                # pprint.pprint(obj)
                HcnCloseEndpoint(nethandle)
                if obj.get('VirtualNetworkName', None) not in ('BluestacksNetwork', 'BluestacksNxt'):
                    continue
                if (vmguid := GUID(obj.get("VirtualMachine"))) not in runningids:
                    continue
                if policies := obj.get("Policies", None):
                    for policy in policies:
                        if policy.get("InternalPort", None) == 5555:
                            port = policy['ExternalPort']
                            logger.debug("found bluestacks hyperv adb port %s for vm %s", port, vmguid)
                            adb_serial = '127.0.0.1:%d' % port
                            vmname = [x.get('Id') for x in runningsystems if GUID(x.get('RuntimeId')) == vmguid][0]
                            for i, defs in enumerate(devices):
                                if defs[1] is ADBConnector and len(defs[2]) == 1:
                                    if compare_adb_serial(defs[2][0], adb_serial):
                                        devices.pop(i)
                            devices.append((f'ADB: {adb_serial} (BlueStacks: {vmname})', ADBConnector, [adb_serial], 'strong'))
else:
    def enum(devices):
        pass

if __name__ == '__main__':
    devices = []
    enum(devices)
    from pprint import pprint
    pprint(devices)
