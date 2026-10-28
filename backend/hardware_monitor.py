"""
Hardware Monitor & PC Resource Analyzer for AetherDeck.
Detects CPU, RAM, GPU on Windows and calculates compatibility tiers for each console
so lightweight PCs can smoothly run lightweight/medium emulators and receive tailored
optimizations.
"""

import ctypes
import os
import platform
import subprocess
import time
import winreg
from typing import Dict, Any, List
import psutil


CONSOLE_SPECS: Dict[str, Dict[str, Any]] = {
    "amstrad_cpc": {
        "id": "amstrad_cpc",
        "name": "Amstrad CPC (464 / 6128)",
        "short_name": "Amstrad CPC",
        "manufacturer": "Amstrad",
        "release_year": 1984,
        "generation": "8-bit Micro-ordinateur",
        "weight_category": "leger",
        "weight_label": "Très Léger",
        "weight_score": 1,  # 1 to 5
        "min_ram_gb": 1.0,
        "min_cpu_cores": 1,
        "engine_name": "Caprice32 (Libretro cap32)",
        "core_file": "cap32_libretro.dll",
        "extensions": [".dsk", ".cdt", ".sna", ".zip", ".cpr"],
        "supported_controllers": [
            {"id": "joystick_retro", "name": "Joystick Rétro / Manette (Port 1)", "icon": "joystick", "recommended": True},
            {"id": "keyboard", "name": "Clavier Amstrad Complet", "icon": "keyboard", "recommended": True},
            {"id": "xbox_ps_switch", "name": "Manette Xbox / PlayStation / Switch", "icon": "gamepad", "recommended": True},
        ],
        "accent_color": "#e11d48",
        "description": "Micro-ordinateur 8-bit mythique d'Alan Sugar. Idéal sur n'importe quel PC, même très modeste.",
    },
    "amiga": {
        "id": "amiga",
        "name": "Commodore Amiga (500 / 1200)",
        "short_name": "Amiga",
        "manufacturer": "Commodore",
        "release_year": 1985,
        "generation": "16/32-bit Micro-ordinateur",
        "weight_category": "leger",
        "weight_label": "Très Léger",
        "weight_score": 1,
        "min_ram_gb": 1.5,
        "min_cpu_cores": 1,
        "engine_name": "PUAE (Commodore Amiga Engine)",
        "core_file": "puae_libretro.dll",
        "extensions": [".adf", ".adz", ".dms", ".ipf", ".lha", ".hdf", ".zip"],
        "supported_controllers": [
            {"id": "xbox_ps_switch", "name": "Manette Standard / Joystick Amiga", "icon": "gamepad", "recommended": True},
            {"id": "mouse_keyboard", "name": "Souris + Clavier (Jeux de stratégie / Point & Click)", "icon": "mouse", "recommended": True},
        ],
        "accent_color": "#f97316",
        "description": "Révolution graphique et sonore des années 80/90 (Lemmings, Turrican, Shadow of the Beast). Très faible consommation CPU.",
    },
    "nes": {
        "id": "nes",
        "name": "Nintendo Entertainment System (NES)",
        "short_name": "NES",
        "manufacturer": "Nintendo",
        "release_year": 1983,
        "generation": "Console 8-bit",
        "weight_category": "leger",
        "weight_label": "Très Léger",
        "weight_score": 1,
        "min_ram_gb": 1.0,
        "min_cpu_cores": 1,
        "engine_name": "FCEUmm (Libretro NES)",
        "core_file": "fceumm_libretro.dll",
        "extensions": [".nes", ".fds", ".unf", ".zip"],
        "supported_controllers": [
            {"id": "xbox_ps_switch", "name": "Manette Xbox / PlayStation / Switch / USB", "icon": "gamepad", "recommended": True},
            {"id": "keyboard", "name": "Clavier PC", "icon": "keyboard", "recommended": False},
        ],
        "accent_color": "#dc2626",
        "description": "La console 8-bit légendaire de Nintendo (Super Mario Bros. 1, 2, 3, Zelda, Metroid). Fonctionne à 60 FPS sur 100% des PC.",
    },
    "snes": {
        "id": "snes",
        "name": "Super Nintendo (SNES)",
        "short_name": "Super Nintendo",
        "manufacturer": "Nintendo",
        "release_year": 1990,
        "generation": "Console 16-bit",
        "weight_category": "leger",
        "weight_label": "Très Léger",
        "weight_score": 1,
        "min_ram_gb": 1.0,
        "min_cpu_cores": 1,
        "engine_name": "Snes9x (Libretro SNES)",
        "core_file": "snes9x_libretro.dll",
        "extensions": [".sfc", ".smc", ".zip"],
        "supported_controllers": [
            {"id": "xbox_ps_switch", "name": "Manette 6 boutons (Xbox, PS, Switch Pro, SNES USB)", "icon": "gamepad", "recommended": True},
            {"id": "keyboard", "name": "Clavier PC", "icon": "keyboard", "recommended": False},
        ],
        "accent_color": "#7c3aed",
        "description": "L'âge d'or du 16-bit (Super Mario World, Mario Kart, Zelda: A Link to the Past). Émulation ultra-légère et instantanée.",
    },
    "gba": {
        "id": "gba",
        "name": "Game Boy / Color / Advance (GBA)",
        "short_name": "Game Boy Advance",
        "manufacturer": "Nintendo",
        "release_year": 2001,
        "generation": "Portable 32-bit",
        "weight_category": "leger",
        "weight_label": "Très Léger",
        "weight_score": 1,
        "min_ram_gb": 1.0,
        "min_cpu_cores": 1,
        "engine_name": "mGBA (Libretro GB/GBC/GBA)",
        "core_file": "mgba_libretro.dll",
        "extensions": [".gba", ".gb", ".gbc", ".zip"],
        "supported_controllers": [
            {"id": "xbox_ps_switch", "name": "Toute Manette USB / Bluetooth", "icon": "gamepad", "recommended": True},
            {"id": "keyboard", "name": "Clavier PC", "icon": "keyboard", "recommended": True},
        ],
        "accent_color": "#4f46e5",
        "description": "Compatible Game Boy, Game Boy Color et Game Boy Advance (Super Mario Advance, Pokémon, Metroid Fusion).",
    },
    "megadrive": {
        "id": "megadrive",
        "name": "Sega Mega Drive / Genesis",
        "short_name": "Mega Drive",
        "manufacturer": "Sega",
        "release_year": 1988,
        "generation": "Console 16-bit",
        "weight_category": "leger",
        "weight_label": "Très Léger",
        "weight_score": 1,
        "min_ram_gb": 1.0,
        "min_cpu_cores": 1,
        "engine_name": "Genesis Plus GX (Libretro Sega)",
        "core_file": "genesis_plus_gx_libretro.dll",
        "extensions": [".md", ".smd", ".gen", ".bin", ".sms", ".gg", ".zip"],
        "supported_controllers": [
            {"id": "xbox_ps_switch", "name": "Manette 3/6 boutons (Xbox, PS, Switch, Sega USB)", "icon": "gamepad", "recommended": True},
            {"id": "keyboard", "name": "Clavier PC", "icon": "keyboard", "recommended": False},
        ],
        "accent_color": "#2563eb",
        "description": "La reine 16-bit de Sega (Sonic the Hedgehog, Streets of Rage, Golden Axe). Très économe en ressources.",
    },
    "n64": {
        "id": "n64",
        "name": "Nintendo 64 (N64)",
        "short_name": "Nintendo 64",
        "manufacturer": "Nintendo",
        "release_year": 1996,
        "generation": "Console 64-bit 3D",
        "weight_category": "moyen",
        "weight_label": "Moyen",
        "weight_score": 2,
        "min_ram_gb": 2.0,
        "min_cpu_cores": 2,
        "engine_name": "Mupen64Plus-Next (OpenGL/ParaLLEl)",
        "core_file": "mupen64plus_next_libretro.dll",
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "supported_controllers": [
            {"id": "analog_gamepad", "name": "Manette avec Stick Analogique (Xbox, PS, Switch Pro)", "icon": "gamepad", "recommended": True},
            {"id": "keyboard", "name": "Clavier PC (Stick émulé)", "icon": "keyboard", "recommended": False},
        ],
        "accent_color": "#16a34a",
        "description": "Pionnière de la 3D temps réel (Super Mario 64, Mario Kart 64, Zelda Ocarina of Time). Stick analogique recommandé.",
    },
    "ps1": {
        "id": "ps1",
        "name": "Sony PlayStation (PS1)",
        "short_name": "PlayStation 1",
        "manufacturer": "Sony",
        "release_year": 1994,
        "generation": "Console 32-bit 3D",
        "weight_category": "moyen",
        "weight_label": "Moyen",
        "weight_score": 2,
        "min_ram_gb": 2.0,
        "min_cpu_cores": 2,
        "engine_name": "SwanStation / PCSX-ReARMed",
        "core_file": "swanstation_libretro.dll",
        "extensions": [".chd", ".cue", ".bin", ".iso", ".pbp", ".m3u"],
        "supported_controllers": [
            {"id": "dualshock", "name": "Manette DualShock / Xbox / Switch Pro", "icon": "gamepad", "recommended": True},
            {"id": "keyboard", "name": "Clavier PC", "icon": "keyboard", "recommended": False},
        ],
        "accent_color": "#0284c7",
        "description": "La première PlayStation de Sony (Crash Bandicoot, Tekken 3, Gran Turismo, Castlevania). Fluide sur tout PC bureautique.",
    },
    "wii": {
        "id": "wii",
        "name": "Nintendo Wii & GameCube",
        "short_name": "Wii / GameCube",
        "manufacturer": "Nintendo",
        "release_year": 2006,
        "generation": "Console 128-bit / Motion",
        "weight_category": "lourd",
        "weight_label": "Lourd (3D HD)",
        "weight_score": 4,
        "min_ram_gb": 4.0,
        "min_cpu_cores": 4,
        "engine_name": "Dolphin Engine (Libretro / Standalone)",
        "core_file": "dolphin_libretro.dll",
        "extensions": [".iso", ".rvz", ".wbfs", ".gcm", ".ciso", ".dol", ".elf"],
        "supported_controllers": [
            {"id": "xbox_ps_switch", "name": "Manette Xbox / PS / Switch (Wiimote & Pad GC émulés)", "icon": "gamepad", "recommended": True},
            {"id": "wiimote", "name": "Wiimote Originale Bluetooth / Manette Classique Wii", "icon": "motion", "recommended": True},
            {"id": "mouse_keyboard", "name": "Clavier + Souris (Pointeur IR Wii émulé)", "icon": "mouse", "recommended": False},
        ],
        "accent_color": "#0ea5e9",
        "description": "Émulation combinée Nintendo Wii et GameCube (Super Mario Galaxy, New Super Mario Bros. Wii, Mario Kart Wii, Super Mario Sunshine).",
    },
    "switch": {
        "id": "switch",
        "name": "Nintendo Switch",
        "short_name": "Nintendo Switch",
        "manufacturer": "Nintendo",
        "release_year": 2017,
        "generation": "Console Hybride HD",
        "weight_category": "lourd",
        "weight_label": "Très Lourd (PC Gaming)",
        "weight_score": 5,
        "min_ram_gb": 8.0,
        "min_cpu_cores": 6,
        "engine_name": "Ryujinx Portable Engine",
        "core_file": "Ryujinx.exe",
        "extensions": [".nsp", ".xci", ".nro", ".nca"],
        "supported_controllers": [
            {"id": "switch_pro_joycon", "name": "Switch Pro Controller / Paire de Joy-Con", "icon": "gamepad", "recommended": True},
            {"id": "xbox_ps", "name": "Manette Xbox Series/One ou DualSense/DS4 (Auto-mappée)", "icon": "gamepad", "recommended": True},
            {"id": "keyboard", "name": "Clavier PC (Profil Pro Controller émulé)", "icon": "keyboard", "recommended": False},
        ],
        "accent_color": "#ef4444",
        "description": "Émulation Nintendo Switch moderne (Super Mario Odyssey, Mario Kart 8 Deluxe, Super Mario Bros. Wonder, Homebrew Switch). Nécessite un PC performant.",
    },
    "nds": {
        "id": "nds",
        "name": "Nintendo DS (NDS)",
        "short_name": "Nintendo DS",
        "manufacturer": "Nintendo",
        "release_year": 2004,
        "generation": "Console Portable Dual-Screen",
        "weight_category": "leger",
        "weight_label": "Très Léger",
        "weight_score": 1,
        "min_ram_gb": 1.0,
        "min_cpu_cores": 1,
        "engine_name": "MelonDS / DeSmuME (Libretro DS)",
        "core_file": "melonds_libretro.dll",
        "extensions": [".nds", ".dsi", ".zip", ".7z"],
        "supported_controllers": [
            {"id": "xbox_ps_switch", "name": "Manette Xbox / PlayStation / Switch / USB", "icon": "gamepad", "recommended": True},
            {"id": "touch_mouse", "name": "Souris / Pointeur (Écran Tactile DS)", "icon": "mouse", "recommended": True},
            {"id": "keyboard", "name": "Clavier PC", "icon": "keyboard", "recommended": False},
        ],
        "accent_color": "#059669",
        "description": "La console portable double écran révolutionnaire de Nintendo (New Super Mario Bros., Mario Kart DS, Pokémon Platine, Zelda Phantom Hourglass).",
    },
    "3ds": {
        "id": "3ds",
        "name": "Nintendo 3DS (3DS)",
        "short_name": "Nintendo 3DS",
        "manufacturer": "Nintendo",
        "release_year": 2011,
        "generation": "Console Portable 3D",
        "weight_category": "moyen",
        "weight_label": "Moyen (GPU 3D)",
        "weight_score": 3,
        "min_ram_gb": 4.0,
        "min_cpu_cores": 4,
        "engine_name": "Citra Engine (Libretro 3DS)",
        "core_file": "citra_libretro.dll",
        "extensions": [".3ds", ".cia", ".cxi", ".app", ".zip", ".7z"],
        "supported_controllers": [
            {"id": "analog_gamepad", "name": "Manette avec Stick Analogique (Xbox, PS, Switch Pro)", "icon": "gamepad", "recommended": True},
            {"id": "touch_mouse", "name": "Souris / Pointeur (Écran Tactile 3DS)", "icon": "mouse", "recommended": True},
            {"id": "keyboard", "name": "Clavier PC", "icon": "keyboard", "recommended": False},
        ],
        "accent_color": "#d97706",
        "description": "La console portable 3D relief de Nintendo (Super Mario 3D Land, Mario Kart 7, The Legend of Zelda: A Link Between Worlds, Pokémon Soleil/Lune).",
    },
    "atari2600": {
        "id": "atari2600",
        "name": "Atari 2600 (VCS)",
        "short_name": "Atari 2600",
        "manufacturer": "Atari",
        "release_year": 1977,
        "generation": "Console 8-bit Pionnière",
        "weight_category": "leger",
        "weight_label": "Très Léger",
        "weight_score": 1,
        "min_ram_gb": 1.0,
        "min_cpu_cores": 1,
        "engine_name": "Stella 2014 (Libretro Atari 2600)",
        "core_file": "stella2014_libretro.dll",
        "extensions": [".a26", ".bin", ".zip"],
        "supported_controllers": [
            {"id": "joystick_retro", "name": "Joystick Atari 1 Bouton / Manette USB", "icon": "joystick", "recommended": True},
            {"id": "keyboard", "name": "Clavier PC", "icon": "keyboard", "recommended": False},
        ],
        "accent_color": "#b45309",
        "description": "La pionnière absolue du jeu vidéo domestique (Pitfall!, Space Invaders, Pac-Man, River Raid, Adventure). Émulation instantanée.",
    },
    "arcade": {
        "id": "arcade",
        "name": "Bornes d'Arcade & SNK Neo Geo",
        "short_name": "Arcade / Neo Geo",
        "manufacturer": "Capcom / SNK / Sega / Namco",
        "release_year": 1990,
        "generation": "Systèmes d'Arcade (CPS / MVS)",
        "weight_category": "leger",
        "weight_label": "Très Léger",
        "weight_score": 1,
        "min_ram_gb": 1.5,
        "min_cpu_cores": 1,
        "engine_name": "FinalBurn Neo (FBNeo Arcade / Neo Geo)",
        "core_file": "fbneo_libretro.dll",
        "extensions": [".zip", ".7z"],
        "supported_controllers": [
            {"id": "arcade_stick", "name": "Stick Arcade / Manette 6 boutons (Xbox, PS, Switch)", "icon": "joystick", "recommended": True},
            {"id": "keyboard", "name": "Clavier PC", "icon": "keyboard", "recommended": False},
        ],
        "accent_color": "#eab308",
        "description": "L'âge d'or des salles d'arcade et de la Neo Geo MVS/AES (Metal Slug, King of Fighters, Street Fighter II, Garou: Mark of the Wolves).",
    },
    "dreamcast": {
        "id": "dreamcast",
        "name": "Sega Dreamcast",
        "short_name": "Dreamcast",
        "manufacturer": "Sega",
        "release_year": 1998,
        "generation": "Console 128-bit 3D",
        "weight_category": "moyen",
        "weight_label": "Moyen (3D HLE)",
        "weight_score": 2,
        "min_ram_gb": 2.0,
        "min_cpu_cores": 2,
        "engine_name": "Flycast (Sega Dreamcast / Naomi HLE)",
        "core_file": "flycast_libretro.dll",
        "extensions": [".chd", ".cdi", ".gdi", ".zip"],
        "supported_controllers": [
            {"id": "analog_gamepad", "name": "Manette avec Gâchettes & Stick Analogique (Xbox, PS, Switch)", "icon": "gamepad", "recommended": True},
            {"id": "keyboard", "name": "Clavier PC", "icon": "keyboard", "recommended": False},
        ],
        "accent_color": "#ea580c",
        "description": "Dernière console mythique de Sega (Sonic Adventure 1 & 2, Crazy Taxi, SoulCalibur, Jet Set Radio, Shenmue) avec BIOS HLE intégré.",
    },
    "psp": {
        "id": "psp",
        "name": "Sony PlayStation Portable (PSP)",
        "short_name": "Sony PSP",
        "manufacturer": "Sony",
        "release_year": 2004,
        "generation": "Console Portable 3D 16:9",
        "weight_category": "moyen",
        "weight_label": "Moyen (3D HD)",
        "weight_score": 2,
        "min_ram_gb": 2.0,
        "min_cpu_cores": 2,
        "engine_name": "PPSSPP (Libretro PSP HLE)",
        "core_file": "ppsspp_libretro.dll",
        "extensions": [".iso", ".cso", ".chd", ".pbp", ".zip"],
        "supported_controllers": [
            {"id": "analog_gamepad", "name": "Manette DualShock / DualSense / Xbox / Switch Pro", "icon": "gamepad", "recommended": True},
            {"id": "keyboard", "name": "Clavier PC", "icon": "keyboard", "recommended": False},
        ],
        "accent_color": "#0284c7",
        "description": "La portable multimédia 3D de Sony (God of War: Chains of Olympus, Crisis Core: Final Fantasy VII, Monster Hunter Freedom Unite, Tekken 6).",
    },
}


