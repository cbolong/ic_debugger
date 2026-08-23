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
3. 用「Spec 全文」逐一對照原廠 TRM／datasheet 核對欄位。
4. 放進對應的廠商資料夾 → push 到 `main` → CI 自動打包出新的 exe。

## 兩條紅線

- **`Offset` 是 bin 檔裡的位元組位移，不是暫存器編號。** 它必須跟你 dump
  腳本的輸出順序一致，這是整個工具唯一的對應依據。
- **不確定的值寫 `-`，不要猜。** 標 `-` 的欄位在 app 裡顯示「無基準」，
  比填一個錯的 reset 值害人誤判好得多。同理，實作定義（IMPLEMENTATION
  DEFINED）的暫存器在沒有文件前，請留在檔尾的 HTML 註解待補清單裡，
  不要先寫進表格。

每份檔案開頭的 `# Status:` 就是給下一個人看的：**目前哪些部分可信、哪些還沒
對過**。補完欄位請一併更新它。
