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
    """標準 CSR 的出處是 RISC-V v1.11 官方規格；Andes 專屬 CSR 的出處是
    Andes 原廠 QEMU（github.com/andestech/qemu）。每顆都必須有其一。"""
    assert riscv.registers, riscv.spec_id
    for r in riscv.registers:
        assert ("v1.11" in r.verified) or ("andestech/qemu" in r.verified), \
            f"{riscv.spec_id}/{r.name} 缺官方出處"
    andes_regs = [r for r in riscv.registers if "andestech/qemu" in r.verified]
    assert len(andes_regs) == 39, "Andes 專屬 CSR 應為 39 顆"


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
        "M": (0, 0),
        "SA": (3, 3),
        "SA0": (4, 4),
        "SED": (8, 8),
        "SPAN": (23, 23),
        "UCI": (26, 26),
        "UCT": (15, 15),
        "UMA": (9, 9),
        "WXN": (19, 19),
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
    assert checked == 121, f"對照過的欄位數變了（{checked}）——是刻意增刪就同步改這個數字"  # 2026-08-29：SCTLR[29:28] 依審查改 RES1，自 lock 表移除


def test_a55_verified_registers_cite_the_machine_readable_spec():
    """標了 Verified 的 A55 暫存器必須指名對照來源；沒對照的就不准標。

    來源只有兩種：Arm 機讀架構規格（sail-arm）或 ARM 官方 TF-A 原始碼
    （實作定義暫存器）。版本佈局與 v8.2 不同的（CCSIDR）與無機讀定義的
    （CurrentEL／DAIF 等 11 顆）必須維持未標。"""
    spec = _spec("arm/cortex_a55.md")
    for r in spec.registers:
        if r.verified:
            assert ("sail-arm" in r.verified) or ("arm-trusted-firmware" in r.verified) \
                or ("DDI 0406C.d" in r.verified), r.name  # CCSIDR：v7/v8 同佈局親驗
    unverified = {r.name for r in spec.registers if not r.verified}
    assert unverified == {"CurrentEL", "DAIF", "VBAR_EL1", "FAR_EL1", "ELR_EL1",
                          "CNTFRQ_EL0", "CNTP_TVAL_EL0", "CNTV_TVAL_EL0",
                          "REVIDR_EL1", "AIDR_EL1"}  # CCSIDR 於 2026-08-29 取得 0406C 佈局親驗
    tfa = {r.name for r in spec.registers if r.verified and "arm-trusted-firmware" in r.verified}
    assert tfa == {"CPUECTLR_EL1", "CPUACTLR_EL1", "CPUPWRCTLR_EL1"}


def test_a55_reset_values_are_not_fabricated():
    """設計如此：Reset 值沒有可交代的出處就寫 `-`，有出處就必須寫在
    Description。例外清單（逐一附來歷）：MIDR_EL1（推導）、REVIDR_EL1／
    AIDR_EL1（R5R：Table 3-49 審查轉錄，待親驗）。"""
    spec = _spec("arm/cortex_a55.md")
    with_reset = {r.name: r for r in spec.registers if r.reset is not None}
    assert set(with_reset) == {"MIDR_EL1", "REVIDR_EL1", "AIDR_EL1"}
    assert "尚未用 A55 TRM 確認" in with_reset["MIDR_EL1"].desc
    for n in ("REVIDR_EL1", "AIDR_EL1"):
        assert with_reset[n].reset == 0
        assert "Table 3-49" in with_reset[n].desc and "轉錄" in with_reset[n].desc


def test_r5_reset_values_are_not_fabricated():
    """R5 同理：沒對照過 DDI 0460D 的重置值一律 `-`。

    CTR 與 CPACR 原本寫死 0x8003C003／0x00000000 —— 前者隨這顆核心配置的
    快取而變、後者在 ARMv7 是 IMPLEMENTATION DEFINED，兩個都不是固定值，
    寫死會讓 UI 標出假的「≠ Reset」。只有 MIDR 留值（可由 r1p2 ＋ 部件編號
    0xC15 推出），且必須在 Description 交代來歷。
    """
    spec = _spec("arm/cortex_r5.md")
    with_reset = [r for r in spec.registers if r.reset is not None]
    assert [r.name for r in with_reset] == ["MIDR"]
    assert "尚未用 DDI 0460D 確認" in with_reset[0].verified
    ctr = _regs(spec)["CTR"]
    fmt = next(f for f in ctr.fields if f.name == "Format")
    assert fmt.reset == 0b100, "Format 是 ARMv7 架構固定值，可以留"
    # PMSA 官方版（DDI 0406C.d B6.1）bits[15:14] 是 RAO，沒有 VMSA 的 L1Ip 欄
    assert not any(f.name == "L1Ip" for f in ctr.fields)
    for name in ("CWG", "ERG", "DminLine", "IminLine"):
        assert next(f for f in ctr.fields if f.name == name).reset is None, name


