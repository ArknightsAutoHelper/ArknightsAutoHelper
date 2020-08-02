# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

import sys
sys.modules['FixTk'] = None

a = Analysis(['akhelper.py'],
             pathex=['D:\\projects\\ArknightsAutoHelper'],
             binaries=[],
             datas=[('imgreco/resources', 'imgreco/resources'), ('config/config-template.yaml', 'config'), ('config/logging.yaml', 'config'), ('screenshot', '.')],
             hiddenimports=['imgreco.ocr.baidu', 'imgreco.ocr.tesseract', 'imgreco.ocr.windows_media_ocr'],
             hookspath=[],
             runtime_hooks=[],
             excludes=['FixTk', 'tcl', 'tk', '_tkinter', 'tkinter', 'Tkinter'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='akhelper',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='akhelper')
