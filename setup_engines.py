"""
AetherDeck — Automated Upstream Engine & Core Provisioning Script.
Downloads and configures RetroArch, all 16 Libretro cores, Dolphin Portable,
and Ryujinx Portable from official upstream repositories.
Does NOT download or bundle any copyrighted BIOS, cryptographic keys, or ROMs.
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.hardware_monitor import CONSOLE_SPECS, HardwareMonitor
from backend.controller_manager import ControllerManager
from backend.emulator_manager import EmulatorManager


def main() -> int:
    print("=" * 72)
    print("  AetherDeck — Installation Automatique des 16 Moteurs d'Émulation")
    print("=" * 72)

    emulators_dir = os.path.join(BASE_DIR, "emulators")
    data_dir = os.path.join(BASE_DIR, "data")
    roms_dir = os.path.join(BASE_DIR, "roms")

    for cid in CONSOLE_SPECS:
        os.makedirs(os.path.join(roms_dir, cid), exist_ok=True)

    hw_mon = HardwareMonitor()
    ctrl_mgr = ControllerManager(data_dir=data_dir, emulators_dir=emulators_dir)
    emu_mgr = EmulatorManager(
        base_dir=BASE_DIR,
        emulators_dir=emulators_dir,
        hardware_monitor=hw_mon,
        controller_manager=ctrl_mgr,
    )

    total = len(CONSOLE_SPECS)
    ready_count = 0

    for idx, (cid, spec) in enumerate(CONSOLE_SPECS.items(), start=1):
        name = spec["full_name"]
        engine = spec["engine_name"]
        if emu_mgr.is_engine_installed(cid):
            print(f"[{idx:02d}/{total:02d}] [OK] {name:<36} -> {engine} (Déjà installé)")
            ready_count += 1
        else:
            print(f"[{idx:02d}/{total:02d}] [..] Installation de {name} ({engine})...")
            res = emu_mgr.install_engine_sync(cid)
            if res.get("ok"):
                print(f"[{idx:02d}/{total:02d}] [OK] {name:<36} -> Installé avec succès")
                ready_count += 1
            else:
                print(f"[{idx:02d}/{total:02d}] [!!] {name:<36} -> Échec : {res.get('message')}")

    print("-" * 72)
    print(f"  Synchronisation des profils manettes et GPU...")
    ctrl_mgr.sync_all_emulator_configs()
    print(f"  Bilan : {ready_count} / {total} moteurs prêts à l'emploi.")
    print("=" * 72)
    return 0 if ready_count == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
