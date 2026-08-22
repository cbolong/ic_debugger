"""App 狀態：載入中的 spec 集合、目前選擇、目前 bin。

純資料（不 import webview），讓測試能直接驗證狀態轉移。
pywebview 的 js_api 呼叫來自 worker thread，所有變更都在 Api 層以 lock 序列化。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.bin_parser import BinFile
from core.resources import builtin_specs_dir
from core.spec_loader import Spec, load_builtin_specs, load_spec_file


@dataclass
class AppState:
    cfg: dict
    specs: dict[str, Spec] = field(default_factory=dict)  # 依插入順序＝顯示順序
    current_id: str | None = None
    binf: BinFile | None = None

    # ── spec 集合 ───────────────────────────────────────────────────
    def load_specs(self) -> None:
        """重建 spec 集合：內建（specs/ 目錄）＋設定檔記錄的外部檔。"""
        specs: dict[str, Spec] = {}
        for spec in load_builtin_specs(builtin_specs_dir()):
            specs[self._unique_id(specs, spec.spec_id)] = spec

        kept_paths: list[str] = []
        for path in self.cfg.get("external_specs", []):
            spec = load_spec_file(path, origin="external")
            specs[self._unique_id(specs, spec.spec_id)] = spec
            kept_paths.append(path)
        self.cfg["external_specs"] = kept_paths
        # dict 的 key 可能被 _unique_id 改名，把 spec_id 同步成 key
        for key, spec in specs.items():
            spec.spec_id = key
        self.specs = specs

        if self.current_id not in specs:
            last = self.cfg.get("last_spec")
            self.current_id = last if last in specs else (next(iter(specs), None))

    @staticmethod
    def _unique_id(existing: dict[str, Spec], base: str) -> str:
        """外部檔與內建檔同名時避免互撞：arm_cortex_r5 → arm_cortex_r5~2。"""
        sid, n = base, 2
        while sid in existing:
            sid = f"{base}~{n}"
            n += 1
        return sid

    def add_external(self, path: str) -> Spec:
        spec = load_spec_file(path, origin="external")
        sid = self._unique_id(self.specs, spec.spec_id)
        spec.spec_id = sid
        self.specs[sid] = spec
        if path not in self.cfg["external_specs"]:
            self.cfg["external_specs"].append(path)
        self.current_id = sid
        return spec

    def remove_external(self, spec_id: str) -> bool:
        spec = self.specs.get(spec_id)
        if spec is None or spec.origin != "external":
            return False
        del self.specs[spec_id]
        self.cfg["external_specs"] = [
            p for p in self.cfg["external_specs"] if p != spec.path
        ]
        if self.current_id == spec_id:
            self.current_id = next(iter(self.specs), None)
        return True

    # ── 目前選擇 ────────────────────────────────────────────────────
    @property
    def current(self) -> Spec | None:
        return self.specs.get(self.current_id) if self.current_id else None

    def choose(self, spec_id: str) -> bool:
        if spec_id not in self.specs:
            return False
        self.current_id = spec_id
        self.cfg["last_spec"] = spec_id
        return True