# ════════════════════════════════════════════════════════════════════
# 完整性鎖定（2026-08-28 完整化改版）：清單本身就是官方事實
# ════════════════════════════════════════════════════════════════════

def test_r5_covers_full_official_pmsa_readable_list():
    """R5 spec 必須涵蓋官方 DDI 0406C.d Table B5-11 的全部可讀暫存器。

    設計如此：TCMTR 事故的根因就是清單不完整。此表照官方 PMSA CP15 總表
    逐顆列出（排除純寫入操作、I 側 MPU（unified 不實作）、Generic Timer
    （R5 未實作）——排除原因都寫在 spec 檔頭註解）。
    """
    spec = _spec("arm/cortex_r5.md")
    names = [r.name for r in spec.registers]
    official_readable = [
        # c0 識別
        "MIDR", "CTR", "TCMTR", "MPUIR", "MPIDR", "REVIDR",
        "ID_PFR0", "ID_PFR1", "ID_DFR0", "ID_AFR0",
        "ID_MMFR0", "ID_MMFR1", "ID_MMFR2", "ID_MMFR3",
        "ID_ISAR0", "ID_ISAR1", "ID_ISAR2", "ID_ISAR3", "ID_ISAR4", "ID_ISAR5",
        "CCSIDR", "CLIDR", "AIDR", "CSSELR",
        # c1 控制
        "SCTLR", "ACTLR", "CPACR",
        # c5/c6 故障
        "DFSR", "IFSR", "ADFSR", "AIFSR", "DFAR", "IFAR",
        # c6 MPU
        "RGNR", "DRBAR", "DRSR", "DRACR",
        # c9 PMU
        "PMCR", "PMCNTENSET", "PMCNTENCLR", "PMOVSR", "PMSELR",
        "PMCEID0", "PMCEID1", "PMCCNTR", "PMXEVTYPER", "PMXEVCNTR",
        "PMUSERENR", "PMINTENSET", "PMINTENCLR",
        # c13
        "CONTEXTIDR", "TPIDRURW", "TPIDRURO", "TPIDRPRW",
    ]
    missing = [n for n in official_readable if n not in names]
    assert not missing, f"官方 Table B5-11 有、spec 沒有：{missing}"
    assert len(spec.registers) == 62  # 官方清單 + ATCMRR/BTCMRR + CPSR + FPU 5 顆（FPSID/FPSCR/FPEXC/MVFR0/MVFR1）


def test_r5_id_registers_verified_against_ddi0406():
    """新增的 CPUID 暫存器全部要有 DDI 0406C.d 出處。"""
    spec = _spec("arm/cortex_r5.md")
    for r in spec.registers:
        if r.name.startswith("ID_"):
            assert "DDI 0406C.d" in r.verified, r.name


def test_riscv_andes_csr_positions_match_official_qemu():
    """Andes 專屬 CSR 的關鍵位元位置鎖定官方 QEMU（andes_cpu_bits.h）。"""
    for spec_name in ("andes/n25.md", "andes/n45.md"):
        regs = _regs(_spec(spec_name))
        f = {x.name: (x.msb, x.lsb) for x in regs["mmsc_cfg"].fields}
        assert f["ECC"] == (0, 0) and f["ECD"] == (3, 3) and f["PFT"] == (4, 4)
        assert f["HSP"] == (5, 5) and f["PMNDS"] == (15, 15) and f["CCTLCSR"] == (16, 16)
        assert f["MSC_EXT"] == (31, 31) and f["ADDPMC"] == (11, 7) and f["EXCSLVL"] == (21, 20)
        f = {x.name: (x.msb, x.lsb) for x in regs["micm_cfg"].fields}
        assert f["ISET"] == (2, 0) and f["IWAY"] == (5, 3) and f["ISZ"] == (8, 6)
        assert f["ILMB"] == (14, 12) and f["ILMSZ"] == (19, 15)
        f = {x.name: (x.msb, x.lsb) for x in regs["mmisc_ctl"].fields}
        assert f["VEC_PLIC"] == (1, 1) and f["RVCOMPM"] == (2, 2) and f["BRPE"] == (3, 3)
        assert f["MSA_UNA"] == (6, 6) and f["NEWNMI"] == (9, 9)
        f = {x.name: (x.msb, x.lsb) for x in regs["mhsp_ctl"].fields}
        assert f["OVF_EN"] == (0, 0) and f["UDF_EN"] == (1, 1) and f["SCHM"] == (2, 2)
        assert f["U"] == (3, 3) and f["S"] == (4, 4) and f["M"] == (5, 5)
        # CSR 編號寫進 Description（0xFC0 等）
        assert "0xFC0" in regs["micm_cfg"].desc and "0x7C4" in regs["mxstatus"].desc


