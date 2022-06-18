import sys
import logging

logger = logging.getLogger(__name__)

def enum():
    return []

def _init():
    import contextlib
    import ctypes
    import json
    # import pprint

    from automator.control.adb.target import ADBControllerTarget
    from rotypes import GUID, HRESULT
    REFGUID = ctypes.POINTER(GUID)
    HCS_SYSTEM = ctypes.POINTER(ctypes.c_void_p)
    HCN_NETWORK = ctypes.POINTER(ctypes.c_void_p)
    HCN_ENDPOINT = ctypes.POINTER(ctypes.c_void_p)

    vmcompute = ctypes.windll.vmcompute
    computenetwork = ctypes.windll.computenetwork

    CoTaskMemFree = ctypes.windll.ole32.CoTaskMemFree
    CoTaskMemFree.argtypes = (ctypes.c_void_p,)

    HcsEnumerateComputeSystems = vmcompute.HcsEnumerateComputeSystems
    HcsEnumerateComputeSystems.argtypes = (ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_wchar_p), ctypes.POINTER(ctypes.c_wchar_p))
    HcsEnumerateComputeSystems.restype = HRESULT

    HcsOpenComputeSystem = vmcompute.HcsOpenComputeSystem
    HcsOpenComputeSystem.argtypes = (ctypes.c_wchar_p, ctypes.POINTER(HCS_SYSTEM), ctypes.POINTER(ctypes.c_wchar_p))
    HcsOpenComputeSystem.restype = HRESULT

    HcsGetComputeSystemProperties = vmcompute.HcsGetComputeSystemProperties
    HcsGetComputeSystemProperties.argtypes = (HCS_SYSTEM , ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_wchar_p), ctypes.POINTER(ctypes.c_wchar_p))
    HcsGetComputeSystemProperties.restype = HRESULT

    HcsCloseComputeSystem = vmcompute.HcsCloseComputeSystem
    HcsCloseComputeSystem.argtypes = (HCS_SYSTEM,)
    HcsCloseComputeSystem.restype = HRESULT

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

    global enum
    def enum():
        from automator.control.adb.client import get_config_adb_server
        server = get_config_adb_server()
        devices = []
        with contextlib.suppress(Exception):
            response = ctypes.c_wchar_p()
            HcsEnumerateComputeSystems('{"State":"Running"}', ctypes.byref(response), None)
            runningsystems = json.loads(ctypes.wstring_at(response))
            CoTaskMemFree(response)
            logger.debug("running compute systems: %r", runningsystems)
            if not runningsystems:
                logger.debug("no running compute systems, skipping")
                return []
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
                HcnCloseEndpoint(nethandle)
                if obj.get('VirtualNetworkName', None) not in ('BluestacksNetwork', 'BluestacksNxt'):
                    continue
                if (vmguid := GUID(obj.get("VirtualMachine"))) not in runningids:
                    continue
                if policies := obj.get("Policies", None):
                    for policy in policies:
                        if policy.get("InternalPort", None) == 5555:
                            port = policy['ExternalPort']
                            vmname = [x.get('Id') for x in runningsystems if GUID(x.get('RuntimeId')) == vmguid][0]
                            logger.debug("found bluestacks hyperv adb port %s for vm %s (%s)", port, vmguid, vmname)
                            adb_address = '127.0.0.1:%d' % port
                            preload = {'emulator_hypervisor': 'hyper-v'}
                            if 'IPAddress' in obj:
                                preload['host_l2_reachable'] = obj['IPAddress']
                            devices.append(ADBControllerTarget(server, None, f'BlueStacks: {vmname}', adb_address, 2, 1, override_identifier=f'hyperv:bstk:{vmname}', preload_device_info=preload))
        return devices

if sys.platform == 'win32':
    try:
        _init()
    except Exception:
        logger.debug("failed to initialize hyper-v enumerator", exc_info=True)
        raise

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, force=True)
    devices = enum()
    from pprint import pprint
    pprint(devices)
