"""打包與啟動診斷的驗證。

這一層補的是單元測試看不到的死角：unit test 讀的是 repo 目錄，
但使用者跑的是 exe。2026-08-23 現場出現「找不到任何 spec」時，
單元測試全綠卻查不出原因 —— 以下三件事就是為了不再發生：

1. spec 搜尋路徑（打包內＋exe 旁）與掃描紀錄。
2. `main.py --selftest`：打包後的 exe 自己驗自己（CI 每次 build 都跑）。
3. 每個 bridge 方法都必須有例外防護網，不准把錯誤吞掉變成空畫面。
"""

import ast
import json
import subprocess
import sys
from pathlib import Path

from app_state import AppState
from core.resources import app_dir, builtin_specs_dir, spec_dirs

ROOT = Path(__file__).resolve().parent.parent


def _fresh_cfg():
    return {"theme": "auto", "last_spec": None, "external_specs": [], "last_dir": None}


# ── spec 搜尋路徑 ───────────────────────────────────────────────────────

def test_spec_dirs_dev_mode_is_deduped():
    """開發模式下打包目錄與 exe 目錄是同一個，不該掃兩次。"""
    dirs = spec_dirs()
    assert len(dirs) == len(set(dirs)) == 1
    assert dirs[0] == builtin_specs_dir() == ROOT / "specs"
    assert app_dir() == ROOT


def test_scan_records_every_searched_dir():
    """load_specs() 必須留下掃描紀錄 —— 這是「找不到 spec」時唯一的線索。"""
    st = AppState(cfg=_fresh_cfg())
    st.load_specs()
    assert st.scan, "load_specs() 沒有留下掃描紀錄"
    for row in st.scan:
        assert set(row) == {"dir", "exists", "loaded", "names"}
        assert isinstance(row["dir"], str) and row["dir"]
    assert sum(r["loaded"] for r in st.scan) == len(st.specs)
    assert st.scan[0]["exists"] is True and st.scan[0]["loaded"] >= 4


def test_scan_reports_missing_dir_without_raising(tmp_path, monkeypatch):
    """搜尋目錄不存在時要照實回報 exists=False，不能丟例外。"""
    missing = tmp_path / "nope"
    monkeypatch.setattr("app_state.spec_dirs", lambda: [missing])
    st = AppState(cfg=_fresh_cfg())
    st.load_specs()
    assert st.scan == [{"dir": str(missing), "exists": False, "loaded": 0, "names": []}]
    assert st.specs == {} and st.current is None


# ── --selftest（CI 用真實 exe 跑的那一關）─────────────────────────────

def test_selftest_exits_zero_and_reports_four_specs(tmp_path):
    r = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "--selftest"],
        cwd=tmp_path, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
        env={"PYTHONPATH": str(ROOT), "PATH": "/usr/bin:/bin", "SYSTEMROOT": "C:\\Windows"},
    )
    assert r.returncode == 0, f"selftest 失敗：\n{r.stdout}\n{r.stderr}"
    report = json.loads((tmp_path / "selftest_report.json").read_text(encoding="utf-8"))
    assert report["ok"] is True and report["problems"] == []
    ids = {s["id"] for s in report["specs"]}
    assert {"cortex_r5", "cortex_a55", "n25", "n45"} <= ids
    assert all(s["warnings"] == [] for s in report["specs"])
    assert report["scan"], "報告必須帶掃描紀錄，才能診斷打包問題"


def test_selftest_fails_when_no_specs(tmp_path, monkeypatch):
    """把搜尋路徑指到空目錄 → selftest 必須回非 0（CI 就會擋下 Release）。"""
    import main as main_mod
    monkeypatch.setattr("app_state.spec_dirs", lambda: [tmp_path / "empty"])
    monkeypatch.chdir(tmp_path)
    assert main_mod.selftest() == 1
    report = json.loads((tmp_path / "selftest_report.json").read_text(encoding="utf-8"))
    assert report["ok"] is False and report["problems"]


# ── bridge 例外防護網 ──────────────────────────────────────────────────

def _api_class():
    src = (ROOT / "ui" / "apis.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    return next(n for n in ast.walk(tree)
                if isinstance(n, ast.ClassDef) and n.name == "Api")


def test_every_public_api_method_is_guarded():
    """每個對 JS 公開的方法都必須掛 @_guard。

    少掛一個，那個方法丟例外時前端只會看到空畫面／被拒絕的 promise，
    使用者完全不知道發生什麼事 —— 這正是現場那次「找不到 spec」的成因類型。
    """
    unguarded = [
        n.name for n in _api_class().body
        if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")
        and "_guard" not in [d.id for d in n.decorator_list if isinstance(d, ast.Name)]
    ]
    assert not unguarded, f"這些 bridge 方法沒有例外防護網：{unguarded}"


def test_get_init_returns_diagnostics():
    """get_init 必須回傳 diag，UI 的空狀態靠它講出「為什麼沒有 spec」。"""
    src = (ROOT / "ui" / "apis.py").read_text(encoding="utf-8")
    assert '"diag"' in src and "_diagnostics" in src
    for key in ('"scan"', '"log_path"', '"frozen"', '"spec_count"'):
        assert key in src, f"診斷缺少 {key}"
