# Spec MD 檔格式說明

IC Debugger 的 CPU spec 以 Markdown 檔存放在 `specs/<廠商>/<型號>.md`，**build 時整個
目錄會打包進 exe**；app 內也可用「Spec 管理 → 載入外部 Spec」在執行時直接載入 .md 測試，
確認沒問題再放進 `specs/` push（push 到 `main` 會自動觸發 CI 重新打包出新的 exe）。

目錄與命名規則見 [`specs/README.md`](specs/README.md)。完整實例請直接看
[`specs/arm/cortex_r5.md`](specs/arm/cortex_r5.md)（ARMv7-R CP15）、
[`specs/arm/cortex_a55.md`](specs/arm/cortex_a55.md)（AArch64 64-bit）與
[`specs/andes/n25.md`](specs/andes/n25.md)（RISC-V CSR）。

## 檔案結構

一個 `.md` 檔＝一顆 CPU（的一個 spec 版本），放在 `specs/<廠商>/` 底下，檔名建議
`型號.md`（小寫、底線）——**子資料夾名就是 UI 的廠商分組**，檔名就是 app 內部的 spec ID。
`README.md` 與底線開頭的檔案會被略過，可以安心把說明或草稿放在 spec 旁邊。

```markdown
# CPU: ARM Cortex-R5          ← 必填：顯示名稱
# Version: r1p2               ← 建議：spec 版號（顯示在下拉選單）
# Width: 32                   ← 選填：預設暫存器寬度（bit），預設 32，可為 8/16/32/64
# Source: ARM DDI 0460D       ← 選填：spec 出處（追溯用）
# Status: 哪些部分已核對       ← 建議：查核狀態，UI 會顯眼標出（見下方說明）
# Description: 一句話說明      ← 選填

## 暫存器名稱                  ← 每個暫存器一節，「## 」後面只放名稱
- Offset: 0x000               ← 必填：此暫存器在 bin dump 中的位元組位移（16 進位）
- Size: 32                    ← 選填：此暫存器寬度，預設用檔頭 Width
- Reset: 0x411FC152           ← 選填：reset 值；未知寫「-」
- Verified: ARM DDI 0460D §4 Table 4.5   ← 選填：已逐欄對照的官方文件出處
- Description: 一句話說明      ← 選填

| Bits  | Field | Access | Reset | Description |     ← 欄位表（bit field 定義）
|-------|-------|--------|-------|-------------|
| 31:24 | Implementer | RO | 0x41 | 實作者代碼 |
| 0     | M     | RW     | 0     | MPU 致能   |

### Enum: M                   ← 選填：某欄位「每個值代表什麼」
- 0: MPU 關閉
- 1: MPU 開啟
```

## 各部分規則

### Offset（最重要）

- **Offset = 此暫存器的值在 bin 檔中的位元組位移**，從 0 開始，不是 CPU 位址、
  也不是 CSR 編號。bin 是 raw dump（little-endian），app 直接用 Offset 到 bin
  對應位置取值。
- 32-bit 暫存器佔 4 bytes、64-bit 佔 8 bytes；Offset 必須是 4 的倍數。
- **Offset 順序必須與 dump 腳本輸出的順序一致**——第一個被 dump 的暫存器就是
  Offset 0x000，第二個 0x004（32-bit 時），依此類推。

### 欄位表

- 表頭必須含 `Bits` 與 `Field` 兩欄（也接受中文：位元／欄位／存取／重置／說明），
  欄位順序不拘，`Access`、`Reset`、`Description` 可省略。
- `Bits`：`31:24`（高:低）或單一位元 `5`。**整個暫存器的每個 bit 都建議被表列
  涵蓋**；沒涵蓋到的位元 app 會顯示成「（未定義）」。
- 保留位元請命名 `RES0`／`RES1`（或 `RESERVED`），app 會淡化顯示；同名欄位
  （多段 RES0）可以重複。
- `Reset`：欄位的 reset 值；不寫時 app 會自動從暫存器層級的 Reset 推導。
  未知寫 `-`。
- 數值一律接受 `0x…`（16 進位）、`0b…`（2 進位）、十進位，可加底線分隔。

### Enum 區塊

- `### Enum: 欄位名稱` 必須放在該暫存器欄位表**之後**，名稱需與表中 `Field` 完全一致。
- 每行 `- 值: 意義`。app 會把目前值對應的意義直接顯示在欄位旁，並在展開時列出
  全部選項——這是「不用翻 spec」的關鍵，**能寫的都寫**。

