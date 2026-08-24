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
        ('icon.png', '.'),   # 系統列圖示（ui/tray.py 經 resource_dir() 讀取）
    ],
    hiddenimports=[
        # pywebview 的 Windows 後端是動態 import，Analysis 掃不到
        'webview.platforms.edgechromium',
        'webview.platforms.winforms',
        'clr_loader',
        'pythonnet',
        'pystray._win32',    # pystray 的平台後端也是動態 import
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # 排除用不到的東西：onefile 每次啟動都要把整包解壓到暫存目錄，
    # 體積直接反映在「開啟速度」上。只排除確定沒用到的，寧可保守
    # （排錯了會在 CI 的 --selftest 那一關當場被抓到）。
    excludes=[
        'tkinter', 'unittest', 'pydoc', 'doctest', 'test', 'idlelib', 'lib2to3',
        'pytest', '_pytest', 'playwright',          # 開發／測試工具，不進產品
        'PIL.ImageQt', 'PIL.ImageTk', 'PIL.ImageShow', 'PIL.ImageGrab',
        'PIL.ImageCms', 'PIL.ImageWin',             # PIL 只用來讀系統列的 PNG
    ],
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