def test_riscv_full_pmp_and_counters_present():
    """完整 PMP（cfg0-3、addr0-15）與計數器群必須都在。"""
    for spec_name in ("andes/n25.md", "andes/n45.md"):
        names = {r.name for r in _spec(spec_name).registers}
        for i in range(4):
            assert f"pmpcfg{i}" in names
        for i in range(16):
            assert f"pmpaddr{i}" in names
        for base in ("mcycle", "minstret"):
            assert base in names and base + "h" in names
        for i in range(3, 7):
            assert f"mhpmcounter{i}" in names and f"mhpmcounter{i}h" in names
            assert f"mhpmevent{i}" in names
        assert len(names) == 90


def test_a55_extended_registers_present():
    """A55 擴充後的清單鎖定（55 顆）。"""
    names = {r.name for r in _spec("arm/cortex_a55.md").registers}
    for n in ("ID_AA64PFR1_EL1", "ID_AA64DFR0_EL1", "ID_AA64ISAR0_EL1", "ID_AA64ISAR1_EL1",
              "ID_AA64MMFR1_EL1", "ID_AA64MMFR2_EL1", "CCSIDR_EL1", "CSSELR_EL1",
              "CONTEXTIDR_EL1", "TPIDR_EL1", "TPIDR_EL0", "TPIDRRO_EL0",
              "CNTKCTL_EL1", "CNTPCT_EL0", "CNTVCT_EL0", "CNTP_CTL_EL0", "CNTV_CTL_EL0",
              "PMCR_EL0", "PMCCNTR_EL0", "PMUSERENR_EL0",
              "CPUECTLR_EL1", "CPUACTLR_EL1", "CPUPWRCTLR_EL1"):
        assert n in names, n
    assert len(names) == 55


def test_andes_mcounterovf_clear_semantics_differ_by_core():
    """2026-08-29 三輪審查決議：官方 QEMU（pinned commit 3290262）的
    write_mcounterovf 明定 N25=寫 1 清除（W1C）、其他核心（含 N45）=寫 0 清除
    （W0C）。兩檔複製時漏掉這個差異曾是實際錯誤——鎖住它。"""
    n25 = _regs(_spec("andes/n25.md"))["mcounterovf"]
    n45 = _regs(_spec("andes/n45.md"))["mcounterovf"]
    assert "寫 1 清除" in n25.desc and "W1C" in n25.desc
    assert "寫 0 清除" in n45.desc and "W0C" in n45.desc
    assert "3290262" in n25.desc and "3290262" in n45.desc


def test_r5_tcm_region_encodings_swapped_fix_locked():
    """2026-08-29 審查修正鎖定：ATCM=c9,c1,1、BTCM=c9,c1,0（Xilinx 官方 BSP
    xreg_cortexr5.h 與 DDI 0460D Table 4-43/4-44 一致）——舊版寫反過，不准改回。"""
    regs = _regs(_spec("arm/cortex_r5.md"))
    assert "c9,c1,1" in regs["ATCMRR"].desc and "c9,c1,0" not in regs["ATCMRR"].desc.split("舊版誤植")[0].split("；MRC")[0][-30:]
    assert "MRC p15,0,Rt,c9,c1,1" in regs["ATCMRR"].desc
    assert "MRC p15,0,Rt,c9,c1,0" in regs["BTCMRR"].desc
    # Size 欄位補上
    assert any(f.name == "Size" for f in regs["ATCMRR"].fields)
    assert any(f.name == "Size" for f in regs["BTCMRR"].fields)