class HardwareMonitor:
    """Detects host PC hardware and computes emulator compatibility & performance profiles."""

    def __init__(self):
        self._cached_specs: Dict[str, Any] = {}

    def get_cpu_name(self) -> str:
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"HARDWARE\DESCRIPTION\System\CentralProcessor\0",
            )
            cpu_name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
            winreg.CloseKey(key)
            return cpu_name.strip()
        except Exception:
            return platform.processor() or "Processeur Windows x64"

    def get_gpu_names(self) -> List[str]:
        gpus = []
        try:
            key_path = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as base_key:
                for i in range(16):
                    subkey_name = f"{i:04d}"
                    try:
                        with winreg.OpenKey(base_key, subkey_name) as subkey:
                            desc, _ = winreg.QueryValueEx(subkey, "DriverDesc")
                            if desc and desc.strip() not in gpus:
                                gpus.append(desc.strip())
                    except OSError:
                        continue
        except Exception:
            pass
        if not gpus:
            gpus.append("Carte Graphique Intégrée / DirectX 11+")
        return gpus

    def get_system_profile(self, force_refresh: bool = False) -> Dict[str, Any]:
        if self._cached_specs and not force_refresh:
            # Update live metrics only
            mem = psutil.virtual_memory()
            self._cached_specs["ram_available_gb"] = round(mem.available / (1024 ** 3), 1)
            self._cached_specs["ram_percent"] = mem.percent
            self._cached_specs["cpu_percent"] = psutil.cpu_percent(interval=None)
            return self._cached_specs

        cpu_name = self.get_cpu_name()
        logical_cores = psutil.cpu_count(logical=True) or 2
        physical_cores = psutil.cpu_count(logical=False) or max(1, logical_cores // 2)
        freq = psutil.cpu_freq()
        cpu_mhz = round(freq.max or freq.current or 2400) if freq else 2400

        mem = psutil.virtual_memory()
        ram_total_gb = round(mem.total / (1024 ** 3), 1)
        ram_avail_gb = round(mem.available / (1024 ** 3), 1)

        gpus = self.get_gpu_names()
        gpu_str = " / ".join(gpus)
        has_dedicated_gpu = any(
            kw in gpu_str.lower()
            for kw in ["nvidia", "geforce", "rtx", "gtx", "radeon rx", "arc "]
        )

        # Classify PC Tier
        if ram_total_gb >= 12 and logical_cores >= 6 and (has_dedicated_gpu or logical_cores >= 8):
            tier = "puissant"
            tier_label = "PC Performant / Gaming"
            tier_description = "Votre PC peut faire tourner tous les émulateurs, y compris les consoles lourdes (Wii, GameCube, Switch)."
            max_recommended_score = 5
        elif ram_total_gb >= 6 and logical_cores >= 4:
            tier = "moyen"
            tier_label = "PC Polyvalent / Multimédia"
            tier_description = "Parfait pour toutes les consoles rétro (Amstrad, Amiga, NES, SNES, GBA, Mega Drive, N64, PS1) et correct pour la Wii/GameCube en résolution native."
            max_recommended_score = 4
        else:
            tier = "leger"
            tier_label = "PC Léger / Économe"
            tier_description = "Mode Éco activé : les émulateurs légers et moyens (Amstrad, Amiga, NES, SNES, GBA, Mega Drive, N64, PS1) tourneront à 100% de vitesse sans ralentissement."
            max_recommended_score = 3

        console_compatibility = {}
        for cid, cspec in CONSOLE_SPECS.items():
            score = cspec["weight_score"]
            if score <= 2:
                status = "optimal"
                status_text = "Fluide (60 FPS garantis)"
                badge_color = "#10b981"
            elif score <= max_recommended_score:
                status = "compatible"
                status_text = "Compatible (Performances normales)"
                badge_color = "#3b82f6"
            else:
                status = "demanding"
                status_text = "Gourmand (Mode Éco auto-appliqué)"
                badge_color = "#f59e0b"

            console_compatibility[cid] = {
                "status": status,
                "status_text": status_text,
                "badge_color": badge_color,
                "weight_category": cspec["weight_category"],
                "weight_label": cspec["weight_label"],
                "weight_score": score,
            }

        self._cached_specs = {
            "os": f"Windows {platform.release()} ({platform.machine()})",
            "cpu_name": cpu_name,
            "cpu_physical_cores": physical_cores,
            "cpu_logical_cores": logical_cores,
            "cpu_mhz": cpu_mhz,
            "cpu_percent": psutil.cpu_percent(interval=None),
            "ram_total_gb": ram_total_gb,
            "ram_available_gb": ram_avail_gb,
            "ram_percent": mem.percent,
            "gpus": gpus,
            "has_dedicated_gpu": has_dedicated_gpu,
            "pc_tier": tier,
            "pc_tier_label": tier_label,
            "pc_tier_description": tier_description,
            "max_recommended_score": max_recommended_score,
            "console_compatibility": console_compatibility,
        }
        return self._cached_specs
