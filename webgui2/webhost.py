
def find_chromium():
    import shutil
    import platform
    import os
    uname = platform.system()
    if uname == 'Windows':
        executables = ['chrome.exe', 'msedge.exe']
        prefixes = [
            os.getenv('ProgramFiles', os.devnull),
            os.getenv('ProgramFiles(X86)', os.devnull),
            os.getenv('LOCALAPPDATA', os.devnull),
        ]
        suffixes = [
            os.path.join('Google', 'Chrome', 'Application', 'chrome.exe'),
            os.path.join('Chromium', 'Application', 'chrome.exe'),
            os.path.join('Microsoft', 'Edge', 'Application', 'msedge.exe'),
        ]
    elif uname == 'Linux':
        executables = ['google-chrome-stable', 'google-chrome-beta', 'google-chrome-unstable', 'chromium-browser', 'chromium', 'microsoft-edge', 'microsoft-edge-dev']
        prefixes = []
        suffixes = []
    elif uname == 'Darwin':
        # TODO
        return None
    else:
        return None
    
    for executable in executables:
        if shutil.which(executable):
            return executable
    import os
    for suffix in suffixes:
        for prefix in prefixes:
            path = os.path.join(prefix, suffix)
            if shutil.which(path):
                return path
    return None

def check_webview2():
    import os
    if os.name != 'nt':
        return None
    try:
        import webview
    except ImportError:
        return None
    import sys
    import winreg
    is64bit = sys.maxsize > 0xFFFFFFFF
    subkey = "SOFTWARE\\"
    if sys.maxsize > 0xFFFFFFFF:
        subkey += "WOW6432Node\\"
    subkey += "Microsoft\\EdgeUpdate\\Clients\\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
    for rootkey in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
        hkey = None
        try:
            with winreg.OpenKey(rootkey, subkey) as hkey:
                val, valtype = winreg.QueryValueEx(hkey, "pv")
                if valtype == winreg.REG_SZ:
                    return val
        except OSError:
            pass
    return None
    
class WebHostWebView:
    def start(self, url, width=None, height=None):
        if [width, height].count(None) == 1:
            raise ValueError("width and height")
        import app
        import multiprocessing
        from . import webview_launcher
        self.p = multiprocessing.Process(target=webview_launcher.launch, args=[url, width, height, app.get('webgui/webview_backend', None)])
        self.p.start()
        self.wait_handle = self.p.join

class WebHostChromePWA:
    def __init__(self, exe):
        self.exe = exe
    def start(self, url, width, height):
        if [width, height].count(None) == 1:
            raise ValueError("width and height")
        import subprocess
        import os
        import app
        data_dir = app.cache_path.joinpath("akhelper-gui-datadir")
        cmd = [self.exe, '--chrome-frame', '--app='+url, '--user-data-dir='+os.fspath(data_dir), '--disable-plugins', '--disable-extensions']
        if width is not None:
            cmd.append('--window-size=%d,%d' % (width, height))
        subprocess.Popen(cmd)
        self.wait_handle = None
        self.poll_interval = 10

class WebHostBrowser:
    def start(self, url, width=None, height=None):
        import webbrowser
        webbrowser.open_new(url)
        self.wait_handle = None
        self.poll_interval = 60

def auto_host():
    import platform
    uname = platform.system()
    if uname == 'Windows':
        if check_webview2():
            return WebHostWebView()
        elif exe := find_chromium():
            return WebHostChromePWA(exe)
        else:
            return WebHostBrowser()
    elif uname == 'Linux':
        try:
            import webview.platforms.gtk
            return WebHostWebView()
        except:
            pass
        if exe := find_chromium():
            return WebHostChromePWA(exe)
        else:
            return WebHostBrowser()
    elif uname == 'Darwin':
        return WebHostWebView()
    else:
        return WebHostBrowser()

def get_host():
    import app
    name = app.get('webgui/host', None)
    if name is None:
        return auto_host()
    elif name == 'chrome_pwa':
        exe = app.get('webgui/chrome_bin', None)
        if exe is None:
            exe = find_chromium()
        if exe is None:
            raise RuntimeError("no compatible browser executable found")
        return WebHostChromePWA(exe)
    elif name == 'webview':
        return WebHostWebView()
    else:
        raise KeyError(name)

if __name__ == '__main__':
    print(find_chromium())