def test_a55_sctlr_2928_res1_locked():
    """2026-08-29 審查修正鎖定：A55 無 FEAT_LSMAOC → SCTLR_EL1[29:28] 為 RES1
    （Linux kernel SCTLR_EL1_RES1 遮罩＋審查確認 TRM Figure 3-162）。"""
    sctlr = _regs(_spec("arm/cortex_a55.md"))["SCTLR_EL1"]
    f = {x.name: (x.msb, x.lsb, x.reset) for x in sctlr.fields}
    assert "LSMAOE" not in f and "nTLSMD" not in f
    row = next((x for x in sctlr.fields if x.msb == 29 and x.lsb == 28), None)
    assert row is not None and row.name == "RES1" and row.reset == 0b11


def test_a55_aidr_is_res0_for_cortex_a55():
    """R4 修正＋R5 精修鎖定（R4-01→R5-03）：A55 TRM §3.2.14／Figure 3-91
    （審查轉錄）——上半部原文是 **Reserved**（不是 RES0，兩者無佐證不可互換）、
    下半部才是 RES0；register reset=0（Table 3-49）。舊版整顆 [63:0] 實作定義
    與 R4R 的「上半部 RES0」都不准回來。"""
    aidr = _regs(_spec("arm/cortex_a55.md"))["AIDR_EL1"]
    f = {(x.msb, x.lsb): x.name for x in aidr.fields}
    assert f == {(63, 32): "RESERVED", (31, 0): "RES0"}
    assert aidr.reset == 0
    assert "未使用" in aidr.desc


def test_r5_id_isar2_r1p2_conflict_is_documented():
    """R4 新發現鎖定（R4-02）：ID_ISAR2 與 ID_ISAR0 同型的 TRM 內部衝突
    （Table 4-2 印 r0p0 值 0x21232131；Table 4-17 明定 r1p0 起 MemHint=0x4
    → r1p2 推導 0x21232141）。總帳必須記錄兩個值並列入衝突節，spec 的
    Reset 不准直接回填任一個。"""
    log = (SPECS.parent / "SPEC_REVIEW_LOG.md").read_text(encoding="utf-8")
    assert "0x21232131" in log and "0x21232141" in log
    assert "ID_ISAR2" in log.split("已知衝突")[1].split("##")[0]
    isar2 = _regs(_spec("arm/cortex_r5.md"))["ID_ISAR2"]
    assert isar2.reset is None


def test_r5_header_has_no_stale_mvfr_todo():
    """R4 審查修正鎖定（R4-05）：MVFR0/MVFR1 已收錄，檔頭註解不得再留
    「待補」；Source 也不得再寫 DDI 0460D「僅 TCMTR」（六顆轉錄表同樣
    依它）。"""
    text = (SPECS / "arm" / "cortex_r5.md").read_text(encoding="utf-8")
    assert "VMRS 可讀——待補" not in text
    assert "僅 TCMTR" not in text


def test_sample_r5_fpsid_is_declared_product_or_synthetic():
    """R4 審查修正鎖定（R4-06）：sample 的 FPSID 必須等於總帳記錄的
    Table 11-7 轉錄值 0x41023153；來路不明的 0x41023154 不准回來。"""
    src = (SPECS.parent / "tools" / "make_sample_bin.py").read_text(encoding="utf-8")
    assert "0x41023153" in src and "0x41023154" not in src


def test_a55_mmfr0_tgran_dual_layer_locked():
    """R4 裁定鎖定（必答 3）：TGran4/TGran64 保留架構欄位切分（0＝支援），
    同欄 Description 必須同時記錄 A55 TRM Figure 3-127 把 [63:24] 併標
    RES0 的產品畫法。兩層語意都不准刪；「讀 0 不是 RES0」這種單層絕對句
    不准回來。"""
    mmfr0 = _regs(_spec("arm/cortex_a55.md"))["ID_AA64MMFR0_EL1"]
    rows = {x.name: x for x in mmfr0.fields}
    assert "支援 4KB" in rows["TGran4"].desc and "3-127" in rows["TGran4"].desc
    assert "支援 64KB" in rows["TGran64"].desc and "3-127" in rows["TGran64"].desc
    assert "讀 0 不是 RES0" not in rows["TGran4"].desc
    assert "3-127" in mmfr0.desc  # 產品畫法也要寫在暫存器層說明


def test_a55_cpuactlr_access_is_hardware_semantics():
    """R4 審查修正鎖定（R4-04）：Access 欄記「硬體存取屬性」——CPUACTLR_EL1
    整顆 RW（TRM accessibility 審查轉錄＋TF-A 以 MSR 寫 errata 位佐證），
    內部保留位不得用 RO 假裝寫入政策；「不得修改」寫在 Description。"""
    cpuactlr = _regs(_spec("arm/cortex_a55.md"))["CPUACTLR_EL1"]
    for x in cpuactlr.fields:
        assert x.access == "RW", (x.name, x.access)
        if x.name.startswith("INTERNAL"):
            assert "不得修改" in x.desc


