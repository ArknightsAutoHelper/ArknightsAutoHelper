import sys
import os
import runpy
import shutil
import subprocess
import argparse

import PyInstaller.__main__

def main():
    argv = sys.argv[1:]
    suffix = ''
    skip_zipball = False
    while len(argv) > 0 and argv[0].startswith('-'):
        opt = argv.pop(0)
        if opt == '--version-suffix':
            suffix = argv.pop(0)
            continue
        elif opt == '--skip-zipball':
            skip_zipball = True
            continue
        elif opt == '--help' or opt == '-h':
            print('usage: %s [--version-suffix SUFFIX] [--skip-zipball] [--] [PyInstaller extra args ...]' % sys.argv[0])
            return
        elif opt == '--':
            break
        else:
            print('unknown option: ' + opt)
            return


    sys._using_makepackage = True

    dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
    scmver = runpy.run_path(os.path.join(dir, 'config', 'scm_version.py'))

    version = scmver['version'] + suffix
    print('version:', version)
    
    with open(os.path.join(os.path.dirname(__file__), '..', 'config', 'release_info.py'), 'w') as f:
        f.write('version = %r\n' % version)

    print('archiving resources')
    stash_id = subprocess.run(['git', 'stash', 'create', 'stashed by makepackage'], capture_output=True, check=True).stdout.decode().strip()
    subprocess.run(['git', 'archive', '-o', 'resources.zip', stash_id or 'HEAD', 'resources'], check=True)

    print('calling PyInstaller')
    PyInstaller.__main__.run([os.path.join(os.path.dirname(__file__), '..', 'akhelper.spec'), '--noconfirm', *argv])

    if skip_zipball:
        return

    print('making archive')

    # monkey-patching ZipFile to use LZMA compression with shutil.make_archive
    import zipfile
    orig_ZipFile = zipfile.ZipFile

    def new_ZipFile(*args, **kwargs):
        if 'compression' in kwargs:
            kwargs['compression'] = zipfile.ZIP_LZMA
        return orig_ZipFile(*args, **kwargs)

    zipfile.ZipFile = new_ZipFile

    distdir = os.path.join(dir, 'dist')
    archive = os.path.join(distdir, 'akhelper')
    zipball = shutil.make_archive(archive, 'zip', distdir, 'akhelper')
    print('zipball:', zipball)

if __name__ == '__main__':
    main()