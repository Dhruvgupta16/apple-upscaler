# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

webview_datas, webview_binaries, webview_hiddenimports = collect_all('webview')
clr_datas, clr_binaries, clr_hiddenimports = collect_all('clr_loader')
py_datas, py_binaries, py_hiddenimports = collect_all('pythonnet')

datas = [
    ('apple_logo.ico', '.'),
    ('apple_logo.png', '.'),
    ('apple_logo_512.png', '.'),
    ('ai_models', 'ai_models'),
    ('luts', 'luts'),
    ('branding.json', '.'),
] + webview_datas + clr_datas + py_datas

binaries = webview_binaries + clr_binaries + py_binaries

hiddenimports = [
    'webview',
    'webview.platforms.winforms',
    'webview.platforms.edgechromium',
    'clr',
    'clr_loader',
    'pythonnet',
    'PIL',
    'PIL.Image',
    'numpy',
] + webview_hiddenimports + clr_hiddenimports + py_hiddenimports

a = Analysis(
    ['apple_upscaler.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Apple_Upscaler',
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
    icon=['apple_logo.ico'],
)
