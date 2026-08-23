"""系統列（system tray）圖示。

行為（使用者指定，與 ic-monitor 相反）：
- 按「縮小」→ 視窗藏到右下角系統列（雙擊圖示或右鍵「開啟」叫回來）
- 按「X」  → 真正關閉程式（同時移除系統列圖示）

pystray 只在 Windows 打包環境保證存在；開發環境（Linux CI）沒裝時
start() 回傳 False，main.py 會讓「縮小」維持一般行為 —— 功能降級不擋啟動。
tray 選單 callback 跑在 pystray 執行緒；pywebview 的 window API 是
跨執行緒安全的（ic-monitor 同模式已在現場驗證多年）。
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable

log = logging.getLogger(__name__)


class Tray:
    def __init__(self, on_open: Callable[[], None], on_quit: Callable[[], None]):
        self._on_open = on_open
        self._on_quit = on_quit
        self._icon = None
        self._hint_shown = False

    def start(self) -> bool:
        """建立系統列圖示（背景 daemon thread）。成功回 True。"""
        try:
            import pystray
            from PIL import Image

            from core.resources import resource_dir
            from core.version import APP_NAME

            image = Image.open(resource_dir() / "icon.png")
            menu = pystray.Menu(
                # default=True → 雙擊系統列圖示也會觸發「開啟」
                pystray.MenuItem(f"開啟 {APP_NAME}",
                                 lambda icon, item: self._on_open(), default=True),
                pystray.MenuItem("結束", lambda icon, item: self._on_quit()),
            )
            self._icon = pystray.Icon("ic_debugger", icon=image,
                                      title=APP_NAME, menu=menu)
            threading.Thread(target=self._icon.run, daemon=True).start()
            return True
        except Exception as e:
            log.info("系統列圖示不可用（%s）——「縮小」將維持一般縮小行為", e)
            self._icon = None
            return False

    def notify_hidden_hint(self) -> None:
        """第一次縮到系統列時提示一次，避免使用者以為程式不見了。"""
        if self._hint_shown or self._icon is None:
            return
        self._hint_shown = True
        try:
            self._icon.notify("已縮到系統列，雙擊圖示可開啟視窗", "IC Debugger")
        except Exception as e:  # 通知失敗不影響功能
            log.debug("系統列提示失敗：%s", e)

    def stop(self) -> None:
        if self._icon is not None:
            try:
                self._icon.stop()
            except Exception as e:
                log.debug("系統列圖示停止失敗：%s", e)
            self._icon = None
