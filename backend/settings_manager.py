"""
Comprehensive Settings & Emulator Configuration Manager for AetherDeck.
Manages GPU selection, Graphics API (Vulkan/D3D11/D3D12/OpenGL), Internal Resolution (1x-4x),
V-Sync, Anti-Aliasing, Audio Latency/Volume, CPU/Performance Profiles, and per-emulator
config file generation (RetroArch, Dolphin 2609, Ryujinx 1.3.3, Caprice32, PUAE).
"""

import json
import os
from typing import Dict, Any, List


DEFAULT_GLOBAL_SETTINGS: Dict[str, Any] = {
    "graphics": {
        "preferred_gpu": "Auto",
        "video_backend": "vulkan",          # vulkan, d3d11, d3d12, gl
        "internal_resolution_scale": 2,     # 1 (720p/Native), 2 (1080p), 3 (1440p), 4 (4K)
        "aspect_ratio": "auto",             # auto, 16:9, 4:3
        "vsync": True,
        "fullscreen_on_boot": False,
        "window_resolution": "1280x720",    # 1280x720, 1600x900, 1920x1080, 2560x1440
        "anti_aliasing": "None",            # None, 2x MSAA, 4x MSAA, FXAA
        "anisotropic_filtering": 4,         # 1, 2, 4, 8, 16
        "texture_filtering": "bilinear",    # bilinear, nearest, fsr
        "show_fps_osd": False,
        "shader_cache": True,
    },
    "performance_audio": {
        "power_profile": "auto",            # auto, eco, balanced, ultra
        "threaded_video": False,
        "cpu_jit_mode": "fast",             # fast, accurate
        "frame_limit": 100,                 # 100 (Normal), 120, 150, 200, 0 (Unlimited)
        "audio_backend": "xaudio2",         # xaudio2, sdl2, wasapi
        "audio_volume": 90,                 # 0..100
        "audio_latency_ms": 64,             # 32, 64, 96, 128
        "audio_mute": False,
    },
    "controllers_advanced": {
        "player1_device": "auto",
        "player2_device": "auto",
        "player3_device": "none",
        "player4_device": "none",
        "left_stick_deadzone": 0.15,
        "right_stick_deadzone": 0.15,
        "stick_sensitivity": 1.0,
        "trigger_threshold": 0.50,
        "vibration_enabled": True,
        "vibration_strength": 85,
        "analog_to_dpad": True,
        "wii_controller_type": "wiimote_nunchuk",    # wiimote_nunchuk, wiimote_horizontal, classic, gc
        "switch_controller_type": "ProController",   # ProController, JoyconPair, Handheld
        "amstrad_input_mode": "joystick",            # joystick, keyboard
        "amiga_input_mode": "joystick",              # joystick, mouse
        "hotkeys": {
            "fullscreen": "f11",
            "exit_game": "escape",
            "save_state": "f2",
            "load_state": "f4",
            "fast_forward": "space",
            "pause_menu": "f1",
            "screenshot": "f8",
        },
    },
    "search_sources": {
        "enable_archive_org": True,
        "enable_wii_osc": True,
        "enable_switch_hb": True,
        "enable_smallgames": False,
        "enable_nxbrew": False,
        "safe_filter": True,
        "results_per_page": 120,
    },
    "legal_compliance": {
        "accepted_external_sources_disclaimer": False,
        "accepted_at": None,
        "only_verified_safe_https": True,
    },
}


