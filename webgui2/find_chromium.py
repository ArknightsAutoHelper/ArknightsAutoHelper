
def find_chromium_windows():
    import shutil

    executables = ['chrome.exe', 'msedge.exe']
    for executable in executables:
        if shutil.which(executable):
            return executable

    import os
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

    for suffix in suffixes:
        for prefix in prefixes:
            path = os.path.join(prefix, suffix)
            if shutil.which(path):
                return path
    return None

if __name__ == '__main__':
    print(find_chromium_windows())
