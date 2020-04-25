"""
get version from git working tree

FIXME: replace with hardcoded value for release
"""
import os
import subprocess

try:
    _dir = os.path.dirname(__file__)
    branch = subprocess.check_output(('git', 'rev-parse', '--abbrev-ref', 'HEAD'), cwd=_dir).strip()
    _description = subprocess.check_output(['git', 'describe', '--always', '--dirty'], cwd=_dir).strip()

    version = (b'%b+%b' % (branch, _description)).decode()
except:
    version = 'UNKNOWN'