def test_r5_sctlr_matches_ddi0460d_table_4_24():
    """R5 審查修正鎖定（R5-01）：SCTLR 套用 DDI 0460D §4.3.16 Table 4-24
    產品 overlay（審查轉錄）——FI[21]/Z[11] 為 SBO（Access=RO；0406C 玻璃屋
    親驗：SBO/SBZ＝硬體忽略寫入）、RR[14]=RW/reset 0、AFE/TRE 具名 RO、
    保留段依產品分組；「依 CFGBR 接腳」無原廠依據，不准回來。"""
    text = (SPECS / "arm" / "cortex_r5.md").read_text(encoding="utf-8")
    assert "CFGBR" not in text  # R6-06：live spec 全面禁用（歷史只留 SPEC_REVIEW_LOG）
    sctlr = _regs(_spec("arm/cortex_r5.md"))["SCTLR"]
    f = {x.name: x for x in sctlr.fields if x.name != "RESERVED"}
    assert f["FI"].access == "RO" and f["Z"].access == "RO"
    assert f["RR"].access == "RW" and f["RR"].reset == 0
    assert f["BR"].access == "RW"
    assert f["AFE"].access == "RO" and f["TRE"].access == "RO"
    groups = {(x.msb, x.lsb) for x in sctlr.fields if x.name == "RESERVED"}
    assert {(23, 22), (9, 7), (6, 3)} <= groups
    assert "U" not in f and "B" not in f  # 產品表不拆架構 U/B 欄


def test_r5_fault_status_uses_product_field_names():
    """R5 審查修正鎖定（R5-02）：DFSR/IFSR 使用 DDI 0460D §4.3.20 產品欄名
    （SD/RW/S/Domain/Status，審查轉錄），架構欄名 ExT/WnR/FS[…] 不准回來；
    DFSR[9:8] 有明文 always-read-0（reset 0）、IFSR[9:8] 無明文（不填）。"""
    regs = _regs(_spec("arm/cortex_r5.md"))
    dfsr = {x.name for x in regs["DFSR"].fields}
    ifsr = {x.name for x in regs["IFSR"].fields}
    assert {"SD", "RW", "S", "Domain", "Status"} <= dfsr
    assert {"SD", "S", "Domain", "Status"} <= ifsr
    for banned in ("ExT", "WnR", "FS[4]", "FS[3:0]"):
        assert banned not in dfsr and banned not in ifsr
    d98 = next(x for x in regs["DFSR"].fields if (x.msb, x.lsb) == (9, 8))
    i98 = next(x for x in regs["IFSR"].fields if (x.msb, x.lsb) == (9, 8))
    assert d98.reset == 0 and i98.reset is None


def test_a55_revidr_product_layout_and_reset():
    """R5-03＋R6-09 鎖定：REVIDR_EL1 上半部依 Figure 3-160 為 RESERVED
    （不是 RES0）、下半部 IMPDEF（Figure 3-160 原圖標籤，非自命名）；
    register reset=0（Table 3-49 審查轉錄）。"""
    revidr = _regs(_spec("arm/cortex_a55.md"))["REVIDR_EL1"]
    f = {(x.msb, x.lsb): x.name for x in revidr.fields}
    assert f == {(63, 32): "RESERVED", (31, 0): "IMPDEF"}  # R6-09：照 Figure 3-160 原圖標籤
    assert revidr.reset == 0


def test_a55_afsr_product_layout_and_register_access_text():
    """R5 審查修正鎖定（R5-04）：AFSR0/1_EL1 上半部 RESERVED（Figure 3-85/3-88）、
    下半部 RES0；Description 必須分層寫明「暫存器介面 RW（MRS/MSR）」——
    RW 的是介面，不是內容。"""
    regs = _regs(_spec("arm/cortex_a55.md"))
    for n in ("AFSR0_EL1", "AFSR1_EL1"):
        r = regs[n]
        f = {(x.msb, x.lsb): x.name for x in r.fields}
        assert f == {(63, 32): "RESERVED", (31, 0): "RES0"}, n
        assert "RW" in r.desc and "MRS/MSR" in r.desc, n
        upper = next(x for x in r.fields if x.msb == 63)
        lower = next(x for x in r.fields if x.msb == 31)
        assert upper.reset is None and lower.reset == 0, n  # R6-04：Reserved 無 reset 依據


