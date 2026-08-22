"""IC Debugger 核心邏輯層。

此 package 只做純資料處理（spec 解析、bin 解析、欄位解碼），
**絕對不 import pywebview / GUI 相關模組**，讓 pytest 能在任何環境
（含 Linux CI）直接測試，也讓核心邏輯與 UI 演進互不牽制。
"""
