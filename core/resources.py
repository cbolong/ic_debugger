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


def builtin_specs_dir() -> Path:
    return resource_dir() / "specs"