def test_r5_qemu_evidence_is_commit_pinned():
    """R5 審查修正鎖定（R5-05）：總帳引用 QEMU 佐證必須釘 40 位 commit，並標示
    該模型 MIDR 是 r1p3——僅作 r1p2 推導的交叉佐證，不取代 DDI 0460D。"""
    log = (SPECS.parent / "SPEC_REVIEW_LOG.md").read_text(encoding="utf-8")
    assert "d2e570cc0f97b936902a5b1b86b73c0f5998b475" in log
    assert "r1p3" in log


def test_r5_sctlr_product_resets_and_enums():
    """R6 審查修正鎖定（R6-01/R6-03）：SCTLR 的 FI/BR reset=0、[6:3]=0b1111
    （0406C.d Figure B6-1 逐位親驗＋CP15BEN 條文：實作→reset 1／未實作→RAO/WI）、
    Z 維持未知（Figure B6-1 標 (†)：可為 RO 且值 implementation-defined、
    否則 reset 0）；FI/Z 不得再掛通用
    ARMv7 開關 enum（產品上此二位不控制功能）；RR enum 兩值都必須講
    random replacement、不得再出現 round-robin。"""
    sctlr = _regs(_spec("arm/cortex_r5.md"))["SCTLR"]
    f = {x.name: x for x in sctlr.fields if x.name != "RESERVED"}
    assert f["FI"].reset == 0 and f["BR"].reset == 0
    assert f["Z"].reset is None
    g63 = next(x for x in sctlr.fields if (x.msb, x.lsb) == (6, 3))
    assert g63.reset == 0b1111
    assert f["FI"].enum == {} and f["Z"].enum == {}
    assert "random" in f["RR"].enum[0] and "random" in f["RR"].enum[1]
    assert "round-robin" not in (f["RR"].enum[0] + f["RR"].enum[1])


# ── DFSR/IFSR 的 Table 4-28 語意檢查器（R8-01：S 分支歸屬鎖）────────────
# full S:Status → (fault 名, FAR 狀態關鍵字)；「有效」列另禁「非同步」子字串誤中
_FSR_FAR_EXPECT = {
    0b00000: ("背景故障", "有效"),
    0b00001: ("對齊故障", "有效"),
    0b00010: ("除錯事件", "保持原值"),
    0b10110: ("非同步外部中止", "UNPREDICTABLE"),
    0b01000: ("同步外部中止", "有效"),
    0b11000: ("非同步同位/ECC", "UNPREDICTABLE"),
    0b11001: ("同步同位/ECC", "有效"),
    0b01101: ("權限故障", "有效"),
}
# 只承載單一 full encoding 的 low-Status 列：另一側分支必須是保留
_FSR_RESERVED_SIDE = ((0b0000, 0), (0b0001, 0), (0b0010, 0),
                      (0b0110, 1), (0b1001, 1), (0b1101, 0))


def _fsr_branch(label, s):
    """自「S=0＝…／S=1＝…」標籤取出指定 S 分支（找不到即斷言失敗）。"""
    prefix = f"S={s}＝"
    part = next((p for p in label.split("／") if p.startswith(prefix)), None)
    assert part is not None, (label, s)
    return part


