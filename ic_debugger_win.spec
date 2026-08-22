# -*- mode: python ; coding: utf-8 -*-
# PyInstaller onefile spec：產出單一 dist/IC_Debugger.exe（不打 zip）。
#
# - specs/ 整個目錄打包進 exe，執行時解壓到 sys._MEIPASS
#   （core/resources.py 依此定位），所以「更新 spec ＝ 改 md → push → 重 build」。
# - upx 關閉：onefile + upx 對 vcruntime/WebView2Loader 這類 DLL 有壓壞前例，
#   也更容易被防毒誤判；體積換穩定，值得。
# - console=False：視窗程式；診斷靠 %APPDATA%/IC_Debugger/ic_debugger.log。

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('specs', 'specs'),
    ],
    hiddenimports=[
        # pywebview 的 Windows 後端是動態 import，Analysis 掃不到
        'webview.platforms.edgechromium',
        'webview.platforms.winforms',
        'clr_loader',
        'pythonnet',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'unittest', 'pydoc', 'doctest'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='IC_Debugger',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon='icon.ico',
    runtime_tmpdir=None,
)
