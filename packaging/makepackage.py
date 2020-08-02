import os
import runpy
import PyInstaller.__main__

def main():
    dir = os.path.join(os.path.dirname(__file__), '..')
    scmver = runpy.run_path(os.path.join(dir, 'config', 'scm_version.py'))

    version = scmver['version']
    print('version:', version)
    
    with open(os.path.join(os.path.dirname(__file__), '..', 'config', 'release_info.py'), 'w') as f:
        f.write('version = %r\n' % version)

    PyInstaller.__main__.run([os.path.join(os.path.dirname(__file__), '..', 'akhelper.spec'), '--noconfirm'])

if __name__ == '__main__':
    main()