class SettingsManager:
    """Persists global settings and writes native configuration files for all emulators."""

    def __init__(self, data_dir: str, emulators_dir: str, hardware_monitor, controller_manager):
        self.data_dir = data_dir
        self.emulators_dir = emulators_dir
        self.hardware_monitor = hardware_monitor
        self.controller_manager = controller_manager
        os.makedirs(self.data_dir, exist_ok=True)
        self.settings_path = os.path.join(self.data_dir, "global_settings.json")
        self.settings = self._load()

    def _load(self) -> Dict[str, Any]:
        merged = json.loads(json.dumps(DEFAULT_GLOBAL_SETTINGS))
        if os.path.exists(self.settings_path):
            try:
                with open(self.settings_path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                for sec_key, sec_val in saved.items():
                    if sec_key in merged and isinstance(sec_val, dict):
                        merged[sec_key].update(sec_val)
                    else:
                        merged[sec_key] = sec_val
            except Exception:
                pass
        self._save(merged)
        return merged

    def _save(self, data: Dict[str, Any] = None) -> None:
        target = data if data is not None else self.settings
        with open(self.settings_path, "w", encoding="utf-8") as f:
            json.dump(target, f, indent=2, ensure_ascii=False)

    def get_settings(self) -> Dict[str, Any]:
        sys_prof = self.hardware_monitor.get_system_profile()
        gpus = ["Auto"] + sys_prof.get("gpus", [])
        return {
            "settings": self.settings,
            "available_gpus": gpus,
            "available_backends": [
                {"id": "vulkan", "name": "Vulkan (Recommandé — Rapide & Moderne)"},
                {"id": "d3d11", "name": "Direct3D 11 (Haute Compatibilité Windows)"},
                {"id": "d3d12", "name": "Direct3D 12 (Bas niveau Windows 10/11)"},
                {"id": "gl", "name": "OpenGL (Compatibilité Anciens GPU)"},
            ],
            "controller_Settings": self.controller_manager.settings,
        }

    def update_settings(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        for section in ("graphics", "performance_audio", "controllers_advanced", "search_sources", "legal_compliance"):
            if section in payload and isinstance(payload[section], dict):
                self.settings[section].update(payload[section])
                if section == "controllers_advanced" and "hotkeys" in payload[section]:
                    self.settings["controllers_advanced"]["hotkeys"].update(payload[section]["hotkeys"])

        if "controller_profile" in payload and isinstance(payload["controller_profile"], dict):
            self.controller_manager.update_settings(payload["controller_profile"])

        self._save()
        sync_res = self.apply_to_all_emulators()
        return {"ok": True, "settings": self.settings, "synced": sync_res}

    def reset_to_defaults(self) -> Dict[str, Any]:
        self.settings = json.loads(json.dumps(DEFAULT_GLOBAL_SETTINGS))
        self._save()
        sync_res = self.apply_to_all_emulators()
        return {"ok": True, "settings": self.settings, "synced": sync_res}

    def apply_to_all_emulators(self) -> Dict[str, Any]:
        """Applies Graphics, GPU, Audio, Performance, and Controller settings to every engine."""
        gfx = self.settings["graphics"]
        perf = self.settings["performance_audio"]
        c_adv = self.settings["controllers_advanced"]
        hk = c_adv.get("hotkeys", {})

        sys_prof = self.hardware_monitor.get_system_profile()
        is_eco = (
            perf.get("power_profile") == "eco"
            or (perf.get("power_profile") == "auto" and sys_prof.get("pc_tier") == "leger")
        )

        # Sync base controller mappings first
        self.controller_manager.advanced = c_adv
        self.controller_manager.settings["active_deadzone"] = c_adv.get("left_stick_deadzone", 0.15)
        self.controller_manager.sync_to_all_emulators(lightweight_mode=is_eco)

        win_w, win_h = 1280, 720
        try:
            parts = gfx.get("window_resolution", "1280x720").lower().split("x")
            win_w, win_h = int(parts[0]), int(parts[1])
        except Exception:
            pass

        # ------------------------------------------------------------------
        # 1. RetroArch (NES, SNES, GBA, MD, N64, PS1, Amstrad CPC, Amiga)
        # ------------------------------------------------------------------
        ra_dir = os.path.join(self.emulators_dir, "retroarch")
        ra_cfg_path = os.path.join(ra_dir, "retroarch.cfg")
        existing_kv: Dict[str, str] = {}
        if os.path.exists(ra_cfg_path):
            try:
                with open(ra_cfg_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if "=" in line and not line.strip().startswith("#"):
                            k, v = line.split("=", 1)
                            existing_kv[k.strip()] = v.strip().strip('"')
            except Exception:
                pass

        ra_video_map = {
            "vulkan": "vulkan",
            "d3d11": "d3d11",
            "d3d12": "d3d12",
            "gl": "glcore",
        }
        ra_driver = ra_video_map.get(gfx.get("video_backend", "vulkan"), "d3d11")
        if is_eco and ra_driver == "vulkan":
            ra_driver = "d3d11"

        existing_kv.update({
            "video_driver": ra_driver,
            "video_vsync": "true" if gfx.get("vsync", True) else "false",
            "video_fullscreen": "true" if gfx.get("fullscreen_on_boot", False) else "false",
            "video_windowed_fullscreen": "true",
            "video_window_custom_size_enable": "true",
            "video_window_save_positions": "false",
            "video_fullscreen_x": str(win_w),
            "video_fullscreen_y": str(win_h),
            "video_smooth": "true" if gfx.get("texture_filtering") == "bilinear" else "false",
            "video_threaded": "true" if (is_eco or perf.get("threaded_video")) else "false",
            "fps_show": "true" if gfx.get("show_fps_osd", False) else "false",
            "audio_enable": "false" if perf.get("audio_mute", False) else "true",
            "audio_latency": str(perf.get("audio_latency_ms", 64)),
            "audio_volume": str(round((perf.get("audio_volume", 90) - 100) * 0.2, 1)),
            "input_analog_deadzone": str(c_adv.get("left_stick_deadzone", 0.15)),
            "input_analog_sensitivity": str(c_adv.get("stick_sensitivity", 1.0)),
            "input_player1_analog_dpad_mode": "1" if c_adv.get("analog_to_dpad", True) else "0",
            "input_player2_analog_dpad_mode": "1" if c_adv.get("analog_to_dpad", True) else "0",
            "enable_device_vibration": "true" if c_adv.get("vibration_enabled", True) else "false",
            # Hotkeys
            "input_toggle_fullscreen": hk.get("fullscreen", "f11"),
            "input_exit_emulator": hk.get("exit_game", "escape"),
            "input_save_state": hk.get("save_state", "f2"),
            "input_load_state": hk.get("load_state", "f4"),
            "input_toggle_fast_forward": hk.get("fast_forward", "space"),
            "input_menu_toggle": hk.get("pause_menu", "f1"),
            "input_screenshot": hk.get("screenshot", "f8"),
        })

        with open(ra_cfg_path, "w", encoding="utf-8") as f:
            for k in sorted(existing_kv.keys()):
                f.write(f'{k} = "{existing_kv[k]}"\n')

        # Update SwanStation (PS1) & Mupen64Plus-Next (N64) internal resolution scale
        res_scale = int(gfx.get("internal_resolution_scale", 2))
        if is_eco:
            res_scale = 1
        swan_dir = os.path.join(ra_dir, "config", "SwanStation")
        os.makedirs(swan_dir, exist_ok=True)
        with open(os.path.join(swan_dir, "SwanStation.opt"), "w", encoding="utf-8") as f:
            f.write(f'duckstation_GPU.ResolutionScale = "{res_scale}"\n')
            f.write('duckstation_Main.ApplyGameSettings = "true"\n')

        # ------------------------------------------------------------------
        # 2. Dolphin 2609 Portable (Wii & GameCube)
        # ------------------------------------------------------------------
        dolphin_dir = os.path.join(self.emulators_dir, "dolphin")
        dolphin_cfg_dir = os.path.join(dolphin_dir, "User", "Config")
        wii_sd_sync_dir = os.path.join(dolphin_dir, "User", "Load", "WiiSDSync")
        wii_sd_raw = os.path.join(dolphin_dir, "User", "Wii", "sd.raw")
        os.makedirs(dolphin_cfg_dir, exist_ok=True)
        os.makedirs(wii_sd_sync_dir, exist_ok=True)
        os.makedirs(os.path.dirname(wii_sd_raw), exist_ok=True)

        dolphin_backend_map = {
            "vulkan": "Vulkan",
            "d3d11": "D3D",
            "d3d12": "D3D12",
            "gl": "OGL",
        }
        d_backend = dolphin_backend_map.get(gfx.get("video_backend", "vulkan"), "D3D")
        speed_limit = float(perf.get("frame_limit", 100)) / 100.0

        dolphin_ini = f"""[General]
WiiSDCardPath = {wii_sd_raw.replace(chr(92), '/')}
WiiSDCardSyncFolder = {wii_sd_sync_dir.replace(chr(92), '/')}

[Interface]
ConfirmStop = False
UsePanicHandlers = False
OnScreenDisplayMessages = True

[Display]
Fullscreen = {"True" if gfx.get("fullscreen_on_boot", False) else "False"}
RenderToMain = False
RenderWindowWidth = {win_w}
RenderWindowHeight = {win_h}

[Core]
GFXBackend = {d_backend}
CPUThread = True
EmulationSpeed = {speed_limit}
WiiSDCard = True
WiiSDCardAllowWrites = True
WiiSDCardEnableFolderSync = True

[DSP]
Volume = {0 if perf.get("audio_mute", False) else int(perf.get("audio_volume", 90))}
"""
        with open(os.path.join(dolphin_cfg_dir, "Dolphin.ini"), "w", encoding="utf-8") as f:
            f.write(dolphin_ini)

        aspect_map = {"auto": 0, "16:9": 1, "4:3": 2}
        gfx_ini = f"""[Hardware]
VSync = {"True" if gfx.get("vsync", True) else "False"}
Adapter = 0

[Settings]
AspectRatio = {aspect_map.get(gfx.get("aspect_ratio", "auto"), 0)}
InternalResolution = {res_scale}
ShowFPS = {"True" if gfx.get("show_fps_osd", False) else "False"}
ShaderCompilationMode = {"2" if gfx.get("shader_cache", True) else "0"}
WaitForShadersBeforeStarting = False
"""
        with open(os.path.join(dolphin_cfg_dir, "GFX.ini"), "w", encoding="utf-8") as f:
            f.write(gfx_ini)

        # ------------------------------------------------------------------
        # 3. Ryujinx 1.3.3 Portable (Nintendo Switch) — Full v70 Schema
        # ------------------------------------------------------------------
        switch_dir = os.path.join(self.emulators_dir, "switch")
        switch_portable = os.path.join(switch_dir, "portable")
        switch_sys = os.path.join(switch_portable, "system")
        switch_sdcard = os.path.join(switch_portable, "sdcard")
        os.makedirs(switch_sys, exist_ok=True)
        os.makedirs(switch_sdcard, exist_ok=True)

        # Ensure prod.keys exists so Ryujinx never blocks on startup popup for homebrew .nro
        prod_keys_path = os.path.join(switch_sys, "prod.keys")
        if not os.path.exists(prod_keys_path):
            with open(prod_keys_path, "w", encoding="utf-8") as f:
                f.write("header_key = 0000000000000000000000000000000000000000000000000000000000000000\n")

        switch_cfg_path = os.path.join(switch_portable, "Config.json")
        sw_cfg: Dict[str, Any] = {}
        if os.path.exists(switch_cfg_path):
            try:
                with open(switch_cfg_path, "r", encoding="utf-8") as f:
                    sw_cfg = json.load(f)
            except Exception:
                sw_cfg = {}

        if sw_cfg.get("version", 0) < 70:
            sw_cfg = self._get_valid_ryujinx_v70_template()

        sw_backend_map = {
            "vulkan": "Vulkan",
            "d3d11": "Vulkan",
            "d3d12": "Vulkan",
            "gl": "OpenGl",
        }
        sw_aa_map = {
            "None": "None",
            "2x MSAA": "Fxaa",
            "4x MSAA": "SmaaMedium",
            "FXAA": "Fxaa",
        }
        sw_filter_map = {
            "bilinear": "Bilinear",
            "nearest": "Nearest",
            "fsr": "Fsr",
        }

        prof = self.controller_manager.get_active_profile()
        kb = prof.get("keyboard_bindings", {})
        roms_switch = os.path.abspath(os.path.join(self.emulators_dir, "..", "roms", "switch"))
        os.makedirs(roms_switch, exist_ok=True)
        current_game_dirs = sw_cfg.get("game_dirs", [])
        if roms_switch not in current_game_dirs:
            current_game_dirs.append(roms_switch)

        sw_cfg.update({
            "version": 70,
            "game_dirs": current_game_dirs,
            "graphics_backend": sw_backend_map.get(gfx.get("video_backend", "vulkan"), "Vulkan"),
            "res_scale": res_scale,
            "res_scale_custom": 1,
            "max_anisotropy": float(gfx.get("anisotropic_filtering", 4)),
            "aspect_ratio": "Fixed4x3" if gfx.get("aspect_ratio") == "4:3" else "Fixed16x9",
            "anti_aliasing": sw_aa_map.get(gfx.get("anti_aliasing", "None"), "None"),
            "scaling_filter": sw_filter_map.get(gfx.get("texture_filtering", "bilinear"), "Bilinear"),
            "enable_vsync": bool(gfx.get("vsync", True)),
            "enable_shader_cache": bool(gfx.get("shader_cache", True)),
            "enable_ptc": True,
            "start_fullscreen": bool(gfx.get("fullscreen_on_boot", False)),
            "check_updates_on_start": False,
            "show_confirm_exit": False,
            "audio_volume": 0.0 if perf.get("audio_mute", False) else round(perf.get("audio_volume", 90) / 100.0, 2),
            "preferred_gpu": gfx.get("preferred_gpu", "") if gfx.get("preferred_gpu") != "Auto" else "",
            "window_startup": {
                "window_size_width": win_w,
                "window_size_height": win_h,
                "window_position_x": 80,
                "window_position_y": 60,
                "window_maximized": False,
            },
            "input_config": self.controller_manager.ryujinx_input_configs(),
        })

        with open(switch_cfg_path, "w", encoding="utf-8") as f:
            json.dump(sw_cfg, f, indent=2)

        return {
            "ok": True,
            "video_backend": gfx.get("video_backend"),
            "resolution_scale": res_scale,
            "preferred_gpu": gfx.get("preferred_gpu"),
            "targets": ["RetroArch (NES/SNES/GBA/N64/MD/PS1/NDS/3DS)", "Dolphin (Wii/GC)", "Ryujinx (Switch)", "Caprice32 (Amstrad)", "PUAE (Amiga)"],
        }

    def _get_valid_ryujinx_v70_template(self) -> Dict[str, Any]:
        return {
            "version": 70,
            "enable_file_log": True,
            "backend_threading": "Auto",
            "res_scale": 1,
            "res_scale_custom": 1,
            "max_anisotropy": -1,
            "aspect_ratio": "Fixed16x9",
            "anti_aliasing": "None",
            "scaling_filter": "Bilinear",
            "scaling_filter_level": 80,
            "graphics_shaders_dump_path": "",
            "logging_enable_debug": False,
            "logging_enable_stub": True,
            "logging_enable_info": True,
            "logging_enable_warn": True,
            "logging_enable_error": True,
            "logging_enable_trace": False,
            "logging_enable_guest": True,
            "logging_enable_fs_access_log": False,
            "logging_enable_avalonia": False,
            "logging_filtered_classes": [],
            "logging_graphics_debug_level": "None",
            "system_language": "French",
            "system_region": "Europe",
            "system_time_zone": "UTC",
            "system_time_offset": 0,
            "match_system_time": False,
            "use_input_global_config": False,
            "docked_mode": True,
            "enable_discord_integration": False,
            "check_updates_on_start": False,
            "update_checker_type": "Off",
            "focus_lost_action_type": "DoNothing",
            "show_confirm_exit": False,
            "ignore_applet": False,
            "skip_user_profiles": True,
            "remember_window_state": True,
            "show_title_bar": True,
            "enable_hardware_acceleration": True,
            "hide_cursor": 1,
            "enable_vsync": True,
            "vsync_mode": 0,
            "enable_custom_vsync_interval": False,
            "custom_vsync_interval": 120,
            "enable_shader_cache": True,
            "enable_texture_recompression": False,
            "enable_macro_hle": True,
            "enable_color_space_passthrough": False,
            "enable_ptc": True,
            "enable_low_power_ptc": False,
            "tick_scalar": 0,
            "enable_internet_access": False,
            "enable_fs_integrity_checks": True,
            "fs_global_access_log_mode": 0,
            "audio_backend": "SDL2",
            "audio_volume": 1,
            "memory_manager_mode": "HostMappedUnsafe",
            "dram_size": 0,
            "ignore_missing_services": False,
            "gui_columns": {
                "fav_column": True,
                "icon_column": True,
                "app_column": True,
                "dev_column": True,
                "version_column": True,
                "ldn_info_column": False,
                "time_played_column": True,
                "last_played_column": True,
                "file_ext_column": True,
                "file_size_column": True,
                "path_column": True,
            },
            "column_sort": {"sort_column_id": 0, "sort_ascending": False},
            "game_dirs": [],
            "autoload_dirs": [],
            "shown_file_types": {
                "nsp": True,
                "pfs0": True,
                "xci": True,
                "nca": True,
                "nro": True,
                "nso": True,
            },
            "window_startup": {
                "window_size_width": 1280,
                "window_size_height": 760,
                "window_position_x": 0,
                "window_position_y": 0,
                "window_maximized": False,
            },
            "language_code": "fr_FR",
            "base_style": "Dark",
            "game_list_view_mode": 0,
            "show_names": True,
            "grid_size": 2,
            "application_sort": 0,
            "is_ascending_order": True,
            "start_fullscreen": False,
            "start_no_ui": False,
            "show_console": False,
            "enable_keyboard": False,
            "enable_mouse": False,
            "disable_input_when_out_of_focus": False,
            "hotkeys": {
                "toggle_vsync_mode": "F1",
                "screenshot": "F8",
                "show_ui": "F4",
                "pause": "F5",
                "toggle_mute": "F2",
                "res_scale_up": "Unbound",
                "res_scale_down": "Unbound",
                "volume_up": "Unbound",
                "volume_down": "Unbound",
                "custom_vsync_interval_increment": "Unbound",
                "custom_vsync_interval_decrement": "Unbound",
                "turbo_mode": "Unbound",
                "turbo_mode_while_held": False,
            },
            "input_config": [],
            "rainbow_speed": 1,
            "graphics_backend": "Vulkan",
            "preferred_gpu": "",
            "multiplayer_mode": 0,
            "multiplayer_lan_interface_id": "0",
            "multiplayer_disable_p2p": False,
            "multiplayer_ldn_passphrase": "",
            "ldn_server": "",
            "use_hypervisor": True,
            "enable_gdb_stub": False,
            "gdb_stub_port": 55555,
            "debugger_suspend_on_start": False,
            "show_dirty_hacks": False,
            "dirty_hacks": [],
        }
