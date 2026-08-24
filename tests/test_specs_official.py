"""內建 spec 對照官方文件後的事實鎖定。

為什麼要有這個檔：spec 寫錯，解出來的每個值都會錯，而且錯得很像對的。
這裡把「已逐欄對照官方文件」的內容釘死，之後任何人（含 AI）想「順手修正」
成憑印象的版本，測試就會紅。

RISC-V 部分的對照來源：官方 riscv/riscv-isa-manual，tag
`Ratified-IMFDQC-and-Priv-v1.11`（RISC-V Privileged Architecture v1.11
ratified）的 src/machine.tex。
"""

from pathlib import Path

import pytest

from core.spec_loader import load_spec_file

SPECS = Path(__file__).resolve().parent.parent / "specs"
RISCV = ["n25", "n45"]


def _spec(rel):
    return load_spec_file(SPECS / rel)


def _regs(spec):
    return {r.name: r for r in spec.registers}


def _fields(reg):
    """{欄位名: (msb, lsb)}；同名欄位（WPRI）取全部的集合。"""
    out = {}
    for f in reg.fields:
        out.setdefault(f.name, []).append((f.msb, f.lsb))
    return out


@pytest.fixture(params=RISCV)
def riscv(request):
    return _spec(f"andes/{request.param}.md")


# ── 對照狀態本身 ────────────────────────────────────────────────────

def test_riscv_specs_fully_verified_against_official_v1_11(riscv):
    assert riscv.registers, riscv.spec_id
    for r in riscv.registers:
        assert "v1.11" in r.verified, f"{riscv.spec_id}/{r.name} 缺官方出處"


def test_n25_and_n45_standard_csrs_are_identical():
    """標準 CSR 的位元定義由 RISC-V 架構規範，兩顆核心必須完全一致。
    設計如此：兩份檔案分開維護，這條測試負責抓「只改了一邊」。"""
    a, b = _spec("andes/n25.md"), _spec("andes/n45.md")
    def shape(spec):
        return [(r.name, r.offset, r.size, r.reset,
                 [(f.name, f.msb, f.lsb, f.reset, f.enum) for f in r.fields])
                for r in spec.registers]
    assert shape(a) == shape(b)


# ── 官方 §3.1.6 mstatus（RV32 圖）＋ §3.3 Reset ─────────────────────

def test_mstatus_layout_matches_official_v1_11(riscv):
    f = _fields(_regs(riscv)["mstatus"])
    assert f["SD"] == [(31, 31)]
    assert f["TSR"] == [(22, 22)] and f["TW"] == [(21, 21)] and f["TVM"] == [(20, 20)]
    assert f["MXR"] == [(19, 19)] and f["SUM"] == [(18, 18)] and f["MPRV"] == [(17, 17)]
    assert f["XS"] == [(16, 15)] and f["FS"] == [(14, 13)] and f["MPP"] == [(12, 11)]
    assert f["SPP"] == [(8, 8)] and f["MPIE"] == [(7, 7)] and f["SPIE"] == [(5, 5)]
    assert f["MIE"] == [(3, 3)] and f["SIE"] == [(1, 1)]
    # 官方 v1.11 的 bit 4／bit 0 是 UPIE／UIE（N 擴充），不是保留位
    assert f["UPIE"] == [(4, 4)] and f["UIE"] == [(0, 0)]
    assert sorted(f["WPRI"]) == [(2, 2), (6, 6), (10, 9), (30, 23)]


def test_mstatus_reset_only_mie_and_mprv_are_defined(riscv):
    """官方 §3.3：重置時只有 mstatus 的 MIE 與 MPRV 明訂為 0，其餘未定義。
    設計如此：未定義一律寫 `-`（UI 顯示「無基準」），寫死 0 會產生假的
    「≠ Reset」差異，比沒有 reset 值更糟。"""
    for f in _regs(riscv)["mstatus"].fields:
        if f.name in ("MIE", "MPRV"):
            assert f.reset == 0, f.name
        else:
            assert f.reset is None, f"{f.name} 不該有重置值（官方未定義）"


# ── 官方 §3.1.9 mie／mip ────────────────────────────────────────────