def _assert_fsr_far_semantics(enum, far, name):
    """逐 full S:Status 驗證 fault 名與 FAR 狀態都落在正確的 S 分支內；
    FAR 狀態必須帶正確 FAR 名（DFAR/IFAR）且三態互斥（R9-01）。"""
    wrong_far = "IFAR" if far == "DFAR" else "DFAR"
    assert set(enum) == {0b0000, 0b0001, 0b0010, 0b0110,
                         0b1000, 0b1001, 0b1101}, name
    for label in enum.values():  # 結構：每列恰好 S=0／S=1 兩個分支、禁 UNKNOWN
        parts = label.split("／")
        assert len(parts) == 2, (name, label)
        assert parts[0].startswith("S=0＝") and parts[1].startswith("S=1＝"), \
            (name, label)
        assert "UNKNOWN" not in label, (name, label)
    for full, (fault, far_kw) in _FSR_FAR_EXPECT.items():
        s, low = full >> 4, full & 0xF
        branch = _fsr_branch(enum[low], s)
        assert fault in branch, (name, f"{full:05b}", branch)
        if fault.startswith("同步"):  # 防「同步…」被「非同步…」子字串誤中
            assert "非同步" not in branch, (name, f"{full:05b}", branch)
        assert wrong_far not in branch, (name, f"{full:05b}", branch)
        if far_kw == "有效":
            assert f"{far} 有效" in branch, (name, f"{full:05b}", branch)
            assert "保持原值" not in branch and "Unchanged" not in branch \
                and "UNPREDICTABLE" not in branch, (name, f"{full:05b}", branch)
        elif far_kw == "保持原值":
            assert f"{far} 保持原值" in branch and "Unchanged" in branch, \
                (name, f"{full:05b}", branch)
            assert "有效" not in branch and "UNPREDICTABLE" not in branch, \
                (name, f"{full:05b}", branch)
        else:
            assert f"{far} 為 UNPREDICTABLE" in branch, \
                (name, f"{full:05b}", branch)
            assert "有效" not in branch and "保持原值" not in branch \
                and "Unchanged" not in branch, (name, f"{full:05b}", branch)
    for low, s_used in _FSR_RESERVED_SIDE:
        other = _fsr_branch(enum[low], 1 - s_used)
        assert "保留" in other, (name, f"{low:04b}", other)
    text = "".join(enum.values())
    assert "Lockdown" not in text and "coprocessor" not in text, name


def test_r5_fault_status_and_far_semantics_match_table_4_28():
    """R6-02＋R7-01/02＋R8-01 鎖定：DFSR/IFSR 的 Status enum 以 DDI 0460D
    Table 4-28（DFSR/IFSR 共用）為準——**七個 low-Status rows 承載八個
    full S:Status 編碼**（01000 與 11000 共用低四位 1000，以 S 分支承載）。
    檢查器逐 full encoding 先切出 S=n 分支再驗 fault 名與 FAR 狀態
    （Valid／Unchanged／UNPREDICTABLE），同步項禁「非同步」子字串誤中，
    單編碼列的另一側必須是保留；R9-01 補強：FAR 狀態必須帶正確的
    FAR 名（DFAR/IFAR，錯名禁入）且三態互斥——同一分支不得同時宣稱
    兩種 FAR 狀態；Status label 禁 UNKNOWN；Lockdown/coprocessor abort
    不得出現。"""
    regs = _regs(_spec("arm/cortex_r5.md"))
    for name, far in (("DFSR", "DFAR"), ("IFSR", "IFAR")):
        status = next(x for x in regs[name].fields if x.name == "Status")
        _assert_fsr_far_semantics(status.enum, far, name)
    # 整檔層級（與 R6 驗收 grep 同標準）：連否定式歷史註記都不留，歷史只在總帳
    text = (SPECS / "arm" / "cortex_r5.md").read_text(encoding="utf-8")
    assert "Lockdown" not in text and "coprocessor abort" not in text


def test_r5_fault_status_check_rejects_swapped_s_branches():
    """R8-01 的負向驗證：把真實 DFSR enum 的 S=0/S=1 分支整組對調後，
    檢查器必須失敗——證明鎖的是 S 分支歸屬，不是整列 substring
    （舊版檢查對調後仍會通過，正是 R8 抓到的缺口）。"""
    status = next(x for x in _regs(_spec("arm/cortex_r5.md"))["DFSR"].fields
                  if x.name == "Status")
    swapped = {}
    for k, label in status.enum.items():
        a, b = label.split("／")
        swapped[k] = "S=0＝" + b.split("＝", 1)[1] + "／S=1＝" + a.split("＝", 1)[1]
    with pytest.raises(AssertionError):
        _assert_fsr_far_semantics(swapped, "DFAR", "DFSR-swapped")


def test_r5_fault_status_check_rejects_wrong_far_register_name():
    """R9-01A 的負向驗證：把 Unchanged/UNPREDICTABLE 分支裡的 FAR 名改成
    另一顆（DFSR 寫成 IFAR、IFSR 寫成 DFAR；Valid 分支保持正確），
    檢查器必須失敗——舊版只驗狀態關鍵字、不驗 FAR 名，此變異會通過。"""
    regs = _regs(_spec("arm/cortex_r5.md"))
    for name, far, wrong in (("DFSR", "DFAR", "IFAR"), ("IFSR", "IFAR", "DFAR")):
        status = next(x for x in regs[name].fields if x.name == "Status")
        mutated = {k: v.replace(f"{far} 保持原值", f"{wrong} 保持原值")
                        .replace(f"{far} 為 UNPREDICTABLE",
                                 f"{wrong} 為 UNPREDICTABLE")
                   for k, v in status.enum.items()}
        assert mutated != status.enum, name  # 變異必須真的有發生
        with pytest.raises(AssertionError):
            _assert_fsr_far_semantics(mutated, far, f"{name}-wrongfar")


