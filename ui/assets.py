"""UI 資產：主題 tokens 與主視窗 HTML/CSS/JS。

慣例（沿襲 ic-monitor 的教訓）：
- 色票單一來源：所有顏色都走 :root 的 --c-* tokens；深色只重定義 tokens。
  不要在下面的 CSS/JS 撒新的 hex 色碼。
- MAIN_HTML 用 raw string（r\"\"\"）：JS 的反斜線不會被 Python 吃掉。
- 這個模組**不准 import webview**：測試與 tools/preview.py 都直接 import 它。
- 值的呈現一律用 payload 給的字串（hex/bin/dec 都在 Python 格式化好了），
  JS 不做任何位元運算 —— 64-bit 會超過 JS Number 安全範圍。
"""

from core.version import APP_VERSION

# ─────────────────────────────────────────────
# 主題 tokens — 淺色定義在 :root，深色只重定義同一組。
# WebView2 不會把 OS 深色偏好反映到 prefers-color-scheme（ic-monitor §48），
# 所以 Python 端偵測 OS 外觀後把 data-theme="dark" 蓋在 <html> 上；
# 使用者手動切換存 localStorage + config，優先於 OS。
# ─────────────────────────────────────────────
_DARK_TOKENS = """
  color-scheme: dark;
  --c-text:#e6eaf0; --c-text-muted:#97a1b0;
  --c-accent:#4a9eff; --c-accent-hover:#67b0ff; --c-accent-bg:#1d2c42;
  --c-danger:#ff5b52; --c-danger-bg:#2d1f21; --c-danger-border:#b03b48; --c-danger-text:#ff9a95;
  --c-success:#35d15f; --c-success-bg:#1f2b25; --c-success-border:#3aa670; --c-success-text:#7ee29d;
  --c-warn:#ffd93d; --c-warn-bg:#2d281d; --c-warn-border:#a88738; --c-warn-text:#e8c15a;
  --c-info:#4aa3e0;
  --c-border:#2e323c; --c-divider:#454b58;
  --c-surface:#1e2027; --c-input-border:#3a3f4a;
  --c-bg-soft:#14161b; --c-bg-softer:#22252e;
  --c-scrollbar:#4a5058;
  --c-elevate: 0 1px 2px rgba(0,0,0,.35), 0 2px 8px rgba(0,0,0,.28);
"""

THEME_ROOT_CSS = """:root {
  color-scheme: light dark;
  --c-text:           #1d1d1f;
  --c-text-muted:     #86868b;
  --c-accent:         #0071e3;
  --c-accent-hover:   #0064d2;
  --c-accent-bg:      #e3effd;
  --c-danger:         #ff3b30;
  --c-danger-bg:      #ffe0e0;
  --c-danger-border:  #eda9a9;
  --c-danger-text:    #c0392b;
  --c-success:        #30d158;
  --c-success-bg:     #d1f0d9;
  --c-success-border: #b6d7a8;
  --c-success-text:   #1e7e34;
  --c-warn:           #ffd93d;
  --c-warn-bg:        #fff8e0;
  --c-warn-border:    #e6cd7a;
  --c-warn-text:      #b8860b;
  --c-info:           #3498db;
  --c-border:         #e5e5ea;
  --c-divider:        #b0b4be;
  --c-surface:        #ffffff;
  --c-input-border:   #d2d2d7;
  --c-bg-soft:        #e9ebf0;
  --c-bg-softer:      #eef0f4;
  --c-scrollbar:      #c1c1c1;
  --c-elevate: 0 1px 2px rgba(0,0,0,.06), 0 2px 8px rgba(0,0,0,.05);
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {__DARK_TOKENS__}
}
:root[data-theme="dark"] {__DARK_TOKENS__}
:root[data-theme="light"] { color-scheme: light; }
""".replace("__DARK_TOKENS__", _DARK_TOKENS)


