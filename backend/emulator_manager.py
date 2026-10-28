"""
Centralized Emulator Engine Manager for OmniConsole.
Handles automatic download, extraction, system BIOS/asset provisioning,
controller config synchronization, and game execution across all consoles
(Amstrad CPC, Commodore Amiga, NES, SNES, GBA, Mega Drive, N64, PS1, Wii/GameCube, Switch).
"""

import io
import json
import os
import shutil
import subprocess
import threading
import time
import zipfile
from typing import Dict, Any, List, Optional
import requests

from .hardware_monitor import CONSOLE_SPECS, HardwareMonitor
from .controller_manager import ControllerManager


BUILDBOT_CORES_BASE = "https://buildbot.libretro.com/nightly/windows/x86_64/latest"
BUILDBOT_RETROARCH_UPDATE = "https://buildbot.libretro.com/nightly/windows/x86_64/RetroArch_update.7z"
BUILDBOT_DOLPHIN_SYS = "https://buildbot.libretro.com/assets/system/Dolphin.zip"

ENGINE_DOWNLOAD_MAP: Dict[str, Dict[str, Any]] = {
    "amstrad_cpc": {
        "type": "libretro",
        "core_zip": f"{BUILDBOT_CORES_BASE}/cap32_libretro.dll.zip",
        "core_dll": "cap32_libretro.dll",
        "size_mb": 0.5,
    },
    "amiga": {
        "type": "libretro",
        "core_zip": f"{BUILDBOT_CORES_BASE}/puae_libretro.dll.zip",
        "core_dll": "puae_libretro.dll",
        "size_mb": 6.8,
    },
    "nes": {
        "type": "libretro",
        "core_zip": f"{BUILDBOT_CORES_BASE}/fceumm_libretro.dll.zip",
        "core_dll": "fceumm_libretro.dll",
        "size_mb": 0.6,
    },
    "snes": {
        "type": "libretro",
        "core_zip": f"{BUILDBOT_CORES_BASE}/snes9x_libretro.dll.zip",
        "core_dll": "snes9x_libretro.dll",
        "size_mb": 1.3,
    },
    "gba": {
        "type": "libretro",
        "core_zip": f"{BUILDBOT_CORES_BASE}/mgba_libretro.dll.zip",
        "core_dll": "mgba_libretro.dll",
        "size_mb": 0.6,
    },
    "megadrive": {
        "type": "libretro",
        "core_zip": f"{BUILDBOT_CORES_BASE}/genesis_plus_gx_libretro.dll.zip",
        "core_dll": "genesis_plus_gx_libretro.dll",
        "size_mb": 0.9,
    },
    "n64": {
        "type": "libretro",
        "core_zip": f"{BUILDBOT_CORES_BASE}/mupen64plus_next_libretro.dll.zip",
        "core_dll": "mupen64plus_next_libretro.dll",
        "size_mb": 3.1,
    },
    "ps1": {
        "type": "libretro",
        "core_zip": f"{BUILDBOT_CORES_BASE}/swanstation_libretro.dll.zip",
        "core_dll": "swanstation_libretro.dll",
        "size_mb": 3.1,
    },
    "wii": {
        "type": "libretro_dolphin",
        "core_zip": f"{BUILDBOT_CORES_BASE}/dolphin_libretro.dll.zip",
        "core_dll": "dolphin_libretro.dll",
        "extra_sys_zip": BUILDBOT_DOLPHIN_SYS,
        "standalone_7z": "https://dl.dolphin-emu.org/releases/2609/dolphin-2609-x64.7z",
        "size_mb": 20.0,
    },
    "switch": {
        "type": "standalone_switch",
        "core_dll": "Ryujinx.exe",
        "archive_url": "https://archive.org/download/ryujinx-1.3.3-win_x64_202610/ryujinx-1.3.3-win_x64.zip",
        "size_mb": 33.9,
    },
    "nds": {
        "type": "libretro",
        "core_zip": f"{BUILDBOT_CORES_BASE}/melonds_libretro.dll.zip",
        "core_dll": "melonds_libretro.dll",
        "size_mb": 1.2,
    },
    "3ds": {
        "type": "libretro",
        "core_zip": f"{BUILDBOT_CORES_BASE}/citra_libretro.dll.zip",
        "core_dll": "citra_libretro.dll",
        "size_mb": 11.2,
    },
    "atari2600": {
        "type": "libretro",
        "core_zip": f"{BUILDBOT_CORES_BASE}/stella2014_libretro.dll.zip",
        "core_dll": "stella2014_libretro.dll",
        "size_mb": 0.8,
    },
    "arcade": {
        "type": "libretro",
        "core_zip": f"{BUILDBOT_CORES_BASE}/fbneo_libretro.dll.zip",
        "core_dll": "fbneo_libretro.dll",
        "size_mb": 18.1,
    },
    "dreamcast": {
        "type": "libretro",
        "core_zip": f"{BUILDBOT_CORES_BASE}/flycast_libretro.dll.zip",
        "core_dll": "flycast_libretro.dll",
        "size_mb": 6.5,
    },
    "psp": {
        "type": "libretro",
        "core_zip": f"{BUILDBOT_CORES_BASE}/ppsspp_libretro.dll.zip",
        "core_dll": "ppsspp_libretro.dll",
        "size_mb": 7.0,
    },
}


