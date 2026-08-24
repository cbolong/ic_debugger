# specs/ — CPU Spec 資料夾

這個資料夾是 **產品內容**：裡面每一份 `.md` 就是軟體用來解碼 register dump 的
依據，build 時整包打進 exe。改這裡的檔案會觸發 CI 重新打包（改根目錄的說明
文件則不會）。

## 目錄規則

```
specs/
├── README.md          ← 本檔（不會被當成 spec 解析）
├── arm/               ← 一個廠商一個子資料夾，資料夾名＝UI 的分組標題
│   ├── cortex_r5.md
│   └── cortex_a55.md
└── andes/
    ├── n25.md
    └── n45.md
```

- **一顆 CPU（的一個 spec 版本）＝一個 `.md` 檔**，檔名建議 `型號.md`（小寫、
  底線），檔名就是 app 內部的 spec ID。
- **子資料夾名＝廠商**，UI 的下拉選單與「Spec 管理」都依此分組。要加新廠商
  （例如 `specs/synopsys/`）直接開資料夾即可，程式不用改。
- `README.md` 與 **底線開頭**的檔案（`_draft.md`）會被略過，可以安心把草稿、
  筆記放在 spec 旁邊。

## 新增一份 spec 的流程

1. 複製最接近的既有檔當骨架（ARM 看 `arm/cortex_r5.md`，RISC-V 看
   `andes/n25.md`），格式規則見根目錄的 [SPEC_FORMAT.md](../SPEC_FORMAT.md)。
   要用 AI 產生時，把 SPEC_FORMAT.md 裡的「指示範本」連同原廠文件一起交給它。
2. 打開 app →「Spec 管理 → 載入外部 Spec」載入你的新檔，**把解析警告清到 0**。
3. 用「Spec 全文」逐一對照原廠 TRM／datasheet 核對欄位，**核完一顆就在該顆
   加上 `- Verified: <文件編號 §章節/表號>`**（app 會據此顯示「已對照官方
   X/N」）。順手用官方文件的暫存器目錄反查：官方有、本檔沒有的，補進檔尾
   HTML 註解的落差清單。
4. 放進對應的廠商資料夾 → push 到 `main` → CI 自動打包出新的 exe。

## 三條紅線

- **`Offset` 是 bin 檔裡的位元組位移，不是暫存器編號。** 它必須跟你 dump
  腳本的輸出順序一致，這是整個工具唯一的對應依據。
- **不確定的值寫 `-`，不要猜。** 標 `-` 的欄位在 app 裡顯示「無基準」，
  比填一個錯的 reset 值害人誤判好得多。同理，實作定義（IMPLEMENTATION
  DEFINED）的暫存器在沒有文件前，請留在檔尾的 HTML 註解待補清單裡，
  不要先寫進表格。

- **架構規格 ≠ 晶片 TRM。** ARM ARM／RISC-V Privileged Spec 只定義架構共通的
  暫存器；`TCMTR`、`micm_cfg` 這類實作相關的暫存器只在原廠 TRM／datasheet 裡。
  只讀架構規格整理出來的 spec 一定會漏，**這種檔不准標 `- Verified:`**，
  `# Status:` 也必須掛 `⚠` 講清楚。
  （2026-08-24 現場事故：R5 官方 TRM 有 `TCMTR`，本工具的 spec 沒有。）

每份檔案開頭的 `# Status:` 就是給下一個人看的：**目前哪些部分可信、哪些還沒
對過**；每顆暫存器的 `- Verified:` 則是逐顆的出處證明。補完欄位請一併更新兩者。

## 目前的對照狀態（2026-08-24）

| Spec | 暫存器 | 位元定義已對照 | 對照的官方文件 | 還缺什麼 |
|------|--------|---------------|---------------|---------|
| andes/n25 | 20 | 20 | RISC-V 特權架構規格 v1.11（ratified，riscv/riscv-isa-manual） | 這顆核心實際有哪些 CSR、Reset 值、Andes 專屬 CSR（需 AndeStar V5 手冊） |
| andes/n45 | 20 | 20 | 同上 | 同上 |
| arm/cortex_a55 | 20 | 14 | Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a bitfield） | 另 6 顆模型無定義；Reset 值、IMPLEMENTATION DEFINED 部分（需 A55 TRM／DDI 0487） |
| arm/cortex_r5 | 18 | 1（TCMTR） | ARM DDI 0460D（Cortex-R5 TRM） | 其餘 17 顆只做過 A-profile 交叉比對（無錯但不足以認證），需 DDI 0460D 原文 |

「位元定義已對照」＝該暫存器的欄位切在第幾位元，已逐欄對著官方文件核過。
它**不代表**暫存器清單完整、也不代表 Reset 值驗過 —— 那些要晶片 TRM。

各檔檔尾的 HTML 註解列有「與官方文件的落差」清單（官方有、本檔還沒收錄的
暫存器）。有原廠文件的人請照著補，補一顆、對一顆、標一顆 `- Verified:`。