def test_r5_fault_status_check_rejects_contradictory_far_states():
    """R9-01B 的負向驗證：同一分支同時宣稱兩種 FAR 狀態必須失敗——
    Valid 分支摻 UNPREDICTABLE、UNPREDICTABLE 分支摻「有效」，雙向都鎖
    （舊版只要求正確狀態存在、不排除矛盾狀態並存，此變異會通過）。"""
    status = next(x for x in _regs(_spec("arm/cortex_r5.md"))["DFSR"].fields
                  if x.name == "Status")
    valid_plus = dict(status.enum)
    valid_plus[0b0000] = valid_plus[0b0000].replace(
        "DFAR 有效", "DFAR 有效、同時為 UNPREDICTABLE")
    assert valid_plus[0b0000] != status.enum[0b0000]
    with pytest.raises(AssertionError):
        _assert_fsr_far_semantics(valid_plus, "DFAR", "DFSR-valid+unpred")
    unpred_plus = dict(status.enum)
    unpred_plus[0b0110] = unpred_plus[0b0110].replace(
        "DFAR 為 UNPREDICTABLE", "DFAR 為 UNPREDICTABLE（DFAR 有效）")
    assert unpred_plus[0b0110] != status.enum[0b0110]
    with pytest.raises(AssertionError):
        _assert_fsr_far_semantics(unpred_plus, "DFAR", "DFSR-unpred+valid")


def test_no_stale_r5_fault_field_references():
    """R6 審查修正鎖定（R6-05）：欄名產品化後，全文不得再出現失效的
    DFSR.FS／IFSR.FS 交叉引用。"""
    text = (SPECS / "arm" / "cortex_r5.md").read_text(encoding="utf-8")
    assert "DFSR.FS" not in text and "IFSR.FS" not in text


def test_spec_headers_match_current_product_overlays():
    """R6 審查修正鎖定（R6-07）：檔頭來源/狀態摘要必須涵蓋現行 overlay 範圍——
    R5 檔頭要列 SCTLR/DFSR/IFSR 的 Table 4-24/4-28 轉錄，A55 檔頭要反映
    R5/R6 輪的 Reserved 分層與 IMPDEF 欄名修正。"""
    r5_head = "\n".join((SPECS / "arm" / "cortex_r5.md")
                        .read_text(encoding="utf-8").splitlines()[:6])
    assert "Table 4-24" in r5_head and "4-28" in r5_head
    a55_head = "\n".join((SPECS / "arm" / "cortex_a55.md")
                         .read_text(encoding="utf-8").splitlines()[:6])
    assert "Reserved" in a55_head and "IMPDEF" in a55_head


def test_review_log_superseded_decisions_are_marked():
    """R6-07＋R7-04＋R9-02 鎖定：被推翻的舊決議 #9/#15/#27 必須以 SUPERSEDED
    標記並指向新決議；僅部分修訂的 #34 必須標 AMENDED by #43、#50 必須標
    AMENDED by #51（其「逐項鎖八個 full S:Status」經 R8-01 證明過度主張）
    ——單獨擷取舊列時不得被當成現行狀態。"""
    log = (SPECS.parent / "SPEC_REVIEW_LOG.md").read_text(encoding="utf-8")
    for prefix, sup in (("| 9 |", "#34"), ("| 15 |", "#38"), ("| 27 |", "#36")):
        row = next(l for l in log.splitlines() if l.startswith(prefix))
        assert "SUPERSEDED" in row and sup in row, prefix
    for num, amend in (("| 34 |", "#43"), ("| 50 |", "#51")):
        row = next(l for l in log.splitlines() if l.startswith(num))
        assert "AMENDED" in row and amend in row, num


def test_sample_r5_branch_prediction_is_attributed_to_actlr():
    """R6 審查修正鎖定（R6-08）：範例產生器不得再把 SCTLR.Z 說成分支預測開關
    ——分支預測歸因 ACTLR.BP=00，Z 標明是產品 SBO。"""
    src = (SPECS.parent / "tools" / "make_sample_bin.py").read_text(encoding="utf-8")
    assert "ACTLR.BP" in src
    assert "SCTLR.Z 是產品 SBO" in src
    assert "M/C/I/Z/BR=1" not in src
