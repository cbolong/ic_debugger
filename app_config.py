"""使用者設定（主題、上次選的 spec、外部 spec 清單）與 OS 外觀偵測。

設定放使用者目錄而非 exe 旁：onefile exe 每次解壓到暫存目錄，
exe 旁寫檔既不穩定也常沒權限。
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

log = logging.getLogger(__name__)

_DEFAULTS: dict = {
    "theme": "auto",          # auto | light | dark（手動切過就不再是 auto）
    "last_spec": None,         # 上次使用的 spec id
    "external_specs": [],      # 外部 spec 的絕對路徑清單
    "last_dir": None,          # 上次開檔目錄
}


def config_dir() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or str(Path.home())
        return Path(base) / "IC_Debugger"
    return Path.home() / ".config" / "ic_debugger"


def config_path() -> Path:
    return config_dir() / "config.json"


def load_config() -> dict:
    cfg = dict(_DEFAULTS)
    try:
        data = json.loads(config_path().read_text(encoding="utf-8"))
        if isinstance(data, dict):
            cfg.update({k: data[k] for k in _DEFAULTS if k in data})
    except FileNotFoundError:
        pass
    except Exception as e:  # 設定檔壞掉就用預設值重來，不要讓 app 起不來
        log.warning("設定檔讀取失敗，改用預設值：%s", e)
    return cfg


def save_config(cfg: dict) -> None:
    try:
        config_dir().mkdir(parents=True, exist_ok=True)
        config_path().write_text(
            json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception as e:  # 存不了設定不該中斷操作
        log.warning("設定檔寫入失敗：%s", e)


def detect_os_theme() -> str:
    """回傳 'dark'／'light'（best-effort，失敗一律 light）。
    WebView2 不會把 OS 深色偏好反映到 prefers-color-scheme（ic-monitor §48），
    所以由 Python 讀 registry 決定。"""
    try:
        if sys.platform == "win32":
            import winreg
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            ) as k:
                v, _ = winreg.QueryValueEx(k, "AppsUseLightTheme")
                return "light" if int(v) == 1 else "dark"
        if sys.platform == "darwin":
            import subprocess
            r = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True, text=True, encoding="utf-8",
                errors="replace", timeout=3,
            )
            return "dark" if "Dark" in (r.stdout or "") else "light"
    except Exception as e:
        log.debug("OS 外觀偵測失敗，用 light：%s", e)
    return "light"


def effective_theme(cfg: dict) -> str:
    t = cfg.get("theme") or "auto"
    if t in ("light", "dark"):
        return t
    return detect_os_theme()
