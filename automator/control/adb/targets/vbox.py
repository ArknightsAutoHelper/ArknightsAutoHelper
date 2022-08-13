from dataclasses import dataclass
import sys
import logging
logger = logging.getLogger(__name__)

def enum():
    return []

@dataclass
class VBoxClass:
    clsid: str
    vendor: str
    tag: str

@dataclass
class VBoxSerever(VBoxClass):
    path: str
    pid: int = 0

def _init_win32():
    try:
        import util.dummy_gencache
        import win32com.client
    except ImportError:
        logger.debug('pywin32 not installed, disabling vbox enumerator')
        return

    import ctypes
    vbox_clsids = [
        VBoxClass('{20190809-47b9-4a1e-82b2-07ccd5323c3f}', 'LDPlayer', 'ld'),
        VBoxClass('{20191216-47b9-4a1e-82b2-07ccd5323c3f}', 'LDPlayer9', 'ld9'),
        VBoxClass('{88888888-47b9-4a1e-82b2-07ccd5323c3f}', 'Nox', 'nox'),
        VBoxClass('{baf3f651-58d8-429d-97ad-2b5699b43567}', 'BlueStacks', 'bstk'),
        VBoxClass('{b1a7a4f2-47b9-4a1e-82b2-07ccd5323c3a}', 'Memu', 'memu'),
        VBoxClass('{81919390-a492-11e5-a837-0800200c9a66}', 'MuMu', 'mumu'),
        # ('{B1A7A4F2-47B9-4A1E-82B2-07CCD5323C3F}', 'Oracle', 'oracle'),  # nobody uses this
    ]

    OpenProcess = ctypes.windll.kernel32.OpenProcess
    OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_bool, ctypes.c_uint32]
    OpenProcess.restype = ctypes.c_void_p
    PROCESS_QUERY_INFORMATION = 0x0400
    CloseHandle = ctypes.windll.kernel32.CloseHandle
    CloseHandle.argtypes = [ctypes.c_void_p]

    import winreg
    from util import win32_process

    def get_server(clsid):
        try:
            with winreg.OpenKeyEx(winreg.HKEY_CLASSES_ROOT, 'CLSID\\%s\\LocalServer32' % clsid, 0, winreg.KEY_READ) as hkey:
                value = winreg.QueryValue(hkey, None)
                filename = value.strip('"')
                return win32_process.get_final_path(filename)
        except OSError:
            return None

    global enum
    def enum():
        from automator.control.adb.client import get_config_adb_server
        from automator.control.adb.target import ADBControllerTarget
        adb_server = get_config_adb_server()
        logger.debug('enumerating vbox targets')
        vbox_servers: list[VBoxSerever] = []
        for vboxcls in vbox_clsids:
            server = get_server(vboxcls.clsid)
            if server:
                vbox_servers.append(VBoxSerever(vboxcls.clsid, vboxcls.vendor, vboxcls.tag, server))

        logger.debug('installed VirtualBox servers: %r', vbox_servers)

        running_processes = {pid: win32_process.resolve_image_name(pid) for pid in win32_process.all_pids()}
        for pid, path in running_processes.items():
            for vbox_server in vbox_servers:
                if vbox_server.path == path:
                    vbox_server.pid = pid
                    break
        running_servers = [x for x in vbox_servers if x.pid]
        # running_servers = [x for x in vbox_servers if x[3] in running_processes]

        logger.debug('running VirtualBox servers: %r', running_servers)
        results = []
        for server in running_servers:
            logger.debug('checking %r', server)
            hproc = OpenProcess(PROCESS_QUERY_INFORMATION, False, server.pid)
            if not hproc:
                logger.debug('try OpenProcess failed for PID %d, skipping', server.pid)
                continue
            CloseHandle(hproc)
            try:
                client = win32com.client.Dispatch(server.clsid)
                for machine in client.Machines:
                    machine_name = machine.Name
                    logger.debug('checking machine %s', machine_name)
                    if not machine.State == 5:
                        # machine is not running
                        continue
                    for adapter_id in range(4):
                        adapter = machine.GetNetworkAdapter(adapter_id)
                        if adapter.Enabled and adapter.AttachmentType == 1:
                            # adapter is enabled and attached to per-machine NAT
                            forwards = adapter.NatEngine.Redirects
                            for forward in forwards:
                                rule_name, proto, host, port, guest_host, guest_port = forward.split(',', 5)
                                if proto == '1' and guest_port == '5555':
                                    address = f'127.0.0.1:{port}'
                                    identifier = f'vbox:{server.tag}:{machine_name}'
                                    results.append(ADBControllerTarget(adb_server, None, f'{server.vendor}: {machine_name}', address, 2, 1, override_identifier=identifier, preload_device_info={'emulator_hypervisor': 'vbox'}))
            except:
                logger.debug('failed to check server %r, skipping', server, exc_info=True)
        return results


if sys.platform == 'win32':
    _init_win32()

def _main():
    import logging
    logging.basicConfig(level=logging.DEBUG, force=True)
    for x in enum():
        print(x)

if __name__ == '__main__':
    _main()