@pytest.mark.parametrize("reg,suffix", [("mie", "E"), ("mip", "P")])
def test_interrupt_registers_layout_matches_official_v1_11(riscv, reg, suffix):
    f = _fields(_regs(riscv)[reg])
    want = {f"MEI{suffix}": 11, f"SEI{suffix}": 9, f"UEI{suffix}": 8,
            f"MTI{suffix}": 7, f"STI{suffix}": 5, f"UTI{suffix}": 4,
            f"MSI{suffix}": 3, f"SSI{suffix}": 1, f"USI{suffix}": 0}
    for name, bit in want.items():
        assert f[name] == [(bit, bit)], name
    assert sorted(f["WPRI"]) == [(2, 2), (6, 6), (10, 10), (15, 12)]
    # 官方：bit 16 以上留給平台自訂中斷源
    assert f["PLAT"] == [(31, 16)]


# ── 官方 §3.1.1 misa（Encoding of Extensions field 表）──────────────

def test_misa_extension_letters_match_official_table(riscv):
    f = _fields(_regs(riscv)["misa"])
    for i, letter in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
        assert f[letter] == [(i, i)], f"misa bit {i} 應為 {letter}"
    assert f["MXL"] == [(31, 30)] and f["WLRL"] == [(29, 26)]


# ── 官方 §3.1.16 mcause（cause 值表）────────────────────────────────

def test_mcause_code_enum_covers_both_readings(riscv):
    """同一個 Code 在 Interrupt=0／1 下意義不同，官方是兩張對照。
    設計如此：MD 格式的 enum 無法依另一個欄位分歧，所以每個編號的標籤
    兩種意義都寫出來 —— 只寫例外那一半會讓中斷被解讀成完全無關的例外。"""
    code = next(f for f in _regs(riscv)["mcause"].fields if f.name == "Code")
    assert set(code.enum) == set(range(16))
    for v, label in code.enum.items():
        assert "例外＝" in label and "中斷＝" in label, v
    assert "機器模式軟體中斷" in code.enum[3] and "中斷點" in code.enum[3]
    assert "機器模式外部中斷" in code.enum[11] and "機器模式 ECALL" in code.enum[11]


# ── 官方 §3.6.1 PMP CSR ＋ §3.3 Reset ───────────────────────────────

def test_pmpcfg0_entry_layout_and_reset(riscv):
    reg = _regs(riscv)["pmpcfg0"]
    by = {f.name: f for f in reg.fields}
    for i in range(4):
        b = i * 8
        assert (by[f"pmp{i}cfg.L"].msb, by[f"pmp{i}cfg.L"].lsb) == (b + 7, b + 7)
        assert (by[f"pmp{i}cfg.RES"].msb, by[f"pmp{i}cfg.RES"].lsb) == (b + 6, b + 5)
        assert (by[f"pmp{i}cfg.A"].msb, by[f"pmp{i}cfg.A"].lsb) == (b + 4, b + 3)
        assert (by[f"pmp{i}cfg.X"].msb, by[f"pmp{i}cfg.X"].lsb) == (b + 2, b + 2)
        assert (by[f"pmp{i}cfg.W"].msb, by[f"pmp{i}cfg.W"].lsb) == (b + 1, b + 1)
        assert (by[f"pmp{i}cfg.R"].msb, by[f"pmp{i}cfg.R"].lsb) == (b, b)
        # 官方 §3.3：重置時只有 A 與 L 設為 0，R/W/X 未定義
        assert by[f"pmp{i}cfg.L"].reset == 0 and by[f"pmp{i}cfg.A"].reset == 0
        assert by[f"pmp{i}cfg.X"].reset is None
        assert by[f"pmp{i}cfg.W"].reset is None
        assert by[f"pmp{i}cfg.R"].reset is None
        # A 的四種模式照官方 Table「Encoding of A field」
        assert set(by[f"pmp{i}cfg.A"].enum) == {0, 1, 2, 3}
        assert "OFF" in by[f"pmp{i}cfg.A"].enum[0] and "TOR" in by[f"pmp{i}cfg.A"].enum[1]
        assert "NA4" in by[f"pmp{i}cfg.A"].enum[2] and "NAPOT" in by[f"pmp{i}cfg.A"].enum[3]


