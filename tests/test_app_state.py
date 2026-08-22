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
    assert "arm_cortex_r5" in st.specs and "andes_n25" in st.specs
    assert st.current_id == "andes_n25"  # 依檔名排序的第一個


def test_last_spec_restored():
    st = AppState(cfg=_fresh_cfg(last_spec="arm_cortex_r5"))
    st.load_specs()
    assert st.current_id == "arm_cortex_r5"


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
    assert not st.remove_external("arm_cortex_r5")
    assert st.remove_external("my_chip")
    assert "my_chip" not in st.specs
    assert st.cfg["external_specs"] == []
    assert st.current_id in st.specs  # 退回其他 spec


def test_external_id_collision_gets_suffix(tmp_path):
    p = tmp_path / "arm_cortex_r5.md"  # 與內建同名
    p.write_text(EXT_SPEC, encoding="utf-8")
    st = AppState(cfg=_fresh_cfg())
    st.load_specs()
    spec = st.add_external(str(p))
    assert spec.spec_id == "arm_cortex_r5~2"
    assert st.specs["arm_cortex_r5"].origin == "builtin"


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
