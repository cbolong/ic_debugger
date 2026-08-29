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
    """設計如此：Reset 值沒對照過原廠 TRM 就寫 `-`。
    唯一的例外 MIDR_EL1 必須在 Description 裡把來歷講出來。"""
    spec = _spec("arm/cortex_a55.md")
    with_reset = [r for r in spec.registers if r.reset is not None]
    assert [r.name for r in with_reset] == ["MIDR_EL1"]
    assert "尚未用 A55 TRM 確認" in with_reset[0].desc


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
