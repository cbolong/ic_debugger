"""JS ↔ Python bridge（pywebview js_api）。

回傳值約定（前端 handle() 依此統一處理）：
    {"ok": True,  "payload": …, "specs": …, …}    成功；帶什麼前端就更新什麼
    {"ok": True,  "cancelled": True}               使用者取消對話框（無事發生）
    {"ok": False, "error": "人看得懂的中文訊息"}    失敗；前端 toast 顯示

pywebview 會在 worker thread 呼叫這些方法：所有進入點都拿 self._lock，
狀態轉移完才組 payload，避免匯入 bin 與切 spec 交錯出殘影。
"""

from __future__ import annotations

import logging
import re
import threading
from pathlib import Path

import webview

from app_config import save_config
from app_state import AppState
from core.analyzer import build_payload, lookup_register, spec_detail, spec_summary
from core.bin_parser import BinError, load_bin
from core.report import render_markdown
from core.version import APP_VERSION

log = logging.getLogger(__name__)


class Api:
    def __init__(self, state: AppState):
        self._state = state
        self._lock = threading.Lock()

    # ── 內部工具 ───────────────────────────────────────────────────
    def _window(self):
        return webview.windows[0] if webview.windows else None

    def _specs_list(self) -> list[dict]:
        return [spec_summary(s) for s in self._state.specs.values()]

    def _payload(self) -> dict | None:
        cur = self._state.current
        if cur is None:
            return None
        return build_payload(cur, self._state.binf)

    def _snapshot(self) -> dict:
        return {"ok": True, "specs": self._specs_list(), "payload": self._payload()}

    def _save_cfg(self) -> None:
        save_config(self._state.cfg)

    # ── 初始化 ─────────────────────────────────────────────────────
    def get_init(self) -> dict:
        with self._lock:
            resp = self._snapshot()
            resp["version"] = APP_VERSION
            return resp

    # ── bin 匯入 ───────────────────────────────────────────────────
    def import_bin(self) -> dict:
        win = self._window()
        if win is None:
            return {"ok": False, "error": "視窗尚未就緒"}
        result = win.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=False,
            directory=self._state.cfg.get("last_dir") or "",
            file_types=("Register dump (*.bin;*.dat;*.dump)", "所有檔案 (*.*)"),
        )
        if not result:
            return {"ok": True, "cancelled": True}
        path = result[0] if isinstance(result, (list, tuple)) else result
        with self._lock:
            try:
                self._state.binf = load_bin(path)
            except BinError as e:
                return {"ok": False, "error": str(e)}
            except Exception as e:
                log.exception("載入 bin 失敗")
                return {"ok": False, "error": f"載入失敗：{e}"}
            self._state.cfg["last_dir"] = str(Path(path).parent)
            self._save_cfg()
            log.info("載入 bin：%s（%d bytes）", path, self._state.binf.size)
            return self._snapshot()

    # ── spec 操作 ──────────────────────────────────────────────────
    def choose_spec(self, spec_id: str) -> dict:
        with self._lock:
            if not self._state.choose(str(spec_id)):
                return {"ok": False, "error": f"找不到 spec：{spec_id}"}
            self._save_cfg()
            return self._snapshot()

    def add_external_spec(self) -> dict:
        win = self._window()
        if win is None:
            return {"ok": False, "error": "視窗尚未就緒"}
        result = win.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=False,
            directory=self._state.cfg.get("last_dir") or "",
            file_types=("Spec MD 檔 (*.md)", "所有檔案 (*.*)"),
        )
        if not result:
            return {"ok": True, "cancelled": True}
        path = result[0] if isinstance(result, (list, tuple)) else result
        with self._lock:
            spec = self._state.add_external(str(path))
            self._state.cfg["last_spec"] = spec.spec_id
            self._save_cfg()
            log.info("載入外部 spec：%s（%d 暫存器、%d 警告）",
                     path, len(spec.registers), len(spec.warnings))
            return self._snapshot()

    def remove_external_spec(self, spec_id: str) -> dict:
        with self._lock:
            if not self._state.remove_external(str(spec_id)):
                return {"ok": False, "error": "只能移除外部 spec"}
            self._save_cfg()
            return self._snapshot()

    def lookup(self, query: str, value_text: str) -> dict:
        """快速反查：offset（或暫存器名稱）＋值 → 單筆解碼（依目前 spec）。"""
        with self._lock:
            spec = self._state.current
            if spec is None:
                return {"ok": False, "error": "尚未選擇 spec"}
            result = lookup_register(spec, str(query or ""), str(value_text or ""))
            if result["ok"]:
                result["spec_id"] = spec.spec_id
            return result

    def get_spec_detail(self, spec_id: str | None = None) -> dict:
        """「Spec 全文」：完整解析內容＋原始 MD。spec_id 省略＝目前使用中的。"""
        with self._lock:
            sid = str(spec_id) if spec_id else self._state.current_id
            spec = self._state.specs.get(sid) if sid else None
            if spec is None:
                return {"ok": False, "error": f"找不到 spec：{spec_id or '(目前未選擇)'}"}
            return {"ok": True, "detail": spec_detail(spec, self._state.detail_binf(sid))}

    def reload_specs(self) -> dict:
        with self._lock:
            self._state.load_specs()
            self._save_cfg()
            return self._snapshot()

    # ── 報告匯出 ───────────────────────────────────────────────────
    def export_report(self, only_differs: bool = False) -> dict:
        with self._lock:
            payload = self._payload()
        if payload is None:
            return {"ok": False, "error": "沒有可匯出的內容"}
        win = self._window()
        if win is None:
            return {"ok": False, "error": "視窗尚未就緒"}
        safe_id = re.sub(r"[^A-Za-z0-9_.-]", "_", str(payload["spec"]["id"])) or "spec"
        default_name = f"ic_debugger_{safe_id}.md"
        result = win.create_file_dialog(
            webview.SAVE_DIALOG,
            directory=self._state.cfg.get("last_dir") or "",
            save_filename=default_name,
        )
        if not result:
            return {"ok": True, "cancelled": True}
        path = result[0] if isinstance(result, (list, tuple)) else result
        try:
            text = render_markdown(payload, only_differs=bool(only_differs))
            Path(path).write_text(text, encoding="utf-8")
        except Exception as e:
            log.exception("匯出報告失敗")
            return {"ok": False, "error": f"寫入失敗：{e}"}
        log.info("匯出報告：%s", path)
        return {"ok": True, "path": str(path)}

    # ── 其他 ───────────────────────────────────────────────────────
    def set_theme(self, theme: str) -> dict:
        if theme not in ("light", "dark", "auto"):
            return {"ok": False, "error": f"未知主題：{theme}"}
        with self._lock:
            self._state.cfg["theme"] = theme
            self._save_cfg()
        return {"ok": True}

    def log_js_error(self, msg: str, stack: str = "") -> dict:
        log.error("[JS] %s\n%s", msg, stack)
        return {"ok": True}
