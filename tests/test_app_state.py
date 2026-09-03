"""AppState 的 spec 集合管理測試（用 repo 內建 spec + tmp 外部檔）。"""

from app_state import AppState

EXT_SPEC = """\
# CPU: 測試外部
## R
- Offset: 0x0

| Bits | Field |
|---|---|
| 31:0 | V |
"""


def _fresh_cfg(**over):
    cfg = {"theme": "auto", "last_spec": None, "external_specs": [], "last_dir": None}
    cfg.update(over)
    return cfg


def test_load_builtin_specs_and_default_selection():
    st = AppState(cfg=_fresh_cfg())
    st.load_specs()
    assert {"cortex_r5", "cortex_a55", "n25", "n45"} <= set(st.specs)
    assert st.current_id == "n25"  # 依 (廠商, 檔名) 排序的第一個


def test_last_spec_restored():
    st = AppState(cfg=_fresh_cfg(last_spec="cortex_r5"))
    st.load_specs()
    assert st.current_id == "cortex_r5"


def test_add_and_remove_external(tmp_path):
    p = tmp_path / "my_chip.md"
    p.write_text(EXT_SPEC, encoding="utf-8")
    st = AppState(cfg=_fresh_cfg())
    st.load_specs()

    spec = st.add_external(str(p))
    assert spec.origin == "external"
    assert st.current_id == "my_chip"
    assert str(p) in st.cfg["external_specs"]

    # 內建不能移除
    assert not st.remove_external("cortex_r5")
    assert st.remove_external("my_chip")
    assert "my_chip" not in st.specs
    assert st.cfg["external_specs"] == []
    assert st.current_id in st.specs  # 退回其他 spec


def test_readd_same_external_path_reloads_in_place(tmp_path):
    """同一個外部檔重複載入＝就地重新讀取（設計如此：cfg 的去重本來就表明
    「同檔只記一次」，specs 集合比照——不產生第二張卡，也順帶滿足
    「改了 .md 想立即更新」的直覺操作）。

    2026-09-03 深度 review 實證的狀態不一致：重加同檔曾產生 my_chip＋my_chip~2
    兩張卡但 cfg 只記一條路徑，移除其中一張後另一張變孤兒（重開 app 即消失）。"""
    p = tmp_path / "my_chip.md"
    p.write_text(EXT_SPEC, encoding="utf-8")
    st = AppState(cfg=_fresh_cfg())
    st.load_specs()
    base = len(st.specs)

    s1 = st.add_external(str(p))
    # 使用者修改檔案後再載入同一檔
    p.write_text(EXT_SPEC.replace("測試外部", "測試外部 v2") + "\n## R2\n- Offset: 0x4\n",
                 encoding="utf-8")
    s2 = st.add_external(str(p))

    assert s2.spec_id == s1.spec_id, "不得產生第二張卡"
    assert len(st.specs) == base + 1
    assert st.current_id == s1.spec_id
    assert s2.cpu == "測試外部 v2" and len(s2.registers) == 2, "必須就地重新讀取檔案內容"
    assert st.cfg["external_specs"].count(str(p)) == 1

    # 移除後不得留孤兒：cfg 與畫面狀態一致，重新載入後外部 spec 歸零
    assert st.remove_external(s1.spec_id)
    st.load_specs()
    assert not [s for s in st.specs.values() if s.origin == "external"]


def test_external_id_collision_gets_suffix(tmp_path):
    p = tmp_path / "cortex_r5.md"  # 與內建同名
    p.write_text(EXT_SPEC, encoding="utf-8")
    st = AppState(cfg=_fresh_cfg())
    st.load_specs()
    spec = st.add_external(str(p))
    assert spec.spec_id == "cortex_r5~2"
    assert st.specs["cortex_r5"].origin == "builtin"


def test_detail_binf_only_for_current_spec():
    """設計如此：Spec 全文只對「目前使用中的 spec」疊 bin 值 ——
    bin 的 offset 對應跟著 spec 走，套到別份 spec 上值是無意義的。"""
    from core.bin_parser import BinFile
    st = AppState(cfg=_fresh_cfg())
    st.load_specs()
    st.binf = BinFile(path="x", name="x.bin", data=bytes(8))
    cur = st.current_id
    other = next(sid for sid in st.specs if sid != cur)
    assert st.detail_binf(cur) is st.binf
    assert st.detail_binf(other) is None
    st.binf = None
    assert st.detail_binf(cur) is None


def test_reload_keeps_external(tmp_path):
    p = tmp_path / "ext.md"
    p.write_text(EXT_SPEC, encoding="utf-8")
    st = AppState(cfg=_fresh_cfg())
    st.load_specs()
    st.add_external(str(p))
    st.load_specs()  # 重新載入（外部清單在 cfg 裡）
    assert "ext" in st.specs
    assert st.specs["ext"].origin == "external"