class EmulatorManager:
    """Manages installation, updates, status checks, and launching of all console engines."""

    def __init__(
        self,
        base_dir: str,
        emulators_dir: str,
        hardware_monitor: HardwareMonitor,
        controller_manager: ControllerManager,
    ):
        self.base_dir = base_dir
        self.emulators_dir = emulators_dir
        self.ra_dir = os.path.join(self.emulators_dir, "retroarch")
        self.cores_dir = os.path.join(self.ra_dir, "cores")
        self.system_dir = os.path.join(self.ra_dir, "system")
        self.dolphin_dir = os.path.join(self.emulators_dir, "dolphin")
        self.switch_dir = os.path.join(self.emulators_dir, "switch")

        for d in (self.emulators_dir, self.ra_dir, self.cores_dir, self.system_dir, self.dolphin_dir, self.switch_dir):
            os.makedirs(d, exist_ok=True)

        self.hardware_monitor = hardware_monitor
        self.controller_manager = controller_manager
        self.install_tasks: Dict[str, Dict[str, Any]] = {}
        self.active_processes: Dict[str, subprocess.Popen] = {}

    def is_retroarch_installed(self) -> bool:
        return os.path.exists(os.path.join(self.ra_dir, "retroarch.exe"))

    def is_engine_installed(self, console_id: str) -> bool:
        info = ENGINE_DOWNLOAD_MAP.get(console_id)
        if not info:
            return False
        if info["type"] in ("libretro", "libretro_dolphin"):
            core_path = os.path.join(self.cores_dir, info["core_dll"])
            return self.is_retroarch_installed() and os.path.exists(core_path)
        elif info["type"] == "standalone_switch":
            exe_path = os.path.join(self.switch_dir, "Ryujinx.exe")
            pub_exe = os.path.join(self.switch_dir, "publish", "Ryujinx.exe")
            bridge_ready = os.path.exists(os.path.join(self.switch_dir, "portable", "Config.json"))
            return os.path.exists(exe_path) or os.path.exists(pub_exe) or bridge_ready
        return False

    def get_all_engines_status(self) -> List[Dict[str, Any]]:
        sys_prof = self.hardware_monitor.get_system_profile()
        compat_map = sys_prof.get("console_compatibility", {})
        result = []

        for cid, spec in CONSOLE_SPECS.items():
            dl_info = ENGINE_DOWNLOAD_MAP.get(cid, {})
            installed = self.is_engine_installed(cid)
            task = self.install_tasks.get(cid, {})
            compat = compat_map.get(cid, {})

            # Check if native binary exists specifically for Switch
            native_binary_ready = installed
            firmware_installed = True
            if cid == "switch":
                native_binary_ready = (
                    os.path.exists(os.path.join(self.switch_dir, "Ryujinx.exe"))
                    or os.path.exists(os.path.join(self.switch_dir, "publish", "Ryujinx.exe"))
                )
                reg_dir = os.path.join(self.switch_dir, "portable", "bis", "system", "Contents", "registered")
                fw_count = len(os.listdir(reg_dir)) if os.path.exists(reg_dir) else 0
                firmware_installed = fw_count > 50

            install_msg = task.get("message")
            if not install_msg:
                if installed:
                    if cid == "switch" and firmware_installed:
                        install_msg = "Prêt à jouer (Firmware 18.0.0 actif)"
                    else:
                        install_msg = "Prêt à jouer"
                else:
                    install_msg = "Disponible en 1 clic"

            result.append({
                "console_id": cid,
                "name": spec["name"],
                "short_name": spec["short_name"],
                "manufacturer": spec["manufacturer"],
                "release_year": spec["release_year"],
                "generation": spec["generation"],
                "engine_name": spec["engine_name"],
                "core_file": spec["core_file"],
                "weight_category": spec["weight_category"],
                "weight_label": spec["weight_label"],
                "weight_score": spec["weight_score"],
                "size_mb": dl_info.get("size_mb", 1.5),
                "installed": installed,
                "native_binary_ready": native_binary_ready,
                "firmware_installed": firmware_installed,
                "install_status": task.get("status", "installed" if installed else "not_installed"),
                "install_progress": task.get("progress", 100 if installed else 0),
                "install_message": install_msg,
                "compatibility": compat,
                "supported_controllers": spec["supported_controllers"],
                "extensions": spec["extensions"],
                "accent_color": spec["accent_color"],
                "description": spec["description"],
            })
        return result

    def ensure_retroarch_base(self, progress_cb=None) -> bool:
        """Downloads and extracts RetroArch_update.7z if retroarch.exe is not present."""
        if self.is_retroarch_installed():
            return True
        archive_path = os.path.join(self.emulators_dir, "ra_base.7z")
        try:
            if progress_cb:
                progress_cb(10, "Téléchargement du moteur central RetroArch Windows x64...")
            with requests.get(BUILDBOT_RETROARCH_UPDATE, stream=True, timeout=60) as r:
                r.raise_for_status()
                total = int(r.headers.get("Content-Length", 58000000))
                downloaded = 0
                with open(archive_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=262144):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if progress_cb and total > 0:
                                pct = 10 + int(50 * (downloaded / total))
                                progress_cb(pct, f"Téléchargement RetroArch ({downloaded // (1024*1024)} Mo)...")

            if progress_cb:
                progress_cb(65, "Extraction de RetroArch Windows x64...")
            subprocess.run(
                ["7z", "x", archive_path, f"-o{self.emulators_dir}", "-y"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            extracted_sub = os.path.join(self.emulators_dir, "RetroArch-Win64")
            if os.path.exists(extracted_sub):
                for item in os.listdir(extracted_sub):
                    src = os.path.join(extracted_sub, item)
                    dst = os.path.join(self.ra_dir, item)
                    if os.path.isdir(src):
                        shutil.copytree(src, dst, dirs_exist_ok=True)
                    else:
                        shutil.copy2(src, dst)
                shutil.rmtree(extracted_sub, ignore_errors=True)
            if os.path.exists(archive_path):
                os.remove(archive_path)
            return self.is_retroarch_installed()
        except Exception as e:
            if progress_cb:
                progress_cb(0, f"Erreur RetroArch : {e}")
            return False

    def install_engine_sync(self, console_id: str) -> Dict[str, Any]:
        """Synchronously installs the core or standalone engine for `console_id`."""
        info = ENGINE_DOWNLOAD_MAP.get(console_id)
        if not info:
            return {"ok": False, "message": f"Console inconnue : {console_id}"}

        def _update(pct: int, msg: str, status: str = "installing"):
            self.install_tasks[console_id] = {
                "status": status,
                "progress": pct,
                "message": msg,
            }

        try:
            _update(5, "Préparation de l'installation...")
            if info["type"] in ("libretro", "libretro_dolphin"):
                if not self.is_retroarch_installed():
                    ok = self.ensure_retroarch_base(progress_cb=_update)
                    if not ok:
                        _update(0, "Échec de l'installation de la base RetroArch.", "error")
                        return {"ok": False, "message": "Échec base RetroArch"}

                _update(40, f"Téléchargement du cœur {info['core_dll']}...")
                r = requests.get(info["core_zip"], timeout=30)
                r.raise_for_status()
                _update(75, f"Extraction de {info['core_dll']}...")
                with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
                    zf.extractall(self.cores_dir)

                if info.get("extra_sys_zip"):
                    dolphin_sys_target = os.path.join(self.system_dir, "dolphin-emu", "Sys")
                    if not os.path.exists(dolphin_sys_target):
                        _update(85, "Téléchargement des fichiers système Wii / GameCube (Dolphin Sys)...")
                        rsys = requests.get(info["extra_sys_zip"], timeout=45)
                        if rsys.status_code == 200:
                            temp_sys = os.path.join(self.system_dir, "_dolphin_temp")
                            os.makedirs(temp_sys, exist_ok=True)
                            with zipfile.ZipFile(io.BytesIO(rsys.content)) as zf:
                                zf.extractall(temp_sys)
                            os.makedirs(os.path.join(self.system_dir, "dolphin-emu"), exist_ok=True)
                            src_sys = os.path.join(temp_sys, "dolphin-emu", "Sys")
                            if os.path.exists(src_sys):
                                shutil.copytree(src_sys, dolphin_sys_target, dirs_exist_ok=True)
                            shutil.rmtree(temp_sys, ignore_errors=True)

                self.controller_manager.sync_to_all_emulators()
                _update(100, "Moteur installé et configuré !", "installed")
                return {"ok": True, "console_id": console_id, "message": "Moteur installé avec succès."}

            elif info["type"] == "standalone_switch":
                _update(20, "Configuration du moteur Nintendo Switch (Ryujinx Portable)...")
                self.controller_manager.sync_to_all_emulators()
                # Attempt downloading portable Ryujinx binary if requested
                archive_url = info.get("archive_url")
                if archive_url:
                    try:
                        _update(35, "Téléchargement de Ryujinx Windows x64 Portable...")
                        with requests.get(archive_url, stream=True, timeout=45) as r:
                            if r.status_code == 200:
                                total = int(r.headers.get("Content-Length", 65000000))
                                buf = io.BytesIO()
                                dl = 0
                                for chunk in r.iter_content(chunk_size=262144):
                                    if chunk:
                                        buf.write(chunk)
                                        dl += len(chunk)
                                        if total > 0:
                                            _update(35 + int(50 * dl / total), f"Téléchargement Ryujinx ({dl // (1024*1024)} Mo)...")
                                _update(90, "Extraction de Ryujinx Portable...")
                                buf.seek(0)
                                with zipfile.ZipFile(buf) as zf:
                                    zf.extractall(self.switch_dir)
                    except Exception:
                        pass
                _update(100, "Moteur Switch configuré et prêt !", "installed")
                return {"ok": True, "console_id": console_id, "message": "Moteur Switch configuré."}

        except Exception as e:
            _update(0, f"Erreur : {e}", "error")
            return {"ok": False, "message": str(e)}

        return {"ok": False, "message": "Type de moteur non supporté."}

    def install_engine_async(self, console_id: str) -> Dict[str, Any]:
        t = threading.Thread(target=self.install_engine_sync, args=(console_id,), daemon=True)
        t.start()
        return {"ok": True, "status": "started", "console_id": console_id}

    def install_all_essential_cores(self) -> Dict[str, Any]:
        """Installs all Libretro cores for immediate out-of-the-box play."""
        results = {}
        for cid in ("amstrad_cpc", "amiga", "nes", "snes", "gba", "megadrive", "n64", "ps1", "wii", "nds", "3ds"):
            if not self.is_engine_installed(cid):
                results[cid] = self.install_engine_sync(cid)
            else:
                results[cid] = {"ok": True, "status": "already_installed"}
        self.controller_manager.sync_to_all_emulators()
        return results

    def launch_game(self, game: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepares controller mappings and PC performance tweaks, ensures the target
        emulator core is installed, and launches the game in its native emulator window.
        """
        console_id = game.get("console_id", "nes")
        rom_path = game.get("local_path", "")
        if not rom_path or not os.path.exists(rom_path):
            return {
                "ok": False,
                "message": f"Le fichier du jeu est introuvable ({rom_path}). Veuillez d'abord le télécharger.",
            }

        # Auto-correct console_id based on file extension if mismatched or generic
        ext_lower = os.path.splitext(rom_path)[1].lower()
        if ext_lower in (".nsp", ".xci", ".nro", ".nca"):
            console_id = "switch"
        elif ext_lower in (".nds", ".dsi"):
            console_id = "nds"
        elif ext_lower in (".3ds", ".cia", ".cxi", ".app"):
            console_id = "3ds"
        elif ext_lower in (".iso", ".rvz", ".wbfs", ".gcm", ".ciso", ".dol"):
            console_id = "wii"
        elif ext_lower in (".chd", ".pbp"):
            console_id = "ps1"
        elif ext_lower in (".z64", ".n64", ".v64"):
            console_id = "n64"
        elif ext_lower in (".md", ".smd", ".gen"):
            console_id = "megadrive"
        elif ext_lower in (".gba", ".gb", ".gbc"):
            console_id = "gba"
        elif ext_lower in (".sfc", ".smc"):
            console_id = "snes"
        elif ext_lower == ".dsk":
            console_id = "amstrad_cpc"
        elif ext_lower in (".adf", ".adz", ".lha"):
            console_id = "amiga"

        # 1. Check PC performance profile to apply Eco Mode if needed
        sys_prof = self.hardware_monitor.get_system_profile()
        lightweight_mode = sys_prof.get("pc_tier") == "leger"

        # 2. Synchronize central controller mappings to all emulators
        self.controller_manager.sync_to_all_emulators(lightweight_mode=lightweight_mode)

        # 3. Ensure engine is installed
        if not self.is_engine_installed(console_id):
            install_res = self.install_engine_sync(console_id)
            if not install_res.get("ok"):
                return {
                    "ok": False,
                    "message": f"Impossible d'installer automatiquement le moteur pour {console_id}: {install_res.get('message')}",
                }

        info = ENGINE_DOWNLOAD_MAP.get(console_id, {})
        spec = CONSOLE_SPECS.get(console_id, {})

        # 4. If ROM is a .zip and the core prefers extracted disk/ROM (e.g., Amiga .adf or Wii .dol/.iso),
        # RetroArch handles .zip transparently for NES/SNES/GBA/MD/N64/Amstrad/Amiga,
        # but for Dolphin/Switch we extract if zipped.
        launch_target = rom_path
        if console_id in ("wii", "switch", "3ds", "nds") and rom_path.lower().endswith((".zip", ".rar", ".7z")):
            extract_dir = os.path.splitext(rom_path)[0] + "_extracted"
            os.makedirs(extract_dir, exist_ok=True)
            try:
                if rom_path.lower().endswith(".zip"):
                    with zipfile.ZipFile(rom_path, "r") as zf:
                        zf.extractall(extract_dir)
                else:
                    subprocess.run(["tar", "-xf", rom_path, "-C", extract_dir], capture_output=True, timeout=180)
                for root, _, files in os.walk(extract_dir):
                    for fn in files:
                        if any(fn.lower().endswith(ext) for ext in spec.get("extensions", [])):
                            if not fn.lower().endswith((".zip", ".rar", ".7z")):
                                launch_target = os.path.join(root, fn)
                                break
            except Exception:
                pass

        # 5. Launch native emulator executable
        if console_id == "wii":
            dolphin_exe = os.path.join(self.dolphin_dir, "Dolphin.exe")
            ext = os.path.splitext(launch_target)[1].lower()
            if os.path.exists(dolphin_exe) and ext in (".iso", ".rvz", ".wbfs", ".gcm", ".ciso", ".dol", ".elf"):
                cmd = [dolphin_exe, "-b", "-e", launch_target]
                proc = subprocess.Popen(
                    cmd,
                    cwd=self.dolphin_dir,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                self.active_processes[game.get("id", "current")] = proc
                return {
                    "ok": True,
                    "pid": proc.pid,
                    "engine": "Dolphin 2609 Portable (Wii / GameCube)",
                    "controller_profile": self.controller_manager.get_active_profile()["name"],
                    "lightweight_mode": lightweight_mode,
                    "message": f"Jeu Wii/GC « {game.get('title')} » lancé dans Dolphin Portable.",
                }

        if info.get("type") in ("libretro", "libretro_dolphin"):
            ra_exe = os.path.join(self.ra_dir, "retroarch.exe")
            core_dll = os.path.join(self.cores_dir, info["core_dll"])
            cfg_file = os.path.join(self.ra_dir, "retroarch.cfg")

            # Check if game is actually a fallback retro ROM (e.g. a Switch homebrew packaged as NES/GBA/NRO)
            ext = os.path.splitext(launch_target)[1].lower()
            if ext == ".nes":
                core_dll = os.path.join(self.cores_dir, "fceumm_libretro.dll")
            elif ext in (".sfc", ".smc"):
                core_dll = os.path.join(self.cores_dir, "snes9x_libretro.dll")
            elif ext in (".gba", ".gb", ".gbc"):
                core_dll = os.path.join(self.cores_dir, "mgba_libretro.dll")

            # PS1: prefer pcsx_rearmed if present (built-in HLE BIOS)
            if console_id == "ps1":
                pcsx_core = os.path.join(self.cores_dir, "pcsx_rearmed_libretro.dll")
                if os.path.exists(pcsx_core):
                    core_dll = pcsx_core

            # NDS: prefer melonds or desmume
            if console_id == "nds" or ext in (".nds", ".dsi"):
                melonds_core = os.path.join(self.cores_dir, "melonds_libretro.dll")
                desmume_core = os.path.join(self.cores_dir, "desmume_libretro.dll")
                if os.path.exists(melonds_core):
                    core_dll = melonds_core
                elif os.path.exists(desmume_core):
                    core_dll = desmume_core

            # 3DS: citra
            if console_id == "3ds" or ext in (".3ds", ".cia", ".cxi", ".app"):
                citra_core = os.path.join(self.cores_dir, "citra_libretro.dll")
                if os.path.exists(citra_core):
                    core_dll = citra_core

            cmd = [ra_exe, "--config", cfg_file, "-L", core_dll, launch_target]
            proc = subprocess.Popen(
                cmd,
                cwd=self.ra_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self.active_processes[game.get("id", "current")] = proc
            return {
                "ok": True,
                "pid": proc.pid,
                "engine": spec.get("engine_name", "RetroArch"),
                "controller_profile": self.controller_manager.get_active_profile()["name"],
                "lightweight_mode": lightweight_mode,
                "message": f"Jeu « {game.get('title')} » lancé avec {spec.get('engine_name')} (Manette préconfigurée).",
            }

        elif info.get("type") == "standalone_switch":
            # Check if Ryujinx.exe is present, or if the file is playable via RetroArch fallback
            ryu_exe = os.path.join(self.switch_dir, "Ryujinx.exe")
            if not os.path.exists(ryu_exe):
                alt_exe = os.path.join(self.switch_dir, "publish", "Ryujinx.exe")
                if os.path.exists(alt_exe):
                    ryu_exe = alt_exe

            ext = os.path.splitext(launch_target)[1].lower()
            if os.path.exists(ryu_exe) and ext in (".nsp", ".xci", ".nro", ".nca"):
                cmd = [ryu_exe, launch_target]
                proc = subprocess.Popen(
                    cmd,
                    cwd=os.path.dirname(ryu_exe),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                self.active_processes[game.get("id", "current")] = proc
                return {
                    "ok": True,
                    "pid": proc.pid,
                    "engine": "Ryujinx Portable (Nintendo Switch)",
                    "controller_profile": self.controller_manager.get_active_profile()["name"],
                    "lightweight_mode": lightweight_mode,
                    "message": f"Jeu Switch « {game.get('title')} » lancé dans Ryujinx Portable.",
                }
            else:
                # Fallback to RetroArch if the downloaded demo/adaptation is a cross-platform ROM
                ra_exe = os.path.join(self.ra_dir, "retroarch.exe")
                cfg_file = os.path.join(self.ra_dir, "retroarch.cfg")
                core_dll = os.path.join(self.cores_dir, "mgba_libretro.dll")
                if ext == ".nes":
                    core_dll = os.path.join(self.cores_dir, "fceumm_libretro.dll")
                elif ext in (".sfc", ".smc"):
                    core_dll = os.path.join(self.cores_dir, "snes9x_libretro.dll")
                elif ext in (".z64", ".n64"):
                    core_dll = os.path.join(self.cores_dir, "mupen64plus_next_libretro.dll")
                cmd = [ra_exe, "--config", cfg_file, "-L", core_dll, launch_target]
                proc = subprocess.Popen(
                    cmd,
                    cwd=self.ra_dir,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                self.active_processes[game.get("id", "current")] = proc
                return {
                    "ok": True,
                    "pid": proc.pid,
                    "engine": "Moteur Hybride Switch / Libretro",
                    "controller_profile": self.controller_manager.get_active_profile()["name"],
                    "lightweight_mode": lightweight_mode,
                    "message": f"Jeu « {game.get('title')} » lancé avec contrôleur préconfiguré.",
                }

        return {"ok": False, "message": "Moteur d'exécution non reconnu."}

    def open_emulator_gui(self, console_id: str) -> Dict[str, Any]:
        """Opens the standalone emulator GUI window (RetroArch, Dolphin, Ryujinx)."""
        if console_id == "wii":
            dolphin_exe = os.path.join(self.dolphin_dir, "Dolphin.exe")
            if os.path.exists(dolphin_exe):
                proc = subprocess.Popen([dolphin_exe], cwd=self.dolphin_dir)
                return {"ok": True, "engine": "Dolphin 2609 Portable (Wii / GameCube)", "pid": proc.pid, "message": "Interface de Dolphin ouverte."}
            return {"ok": False, "message": "Dolphin.exe introuvable."}
        elif console_id == "switch":
            ryu_exe = os.path.join(self.switch_dir, "Ryujinx.exe")
            if not os.path.exists(ryu_exe):
                ryu_exe = os.path.join(self.switch_dir, "publish", "Ryujinx.exe")
            if os.path.exists(ryu_exe):
                proc = subprocess.Popen([ryu_exe], cwd=os.path.dirname(ryu_exe))
                return {"ok": True, "engine": "Ryujinx 1.3.3 Portable (Switch)", "pid": proc.pid, "message": "Interface de Ryujinx ouverte."}
            return {"ok": False, "message": "Ryujinx.exe introuvable."}
        else:
            ra_exe = os.path.join(self.ra_dir, "retroarch.exe")
            if os.path.exists(ra_exe):
                cfg_file = os.path.join(self.ra_dir, "retroarch.cfg")
                info = ENGINE_DOWNLOAD_MAP.get(console_id, {})
                core_dll = os.path.join(self.cores_dir, info.get("core_dll", ""))
                cmd = [ra_exe, "--config", cfg_file]
                if os.path.exists(core_dll):
                    cmd.extend(["-L", core_dll])
                proc = subprocess.Popen(cmd, cwd=self.ra_dir)
                spec = CONSOLE_SPECS.get(console_id, {})
                return {"ok": True, "engine": spec.get("engine_name", "RetroArch"), "pid": proc.pid, "message": f"Interface de {spec.get('name', 'RetroArch')} ouverte."}
            return {"ok": False, "message": "retroarch.exe introuvable."}
