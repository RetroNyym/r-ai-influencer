# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — AI Influencer Otomasyonu

block_cipher = None

a = Analysis(
    ['baslat.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('varlik', 'varlik'),
    ],
    hiddenimports=[
        'core', 'core.depolama', 'core.kisilik', 'core.yuz_donusum',
        'core.uretim', 'core.sahne_kutuphanesi', 'core.zamanlayici',
        'core.paylasim', 'core.paylasim.instagram', 'core.paylasim.tiktok',
        'core.paylasim.host',
        'gui', 'gui.ana_pencere', 'gui.sekme_kisilik', 'gui.sekme_uretim',
        'gui.sekme_takvim', 'gui.sekme_ayarlar',
        'cv2', 'numpy', 'requests', 'PIL',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='R-AIInfluencer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='varlik/retro-logo.ico',
)