def test_pmpaddr_registers_are_address_33_2(riscv):
    for i in range(4):
        reg = _regs(riscv)[f"pmpaddr{i}"]
        assert [(f.name, f.msb, f.lsb) for f in reg.fields] == [("ADDR", 31, 0)]
        assert "[33:2]" in reg.desc


# ── ARM 側：TCMTR（現場漏列事故）────────────────────────────────────

def test_r5_tcmtr_fields_match_official_trm_figure():
    """官方 DDI 0460D Figure 4.9／Table 4.5：BTCM[18:16]、ATCM[2:0]，其餘保留。"""
    reg = _regs(_spec("arm/cortex_r5.md"))["TCMTR"]
    f = _fields(reg)
    assert f["BTCM"] == [(18, 16)] and f["ATCM"] == [(2, 0)]
    assert sum(m - l + 1 for rng in f.values() for m, l in rng) == 32  # 完整覆蓋


# ════════════════════════════════════════════════════════════════════
# ARM：Cortex-A55 的欄位位置對照 Arm 機器可讀架構規格
# ════════════════════════════════════════════════════════════════════

# 從 Arm 官方機器可讀規格抄下來的欄位位置（rems-project/sail-arm，
# arm-v9.4-a/src/v8_base.sail 的 bitfield 定義）。CI 上沒有那份模型，
# 所以把當時比對過的結果固定在這裡當基準。
ARM_OFFICIAL_FIELDS = {
    "MIDR_EL1": {
        "Architecture": (19, 16),
        "Implementer": (31, 24),
        "PartNum": (15, 4),
        "Revision": (3, 0),
        "Variant": (23, 20),
    },
    "MPIDR_EL1": {
        "Aff0": (7, 0),
        "Aff1": (15, 8),
        "Aff2": (23, 16),
        "Aff3": (39, 32),
        "MT": (24, 24),
        "U": (30, 30),
    },
    "SCTLR_EL1": {
        "A": (1, 1),
        "C": (2, 2),
        "CP15BEN": (5, 5),
        "DZE": (14, 14),
        "E0E": (24, 24),
        "EE": (25, 25),
        "I": (12, 12),
        "IESB": (21, 21),
        "ITD": (7, 7),
        "LSMAOE": (29, 29),
        "M": (0, 0),
        "SA": (3, 3),
        "SA0": (4, 4),
        "SED": (8, 8),
        "SPAN": (23, 23),
        "UCI": (26, 26),
        "UCT": (15, 15),
        "UMA": (9, 9),
        "WXN": (19, 19),
        "nTLSMD": (28, 28),
        "nTWE": (18, 18),
        "nTWI": (16, 16),
    },
    "CPACR_EL1": {
        "FPEN": (21, 20),
        "TTA": (28, 28),
    },
    "TCR_EL1": {
        "A1": (22, 22),
        "AS": (36, 36),
        "EPD0": (7, 7),
        "EPD1": (23, 23),
        "HA": (39, 39),
        "HD": (40, 40),
        "HPD0": (41, 41),
        "HPD1": (42, 42),
        "IPS": (34, 32),
        "IRGN0": (9, 8),
        "IRGN1": (25, 24),
        "ORGN0": (11, 10),
        "ORGN1": (27, 26),
        "SH0": (13, 12),
        "SH1": (29, 28),
        "T0SZ": (5, 0),
        "T1SZ": (21, 16),
        "TBI0": (37, 37),
        "TBI1": (38, 38),
        "TG0": (15, 14),
        "TG1": (31, 30),
    },
    "MAIR_EL1": {
        "Attr0": (7, 0),
        "Attr1": (15, 8),
        "Attr2": (23, 16),
        "Attr3": (31, 24),
        "Attr4": (39, 32),
        "Attr5": (47, 40),
        "Attr6": (55, 48),
        "Attr7": (63, 56),
    },
    "ESR_EL1": {
        "EC": (31, 26),
        "IL": (25, 25),
        "ISS": (24, 0),
    },
    "SPSR_EL1": {
        "A": (8, 8),
        "C": (29, 29),
        "D": (9, 9),
        "F": (6, 6),
        "I": (7, 7),
        "IL": (20, 20),
        "N": (31, 31),
        "PAN": (22, 22),
        "SS": (21, 21),
        "UAO": (23, 23),
        "V": (28, 28),
        "Z": (30, 30),
    },
    "CLIDR_EL1": {
        "Ctype1": (2, 0),
        "Ctype2": (5, 3),
        "Ctype3": (8, 6),
        "Ctype4": (11, 9),
        "Ctype5": (14, 12),
        "Ctype6": (17, 15),
        "Ctype7": (20, 18),
        "LoC": (26, 24),
        "LoUIS": (23, 21),
        "LoUU": (29, 27),
    },
    "CTR_EL0": {
        "CWG": (27, 24),
        "DIC": (29, 29),
        "DminLine": (19, 16),
        "ERG": (23, 20),
        "IDC": (28, 28),
        "IminLine": (3, 0),
        "L1Ip": (15, 14),
    },
    "ID_AA64PFR0_EL1": {
        "AMU": (47, 44),
        "AdvSIMD": (23, 20),
        "CSV2": (59, 56),
        "CSV3": (63, 60),
        "DIT": (51, 48),
        "EL0": (3, 0),
        "EL1": (7, 4),
        "EL2": (11, 8),
        "EL3": (15, 12),
        "FP": (19, 16),
        "GIC": (27, 24),
        "MPAM": (43, 40),
        "RAS": (31, 28),
        "SEL2": (39, 36),
        "SVE": (35, 32),
    },
    "ID_AA64MMFR0_EL1": {
        "ASIDBits": (7, 4),
        "BigEnd": (11, 8),
        "BigEndEL0": (19, 16),
        "ExS": (47, 44),
        "PARange": (3, 0),
        "SNSMem": (15, 12),
        "TGran16": (23, 20),
        "TGran16_2": (35, 32),
        "TGran4": (31, 28),
        "TGran4_2": (43, 40),
        "TGran64": (27, 24),
        "TGran64_2": (39, 36),
    },
}