MAIN_HTML = r"""<!DOCTYPE html>
<html __html_theme_attr__>
<head>
<meta charset="utf-8">
<script>
// ── 主題（沿 ic-monitor §47/§48/§59 的作法）────────────────────────────
// Python 依 OS 外觀先蓋 data-theme；localStorage 有手動覆寫時以覆寫為準，
// 在 body render 前套用（不閃爍）。🌓 按鈕切換 + 存 localStorage + 回寫 config。
(function(){
  var KEY = 'icd-theme';
  function apply(t){
    var r = document.documentElement;
    if (t === 'dark' || t === 'light') r.setAttribute('data-theme', t);
    else r.removeAttribute('data-theme');
  }
  var ov = null;
  try { ov = localStorage.getItem(KEY); } catch (e) {}
  if (ov === 'dark' || ov === 'light') apply(ov);
  window._toggleTheme = function(){
    var cur = document.documentElement.getAttribute('data-theme') || 'light';
    var next = (cur === 'dark') ? 'light' : 'dark';
    apply(next);
    try { localStorage.setItem(KEY, next); } catch (e) {}
    try { if (window.pywebview && pywebview.api && pywebview.api.set_theme) pywebview.api.set_theme(next); } catch (e) {}
  };
})();
// ── JS 錯誤緩衝：pywebview.api 可能還沒注入，先收著再回傳 Python 寫 log ──
window._jsErrors = [];
window.addEventListener('error', function(e){
  window._jsErrors.push({ msg: (e && e.message) || String(e), line: (e && e.lineno) || 0, stack: (e && e.error && e.error.stack) || '' });
});
setInterval(function(){
  if (!window._jsErrors.length) return;
  if (!(window.pywebview && pywebview.api && pywebview.api.log_js_error)) return;
  while (window._jsErrors.length) {
    var e = window._jsErrors.shift();
    try { pywebview.api.log_js_error(e.msg + ' @' + e.line, e.stack || ''); }
    catch (_) { window._jsErrors.unshift(e); break; }
  }
}, 1000);
</script>
<!-- 刻意不載入任何外部字型／資源：IC 設計環境常是封閉網路，
     對 fonts.googleapis.com 的 DNS 與連線逾時會讓啟動多等好幾秒。
     改用 Windows 內建字型，離線也完全一致。 -->
<style>
__THEME_ROOT_CSS__
* { box-sizing: border-box; margin: 0; padding: 0; }
:root { --font-mono: "Cascadia Mono", Consolas, "SF Mono", ui-monospace, monospace; }
body {
  /* 全部走系統內建字型（Windows 一定有），不依賴網路 */
  font-family: "Microsoft JhengHei UI", "Microsoft JhengHei", "Segoe UI",
               "PingFang TC", "Noto Sans TC", -apple-system, sans-serif;
  background: var(--c-bg-soft); color: var(--c-text);
  height: 100vh; display: flex; flex-direction: column; overflow: hidden;
  font-size: 14px;
}
.mono { font-family: var(--font-mono); }
.muted { color: var(--c-text-muted); }

/* ── Top bar（深淺色都維持深色，同 ic-monitor）── */
.topbar {
  background: #1c1c1e; color: #fff;
  padding: 0 16px; height: 48px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
}
.topbar-left { display: flex; align-items: center; gap: 12px; min-width: 0; }
.topbar-title { font-size: 15px; font-weight: 600; letter-spacing: -0.2px; white-space: nowrap; }
.bin-chip {
  font-size: 12px; color: #ccc; background: rgba(255,255,255,.10);
  padding: 4px 10px; border-radius: 7px; font-family: var(--font-mono);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 340px;
}
.topbar-right { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
.spec-label { font-size: 11px; color: #999; text-transform: uppercase; letter-spacing: .6px; }
.spec-select {
  background: #3a3a3c; color: #fff; border: 1px solid #48484a; border-radius: 7px;
  padding: 6px 8px; font-size: 13px; cursor: pointer; outline: none; max-width: 280px;
}
.spec-select:focus { border-color: var(--c-accent); }
.btn-accent {
  background: var(--c-accent); color: #fff; border: none; border-radius: 7px;
  padding: 7px 14px; font-size: 13px; font-weight: 600; cursor: pointer; line-height: 1.4;
}
.btn-accent:hover { background: var(--c-accent-hover); }
.theme-toggle {
  background: rgba(255,255,255,.12); border: none; color: #fff; width: 30px; height: 30px;
  border-radius: 7px; cursor: pointer; font-size: 14px; line-height: 1;
  display: flex; align-items: center; justify-content: center; padding: 0;
}
.theme-toggle:hover { background: rgba(255,255,255,.22); }

/* ── Layout ── */
.layout { display: flex; flex: 1; overflow: hidden; }
.sidebar {
  width: 190px; flex-shrink: 0; background: #2c2c2e; color: #fff;
  display: flex; flex-direction: column; overflow-y: auto;
}
.sidebar-section {
  padding: 14px 12px 6px; font-size: 10px; font-weight: 600; color: #888;
  text-transform: uppercase; letter-spacing: .8px;
}
.nav-item {
  display: flex; align-items: center; gap: 9px;
  padding: 9px 14px; font-size: 13px; line-height: 1.5; color: #ccc;
  cursor: pointer; border-radius: 7px; margin: 1px 6px;
  border: none; background: none; width: calc(100% - 12px); text-align: left;
  font-family: inherit;
}
.nav-item:hover { background: #3a3a3c; color: #fff; }
.nav-item.active { background: var(--c-accent); color: #fff; }
.nav-badge {
  margin-left: auto; font-size: 11px; font-weight: 600; font-family: var(--font-mono);
  background: rgba(255,255,255,.15); border-radius: 9px; padding: 1px 7px;
}
.sidebar-footer { margin-top: auto; padding: 12px 14px; font-size: 11px; color: #777; }

.content { flex: 1; overflow-y: auto; padding: 20px 24px; scrollbar-color: var(--c-scrollbar) transparent; }
.content::-webkit-scrollbar { width: 10px; }
.content::-webkit-scrollbar-track { background: transparent; }
.content::-webkit-scrollbar-thumb { background: var(--c-scrollbar); border-radius: 5px; }

/* ── 卡片與區塊 ── */
.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px,1fr)); gap: 12px; margin-bottom: 20px; }
.card {
  background: var(--c-surface); border: 1px solid var(--c-border); border-radius: 12px;
  padding: 14px 16px; box-shadow: var(--c-elevate);
}
.card-num { font-size: 26px; font-weight: 700; color: var(--c-text); font-family: var(--font-mono); }
.card-num.accent { color: var(--c-accent); }
.card-num.warn { color: var(--c-warn-text); }
.card-label { font-size: 12px; color: var(--c-text-muted); margin-top: 3px; }
.card-sub { font-size: 11px; color: var(--c-text-muted); margin-top: 2px; font-family: var(--font-mono); }
.card.card-warn { background: var(--c-warn-bg); border-color: var(--c-warn-border); }
.card.clickable { cursor: pointer; }
.card.clickable:hover { border-color: var(--c-accent); }

.section-title {
  font-size: 14px; font-weight: 600; margin: 18px 0 10px; display: flex; align-items: center; gap: 8px;
}
.banner {
  border-radius: 10px; padding: 10px 14px; font-size: 13px; margin-bottom: 14px;
  border: 1px solid var(--c-warn-border); background: var(--c-warn-bg); color: var(--c-warn-text);
}
.banner.info { border-color: var(--c-border); background: var(--c-accent-bg); color: var(--c-text); }

.table-wrap {
  background: var(--c-surface); border-radius: 12px; border: 1px solid var(--c-border);
  overflow-x: auto; box-shadow: var(--c-elevate); margin-bottom: 16px;
  scrollbar-color: var(--c-scrollbar) transparent;
}
.table-wrap::-webkit-scrollbar { height: 8px; width: 8px; }
.table-wrap::-webkit-scrollbar-track { background: transparent; }
.table-wrap::-webkit-scrollbar-thumb { background: var(--c-scrollbar); border-radius: 4px; }

table { width: 100%; border-collapse: collapse; font-size: 13px; }
th {
  text-align: left; padding: 9px 12px; color: var(--c-text-muted); font-weight: 600;
  font-size: 11px; letter-spacing: .4px; border-bottom: 1px solid var(--c-divider);
  white-space: nowrap; background: var(--c-surface);
}
td { padding: 8px 12px; border-bottom: 1px solid var(--c-border); vertical-align: top; }
tr:last-child > td { border-bottom: none; }
tr.reg-row { cursor: pointer; }
tr.reg-row:hover > td { background: var(--c-bg-softer); }
tr.reg-row.open > td { background: var(--c-bg-softer); }
.reg-name { font-weight: 600; font-family: var(--font-mono); }
.reg-desc { font-size: 12px; color: var(--c-text-muted); }
.caret { display: inline-block; width: 14px; color: var(--c-text-muted); font-size: 11px; }

/* 狀態 chips */
.chip {
  display: inline-block; padding: 2px 8px; border-radius: 6px;
  font-size: 11px; font-weight: 600; white-space: nowrap;
}
.chip-diff { color: var(--c-accent); background: var(--c-accent-bg); }
.chip-same { color: var(--c-text-muted); background: var(--c-bg-softer); }
.chip-warn { color: var(--c-warn-text); background: var(--c-warn-bg); }
.chip-none { color: var(--c-text-muted); background: transparent; border: 1px dashed var(--c-border); }
.chip-builtin { color: var(--c-success-text); background: var(--c-success-bg); }
.chip-ext { color: var(--c-accent); background: var(--c-accent-bg); }

/* ── 工具列 ── */
.toolbar { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; flex-wrap: wrap; }
.search-input {
  flex: 1; min-width: 220px; max-width: 420px;
  background: var(--c-surface); color: var(--c-text);
  border: 1px solid var(--c-input-border); border-radius: 8px;
  padding: 7px 12px; font-size: 13px; outline: none; font-family: inherit;
}
.search-input:focus { border-color: var(--c-accent); }
.seg { display: flex; border: 1px solid var(--c-input-border); border-radius: 8px; overflow: hidden; }
.seg button {
  border: none; background: var(--c-surface); color: var(--c-text-muted);
  padding: 7px 12px; font-size: 12px; cursor: pointer; font-family: inherit;
}
.seg button.active { background: var(--c-accent); color: #fff; }
.btn {
  background: var(--c-surface); color: var(--c-text); border: 1px solid var(--c-input-border);
  border-radius: 8px; padding: 7px 12px; font-size: 12px; cursor: pointer; font-family: inherit;
}
.btn:hover { border-color: var(--c-accent); color: var(--c-accent); }

/* ── 展開的暫存器細節 ── */
tr.detail-row > td { background: var(--c-bg-softer); padding: 14px 16px 18px; }
.detail-head { display: flex; align-items: center; gap: 18px; flex-wrap: wrap; margin-bottom: 8px; }
.detail-val { font-family: var(--font-mono); font-size: 16px; font-weight: 700; }
.detail-meta { font-size: 12px; color: var(--c-text-muted); font-family: var(--font-mono); }
.kv { display: flex; flex-direction: column; }
.kv-label { font-size: 10px; font-weight: 600; color: var(--c-text-muted);
            text-transform: uppercase; letter-spacing: .5px; }
.val-accent { color: var(--c-accent); }

/* bit ruler：由 MSB 到 LSB 一格一 bit，依欄位分組 */
.bitruler { display: flex; align-items: flex-end; overflow-x: auto; padding: 8px 2px 12px; gap: 5px;
            scrollbar-color: var(--c-scrollbar) transparent; }
.bitruler::-webkit-scrollbar { height: 6px; }
.bitruler::-webkit-scrollbar-thumb { background: var(--c-scrollbar); border-radius: 3px; }
.bitgroup { cursor: pointer; flex-shrink: 0; }
.bitidx { display: flex; justify-content: space-between; font-size: 9px; color: var(--c-text-muted);
          font-family: var(--font-mono); padding: 0 1px 2px; min-height: 14px; }
.bitcells { display: flex; }
.bitcell {
  width: 21px; height: 26px; margin-left: -1px;
  border: 1px solid var(--c-divider); background: var(--c-surface);
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-mono); font-size: 12px;
}
.bitcells .bitcell:first-child { margin-left: 0; border-radius: 4px 0 0 4px; }
.bitcells .bitcell:last-child { border-radius: 0 4px 4px 0; }
.bitlabel {
  font-size: 10px; text-align: center; color: var(--c-text-muted); padding-top: 3px;
  max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.bitgroup.res .bitcell { color: var(--c-text-muted); background: var(--c-bg-softer); }
.bitgroup.diff .bitcell { background: var(--c-accent-bg); border-color: var(--c-accent); color: var(--c-accent); font-weight: 700; }
.bitgroup.diff .bitlabel { color: var(--c-accent); font-weight: 600; }
.bitgroup:hover .bitlabel { color: var(--c-accent); }

/* 欄位表 */
.field-table td { padding: 6px 10px; font-size: 12.5px; }
.field-table .frow.dim > td { color: var(--c-text-muted); }
.field-table .frow.diff > td:first-child { box-shadow: inset 3px 0 0 var(--c-accent); }
.field-table .frow.flash > td { background: var(--c-accent-bg); }
.fname { font-weight: 600; font-family: var(--font-mono); }
.fmeaning b { font-weight: 600; }
.fmeaning .fdesc { display: block; font-size: 11.5px; color: var(--c-text-muted); margin-top: 1px; }
.enum-details { margin-top: 4px; }
.enum-details summary { cursor: pointer; font-size: 11px; color: var(--c-accent); user-select: none; }
.enum-table { width: auto; margin-top: 4px; font-size: 11.5px; }
.enum-table td { padding: 2px 10px 2px 0; border: none; color: var(--c-text-muted); }
.enum-table tr.current td { color: var(--c-accent); font-weight: 600; }

/* ── Hex dump ── */
.hex-table td { font-family: var(--font-mono); white-space: nowrap; }
.hex-off { color: var(--c-text-muted); font-size: 12px; }
.hexword { cursor: pointer; border-radius: 6px; padding: 3px 6px; margin: -3px -6px; }
.hexword:hover { background: var(--c-bg-softer); }
.hw-val { font-size: 13px; }
.hw-val.diff { color: var(--c-accent); font-weight: 700; }
.hw-reg { font-size: 10.5px; color: var(--c-text-muted); }

/* ── Spec 管理 ── */
.spec-card {
  background: var(--c-surface); border: 1px solid var(--c-border); border-radius: 12px;
  padding: 14px 16px; box-shadow: var(--c-elevate); margin-bottom: 12px;
}
.spec-card.current { border-color: var(--c-accent); }
.spec-card-head { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.spec-card-name { font-weight: 600; font-size: 14px; }
.spec-card-path { font-size: 11px; color: var(--c-text-muted); font-family: var(--font-mono); margin-top: 4px; word-break: break-all; }
.spec-card-actions { margin-left: auto; display: flex; gap: 8px; }
.spec-status {
  margin-top: 6px; font-size: 12px; color: var(--c-warn-text);
  background: var(--c-warn-bg); border: 1px solid var(--c-warn-border);
  border-radius: 8px; padding: 5px 9px; display: inline-block;
}
.spec-warnings { margin-top: 8px; }
.spec-warnings summary { cursor: pointer; font-size: 12px; color: var(--c-warn-text); }
.spec-warnings li { font-size: 12px; color: var(--c-warn-text); margin: 4px 0 0 18px; font-family: var(--font-mono); }

/* ── 快速反查 ── */
.lk-form { display: flex; align-items: flex-end; gap: 12px; flex-wrap: wrap; }
.lk-form .btn-accent { height: 34px; }
.lk-form .kv-label { margin-bottom: 3px; }
.lk-detail {
  background: var(--c-bg-softer); border: 1px solid var(--c-border);
  border-radius: 12px; padding: 14px 16px 18px; margin-bottom: 16px;
}

/* ── Spec 全文 ── */
.doc-head { margin-bottom: 16px; }
.doc-meta { font-size: 12.5px; color: var(--c-text-muted); margin-top: 6px; line-height: 1.8; }
.doc-meta b { color: var(--c-text); font-weight: 600; }
.doc-reg-head {
  display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap;
  padding: 10px 12px; border-bottom: 1px solid var(--c-divider); background: var(--c-bg-softer);
  border-radius: 12px 12px 0 0;
}
.doc-reg-name { font-family: var(--font-mono); font-weight: 700; font-size: 14.5px; }
.doc-reg-meta { font-size: 12px; color: var(--c-text-muted); font-family: var(--font-mono); }
.doc-reg-desc { font-size: 12.5px; color: var(--c-text-muted); padding: 8px 12px 0; }
.doc-reg-verify { font-size: 12px; color: var(--c-success-text); padding: 6px 12px 0; line-height: 1.7; }
.rawspec {
  background: var(--c-surface); border: 1px solid var(--c-border); border-radius: 12px;
  box-shadow: var(--c-elevate); padding: 16px 18px; overflow-x: auto;
  font-family: var(--font-mono); font-size: 12px; line-height: 1.65;
  white-space: pre; color: var(--c-text);
  scrollbar-color: var(--c-scrollbar) transparent;
}
.enum-inline { width: auto; font-size: 12px; margin-top: 4px; }
.enum-inline td { padding: 2px 12px 2px 0; border: none; color: var(--c-text-muted); }

/* 空狀態 */
.empty {
  text-align: center; padding: 48px 20px; color: var(--c-text-muted);
  background: var(--c-surface); border: 1px dashed var(--c-input-border); border-radius: 12px;
}
.empty .big { font-size: 34px; margin-bottom: 10px; }
.empty p { margin: 4px 0 14px; font-size: 13px; }

/* Toast */
#toast {
  position: fixed; left: 50%; bottom: 26px; transform: translateX(-50%) translateY(20px);
  background: #1c1c1e; color: #fff; padding: 10px 18px; border-radius: 10px;
  font-size: 13px; opacity: 0; pointer-events: none; transition: all .25s; z-index: 99;
  max-width: 70vw; box-shadow: 0 4px 16px rgba(0,0,0,.3);
}
#toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }
#toast.err { background: var(--c-danger-text); }
</style>
</head>
<body>
<div class="topbar">
  <div class="topbar-left">
    <span class="topbar-title">IC Debugger</span>
    <span class="bin-chip" id="binChip">未載入 bin（spec 閱讀模式）</span>
  </div>
  <div class="topbar-right">
    <span class="spec-label">CPU Spec</span>
    <select class="spec-select" id="specSelect" onchange="chooseSpec(this.value)"></select>
    <button class="btn-accent" onclick="importBin()">匯入 bin</button>
    <button class="theme-toggle" onclick="_toggleTheme()" title="切換 淺色 / 深色">🌓</button>
  </div>
</div>

<div class="layout">
  <div class="sidebar">
    <div class="sidebar-section">分析</div>
    <button class="nav-item active" data-view="overview" onclick="nav('overview')">📊 總覽</button>
    <button class="nav-item" data-view="regs" onclick="nav('regs')">🧾 暫存器 <span class="nav-badge" id="navRegCount"></span></button>
    <button class="nav-item" data-view="lookup" onclick="nav('lookup')">🔍 快速反查</button>
    <button class="nav-item" data-view="hex" onclick="nav('hex')">🔢 原始資料</button>
    <button class="nav-item" data-view="specdoc" onclick="openSpecDoc(null)">📖 Spec 全文</button>
    <div class="sidebar-section">設定</div>
    <button class="nav-item" data-view="specs" onclick="nav('specs')">📚 Spec 管理</button>
    <div class="sidebar-footer">IC Debugger v__APP_VERSION__</div>
  </div>
  <div class="content" id="content"><div id="view"></div></div>
</div>
<div id="toast"></div>

<script>
'use strict';
// ────────────────────────────────────────────────────────────────────
// App 狀態：payload 由 Python 的 core.analyzer 整包給（值都是格式化字串），
// JS 只做過濾與渲染。
// ────────────────────────────────────────────────────────────────────
var S = {
  inited: false,
  specs: [],        // spec 摘要清單（下拉選單 / Spec 管理用）
  payload: null,    // 目前分析結果
  view: 'overview',
  q: '',
  onlyDiff: false,
  expanded: {},     // 暫存器名稱 → 是否展開
  diag: null,       // 啟動診斷（掃了哪些 spec 目錄、各找到幾份）
  lastError: null,  // 最近一次失敗的原因（空狀態會顯示；toast 會消失，這個不會）
  doc: null,        // Spec 全文檢視的內容（get_spec_detail 的 detail）
  docTab: 'parsed', // 'parsed'（解析後）| 'raw'（原始 Markdown）
  lk: { q: '', v: '', result: null, note: null, error: null,
        history: [], spec_id: null },  // 快速反查（歷史限本次執行）
  hideRes: true,    // 預設隱藏「與 Reset 相同的保留／未定義位元」列（降噪）
};

function esc(s){
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
// 嵌進 inline handler 單引號字串的跳脫（先處理 JS 字串層，再過 esc 處理 HTML 層）
function jsq(s){
  return esc(String(s == null ? '' : s).replace(/\\/g, '\\\\').replace(/'/g, "\\'"));
}

var _toastTimer = null;
function showToast(msg, isErr){
  var t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'show' + (isErr ? ' err' : '');
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(function(){ t.className = ''; }, isErr ? 5000 : 2600);
}

// ── Python bridge ──────────────────────────────────────────────────
function api(name){
  var args = Array.prototype.slice.call(arguments, 1);
  if (!window.pywebview || !window.pywebview.api) {
    showToast('預覽模式：「' + name + '」需在應用程式中執行', true);
    return Promise.reject('no-api');
  }
  if (typeof window.pywebview.api[name] !== 'function') {
    // bridge 在但方法不在 —— 這是真的異常，不能當成預覽模式默默吞掉
    return Promise.reject('Python 端沒有提供「' + name + '」這個方法');
  }
  return window.pywebview.api[name].apply(window.pywebview.api, args);
}

// 統一處理 API 回應：{ok, error?, cancelled?, payload?, specs?}
function handle(resp, after){
  if (!resp || resp.cancelled) return;
  if (resp.diag) S.diag = resp.diag;   // 失敗也要留診斷，不然什麼線索都沒有
  if (!resp.ok) {
    S.lastError = resp.error || '操作失敗';
    showToast(S.lastError, true);
    renderAll();
    return;
  }
  S.lastError = null;
  if (resp.specs) { S.specs = resp.specs; S.doc = null; }  // spec 集合變動 → 全文快取作廢
  if ('payload' in resp) { S.payload = resp.payload; prepPayload(); }
  // 換了 spec → 反查結果與歷史是舊 spec 解的，全部作廢
  if (S.payload && S.lk.spec_id && S.payload.spec.id !== S.lk.spec_id) {
    S.lk = { q: '', v: '', result: null, note: null, error: null, history: [], spec_id: null };
  }
  renderAll();
  if (S.view === 'specdoc' && !S.doc) openSpecDoc(null);   // 正在看全文就馬上重抓
  if (after) after(resp);
}
function apiFail(e){ if (e !== 'no-api') showToast('操作失敗：' + e, true); }

// ── 初始化：pywebview 就緒後拉初始資料；預覽模式吃 window.__PREVIEW__ ──
// pywebview 是先注入 window.pywebview = {api: {}, …}，之後才用 _createApi()
// 把方法一個個掛上去。只檢查「pywebview.api 存在」會落在這個空窗期：
// 取到 undefined 的 get_init → promise 被拒 → 畫面永遠停在空狀態，
// 而且 S.inited 已經 latch，後來的 pywebviewready 也不會重試。
// 2026-08-24 現場「找不到任何 CPU spec」就是這個競態，所以一定要確認
// 「那個方法真的已經是 function」才算就緒。
function bridgeReady(){
  return !!(window.pywebview && window.pywebview.api
            && typeof window.pywebview.api.get_init === 'function');
}

function init(){
  if (S.inited) return;
  if (window.__PREVIEW__) {
    S.inited = true;
    S.specs = window.__PREVIEW__.specs || [];
    S.payload = window.__PREVIEW__.payload || null;
    S.diag = window.__PREVIEW__.diag || null;
    prepPayload(); renderAll();
    return;
  }
  if (!bridgeReady()) return;   // 還沒掛好 → 不要 latch，讓輪詢繼續等
  S.inited = true;
  api('get_init').then(function(resp){
    handle(resp);
  }).catch(function(e){
    S.lastError = '取得初始資料失敗：' + e;
    renderAll();
  });
}
window.addEventListener('pywebviewready', init);
var _initTries = 0;
var _initPoll = setInterval(function(){
  if (window.__PREVIEW__ || bridgeReady()) { clearInterval(_initPoll); init(); return; }
  // 約 30 秒還等不到就別再空等，直接把狀況講出來
  if (++_initTries > 200) {
    clearInterval(_initPoll);
    S.inited = true;
    S.lastError = '等不到 Python 端介面（pywebview bridge）就緒，請把 log 檔提供給維護者。';
    renderAll();
  }
}, 150);

// ── 動作 ───────────────────────────────────────────────────────────
function importBin(){ api('import_bin').then(function(r){ handle(r, function(){ showToast('已載入 ' + (S.payload && S.payload.bin ? S.payload.bin.name : 'bin')); }); }).catch(apiFail); }
function chooseSpec(id){ api('choose_spec', id).then(handle).catch(apiFail); }
function addSpec(){ api('add_external_spec').then(function(r){ handle(r, function(){ showToast('已載入外部 spec'); }); }).catch(apiFail); }
function removeSpec(id){ api('remove_external_spec', id).then(function(r){ handle(r, function(){ showToast('已移除'); }); }).catch(apiFail); }
function reloadSpecs(){ api('reload_specs').then(function(r){ handle(r, function(){ showToast('已重新載入 spec'); }); }).catch(apiFail); }
function exportReport(){
  api('export_report', S.onlyDiff).then(function(r){
    if (!r || r.cancelled) return;
    if (r.ok) showToast('已匯出：' + r.path); else showToast(r.error || '匯出失敗', true);
  }).catch(apiFail);
}
function nav(v){ S.view = v; renderAll(); }
// 開啟「Spec 全文」：id=null 表示目前使用中的 spec；每張 spec 卡也有各自的按鈕
function openSpecDoc(id){
  S.view = 'specdoc';
  var want = id || (S.payload ? S.payload.spec.id : null);
  if (S.doc && S.doc.summary.id === want) { renderAll(); return; }
  if (window.__PREVIEW__) {
    var d = window.__PREVIEW__.spec_detail;
    if (d && (!want || d.summary.id === want)) { S.doc = d; S.docTab = 'parsed'; }
    renderAll(); return;
  }
  S.doc = null; renderAll();  // 先顯示載入中
  api('get_spec_detail', id).then(function(r){
    if (!r) return;
    if (!r.ok) { showToast(r.error || '載入失敗', true); return; }
    S.doc = r.detail; S.docTab = 'parsed';
    renderAll();
  }).catch(apiFail);
}
function setDocTab(t){ S.docTab = t; renderView(); }
function setQuery(q){ S.q = q; renderView(); }
function setOnlyDiff(v){ S.onlyDiff = v; renderView(); }
function toggleReg(name){ S.expanded[name] = !S.expanded[name]; renderView(); }
function setAll(open){
  visibleRegs().forEach(function(r){ S.expanded[r.name] = open; });
  renderView();
}
// 從其他頁跳到某個暫存器（展開 + 捲動；必要時解除搜尋／篩選讓目標可見）
function goReg(name){
  S.view = 'regs'; S.expanded[name] = true;
  var reg = (S.payload ? S.payload.registers : []).filter(function(r){ return r.name === name; })[0];
  if (reg) {
    if (S.q && reg._search.indexOf(S.q.trim().toLowerCase()) < 0) S.q = '';
    if (S.onlyDiff && reg.differs !== true) S.onlyDiff = false;
  }
  renderAll();
  var el = document.getElementById('reg-' + cssId(name));
  if (el) { el.scrollIntoView({ block: 'center' }); }
}
// bit ruler 點欄位 → 對應表格列捲動 + 閃爍；點到被「隱藏保留位」過濾掉的列
// 時自動展開（使用者點了就是想看，不能只給沉默）
function focusField(ri, fi){
  var row = document.getElementById('ft-' + ri + '-' + fi);
  if (!row && S.hideRes) {
    S.hideRes = false;
    renderView();
    row = document.getElementById('ft-' + ri + '-' + fi);
  }
  if (!row) return;
  row.scrollIntoView({ block: 'center' });
  row.classList.add('flash');
  setTimeout(function(){ row.classList.remove('flash'); }, 900);
}

// ── payload 前處理：搜尋索引 ───────────────────────────────────────
function prepPayload(){
  S.expanded = {};
  if (!S.payload) return;
  S.payload.registers.forEach(function(r){
    var parts = [r.name, r.desc || ''];
    r.rows.forEach(function(f){
      parts.push(f.name, f.desc || '');
      (f.enum || []).forEach(function(e){ parts.push(e.label); });
    });
    r._search = parts.join(' ').toLowerCase();
  });
}

function visibleRegs(){
  if (!S.payload) return [];
  var q = S.q.trim().toLowerCase();
  return S.payload.registers.filter(function(r){
    if (S.onlyDiff && r.differs !== true) return false;
    return !q || r._search.indexOf(q) >= 0;
  });
}

function cssId(s){ return String(s).replace(/[^A-Za-z0-9_-]/g, '_'); }

// 廠商顯示名與分組：下拉選單與「Spec 管理」共用這兩支（不准各分各的）
var VENDOR_LABELS = { arm: 'ARM', andes: 'Andes', riscv: 'RISC-V', 'intel': 'Intel' };
function vendorLabel(v){
  if (!v) return '其他';
  return VENDOR_LABELS[String(v).toLowerCase()] || String(v).toUpperCase();
}
// 回傳 [[廠商標籤, [spec…]], …]，順序＝specs 陣列裡第一次出現的順序（＝檔案系統排序）
function groupSpecsByVendor(specs){
  var order = [], map = {};
  specs.forEach(function(s){
    var key = s.origin === 'external' ? '__ext__' : (s.vendor || '');
    if (!(key in map)) { map[key] = []; order.push(key); }
    map[key].push(s);
  });
  return order.map(function(k){
    return [k === '__ext__' ? '外部載入' : vendorLabel(k), map[k]];
  });
}

// 狀態 chip 的唯一渲染來源（暫存器清單、反查歷史都用這支——不准各寫各的）
// always=false：沒載入 bin 時不顯示（spec 閱讀模式沒有「狀態」可言）
function statusChipHtml(r, always){
  if (!always && !(S.payload && S.payload.bin)) return '';
  if (!r.covered) return '<span class="chip chip-warn">' + (r.partial ? '截斷' : '未涵蓋') + '</span>';
  if (r.differs === true) return '<span class="chip chip-diff">≠ Reset</span>';
  if (r.differs === false) return '<span class="chip chip-same">= Reset</span>';
  return '<span class="chip chip-none">無基準</span>';
}

// 官方文件對照狀態的唯一渲染來源（spec 卡片、Spec 全文共用——不准各寫各的）。
// 使用者真正要回答的問題是「這份 spec 可不可信」：沒對照過原廠文件的內容
// 一律要講出來，不准用沉默假裝已驗證（CLAUDE.md 不變條件 5）。
function verifyChipHtml(s){
  // 講「位元定義」而不是含糊的「已對照」：對照過的是欄位切分，不代表這份
  // spec 的暫存器清單就是完整的（那要看 Status 的 ⚠ 與檔內的落差清單）
  var n = s.register_count || 0, v = s.verified_count || 0;
  if (n && v === n) return '<span class="chip chip-builtin">位元定義已對照官方 ' + v + '/' + n + '</span>';
  if (v) return '<span class="chip chip-warn">位元定義已對照官方 ' + v + '/' + n + '</span>';
  return '<span class="chip chip-none">位元定義尚未對照官方 0/' + n + '</span>';
}

// 單顆暫存器的對照狀態。always=false 時「未對照」不出 chip（每顆都掛灰標籤
// 只會變成雜訊）；Spec 全文是稽核頁面，兩種狀態都必須明講。
function verifyRegChipHtml(r, always){
  if (r.verified) return '<span class="chip chip-builtin" title="' + esc(r.verified) + '">位元定義已對照官方</span>';
  return always ? '<span class="chip chip-none">未對照官方文件</span>' : '';
}

function toggleHideRes(){ S.hideRes = !S.hideRes; renderView(); }

// ────────────────────────────────────────────────────────────────────
// 渲染
// ────────────────────────────────────────────────────────────────────
function renderAll(){
  var hasBin = S.payload && S.payload.bin;
  document.getElementById('binChip').textContent = hasBin
    ? S.payload.bin.name + '（' + S.payload.bin.size.toLocaleString() + ' bytes）'
    : '未載入 bin（spec 閱讀模式）';

  var sel = document.getElementById('specSelect');
  sel.innerHTML = groupSpecsByVendor(S.specs).map(function(g){
    return '<optgroup label="' + esc(g[0]) + '">' + g[1].map(function(s){
      return '<option value="' + esc(s.id) + '">' + esc(s.display_name) + '</option>';
    }).join('') + '</optgroup>';
  }).join('');
  if (S.payload) sel.value = S.payload.spec.id;

  document.getElementById('navRegCount').textContent = S.payload ? S.payload.stats.total : '';
  document.querySelectorAll('.nav-item').forEach(function(b){
    b.classList.toggle('active', b.getAttribute('data-view') === S.view);
  });
  renderView();
}

// 「找不到 spec」不能只是一句話 —— 直接把掃描結果攤開，
// 使用者／維護者一眼就知道是資源沒解壓、目錄不在、還是檔案被擋掉。
function noSpecHtml(){
  var h = '<div class="empty"><div class="big">📂</div>';
  h += '<p><b>找不到任何 CPU spec</b><br>正常情況下軟體內建 ARM Cortex-R5／A55 與 Andes N25／N45 四份。</p></div>';
  if (S.lastError) {
    h += '<div class="banner" style="margin-top:14px">⚠ ' + esc(S.lastError) + '</div>';
  }
  var d = S.diag;
  if (d) {
    h += '<div class="card" style="margin-top:14px">';
    h += '<div class="section-title" style="margin-top:0">診斷資訊</div>';
    h += '<div class="doc-meta">版本 v' + esc(d.version) +
         '　執行方式：' + (d.frozen ? '打包後的 exe' : '開發模式') + '</div>';
    h += '<div class="table-wrap" style="margin-top:10px"><table><thead><tr>' +
         '<th>搜尋的 spec 目錄</th><th>目錄存在</th><th>載入份數</th></tr></thead><tbody>';
    (d.scan || []).forEach(function(row){
      h += '<tr><td class="mono" style="word-break:break-all">' + esc(row.dir) + '</td>' +
           '<td>' + (row.exists ? '<span class="chip chip-same">是</span>'
                                : '<span class="chip chip-warn">否</span>') + '</td>' +
           '<td class="mono">' + row.loaded + '</td></tr>';
    });
    h += '</tbody></table></div>';
    h += '<div class="doc-meta" style="margin-top:10px">' +
         '<b>可以這樣救：</b>在上表第二個目錄（exe 旁邊）建立 <span class="mono">specs\\廠商\\型號.md</span>，' +
         '或用「Spec 管理 → 載入外部 Spec」直接指定檔案。<br>' +
         '詳細錯誤在 log：<span class="mono">' + esc(d.log_path) + '</span></div>';
    h += '</div>';
  }
  return h;
}

function renderView(){
  var el = document.getElementById('view');
  // 重繪會換掉整個 innerHTML：先記住搜尋框是否持有焦點，繪完還回去
  var hadFocus = document.activeElement && document.activeElement.id === 'searchInput';
  if (!S.payload && S.view !== 'specs' && !(S.view === 'specdoc' && S.doc)) {
    el.innerHTML = S.inited ? noSpecHtml() :
      '<div class="empty"><div class="big">🕐</div><p>載入中…</p></div>';
    return;
  }
  if (S.view === 'overview') el.innerHTML = renderOverview();
  else if (S.view === 'regs') el.innerHTML = renderRegs();
  else if (S.view === 'lookup') el.innerHTML = renderLookup();
  else if (S.view === 'hex') el.innerHTML = renderHex();
  else if (S.view === 'specdoc') el.innerHTML = renderSpecDoc();
  else el.innerHTML = renderSpecs();
  var q = document.getElementById('searchInput');
  if (q) {
    q.value = S.q;
    if (hadFocus) { q.focus(); q.setSelectionRange(q.value.length, q.value.length); }
  }
  // 反查輸入框：重繪後把使用者打到一半的內容還回去
  var lq = document.getElementById('lkQuery');
  var lv = document.getElementById('lkValue');
  if (lq) lq.value = S.lk.q;
  if (lv) lv.value = S.lk.v;
}

// ── 總覽 ───────────────────────────────────────────────────────────
function renderOverview(){
  var p = S.payload, st = p.stats, h = '';
  var warnCount = p.spec.warnings.length;

  h += '<div class="cards">';
  h += '<div class="card"><div class="card-num" style="font-size:17px; line-height:2.1">' + esc(p.spec.display_name) + '</div>' +
       '<div class="card-label">目前 Spec ・ ' + st.total + ' 個暫存器</div>' +
       (p.spec.source ? '<div class="card-sub">' + esc(p.spec.source) + '</div>' : '') + '</div>';
  if (p.bin) {
    h += '<div class="card"><div class="card-num" style="font-size:17px; line-height:2.1">' + esc(p.bin.name) + '</div>' +
         '<div class="card-label">bin 檔 ・ ' + p.bin.size.toLocaleString() + ' bytes</div></div>';
    h += '<div class="card"><div class="card-num">' + st.covered + '<span class="muted" style="font-size:15px">/' + st.total + '</span></div><div class="card-label">有值的暫存器</div></div>';
    h += '<div class="card clickable" onclick="setOnlyDiff(true); nav(\'regs\')"><div class="card-num accent">' + st.differs + '</div><div class="card-label">與 Reset 不同</div></div>';
  }
  h += '</div>';

  if (warnCount) {
    h += '<div class="card card-warn clickable" style="margin-bottom:14px" onclick="nav(\'specs\')">⚠ 這份 spec 有 ' +
         warnCount + ' 個解析警告，內容可能不完整 — 點此到「Spec 管理」檢視</div>';
  }
  if (p.hexdump && p.hexdump.note) {
    h += '<div class="banner">⚠ ' + esc(p.hexdump.note) + '</div>';
  }

  if (!p.bin) {
    h += '<div class="empty"><div class="big">📥</div>' +
         '<p>匯入 register dump（raw bin、little-endian）後，這裡會依「' + esc(p.spec.display_name) +
         '」spec 解碼每個暫存器。<br>現在也可以直接到「暫存器」頁把這份 spec 當手冊翻。</p>' +
         '<button class="btn-accent" onclick="importBin()">匯入 bin 檔</button></div>';
    return h;
  }

  var diffs = p.registers.filter(function(r){ return r.differs === true; });
  h += '<div class="section-title">與 Reset 不同的暫存器 <span class="muted">(' + diffs.length + ')</span></div>';
  if (!diffs.length) {
    h += '<div class="banner info">所有可比較的暫存器都與 Reset 相同。</div>';
  } else {
    h += '<div class="table-wrap"><table><thead><tr><th>暫存器</th><th>Offset</th><th>目前值</th><th>Reset</th><th>不同的欄位</th></tr></thead><tbody>';
    diffs.forEach(function(r){
      var changed = r.rows.filter(function(f){ return f.differs === true; }).map(function(f){ return f.name; });
      h += '<tr class="reg-row" onclick="goReg(\'' + jsq(r.name) + '\')">' +
           '<td class="reg-name">' + esc(r.name) + '</td>' +
           '<td class="mono muted">' + r.offset_hex + '</td>' +
           '<td class="mono">' + r.value_hex + '</td>' +
           '<td class="mono muted">' + (r.reset_hex || '—') + '</td>' +
           '<td>' + esc(changed.join('、') || '（依欄位無法判定）') + '</td></tr>';
    });
    h += '</tbody></table></div>';
  }

  var uncovered = p.registers.filter(function(r){ return !r.covered; });
  if (uncovered.length) {
    h += '<div class="section-title">bin 未涵蓋的暫存器 <span class="muted">(' + uncovered.length + ')</span></div>';
    h += '<div class="banner">' + uncovered.map(function(r){ return esc(r.name); }).join('、') +
         '：bin 檔長度不足（檔案 ' + st.bin_size + ' bytes，spec 定義到 0x' +
         st.spec_span_bytes.toString(16).toUpperCase() + '）。</div>';
  }
  return h;
}

// ── 暫存器 ─────────────────────────────────────────────────────────
function renderRegs(){
  var regs = visibleRegs();
  var hasBin = !!S.payload.bin;
  var h = '<div class="toolbar">';
  h += '<input id="searchInput" class="search-input" placeholder="搜尋暫存器 / 欄位 / 說明…" oninput="setQuery(this.value)">';
  if (hasBin) {
    h += '<div class="seg">' +
         '<button class="' + (S.onlyDiff ? '' : 'active') + '" onclick="setOnlyDiff(false)">全部</button>' +
         '<button class="' + (S.onlyDiff ? 'active' : '') + '" onclick="setOnlyDiff(true)">≠ Reset</button></div>';
  }
  h += '<button class="btn" onclick="setAll(true)">全部展開</button>';
  h += '<button class="btn" onclick="setAll(false)">全部收合</button>';
  h += '<button class="btn" onclick="toggleHideRes()">' + (S.hideRes ? '顯示保留位' : '隱藏保留位') + '</button>';
  h += '<button class="btn" onclick="exportReport()">匯出報告 (.md)</button>';
  h += '</div>';

  if (!regs.length) {
    h += '<div class="empty"><div class="big">🔍</div><p>沒有符合條件的暫存器</p></div>';
    return h;
  }

  h += '<div class="table-wrap"><table><thead><tr>' +
       '<th></th><th>暫存器</th><th>Offset</th><th>目前值</th><th>Reset</th>' +
       (hasBin ? '<th>狀態</th>' : '') + '<th>說明</th></tr></thead><tbody>';
  regs.forEach(function(r, ri){
    var open = !!S.expanded[r.name];
    h += '<tr class="reg-row' + (open ? ' open' : '') + '" id="reg-' + cssId(r.name) + '" onclick="toggleReg(\'' + jsq(r.name) + '\')">';
    h += '<td class="caret">' + (open ? '▼' : '▶') + '</td>';
    h += '<td class="reg-name">' + esc(r.name) + '</td>';
    h += '<td class="mono muted">' + r.offset_hex + '</td>';
    h += '<td class="mono' + (r.differs === true ? ' val-accent' : '') + '">' +
         (r.value_hex || '<span class="muted">—</span>') + '</td>';
    h += '<td class="mono muted">' + (r.reset_hex || '—') + '</td>';
    if (hasBin) h += '<td>' + statusChipHtml(r, false) + '</td>';
    h += '<td class="reg-desc">' + esc(r.desc || '') + '</td></tr>';
    if (open) {
      h += '<tr class="detail-row"><td colspan="' + (hasBin ? 7 : 6) + '">' + registerBlock(r, ri, {}) + '</td></tr>';
    }
  });
  h += '</tbody></table></div>';
  return h;
}

// 單一暫存器的完整呈現（標頭「目前值/Reset」成對＋bit ruler＋欄位表）。
// 「暫存器」展開與「快速反查」共用這一支 —— 同一種資訊只准有一份渲染程式，
// 避免改 A 壞 B（CLAUDE.md 不變條件 12）。
function registerBlock(r, ri, opts){
  opts = opts || {};
  var h = '<div class="detail-head">';
  if (opts.showName) h += '<span class="reg-name" style="font-size:15px">' + esc(r.name) + '</span>';
  if (r.value_hex) {
    h += '<span class="kv"><span class="kv-label">目前值</span>' +
         '<span class="detail-val' + (r.differs === true ? ' val-accent' : '') + '">' + r.value_hex + '</span></span>';
  }
  h += '<span class="kv"><span class="kv-label">Reset</span>' +
       '<span class="detail-val muted">' + (r.reset_hex || '—') + '</span></span>';
  h += '<span class="detail-meta">' + r.size + '-bit ・ Offset ' + r.offset_hex + '</span>';
  if (r.differs === true) h += '<span class="chip chip-diff">≠ Reset</span>';
  if (r.nonzero_undef) h += '<span class="chip chip-warn">未定義位元有非 0 值</span>';
  h += verifyRegChipHtml(r, false);
  h += '</div>';
  if (opts.showDesc && r.desc) h += '<div class="reg-desc" style="margin-bottom:4px">' + esc(r.desc) + '</div>';
  h += bitRuler(r, ri);
  h += fieldTable(r, ri, { hideReserved: S.hideRes });
  return h;
}

function bitRuler(r, ri){
  var h = '<div class="bitruler">';
  r.rows.forEach(function(row, fi){
    var cls = 'bitgroup' +
      (row.differs === true ? ' diff' : '') +
      ((row.reserved || row.kind === 'undef') && row.differs !== true ? ' res' : '');
    h += '<div class="' + cls + '" onclick="focusField(' + ri + ',' + fi + ')" title="' +
         esc(row.name + ' [' + row.bits + ']' + (row.enum_label ? '：' + row.enum_label : '')) + '">';
    h += '<div class="bitidx"><span>' + row.msb + '</span>' + (row.msb !== row.lsb ? '<span>' + row.lsb + '</span>' : '') + '</div>';
    h += '<div class="bitcells">';
    for (var b = row.msb; b >= row.lsb; b--) {
      var v = r.value_bits ? r.value_bits.charAt(r.size - 1 - b) : '';
      h += '<div class="bitcell">' + v + '</div>';
    }
    h += '</div><div class="bitlabel">' + esc(row.name) + '</div></div>';
  });
  return h + '</div>';
}

function fieldTable(r, ri, opts){
  opts = opts || {};
  var hasVal = !!r.value_hex;
  var hidden = 0;
  // 欄位順序刻意讓「目前值」與「Reset」相鄰：一眼比對，不用左右掃（設計如此）
  var h = '<div class="table-wrap" style="margin-bottom:0"><table class="field-table"><thead><tr>' +
          '<th>Bits</th><th>欄位</th>' + (hasVal ? '<th>目前值</th>' : '') +
          '<th>Reset</th><th>意義</th><th>Access</th></tr></thead><tbody>';
  r.rows.forEach(function(f, fi){
    var dim = f.reserved || f.kind === 'undef';
    // 降噪：與 Reset 相同的保留／未定義位元預設隱藏；「異常的保留位」
    //（值≠Reset、未定義非 0）一律強制顯示 —— 這是安全網，不准藏掉異常（設計如此）
    if (opts.hideReserved && dim && f.differs !== true && !f.nonzero) { hidden++; return; }
    h += '<tr class="frow' + (dim ? ' dim' : '') + (f.differs === true ? ' diff' : '') + '" id="ft-' + ri + '-' + fi + '">';
    h += '<td class="mono muted">' + f.bits + '</td>';
    h += '<td class="fname">' + esc(f.name) + '</td>';
    if (hasVal) {
      var v = f.value_hex || '—';
      var sub = '';
      if (f.value_bin && (f.msb - f.lsb + 1) <= 16) sub = f.value_bin;
      else if (f.value_dec && (f.msb - f.lsb + 1) > 4) sub = f.value_dec + ' (dec)';
      h += '<td class="mono' + (f.differs === true ? ' val-accent' : '') + '">' + v +
           (sub ? '<br><span class="muted" style="font-size:11px">' + sub + '</span>' : '') + '</td>';
    }
    h += '<td class="mono muted">' + (f.reset_hex || '—') + '</td>';
    h += '<td class="fmeaning">' + meaningCell(f, opts.expandEnums) + '</td>';
    h += '<td class="mono muted">' + esc(f.access || '') + '</td>';
    h += '</tr>';
  });
  if (hidden) {
    h += '<tr class="frow dim"><td colspan="' + (hasVal ? 6 : 5) + '" style="cursor:pointer" ' +
         'onclick="toggleHideRes()">… 已隱藏 ' + hidden + ' 個與 Reset 相同的保留／未定義位元（點此顯示）</td></tr>';
  }
  return h + '</tbody></table></div>';
}

function meaningCell(f, expandEnums){
  var h = '';
  if (f.enum_label) {
    h += '<b>' + esc(f.enum_label) + '</b>';
    if (f.desc) h += '<span class="fdesc">' + esc(f.desc) + '</span>';
  } else {
    h += esc(f.desc || '');
  }
  if (f.enum && f.enum.length) {
    if (expandEnums) {
      // Spec 全文（稽核）模式：列舉全表直接攤開，方便逐項對照 TRM
      h += '<table class="enum-inline">';
      f.enum.forEach(function(e){
        h += '<tr><td class="mono">' + esc(e.v) + '</td><td>' + esc(e.label) + '</td></tr>';
      });
      h += '</table>';
    } else {
      h += '<details class="enum-details"><summary>全部數值（' + f.enum.length + '）</summary><table class="enum-table">';
      f.enum.forEach(function(e){
        h += '<tr' + (e.current ? ' class="current"' : '') + '><td class="mono">' + esc(e.v) + '</td><td>' +
             esc(e.label) + (e.current ? '　← 目前值' : '') + '</td></tr>';
      });
      h += '</table></details>';
    }
  }
  return h;
}

// ── Spec 全文（稽核目前依據的 spec 是否正確）───────────────────────
function renderSpecDoc(){
  if (!S.doc) {
    return '<div class="empty"><div class="big">📖</div><p>載入 Spec 全文中…</p></div>';
  }
  var s = S.doc.summary;
  var h = '<div class="doc-head card">';
  h += '<div class="spec-card-head">';
  h += '<span class="spec-card-name" style="font-size:16px">' + esc(s.display_name) + '</span>';
  h += '<span class="chip ' + (s.origin === 'external' ? 'chip-ext' : 'chip-builtin') + '">' +
       (s.origin === 'external' ? '外部載入' : '內建（隨 exe 打包）') + '</span>';
  h += '<span class="chip chip-same">' + s.register_count + ' 個暫存器</span>';
  h += verifyChipHtml(s);
  if (s.warnings.length) h += '<span class="chip chip-warn">' + s.warnings.length + ' 個解析警告</span>';
  h += '</div>';
  var overlaid = S.doc.registers.some(function(r){ return r.value_hex; });
  h += '<div class="doc-meta">';
  h += '本頁是軟體<b>實際依據</b>的 spec 內容（解析後），分析結果對不對、先從這裡查。';
  h += overlaid
    ? '目前已載入 bin，下方同頁疊上<b>目前值</b>（藍色＝與 Reset 不同）。'
    : '載入 bin 後，本頁會同頁疊上目前值（僅目前使用中的 spec）。';
  if (s.status) h += '<br>查核狀態：<b>' + esc(s.status) + '</b>';
  if (s.source) h += '<br>來源文件：<b>' + esc(s.source) + '</b>';
  if (s.path) h += '<br>檔案：<span class="mono">' + esc(s.path) + '</span>';
  if (s.desc) h += '<br>' + esc(s.desc);
  h += '</div>';
  if (s.warnings.length) {
    h += '<details class="spec-warnings"><summary>解析警告（' + s.warnings.length + '）—— 有警告代表下面的內容可能不完整</summary><ul>';
    s.warnings.forEach(function(w){ h += '<li>' + esc(w) + '</li>'; });
    h += '</ul></details>';
  }
  h += '</div>';

  h += '<div class="toolbar"><div class="seg">' +
       '<button class="' + (S.docTab === 'parsed' ? 'active' : '') + '" onclick="setDocTab(\'parsed\')">解析後內容（引擎實際使用）</button>' +
       '<button class="' + (S.docTab === 'raw' ? 'active' : '') + '" onclick="setDocTab(\'raw\')">原始 Markdown</button>' +
       '</div></div>';

  if (S.docTab === 'raw') {
    if (S.doc.raw == null) {
      h += '<div class="banner">⚠ ' + esc(S.doc.raw_error || '無法取得原始檔') + '</div>';
    } else {
      h += '<div class="rawspec">' + esc(S.doc.raw) + '</div>';
    }
    return h;
  }

  S.doc.registers.forEach(function(r, ri){
    h += '<div class="table-wrap">';
    h += '<div class="doc-reg-head">';
    h += '<span class="doc-reg-name">' + esc(r.name) + '</span>';
    h += '<span class="doc-reg-meta">Offset ' + r.offset_hex + ' ・ ' + r.size + '-bit</span>';
    h += '<span class="doc-reg-meta">Reset ' + (r.reset_hex || '—（未知／依組態）') + '</span>';
    if (r.value_hex) {
      h += '<span class="doc-reg-meta">目前值 <b class="' + (r.differs === true ? 'val-accent' : '') + '">' +
           r.value_hex + '</b></span>';
      if (r.differs === true) h += '<span class="chip chip-diff">≠ Reset</span>';
    }
    h += verifyRegChipHtml(r, true);
    h += '</div>';
    if (r.desc) h += '<div class="doc-reg-desc">' + esc(r.desc) + '</div>';
    // 出處只在「有對照過」時展開一行（每顆都印一句「沒對照」＝17 行雜訊，
    // 未對照用標頭那顆 chip 講就夠了）
    if (r.verified) h += '<div class="doc-reg-verify">✔ 位元定義對照自：' + esc(r.verified) + '</div>';
    h += fieldTable(r, 'doc' + ri, { expandEnums: true });
    h += '</div>';
  });
  return h;
}

// ── 快速反查：offset（或名稱）＋值 → 單筆解碼，免做 bin 檔 ──────────
function renderLookup(){
  // 預覽模式：塞示範結果讓截圖看得到成品
  if (window.__PREVIEW__ && window.__PREVIEW__.lookup_demo && !S.lk.result && !S.lk.error && !S.lk.q) {
    var d = window.__PREVIEW__.lookup_demo;
    S.lk.q = 'SCTLR'; S.lk.v = '0x00C7187D';
    S.lk.result = d.register; S.lk.note = d.note;
  }
  var specName = S.payload ? S.payload.spec.display_name : '';
  var h = '<div class="card" style="margin-bottom:14px">';
  h += '<div class="lk-form">';
  h += '<span class="kv" style="flex:1; min-width:220px"><span class="kv-label">暫存器（名稱或 Offset）</span>' +
       '<input id="lkQuery" class="search-input mono" style="max-width:none" list="lkRegs" placeholder="例：SCTLR 或 0x010"' +
       ' oninput="S.lk.q=this.value" onchange="S.lk.q=this.value" onkeydown="if(event.key===\'Enter\')doLookup()"></span>';
  h += '<span class="kv" style="flex:1.4; min-width:260px"><span class="kv-label">值（0x…／0b…／十進位）</span>' +
       '<input id="lkValue" class="search-input mono" style="max-width:none" placeholder="例：0x00C7187D"' +
       ' oninput="S.lk.v=this.value" onchange="S.lk.v=this.value" onkeydown="if(event.key===\'Enter\')doLookup()"></span>';
  h += '<button class="btn-accent" onclick="doLookup()">解碼</button>';
  h += '</div>';
  h += '<datalist id="lkRegs">';
  (S.payload ? S.payload.registers : []).forEach(function(r){
    h += '<option value="' + esc(r.name) + '">' + r.offset_hex + '　' + esc(r.desc || '') + '</option>';
  });
  h += '</datalist>';
  h += '<div class="doc-meta" style="margin-top:8px">依目前 spec「' + esc(specName) +
       '」解碼；只有一組值要查時不用做 bin 檔。按 Enter 也可解碼。</div>';
  h += '</div>';

  if (S.lk.error) h += '<div class="banner">⚠ ' + esc(S.lk.error) + '</div>';
  if (S.lk.note) h += '<div class="banner info">ℹ ' + esc(S.lk.note) + '</div>';

  var r = S.lk.result;
  if (r) {
    // 與「暫存器」展開共用同一支 registerBlock —— 呈現永遠一致
    h += '<div class="lk-detail">' + registerBlock(r, 'lk', { showName: true, showDesc: true }) + '</div>';
  } else if (!S.lk.error) {
    h += '<div class="empty"><div class="big">🔍</div><p>輸入暫存器（可打名稱，會自動提示）與讀到的值，立即解碼<br>' +
         '不用準備 bin 檔 —— 適合只想確認一兩個暫存器的時候。</p></div>';
  }

  if (S.lk.history.length) {
    h += '<div class="section-title" style="margin-top:18px">最近查詢 <span class="muted">(' + S.lk.history.length + ')</span>' +
         '　<button class="btn" style="font-size:11px; padding:3px 8px" onclick="clearLookupHistory()">清除</button></div>';
    h += '<div class="table-wrap"><table><thead><tr><th>暫存器</th><th>Offset</th><th>值</th><th>狀態</th></tr></thead><tbody>';
    S.lk.history.forEach(function(entry, i){
      var hr = entry.register;
      h += '<tr class="reg-row" onclick="lookupFromHistory(' + i + ')">' +
           '<td class="reg-name">' + esc(hr.name) + '</td>' +
           '<td class="mono muted">' + hr.offset_hex + '</td>' +
           '<td class="mono' + (hr.differs === true ? ' val-accent' : '') + '">' + hr.value_hex + '</td>' +
           '<td>' + statusChipHtml(hr, true) + '</td></tr>';
    });
    h += '</tbody></table></div>';
  }
  return h;
}

function doLookup(){
  var q = document.getElementById('lkQuery');
  var v = document.getElementById('lkValue');
  if (q) S.lk.q = q.value;
  if (v) S.lk.v = v.value;
  api('lookup', S.lk.q, S.lk.v).then(function(resp){
    if (!resp) return;
    if (!resp.ok) { S.lk.error = resp.error || '查詢失敗'; S.lk.result = null; S.lk.note = null; }
    else {
      S.lk.error = null; S.lk.result = resp.register; S.lk.note = resp.note || null;
      S.lk.spec_id = resp.spec_id || (S.payload ? S.payload.spec.id : null);
      S.lk.history.unshift({ register: resp.register, note: resp.note || null });
      if (S.lk.history.length > 10) S.lk.history.pop();
    }
    renderView();
  }).catch(apiFail);
}
function lookupFromHistory(i){
  var entry = S.lk.history[i];
  if (!entry) return;
  S.lk.result = entry.register; S.lk.note = entry.note; S.lk.error = null;
  renderView();
}
function clearLookupHistory(){ S.lk.history = []; renderView(); }

// ── 原始資料（hex dump + 暫存器對照）───────────────────────────────
function renderHex(){
  var p = S.payload;
  if (!p.bin) {
    return '<div class="empty"><div class="big">🔢</div><p>尚未載入 bin 檔。</p>' +
           '<button class="btn-accent" onclick="importBin()">匯入 bin 檔</button></div>';
  }
  var diffMap = {};
  p.registers.forEach(function(r){ diffMap[r.name] = (r.differs === true); });

  var h = '<div class="toolbar"><span class="muted" style="font-size:12.5px">' +
          '每格一個 32-bit word（little-endian 組回的值），下方標註對應的暫存器；點格子可跳到該暫存器。</span></div>';
  if (p.hexdump.note) h += '<div class="banner">⚠ ' + esc(p.hexdump.note) + '</div>';
  h += '<div class="table-wrap"><table class="hex-table"><thead><tr>' +
       '<th>Offset</th><th>+0x0</th><th>+0x4</th><th>+0x8</th><th>+0xC</th></tr></thead><tbody>';
  p.hexdump.rows.forEach(function(row){
    h += '<tr><td class="hex-off">' + row.offset_hex + '</td>';
    row.words.forEach(function(w){
      var base = w.reg ? w.reg.replace(/ \[.*$/, '') : null;
      var diff = base && diffMap[base];
      h += '<td>';
      if (w.partial) {
        h += '<div class="hw-val muted">' + esc(w.hex) + '</div><div class="hw-reg">（不足一個 word）</div>';
      } else if (base) {
        h += '<div class="hexword" onclick="goReg(\'' + jsq(base) + '\')">' +
             '<div class="hw-val' + (diff ? ' diff' : '') + '">' + esc(w.hex) + '</div>' +
             '<div class="hw-reg">' + esc(w.reg) + (diff ? ' ・ ≠Reset' : '') + '</div></div>';
      } else {
        h += '<div class="hw-val muted">' + esc(w.hex) + '</div><div class="hw-reg">未對應</div>';
      }
      h += '</td>';
    });
    for (var i = row.words.length; i < 4; i++) h += '<td></td>';
    h += '</tr>';
  });
  h += '</tbody></table></div>';
  return h;
}

// ── Spec 管理 ──────────────────────────────────────────────────────
function renderSpecs(){
  var cur = S.payload ? S.payload.spec.id : null;
  var h = '<div class="toolbar">' +
          '<button class="btn-accent" onclick="addSpec()">載入外部 Spec（.md）</button>' +
          '<button class="btn" onclick="reloadSpecs()">重新載入全部</button>' +
          '</div>';
  h += '<div class="banner info">內建 spec 打包在執行檔內；外部 spec 供測試新格式，' +
       '修改 .md 存檔後按「重新載入全部」即可更新。格式說明見 repo 的 SPEC_FORMAT.md。</div>';
  if (!S.specs.length) {
    h += '<div class="empty"><div class="big">📚</div><p>沒有任何 spec</p></div>';
    return h;
  }
  groupSpecsByVendor(S.specs).forEach(function(g){
    h += '<div class="section-title">' + esc(g[0]) + ' <span class="muted">(' + g[1].length + ')</span></div>';
    g[1].forEach(function(s){ h += specCard(s, cur); });
  });
  return h;
}

function specCard(s, cur){
  var h = '';
  {
    var isCur = s.id === cur;
    h += '<div class="spec-card' + (isCur ? ' current' : '') + '">';
    h += '<div class="spec-card-head">';
    h += '<span class="spec-card-name">' + esc(s.display_name) + '</span>';
    h += '<span class="chip ' + (s.origin === 'external' ? 'chip-ext' : 'chip-builtin') + '">' +
         (s.origin === 'external' ? '外部' : '內建') + '</span>';
    h += '<span class="chip chip-same">' + s.register_count + ' 個暫存器</span>';
    h += verifyChipHtml(s);
    if (s.warnings.length) h += '<span class="chip chip-warn">' + s.warnings.length + ' 個警告</span>';
    if (isCur) h += '<span class="chip chip-diff">使用中</span>';
    h += '<span class="spec-card-actions">';
    h += '<button class="btn" onclick="openSpecDoc(\'' + jsq(s.id) + '\')">檢視全文</button>';
    if (!isCur) h += '<button class="btn" onclick="chooseSpec(\'' + jsq(s.id) + '\')">使用</button>';
    if (s.origin === 'external') h += '<button class="btn" onclick="removeSpec(\'' + jsq(s.id) + '\')">移除</button>';
    h += '</span></div>';
    if (s.status) h += '<div class="spec-status">查核狀態：' + esc(s.status) + '</div>';
    if (s.desc) h += '<div class="reg-desc" style="margin-top:6px">' + esc(s.desc) + '</div>';
    if (s.origin === 'external' && s.path) h += '<div class="spec-card-path">' + esc(s.path) + '</div>';
    if (s.warnings.length) {
      h += '<details class="spec-warnings"><summary>解析警告（' + s.warnings.length + '）</summary><ul>';
      s.warnings.forEach(function(w){ h += '<li>' + esc(w) + '</li>'; });
      h += '</ul></details>';
    }
    h += '</div>';
  }
  return h;
}
</script>
</body>
</html>
"""


def build_main_html(theme_attr: str = "") -> str:
    """組出最終 HTML：注入色票、主題屬性與版本號。

    theme_attr: '' 或 'data-theme="dark"'（由 main.py 依 OS／設定決定）。
    """
    html = MAIN_HTML.replace("__THEME_ROOT_CSS__", THEME_ROOT_CSS)
    html = html.replace("__html_theme_attr__", theme_attr)
    html = html.replace("__APP_VERSION__", APP_VERSION)
    return html
