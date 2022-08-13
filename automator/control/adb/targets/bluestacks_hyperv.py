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
    from rotypes.inspectable import CoTaskMemFree

    HCS_SYSTEM = ctypes.POINTER(ctypes.c_void_p)

    vmcompute = ctypes.windll.vmcompute
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

    def enum_compute_system(query: dict):
        response = ctypes.c_wchar_p()
        try:
            HcsEnumerateComputeSystems(json.dumps(query), ctypes.byref(response), None)
            return json.loads(ctypes.wstring_at(response))
        finally:
            if response.value:
                CoTaskMemFree(response) 

    def dump_endpoints():
        try:
            from .hnsapi import dump_endpoints_state
            return dump_endpoints_state()
        except Exception:
            logger.debug('HNS API failed, trying read registry directly')
            from .hnsdump import dump_endpoints_state
            return dump_endpoints_state()

    global enum
    def enum():
        from automator.control.adb.client import get_config_adb_server
        server = get_config_adb_server()
        devices = []
        with contextlib.suppress(Exception):
            runningsystems = enum_compute_system({"State":"Running"})
            logger.debug("running compute systems: %r", runningsystems)
            if not runningsystems:
                logger.debug("no running compute systems, skipping")
                return []
            runningids = [GUID(x['RuntimeId']) for x in runningsystems]
            
            endpoints = dump_endpoints()

            for guidstr, obj in endpoints.items():
                logger.debug("probing endpoint %s", guidstr)
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

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, force=True)
    devices = enum()
    from pprint import pprint
    pprint(devices)
