"""IC Debugger 進入點。

流程：讀設定 → 偵測 OS 外觀（先蓋 data-theme，避免深色系統閃白）→
載入 spec（打包在 exe 內的 specs/ ＋ 設定檔記錄的外部檔）→ 開 pywebview 視窗。

除錯：設環境變數 IC_DEBUGGER_DEBUG=1 會開 WebView2 開發者工具；
log 寫在使用者設定目錄（Windows：%APPDATA%/IC_Debugger/ic_debugger.log）。
"""

from __future__ import annotations

import logging
import os
import sys

import webview

from app_config import config_dir, effective_theme, load_config
from app_state import AppState
from core.version import APP_NAME, APP_VERSION

log = logging.getLogger("ic_debugger")


def _setup_logging() -> None:
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    try:
        config_dir().mkdir(parents=True, exist_ok=True)
        handlers.append(
            logging.FileHandler(config_dir() / "ic_debugger.log", encoding="utf-8")
        )
    except Exception:
        pass  # 寫不了 log 檔就只留 console，不擋啟動
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
    )


def main() -> None:
    _setup_logging()
    log.info("%s v%s 啟動（Python %s）", APP_NAME, APP_VERSION, sys.version.split()[0])

    cfg = load_config()
    theme = effective_theme(cfg)
    theme_attr = 'data-theme="dark"' if theme == "dark" else ""

    state = AppState(cfg=cfg)
    state.load_specs()
    log.info("載入 %d 份 spec：%s", len(state.specs), "、".join(state.specs) or "（無）")

    # import 放這裡：ui.apis 會 import webview；讓上面的錯誤先進 log
    from ui.apis import Api
    from ui.assets import build_main_html

    api = Api(state)
    webview.create_window(
        f"{APP_NAME} v{APP_VERSION}",
        html=build_main_html(theme_attr=theme_attr),
        js_api=api,
        width=1280,
        height=840,
        min_size=(1024, 660),
    )
    webview.start(debug=os.environ.get("IC_DEBUGGER_DEBUG") == "1")
    log.info("視窗關閉，結束")


if __name__ == "__main__":
    main()
