# IC Debugger

CPU register dump 分析工具（Windows 桌面程式）。把 debugger dump 出來的
register 值（raw bin）匯入後，依內建的 CPU spec 自動解碼每一個暫存器：
名稱、目前值、每個 bit field 的意義、與 reset 值的差異 —— 不用再翻 spec PDF。

內建四顆 CPU 的 spec，在畫面右上角依廠商分組切換：

| 廠商 | 型號 | 內容 |
|---|---|---|
| ARM | Cortex-R5 | ARMv7-R CP15 系統控制、故障狀態、MPU 區域暫存器 |
| ARM | Cortex-A55 | ARMv8.2-A AArch64 EL1 系統暫存器（64-bit） |
| Andes | N25 | RISC-V RV32 標準機器模式 CSR |
| Andes | N45 | RISC-V RV32 標準機器模式 CSR |

spec 以 Markdown 檔維護在 [`specs/<廠商>/`](specs/)，push 後由 CI 自動打包出新的 exe。

> ⚠ **這四份 spec 各驗到什麼程度，app 會直接標在畫面上**（Spec 管理卡片顯示
> 「位元定義已對照官方 X/N」，「Spec 全文」頁每顆暫存器標出處或「未對照官方文件」）：
>
> | Spec | 位元定義已對照 | 對照的官方文件 |
> |---|---|---|
> | ARM Cortex-R5 | 58/60 | ARM DDI 0406C.d 官方 PDF（ARMv7-A/R ARM）＋DDI 0460D（TCMTR） |
> | Andes N25／N45 | 90/90 | RISC-V 特權架構規格 v1.11 ＋ Andes 官方 QEMU（andestech/qemu） |
> | ARM Cortex-A55 | 44/55 | Arm 機讀架構規格（sail-arm）＋ARM 官方 TF-A（實作定義顆） |
>
> 「位元定義已對照」只保證**欄位切在第幾位元**是照官方文件抄的。它不保證
> 暫存器清單完整、也不保證 Reset 值正確 —— 那些只有晶片 TRM／datasheet 說了算，
> 而 `TCMTR`、`micm_cfg` 這類實作相關暫存器只存在於 TRM。每份 spec 的檔頭
> 註解都列了「已驗／未驗／還缺哪些暫存器」。有原廠文件的人請照
> [specs/README.md](specs/README.md) 的流程補，對完一顆就在該顆加一行
> `- Verified: <文件編號 §章節/表號>`。

**下載**：到 [Releases](../../releases) 抓最新 `build-*` 的 `IC_Debugger.exe`，
單一執行檔，下載後直接執行。
（未簽章的下載檔第一次執行會跳 Windows SmartScreen：點「其他資訊」→「仍要執行」。）

## 使用流程

1. 右上角選擇 CPU spec（沒匯入 bin 時，「暫存器」頁就是一份可搜尋的 spec 手冊）。
2. 「匯入 bin」選擇 register dump 檔。
3. 「總覽」看統計與「與 Reset 不同」清單；「暫存器」逐一展開看 bit ruler
   與欄位解碼；「原始資料」檢查 dump 與 spec 的對齊；「匯出報告 (.md)」把
   結果帶去寫 issue。
4. 只想查一兩個暫存器？用「**快速反查**」：輸入暫存器名稱（或 offset）＋
   讀到的值，立即解碼，免做 bin 檔。
5. 視窗按「縮小」會收到**右下角系統列**（雙擊圖示叫回來）；按「X」才是
   真正關閉。與 Reset 相同的保留位元預設收合，按「顯示保留位」展開。

> **想加 spec 又不想等重新 build？** 在 `IC_Debugger.exe` 旁邊建一個
> `specs\<廠商>\<型號>.md`，啟動時會自動一起載入。
> 萬一畫面顯示「找不到任何 CPU spec」，上面會直接列出軟體搜尋過的目錄與
> log 路徑，照著看就知道問題在哪。

**bin 檔格式約定**：純 raw dump、little-endian，從 spec 的第一個暫存器
（Offset 0x000）開始依序排列；每個暫存器佔 Size/8 bytes（預設 32-bit＝4 bytes）。

## 新增／更新 CPU spec

1. 依 [SPEC_FORMAT.md](SPEC_FORMAT.md) 的格式寫一份 `specs/<廠商>/<型號>.md`
   （可把該文件內附的指示範本連同 spec 原文交給 AI 產生；目錄規則見
   [specs/README.md](specs/README.md)）。
2. 先在 app 內「Spec 管理 → 載入外部 Spec」載入測試，把解析警告清乾淨。
3. 用「Spec 全文」對著原廠文件逐顆核對，核完一顆就補一行
   `- Verified: <文件編號 §章節/表號>`（沒真的對照過就不要寫）。
4. 放進 `specs/<廠商>/`、push 到 `main` → CI 自動重新打包並發佈 Release（保留最新 2 個）。

## 開發快速上手

```bash
python main.py                       # 開發模式直接跑（Windows；免打包）
PYTHONPATH=. pytest tests/ -q        # 全套測試（push 前必須全綠）
PYTHONPATH=. python tools/preview.py # 免 GUI 渲染 UI + 截圖（需 playwright）
```

push 到 `main` 即觸發 [auto-build](.github/workflows/auto-build.yml)：
跑測試 → PyInstaller 打包單一 exe → 發佈 Release。
（改根目錄的 `*.md` 說明文件不會觸發；改 `specs/` 內的 spec 一定會觸發。）

| 文件 | 內容 |
|---|---|
| [SPEC_FORMAT.md](SPEC_FORMAT.md) | Spec MD 格式契約＋給 AI 的產生指示範本 |
| [VERIFICATION.md](VERIFICATION.md) | 功能 × 驗證追溯表（窮舉驗證）＋ Windows 實機檢查清單 |
| [CLAUDE.md](CLAUDE.md) | 架構地圖、開發慣例與不變條件（AI 助手也讀這份） |
