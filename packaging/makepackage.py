import sys
import os
import runpy
import PyInstaller.__main__
import shutil

def main():
    sys._using_makepackage = True

    dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
    scmver = runpy.run_path(os.path.join(dir, 'config', 'scm_version.py'))

    version = scmver['version']
    print('version:', version)
    
    with open(os.path.join(os.path.dirname(__file__), '..', 'config', 'release_info.py'), 'w') as f:
        f.write('version = %r\n' % version)

    print('archiving resources')
    shutil.rmtree(os.path.join(dir, 'resources', '__pycache__'), ignore_errors=True)
    shutil.make_archive(os.path.join(dir, 'resources'), 'zip', dir, 'resources')

    print('calling PyInstaller')
    PyInstaller.__main__.run([os.path.join(os.path.dirname(__file__), '..', 'akhelper.spec'), '--noconfirm', *sys.argv[1:]])

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