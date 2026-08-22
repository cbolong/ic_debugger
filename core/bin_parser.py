"""bin 檔（register raw dump）解析。

格式約定（已與使用者確認）：
- 純 raw dump：register 值一個接一個，**little-endian**。
- dump 從 spec 的第一個暫存器開始，即 bin 位移 0 對應 spec 的 Offset 0x0，
  之後依 spec 各暫存器的 Offset 對應。
- 每個暫存器佔 Size/8 bytes（預設 32-bit = 4 bytes）。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# 防呆上限：register dump 不可能大到哪裡去；擋下誤選 image/log 之類的大檔
MAX_BIN_SIZE = 16 * 1024 * 1024


class BinError(Exception):
    """使用者看得懂的載入錯誤（UI 直接顯示 str(e)）。"""


@dataclass
class BinFile:
    path: str
    name: str
    data: bytes

    @property
    def size(self) -> int:
        return len(self.data)


def load_bin(path: str | Path) -> BinFile:
    p = Path(path)
    try:
        size = p.stat().st_size
    except OSError as e:
        raise BinError(f"無法讀取檔案：{e}") from e
    if size == 0:
        raise BinError("檔案是空的（0 bytes）")
    if size > MAX_BIN_SIZE:
        raise BinError(
            f"檔案大小 {size:,} bytes 超過上限 {MAX_BIN_SIZE:,} bytes，"
            "看起來不像 register dump，請確認選對檔案"
        )
    try:
        data = p.read_bytes()
    except OSError as e:
        raise BinError(f"無法讀取檔案：{e}") from e
    return BinFile(path=str(p), name=p.name, data=data)


def word_at(data: bytes, offset: int, size_bits: int) -> int | None:
    """取出 offset 處的 little-endian 值；資料不足（含只剩部分 bytes）回 None。"""
    nbytes = size_bits // 8
    if offset < 0 or offset + nbytes > len(data):
        return None
    return int.from_bytes(data[offset:offset + nbytes], "little")
