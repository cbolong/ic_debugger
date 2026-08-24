"""IC Debugger 進入點。

流程：讀設定 → 偵測 OS 外觀（先蓋 data-theme，避免深色系統閃白）→
載入 spec（打包在 exe 內的 specs/ ＋ exe 旁的 specs/ ＋設定檔記錄的外部檔）
→ 開 pywebview 視窗 → 視窗出現後才起系統列（PIL 匯入要 0.5 秒，不擋第一幀）。

除錯：
- `IC_Debugger.exe --selftest`：不開視窗，檢查打包進 exe 的 spec 能不能載入，
  結果寫成 selftest_report.json 並用 exit code 表示成敗（CI 每次 build 都會跑）。
- 環境變數 IC_DEBUGGER_DEBUG=1 會開 WebView2 開發者工具。
- log 寫在使用者設定目錄（Windows：%APPDATA%/IC_Debugger/ic_debugger.log）。
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

from app_config import config_dir, effective_theme, load_config
from app_state import AppState
from core.version import APP_NAME, APP_VERSION

log = logging.getLogger("ic_debugger")

# 產品承諾：內建 ARM Cortex-R5／A55 與 Andes N25／N45 四份 spec。
# selftest 以此為下限（之後加第五顆 CPU 不會誤判失敗，但打包壞掉一定抓得到）。
MIN_BUILTIN_SPECS = 4


def _setup_logging(console_only: bool = False) -> None:
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if not console_only:
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


def _fresh_cfg() -> dict:
    """selftest 專用的乾淨設定：不要讓使用者既有的 config 影響驗證結果。"""
    return {"theme": "auto", "last_spec": None, "external_specs": [], "last_dir": None}


def selftest() -> int:
    """驗證「打包後的這個 exe」真的看得到內建 spec。

    單元測試讀的是 repo 目錄，看不到 exe 內部；這支才是打包路徑的守門員，
    CI 在發佈 Release 前會執行它，失敗就不出版本。
    """
    _setup_logging(console_only=True)
    state = AppState(cfg=_fresh_cfg())
    state.load_specs()

    specs = [
        {"id": sid, "cpu": s.cpu, "vendor": s.vendor,
         "registers": len(s.registers), "warnings": s.warnings}
        for sid, s in state.specs.items()
    ]
    problems: list[str] = []
    if len(specs) < MIN_BUILTIN_SPECS:
        problems.append(f"只載入 {len(specs)} 份 spec，少於預期的 {MIN_BUILTIN_SPECS} 份")
    for item in specs:
        if item["warnings"]:
            problems.append(f"{item['id']} 有解析警告：{item['warnings']}")
        if item["registers"] < 1:
            problems.append(f"{item['id']} 沒有任何暫存器")

    report = {
        "app": APP_NAME,
        "version": APP_VERSION,
        "frozen": bool(getattr(sys, "frozen", False)),
        "executable": sys.executable,
        "scan": state.scan,
        "specs": specs,
        "problems": problems,
        "ok": not problems,
    }
    text = json.dumps(report, ensure_ascii=False, indent=2)
    print(text)
    # console=False 的 exe 沒有 stdout，所以一定要落檔（CI 讀這個檔）
    try:
        Path("selftest_report.json").write_text(text, encoding="utf-8")
    except OSError as e:
        print(f"（報告寫檔失敗：{e}）", file=sys.stderr)
    return 0 if not problems else 1


def run_gui() -> None:
    # webview 只在真的要開視窗時才 import：--selftest 不需要 GUI 相依
    import webview

    from ui.apis import Api
    from ui.assets import build_main_html
    from ui.tray import Tray

    cfg = load_config()
    theme_attr = 'data-theme="dark"' if effective_theme(cfg) == "dark" else ""

    state = AppState(cfg=cfg)
    state.load_specs()
    for row in state.scan:
        log.info("spec 目錄 %s（存在=%s）→ %d 份", row["dir"], row["exists"], row["loaded"])
    log.info("共載入 %d 份 spec：%s", len(state.specs), "、".join(state.specs) or "（無）")

    api = Api(state)
    window = webview.create_window(
        f"{APP_NAME} v{APP_VERSION}",
        html=build_main_html(theme_attr=theme_attr),
        js_api=api,
        width=1280,
        height=840,
        min_size=(1024, 660),
    )

    # ── 系統列行為（使用者指定）：縮小 → 縮到系統列；X → 真正關閉 ──────
    def _tray_open() -> None:
        try:
            window.restore()  # 縮小狀態要先 restore，只 show 會維持縮小
        except Exception as e:
            log.debug("restore 失敗：%s", e)
        try:
            window.show()
        except Exception as e:
            log.warning("從系統列開啟視窗失敗：%s", e)

    def _tray_quit() -> None:
        try:
            window.destroy()  # 讓 webview.start() 返回、走正常收尾
        except Exception as e:
            log.warning("從系統列結束失敗：%s", e)

    tray = Tray(on_open=_tray_open, on_quit=_tray_quit)

    def _on_started() -> None:
        """視窗跑起來之後才做的事 —— pystray 會拉進 PIL（實測約 0.5 秒），
        放在啟動路徑上會讓使用者多等半秒才看到畫面。"""
        try:
            if tray.start():
                def _on_minimized() -> None:
                    try:
                        window.hide()  # 從工作列消失，只留系統列圖示
                    except Exception as e:
                        log.warning("縮到系統列失敗：%s", e)
                        return
                    tray.notify_hidden_hint()

                window.events.minimized += _on_minimized
        except Exception:
            log.exception("系統列初始化失敗（不影響主功能）")

    def _on_closing():
        tray.stop()  # X → 真正關閉：先收掉系統列圖示（不回傳 False，放行關閉）

    window.events.closing += _on_closing

    webview.start(func=_on_started, debug=os.environ.get("IC_DEBUGGER_DEBUG") == "1")
    tray.stop()  # 保險：不論怎麼離開主迴圈，圖示都不得殘留
    log.info("視窗關閉，結束")


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    _setup_logging()
    log.info("%s v%s 啟動（Python %s）", APP_NAME, APP_VERSION, sys.version.split()[0])
    run_gui()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
