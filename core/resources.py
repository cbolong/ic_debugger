"""打包資源定位：開發模式讀 repo 目錄，PyInstaller onefile 讀 _MEIPASS 解壓目錄。"""

from __future__ import annotations

import sys
from pathlib import Path


def resource_dir() -> Path:
    """資源根目錄。onefile exe 啟動時會把打包的 datas 解壓到 sys._MEIPASS。"""
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass)
    return Path(__file__).resolve().parent.parent


def app_dir() -> Path:
    """exe 實際所在的目錄（開發模式＝repo 根）。

    與 resource_dir() 不同：onefile 的 resource_dir() 是每次啟動都會換的暫存
    解壓目錄，app_dir() 才是使用者看得到、放得了檔案的地方。
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def builtin_specs_dir() -> Path:
    return resource_dir() / "specs"


def spec_dirs() -> list[Path]:
    """spec 的搜尋順序：

    1. 打包在 exe 內的 specs/（隨版本更新）
    2. exe 旁邊的 specs/（使用者自己放的，免重新 build 就能加 spec；
       萬一內建資源解壓失敗，這裡也是救援路徑）

    開發模式兩者同一個目錄，會自動去重。
    """
    dirs = [builtin_specs_dir()]
    side = app_dir() / "specs"
    if side.resolve() != builtin_specs_dir().resolve():
        dirs.append(side)
    return dirs
