# CLAUDE.md — 開發慣例與架構地圖

IC Debugger：Windows 桌面工具，匯入 CPU register raw dump（bin），依 Markdown
spec 解碼呈現每個暫存器與 bit field 的意義。技術棧與 UI 風格沿用 ic-monitor
（Python + pywebview/WebView2 + PyInstaller，深色 topbar/sidebar、淺灰底白卡片、
--c-* design tokens 深淺色）。

## 架構地圖

```
main.py              進入點：logging、讀設定、OS 外觀偵測、開 pywebview 視窗
app_config.py        使用者設定（%APPDATA%/IC_Debugger/config.json）＋ OS 主題偵測
app_state.py         spec 集合／目前選擇／目前 bin 的狀態轉移（純資料，可測）
core/
  spec_loader.py     specs/*.md → Spec/Register/Field 資料模型（寬容輸入、警告帶行號）
  bin_parser.py      raw dump 載入與取值（little-endian）
  analyzer.py        解碼引擎：Spec × Bin → UI payload（值全是格式化字串）
  report.py          payload → Markdown 報告
  resources.py       資源定位（開發＝repo；onefile exe＝sys._MEIPASS）
  version.py         APP_NAME / APP_VERSION 單一來源
ui/
  assets.py          唯一的 UI 文件：THEME_ROOT_CSS tokens ＋ MAIN_HTML（HTML/CSS/JS）
  apis.py            pywebview js_api bridge（唯一 import webview 的模組之一）
specs/               內建 CPU spec（打包進 exe）；格式見 SPEC_FORMAT.md
tools/               preview.py（免 GUI 渲染＋截圖）、make_sample_bin.py
tests/               pytest；CI 的品質關卡
```

## 不變條件（改 code 前先讀）

1. **core/ 不准 import webview／GUI**。測試與 tools/preview.py 直接吃 core＋
   ui.assets；ui/assets.py 也必須維持純字串（不 import webview）。
2. **所有位元運算留在 Python**。payload 裡的值一律是格式化好的字串
   （hex/bin/dec）：64-bit 整數過 JS bridge 會超過 Number 安全範圍掉精度。
   JS 只渲染、過濾，絕不做位元運算。
3. **色票單一來源**：`ui/assets.py` 的 `THEME_ROOT_CSS`（淺色 :root ＋ 深色
   只重定義同組 tokens）。不要在 CSS/JS 撒新的 hex 色碼；新顏色先加 token。
   深色 token 不得多於淺色（test_theme_tokens_complete 會抓）。
4. **MAIN_HTML 是 raw string**（r\"\"\"）夾 JS：改動後靠
   `tests/test_ui.py` 的 node --check 驗語法，佔位符（`__THEME_ROOT_CSS__`／
   `__html_theme_attr__`／`__APP_VERSION__`）只能在 `build_main_html()` 替換。
5. **內建 spec 必須解析零警告**（test_builtin_specs_parse_clean）。改
   spec_loader 的警告文字時同步看測試斷言。
6. **bin 格式契約**：純 raw dump、little-endian、spec 的 Offset＝bin 位元組
   位移（從 0 起）。改這個契約要先跟使用者確認，並同步 SPEC_FORMAT.md 與 README。
7. **WebView2 不回報 OS 深色**到 prefers-color-scheme：深色是 Python 偵測後
   蓋 `data-theme="dark"`（main.py）＋ localStorage 手動覆寫。不要移掉任一半。
8. **打包是 onefile 單一 exe**（ic_debugger_win.spec）：資源一律走
   core/resources.py 的 `resource_dir()`；寫檔（設定、log）一律走
   app_config.py 的使用者目錄，絕不可寫 exe 旁。upx 保持關閉。
9. **CI 的 paths-ignore 只忽略根目錄 `*.md`**：specs/**/*.md 是產品內容，
   改了必須觸發 build。不要改成 `**.md`。
10. requirements 的 pythonnet／clr_loader／PyInstaller 版本 pin 是有前例的
    （見 requirements.txt 註解）：要動就兩個一起動，並用真的從 Releases
    下載的 exe 實測。
11. **驗證追溯**：每個功能行為都在 VERIFICATION.md 有對應的驗證項目
    （窮舉原則）。標「設計如此」的行為是刻意決策，不是 bug，禁止當錯誤
    修掉；新增/變更行為必須同步加測試與追溯列。動手改任何行為之前先查
    VERIFICATION.md 該行為是不是被鎖的設計。
12. **共用原則（防改 A 壞 B）**：同一種資訊只准有一份程式在算/在畫。
    現有的單一來源：解碼＝`_register_dict`（bin 分析、Spec 全文疊值、
    快速反查三條路都走它）、暫存器完整呈現＝JS `registerBlock()`、
    狀態 chip＝`statusChipHtml()`、欄位表＝`fieldTable()`、數值格式
    ＝`fmt_hex`/`fmt_bin`、數值解析＝`parse_int`。新功能要先找有沒有
    現成的可掛，不准為同一件事再寫第二支 function；真的要分岔就加
    參數，並讓測試鎖住兩條路輸出一致（如 test_lookup_identical_to_bin_path）。
13. **系統列語意（使用者指定）**：「縮小」→ 縮到系統列（tray），
    「X」→ 真正關閉。與 ic-monitor 的行為相反，不要照 ic-monitor 改回去。
    tray 不可用（pystray 缺席）時縮小維持一般行為，不得擋啟動。

## 常用指令

```bash
PYTHONPATH=. pytest tests/ -q               # push 前必須全綠
python main.py                              # 開發模式（Windows）
PYTHONPATH=. python tools/preview.py        # 免 GUI 渲染＋截圖驗 UI（改 UI 後必跑）
python tools/make_sample_bin.py             # 重新產生 examples/sample_r5.bin
python create_icon.py                       # 重畫 icon（需 pillow）
```

## Release 流程

push `main` → `.github/workflows/auto-build.yml`：測試 → PyInstaller →
`dist/IC_Debugger.exe` 直接上 Release（tag `build-日期-SHA`，保留最新 2 個）。
沒有手動步驟；build 壞了先看 Actions log 的測試段。
