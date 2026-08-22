"""IC Debugger UI 層（pywebview + HTML/CSS/JS）。

- assets.py：唯一的 UI 文件（HTML/CSS/JS 字串）＋ 主題 tokens。純字串、
  不 import webview，讓測試與預覽工具可在無 GUI 環境使用。
- apis.py：JS ↔ Python bridge（有 import webview，只有 app 本體 import 它）。
"""