### Status（查核狀態）

`# Status:` 是寫給**下一個維護者**看的一句話：這份 spec 哪些部分已經對過原廠文件、
哪些還沒。app 的「Spec 管理」與「Spec 全文」都會把它標成醒目的提示。

因為 spec 寫錯會讓分析結果整個錯，本專案的規矩是：

- **不確定的值寫 `-`，不要猜**（app 會顯示「無基準」，比填錯的 reset 值安全得多）。
- **實作定義（IMPLEMENTATION DEFINED）的暫存器**在拿到文件前，先寫在檔尾的 HTML
  註解待補清單裡（含編號與用途），不要先寫進表格。註解不會被解析，但在 app 的
  「原始 Markdown」分頁看得到，補的人一目瞭然。
- 補完欄位就更新 `# Status:`。

### Verified（官方文件對照出處）

`- Verified:` 是**逐顆暫存器**的出處註記：這顆暫存器的欄位切分、Reset 值是對照
哪一份官方文件的哪一段抄出來的（例：`ARM DDI 0460D（Cortex-R5 TRM r1p2）§4
Table 4.5`）。

- **有寫＝已逐欄對照原廠文件**，app 會標綠色「已對照官方」並顯示出處。
- **沒寫＝還沒對照**，app 會標「未對照官方文件」，Spec 管理頁的卡片也會顯示
  `已對照官方 1/18` 這樣的比例。
- 沒把握就**不要寫**。這一行的唯一意義是「可以信」，寫了卻沒真的對照，比不寫
  更危險。
- 「對照」指的是拿著官方文件逐欄核對，不是憑架構知識推論。架構規格（ARM ARM、
  RISC-V Privileged Spec）與晶片 TRM 不等價：TRM 才會有 TCMTR 這類實作相關的
  暫存器，只讀架構規格必然漏。

現場事故（2026-08-24）：R5 的官方 TRM 有 `TCMTR`，本工具的 spec 卻沒有——因為
內容是依架構知識整理、沒有逐顆對照原廠文件，而畫面上完全沒有任何線索。
`- Verified:` 就是為了讓這件事**在畫面上看得見**。

## 品質檢查

app 的「Spec 管理」頁會列出每份 spec 的解析警告（缺 Offset、位元重疊、超出寬度、
Enum 對不到欄位…），**新 spec 先用「載入外部 Spec」載入看警告清單，清空後再收進
repo**。CI 也會驗證 `specs/` 內所有檔案解析無警告，有問題會擋下 build。

## 給 AI 產生新 spec 的指示範本

要新增 CPU spec 時，把下面這段連同 spec 來源（TRM/datasheet 的 PDF 或文字）
交給 AI 即可：

> 請依照 repo 中 `SPEC_FORMAT.md` 的格式與 `specs/arm/cortex_r5.md` 的實例，
> 把我提供的 CPU spec 轉成一份新的 spec MD 檔。要求：
> 1. Offset 依我的 dump 腳本輸出順序從 0x000 開始遞增（32-bit 暫存器一個佔 4 bytes）。
> 2. 每個暫存器的每個 bit 都要被欄位表涵蓋，保留位元命名 RES0／RES1。
> 3. 有列舉意義的欄位（模式、開關、狀態碼）務必補上 `### Enum:` 區塊，意義用繁體中文。
> 4. Reset 值照 spec 抄；依組態接腳或實作而異的寫 `-`。
> 5. 只根據我提供的 spec 內容填寫，不確定的值寫 `-` 並在 Description 註明，不要編造。
> 6. 實作定義（IMPLEMENTATION DEFINED）而我沒提供文件的暫存器，不要寫進表格，
>    改列在檔尾的 HTML 註解待補清單（含暫存器編號與用途）。
> 7. 檔頭補上 `# Status:` 說明哪些部分已核對、哪些待補；只要還有暫存器沒對照
>    官方文件，Status 就要掛 `⚠`。
> 8. 逐欄對照過官方文件的暫存器，補上 `- Verified: <文件編號 §章節/表號>`；
>    沒真的對照過就不要寫這一行。
> 9. 檔尾用 HTML 註解列出「與官方文件目錄的落差」：官方有、本檔還沒收錄的
>    暫存器清單（✔ 已收錄／✘ 尚未收錄），讓下一個人知道還差什麼。
