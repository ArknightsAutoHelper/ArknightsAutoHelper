"""
get version from git working tree
"""
import os
import subprocess

version = os.environ.get('_AAH_SCM_VERSION_CACHE', None)
if version is None:
    try:
        _dir = os.path.dirname(__file__)
        _CREATE_NO_WINDOW = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
        branch = subprocess.check_output(('git', 'rev-parse', '--abbrev-ref', 'HEAD'), cwd=_dir, creationflags=_CREATE_NO_WINDOW).strip()
        _description = subprocess.check_output(['git', 'describe', '--tags', '--always', '--dirty'], cwd=_dir, creationflags=_CREATE_NO_WINDOW).strip()

        version = (b'%b+%b' % (branch, _description)).decode()
    except:
        version = 'UNKNOWN'
    os.environ['_AAH_SCM_VERSION_CACHE'] = version
