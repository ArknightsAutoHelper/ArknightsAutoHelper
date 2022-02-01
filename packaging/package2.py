import sys
import os
from pathlib import Path
import subprocess
import runpy
import py_compile
import shutil
import zipfile

exclude_prefixes = [
    'venv',
    'packaging',
    'dist',
    'app/scm_version.py',
]

root = Path(__file__).parent.parent
build_dir = root / 'build'
dist_dir = build_dir / 'dist'

def main():
    os.chdir(root)

    if 'app' in sys.argv:
        build_app()
    if 'runtime' in sys.argv:
        build_runtime()

def build_app():
    shutil.rmtree(dist_dir, ignore_errors=True)
    os.makedirs(dist_dir, exist_ok=True)

    scmver = runpy.run_path(os.path.join(root, 'app', 'scm_version.py'))
    version = scmver['version']
    print('version:', version)
    
    with open(os.path.join(build_dir, 'release_info.py'), 'w') as f:
        f.write('version = %r\n' % version)

    print('making bytecode archive')
    git_files = [x.decode() for x in subprocess.check_output(['git', 'ls-files', '-z']).split(b'\0')]
    app_unpacked_dir = build_dir / 'app-unpacked'
    shutil.rmtree(app_unpacked_dir, ignore_errors=True)
    os.makedirs(app_unpacked_dir, exist_ok=True)
    for f in git_files:
        if any(f.startswith(x) for x in exclude_prefixes):
            continue
        if f.endswith('.py') or f.endswith('.pyw'):
            basename = f[:f.rfind('.')]
            print("compiling", f)
            py_compile.compile(f, app_unpacked_dir / (basename + '.pyc'))
        elif f.startswith('resources/'):
            print("copying", f)
            os.makedirs(os.path.dirname(app_unpacked_dir / f), exist_ok=True)
            shutil.copy(f, app_unpacked_dir / f)
    py_compile.compile(os.path.join(build_dir, 'release_info.py'), str(app_unpacked_dir / 'app' / 'release_info.pyc'))
    
    shutil.move(app_unpacked_dir / 'vendor/penguin_client/penguin_client', app_unpacked_dir / 'penguin_client')
    shutil.rmtree(app_unpacked_dir / 'vendor')
    shutil.copytree(root / 'webgui2' / 'dist', app_unpacked_dir / 'webgui2' / 'dist')

    print('archiving app')
    shutil.make_archive(str(dist_dir / 'app-cp39'), 'zip', app_unpacked_dir)
    shutil.move(dist_dir / 'app-cp39.zip', dist_dir / 'app-cp39.bin')

    print('copying misc resource files')
    shutil.copytree(root / 'vendor', dist_dir / 'vendor')
    # TODO: remove binaries for other platforms
    shutil.rmtree(dist_dir / 'vendor/penguin_client')
    shutil.copytree(root / 'custom_record', dist_dir / 'custom_record')
    shutil.make_archive(str(build_dir / 'app'), 'zip', dist_dir)


def build_runtime():
    shutil.rmtree(build_dir / 'runtime', ignore_errors=True)

    print('making runtime archive')
    python_bin_zip = build_dir / 'python-3.9.10-embed-amd64.zip'
    subprocess.run(['curl', '-Lo', os.fspath(python_bin_zip), 'https://www.python.org/ftp/python/3.9.10/python-3.9.10-embed-amd64.zip'], check=True)
    with zipfile.ZipFile(python_bin_zip, 'r') as zf:
        zf.extractall(build_dir / 'runtime')
    print('copying venv libs')
    shutil.copytree(root / 'venv' / 'Lib', build_dir / 'runtime' / 'Lib', ignore=lambda dir, files: [x for x in files if x.endswith('.pyc')] + ['__pycache__'])
    print('precompiling venv libs')
    import compileall
    compileall.compile_dir(build_dir / 'runtime' / 'Lib', ddir=None, force=True, quiet=1)
    with open(build_dir / 'runtime' / 'python39._pth', 'a') as f:
        f.write("\n")
        f.write("import site\n")
        f.write("../app-cp39.bin\n")
    print("archiving runtime")
    shutil.make_archive(str(build_dir / 'runtime-cp39-win_amd64'), 'zip', build_dir / 'runtime')

if __name__ == '__main__':
    main()