def test_a55_field_positions_match_arm_machine_readable_spec():
    """A55 已對照的欄位，位元位置必須與 Arm 官方機器可讀規格一致。

    只鎖「欄位在第幾位元」——欄位語意、Reset 值、以及「這顆核心到底有沒有
    這個欄位」仍需 Cortex-A55 TRM，spec 檔的 Status 有講清楚。
    對照用的模型是 Armv9.4-A、本核心是 Armv8.2-A：既有欄位的位置在版本間
    不會移動（新功能佔用原本的 RES0），所以位置相符可信。
    """
    regs = _regs(_spec("arm/cortex_a55.md"))
    checked = 0
    for name, want in ARM_OFFICIAL_FIELDS.items():
        got = {f.name: (f.msb, f.lsb) for f in regs[name].fields}
        for field, pos in want.items():
            assert got.get(field) == pos, f"{name}.{field} 應在 [{pos[0]}:{pos[1]}]，實際 {got.get(field)}"
            checked += 1
    assert checked == 123, f"對照過的欄位數變了（{checked}）——是刻意增刪就同步改這個數字"


def test_a55_verified_registers_cite_the_machine_readable_spec():
    """標了 Verified 的 A55 暫存器必須指名對照來源；沒對照的就不准標。"""
    spec = _spec("arm/cortex_a55.md")
    verified = {r.name for r in spec.registers if r.verified}
    assert verified == set(ARM_OFFICIAL_FIELDS) | {"TTBR0_EL1", "TTBR1_EL1"}
    for r in spec.registers:
        if r.verified:
            assert "sail-arm" in r.verified, r.name


def test_a55_reset_values_are_not_fabricated():
    """設計如此：Reset 值沒對照過原廠 TRM 就寫 `-`。
    唯一的例外 MIDR_EL1 必須在 Description 裡把來歷講出來。"""
    spec = _spec("arm/cortex_a55.md")
    with_reset = [r for r in spec.registers if r.reset is not None]
    assert [r.name for r in with_reset] == ["MIDR_EL1"]
    assert "尚未用 A55 TRM 確認" in with_reset[0].desc
