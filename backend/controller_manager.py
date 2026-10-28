"""
Centralized Controller Hub & Auto-Configuration Engine for AetherDeck.

Detects XInput (Xbox), DirectInput / WinMM (PlayStation, Switch Pro, USB retro joysticks) and the
keyboard, keeps one set of user bindings (per-action keyboard key + gamepad button) and translates
them into the native formats of every emulator:
  - RetroArch (all Libretro cores: Amstrad CPC, Amiga, NES, SNES, GBA, Mega Drive, N64, PS1)
  - Dolphin standalone (GameCube pad + Wii Remote / Nunchuk / Classic Controller)
  - Ryujinx (Nintendo Switch) -> input_config entries (written by SettingsManager in Config.json v70)
"""

import ctypes
import copy
import json
import os
import threading
import uuid
from ctypes import wintypes
from typing import Any, Dict, List, Optional


# --- Windows XInput Structures ---
class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_ = [
        ("wButtons", ctypes.c_ushort),
        ("bLeftTrigger", ctypes.c_ubyte),
        ("bRightTrigger", ctypes.c_ubyte),
        ("sThumbLX", ctypes.c_short),
        ("sThumbLY", ctypes.c_short),
        ("sThumbRX", ctypes.c_short),
        ("sThumbRY", ctypes.c_short),
    ]


class XINPUT_STATE(ctypes.Structure):
    _fields_ = [
        ("dwPacketNumber", ctypes.c_ulong),
        ("Gamepad", XINPUT_GAMEPAD),
    ]


class XINPUT_VIBRATION(ctypes.Structure):
    _fields_ = [
        ("wLeftMotorSpeed", ctypes.c_ushort),
        ("wRightMotorSpeed", ctypes.c_ushort),
    ]


# --- Windows WinMM (DirectInput / Joystick) Structures ---
class JOYINFOEX(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("dwXpos", wintypes.DWORD),
        ("dwYpos", wintypes.DWORD),
        ("dwZpos", wintypes.DWORD),
        ("dwRpos", wintypes.DWORD),
        ("dwUpos", wintypes.DWORD),
        ("dwVpos", wintypes.DWORD),
        ("dwButtons", wintypes.DWORD),
        ("dwButtonNumber", wintypes.DWORD),
        ("dwPOV", wintypes.DWORD),
        ("dwReserved1", wintypes.DWORD),
        ("dwReserved2", wintypes.DWORD),
    ]


class JOYCAPSW(ctypes.Structure):
    _fields_ = [
        ("wMid", wintypes.WORD),
        ("wPid", wintypes.WORD),
        ("szPname", wintypes.WCHAR * 32),
        ("wXmin", wintypes.UINT),
        ("wXmax", wintypes.UINT),
        ("wYmin", wintypes.UINT),
        ("wYmax", wintypes.UINT),
        ("wZmin", wintypes.UINT),
        ("wZmax", wintypes.UINT),
        ("wNumButtons", wintypes.UINT),
        ("wPeriodMin", wintypes.UINT),
        ("wPeriodMax", wintypes.UINT),
        ("wRmin", wintypes.UINT),
        ("wRmax", wintypes.UINT),
        ("wUmin", wintypes.UINT),
        ("wUmax", wintypes.UINT),
        ("wVmin", wintypes.UINT),
        ("wVmax", wintypes.UINT),
        ("wCaps", wintypes.UINT),
        ("wMaxAxes", wintypes.UINT),
        ("wNumAxes", wintypes.UINT),
        ("wMaxButtons", wintypes.UINT),
        ("szRegKey", wintypes.WCHAR * 32),
        ("szOEMVxD", wintypes.WCHAR * 260),
    ]


class _SDLGUID(ctypes.Structure):
    _fields_ = [("data", ctypes.c_ubyte * 16)]


XINPUT_BUTTON_MAP = {
    0x0001: "dpad_up",
    0x0002: "dpad_down",
    0x0004: "dpad_left",
    0x0008: "dpad_right",
    0x0010: "start",
    0x0020: "select",
    0x0040: "l3",
    0x0080: "r3",
    0x0100: "l1",
    0x0200: "r1",
    0x1000: "a",
    0x2000: "b",
    0x4000: "x",
    0x8000: "y",
}

KNOWN_VENDORS = {
    0x045E: ("Microsoft Xbox Controller", "xbox"),
    0x054C: ("Sony PlayStation DualShock / DualSense", "playstation"),
    0x057E: ("Nintendo Switch Pro / Joy-Con", "switch"),
    0x2DC8: ("8BitDo Retro Controller", "retro"),
    0x046D: ("Logitech Gamepad", "generic"),
    0x0738: ("Mad Catz Arcade Stick", "joystick"),
    0x0F0D: ("Hori Fighting Stick / Pad", "switch"),
    0x1532: ("Razer Controller", "xbox"),
}

ALL_CONSOLES = ["amstrad_cpc", "amiga", "nes", "snes", "gba", "megadrive", "n64", "ps1", "wii", "switch"]

ACTIONS = ["up", "down", "left", "right", "a", "b", "x", "y", "l1", "r1", "l2", "r2", "l3", "r3", "start", "select"]

# Default keyboard layout (RetroArch key names)
_DEFAULT_KB = {
    "up": "up", "down": "down", "left": "left", "right": "right",
    "a": "x", "b": "z", "x": "s", "y": "a",
    "l1": "q", "r1": "w", "l2": "e", "r2": "r", "l3": "c", "r3": "v",
    "start": "enter", "select": "rshift",
}

# Gamepad bindings: RetroPad action -> XInput/RetroArch input ("0".."9" buttons, "h0up" hat, "+4"/"+5" trigger axes)
# "Label" layout: the button printed "A" on an Xbox pad triggers the console "A" button.
_GP_LABEL = {
    "up": "h0up", "down": "h0down", "left": "h0left", "right": "h0right",
    "a": "0", "b": "1", "x": "2", "y": "3",
    "l1": "4", "r1": "5", "l2": "+4", "r2": "+5", "l3": "8", "r3": "9",
    "start": "7", "select": "6",
}
# "Position" layout (RetroArch / Nintendo standard): bottom button = B, right button = A.
_GP_POSITION = dict(_GP_LABEL, a="1", b="0", x="3", y="2")

DEFAULT_PROFILES: Dict[str, Dict[str, Any]] = {
    "xbox_standard": {
        "id": "xbox_standard",
        "name": "Standard Xbox / PC",
        "description": "Le bouton marqué A sur la manette correspond au bouton A de la console.",
        "swap_ab_xy": False,
        "deadzone": 0.15,
        "vibration_enabled": True,
        "keyboard_bindings": dict(_DEFAULT_KB),
        "gamepad_bindings": dict(_GP_LABEL),
    },
    "nintendo_layout": {
        "id": "nintendo_layout",
        "name": "Disposition Nintendo (position physique)",
        "description": "Respecte la position des boutons Nintendo : bouton du bas = B, bouton de droite = A.",
        "swap_ab_xy": True,
        "deadzone": 0.15,
        "vibration_enabled": True,
        "keyboard_bindings": dict(_DEFAULT_KB),
        "gamepad_bindings": dict(_GP_POSITION),
    },
    "playstation_layout": {
        "id": "playstation_layout",
        "name": "PlayStation (DualShock 4 / DualSense)",
        "description": "Croix = action principale, Rond = retour, Carré / Triangle = actions secondaires.",
        "swap_ab_xy": False,
        "deadzone": 0.12,
        "vibration_enabled": True,
        "keyboard_bindings": dict(_DEFAULT_KB),
        "gamepad_bindings": dict(_GP_LABEL),
    },
    "retro_amstrad_amiga": {
        "id": "retro_amstrad_amiga",
        "name": "Joystick micro-ordinateur (Amstrad CPC / Amiga)",
        "description": "Optimisé pour les jeux à 1 ou 2 boutons de tir. Espace = tir au clavier.",
        "swap_ab_xy": False,
        "deadzone": 0.20,
        "vibration_enabled": False,
        "keyboard_bindings": dict(_DEFAULT_KB, a="space", b="x", x="z", y="c"),
        "gamepad_bindings": dict(_GP_LABEL),
    },
}

# ---------------------------------------------------------------------------------------------
# Key name translation tables (RetroArch name -> Dolphin DInput name / Ryujinx Key enum name)
# ---------------------------------------------------------------------------------------------
_RA_TO_DOLPHIN_SPECIAL = {
    "up": "UP", "down": "DOWN", "left": "LEFT", "right": "RIGHT",
    "enter": "RETURN", "space": "SPACE", "rshift": "RSHIFT", "lshift": "LSHIFT", "shift": "LSHIFT",
    "ctrl": "LCONTROL", "rctrl": "RCONTROL", "alt": "LMENU", "ralt": "RMENU", "tab": "TAB",
    "backspace": "BACK", "escape": "ESCAPE", "minus": "MINUS", "equals": "EQUALS",
}
_RA_TO_RYU_SPECIAL = {
    "up": "Up", "down": "Down", "left": "Left", "right": "Right",
    "enter": "Enter", "space": "Space", "rshift": "ShiftRight", "lshift": "ShiftLeft", "shift": "ShiftLeft",
    "ctrl": "ControlLeft", "rctrl": "ControlRight", "alt": "AltLeft", "ralt": "AltRight", "tab": "Tab",
    "backspace": "BackSpace", "escape": "Escape", "minus": "Minus", "equals": "Plus",
}

# XInput / RetroArch input -> Dolphin XInput control name
_GP_TO_DOLPHIN = {
    "0": "Button A", "1": "Button B", "2": "Button X", "3": "Button Y",
    "4": "Shoulder L", "5": "Shoulder R", "6": "Back", "7": "Start", "8": "Thumb L", "9": "Thumb R",
    "h0up": "Pad N", "h0down": "Pad S", "h0left": "Pad W", "h0right": "Pad E",
    "+4": "Trigger L", "+5": "Trigger R",
}
# XInput / RetroArch input -> Ryujinx GamepadButtonInputId
_GP_TO_RYU = {
    "0": "A", "1": "B", "2": "X", "3": "Y",
    "4": "LeftShoulder", "5": "RightShoulder", "6": "Minus", "7": "Plus", "8": "LeftStick", "9": "RightStick",
    "h0up": "DpadUp", "h0down": "DpadDown", "h0left": "DpadLeft", "h0right": "DpadRight",
    "+4": "LeftTrigger", "+5": "RightTrigger",
}


def ra_key_to_dolphin(key: str) -> str:
    k = (key or "").strip().lower()
    if k in _RA_TO_DOLPHIN_SPECIAL:
        return _RA_TO_DOLPHIN_SPECIAL[k]
    if len(k) == 1 and k.isalpha():
        return k.upper()
    if k.startswith("num") and k[3:].isdigit():
        return k[3:]
    if k.startswith("keypad") and k[6:].isdigit():
        return "NUMPAD" + k[6:]
    if k.startswith("f") and k[1:].isdigit():
        return k.upper()
    return k.upper() or "SPACE"


def ra_key_to_ryujinx(key: str) -> str:
    k = (key or "").strip().lower()
    if k in _RA_TO_RYU_SPECIAL:
        return _RA_TO_RYU_SPECIAL[k]
    if len(k) == 1 and k.isalpha():
        return k.upper()
    if k.startswith("num") and k[3:].isdigit():
        return "Number" + k[3:]
    if k.startswith("keypad") and k[6:].isdigit():
        return "Keypad" + k[6:]
    if k.startswith("f") and k[1:].isdigit():
        return k.upper()
    return "Unbound"


class ControllerManager:
    """Centralized controller detection, state polling, and multi-emulator config generator."""

    def __init__(self, data_dir: str, emulators_dir: str):
        self.data_dir = data_dir
        self.emulators_dir = emulators_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.config_path = os.path.join(self.data_dir, "controllers_config.json")
        self._xinput = self._load_xinput()
        self._winmm = self._load_winmm()
        self._sdl_lock = threading.Lock()
        # Advanced options (deadzones, Wii / Switch modes...) pushed by SettingsManager
        self.advanced: Dict[str, Any] = {}
        self.settings = self._load_settings()

    # ------------------------------------------------------------------ persistence
    def _load_xinput(self):
        for dll_name in ("xinput1_4.dll", "xinput1_3.dll", "xinput9_1_0.dll"):
            try:
                return ctypes.windll.LoadLibrary(dll_name)
            except Exception:
                continue
        return None

    def _load_winmm(self):
        try:
            return ctypes.windll.winmm
        except Exception:
            return None

    def _default_settings(self) -> Dict[str, Any]:
        return {
            "schema": 2,
            "active_profile": "xbox_standard",
            "auto_configure_on_launch": True,
            "profiles": copy.deepcopy(DEFAULT_PROFILES),
            "custom_controllers": [],
        }

    def _load_settings(self) -> Dict[str, Any]:
        data = None
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = None
        if not isinstance(data, dict) or data.get("schema") != 2 or "profiles" not in data:
            # Migrate older files: keep the active profile id and any custom keyboard keys
            fresh = self._default_settings()
            if isinstance(data, dict):
                if data.get("active_profile") in fresh["profiles"]:
                    fresh["active_profile"] = data["active_profile"]
                for pid, prof in (data.get("profiles") or {}).items():
                    if pid in fresh["profiles"] and isinstance(prof, dict):
                        fresh["profiles"][pid]["keyboard_bindings"].update(prof.get("keyboard_bindings") or {})
            data = fresh
        # Ensure every profile has every action
        for pid, prof in data["profiles"].items():
            base = DEFAULT_PROFILES.get(pid, DEFAULT_PROFILES["xbox_standard"])
            for sec in ("keyboard_bindings", "gamepad_bindings"):
                merged = dict(base[sec])
                merged.update(prof.get(sec) or {})
                prof[sec] = merged
        self._save_settings(data)
        return data

    def _save_settings(self, data: Optional[Dict[str, Any]] = None) -> None:
        target = data if data is not None else self.settings
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(target, f, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------------ detection
    def detect_controllers(self) -> List[Dict[str, Any]]:
        """Polls XInput, WinMM DirectInput and adds the always-available keyboard."""
        connected: List[Dict[str, Any]] = []
        xinput_count = 0

        if self._xinput:
            for port in range(4):
                state = XINPUT_STATE()
                try:
                    res = self._xinput.XInputGetState(port, ctypes.byref(state))
                except Exception:
                    res = 1
                if res != 0:
                    continue
                xinput_count += 1
                gp = state.Gamepad
                pressed = [name for mask, name in XINPUT_BUTTON_MAP.items() if gp.wButtons & mask]
                if gp.bLeftTrigger > 60:
                    pressed.append("l2")
                if gp.bRightTrigger > 60:
                    pressed.append("r2")
                connected.append({
                    "id": f"xinput_{port}",
                    "port": port,
                    "name": f"Manette XInput {port + 1} (Xbox / compatible)",
                    "type": "xbox",
                    "api": "XInput",
                    "status": "connected",
                    "buttons_pressed": pressed,
                    "axes": {
                        "lx": round(gp.sThumbLX / 32767.0, 2), "ly": round(gp.sThumbLY / 32767.0, 2),
                        "rx": round(gp.sThumbRX / 32767.0, 2), "ry": round(gp.sThumbRY / 32767.0, 2),
                        "lt": round(gp.bLeftTrigger / 255.0, 2), "rt": round(gp.bRightTrigger / 255.0, 2),
                    },
                    "supports_vibration": True,
                    "compatible_consoles": list(ALL_CONSOLES),
                })

        if self._winmm:
            try:
                num_devs = self._winmm.joyGetNumDevs()
                for joy_id in range(min(num_devs, 16)):
                    info = JOYINFOEX()
                    info.dwSize = ctypes.sizeof(JOYINFOEX)
                    info.dwFlags = 0x00FF  # JOY_RETURNALL
                    if self._winmm.joyGetPosEx(joy_id, ctypes.byref(info)) != 0:
                        continue
                    caps = JOYCAPSW()
                    self._winmm.joyGetDevCapsW(joy_id, ctypes.byref(caps), ctypes.sizeof(JOYCAPSW))
                    pname = (caps.szPname or "").strip()
                    # XInput pads also appear in WinMM: skip them (already listed above)
                    if caps.wMid == 0x045E or "xbox" in pname.lower() or "xinput" in pname.lower():
                        continue
                    vendor_name, dev_type = KNOWN_VENDORS.get(caps.wMid, (pname or f"Manette USB {joy_id + 1}", "generic"))
                    dev_name = pname or vendor_name
                    low = dev_name.lower()
                    if "wireless controller" in low or "dualsense" in low or caps.wMid == 0x054C:
                        dev_type, dev_name = "playstation", f"Sony PlayStation ({dev_name})"
                    elif "pro controller" in low or "joy-con" in low or caps.wMid == 0x057E:
                        dev_type, dev_name = "switch", f"Nintendo Switch ({dev_name})"
                    pressed = [f"btn_{b + 1}" for b in range(min(caps.wNumButtons, 32)) if info.dwButtons & (1 << b)]
                    pov_map = {0: "dpad_up", 9000: "dpad_right", 18000: "dpad_down", 27000: "dpad_left"}
                    if info.dwPOV in pov_map:
                        pressed.append(pov_map[info.dwPOV])
                    connected.append({
                        "id": f"dinput_{joy_id}",
                        "port": joy_id,
                        "name": dev_name,
                        "type": dev_type,
                        "api": "DirectInput / HID",
                        "vendor_id": f"0x{caps.wMid:04X}",
                        "product_id": f"0x{caps.wPid:04X}",
                        "num_buttons": caps.wNumButtons,
                        "status": "connected",
                        "buttons_pressed": pressed,
                        "axes": {
                            "lx": round((info.dwXpos - 32767) / 32767.0, 2),
                            "ly": round(-(info.dwYpos - 32767) / 32767.0, 2),
                            "rx": 0.0, "ry": 0.0, "lt": 0.0, "rt": 0.0,
                        },
                        "supports_vibration": False,
                        "compatible_consoles": list(ALL_CONSOLES),
                    })
            except Exception:
                pass

        for custom in self.settings.get("custom_controllers", []):
            if not any(c["id"] == custom.get("id") for c in connected):
                connected.append(custom)

        connected.append({
            "id": "keyboard_mouse_0",
            "port": 99,
            "name": "Clavier + souris",
            "type": "keyboard",
            "api": "Windows",
            "status": "ready",
            "buttons_pressed": [],
            "axes": {"lx": 0.0, "ly": 0.0, "rx": 0.0, "ry": 0.0, "lt": 0.0, "rt": 0.0},
            "supports_vibration": False,
            "bindings_summary": self.get_active_profile().get("keyboard_bindings", {}),
            "compatible_consoles": list(ALL_CONSOLES),
        })
        return connected

    def has_xinput_pad(self) -> bool:
        return any(c["api"] == "XInput" for c in self.detect_controllers())

    def has_dinput_pad(self) -> bool:
        return any(c["api"].startswith("DirectInput") for c in self.detect_controllers())

    def sdl_gamepads(self) -> List[Dict[str, str]]:
        """
        Enumerates gamepads through Ryujinx's own SDL2.dll with the same hints Ryujinx uses, and builds
        the gamepad id format of Ryujinx (`<index>-<guid with CRC zeroed>`).
        """
        dll = os.path.join(self.emulators_dir, "switch", "SDL2.dll")
        if not os.path.exists(dll):
            return []
        result: List[Dict[str, str]] = []
        with self._sdl_lock:
            try:
                os.add_dll_directory(os.path.dirname(dll))
            except Exception:
                pass
            try:
                sdl = ctypes.CDLL(dll)
                sdl.SDL_SetHint.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
                sdl.SDL_JoystickGetDeviceGUID.restype = _SDLGUID
                sdl.SDL_JoystickGetDeviceGUID.argtypes = [ctypes.c_int]
                sdl.SDL_JoystickNameForIndex.restype = ctypes.c_char_p
                sdl.SDL_JoystickNameForIndex.argtypes = [ctypes.c_int]
                for k, v in (
                    (b"SDL_JOYSTICK_HIDAPI_PS4_RUMBLE", b"1"),
                    (b"SDL_JOYSTICK_HIDAPI_PS5_RUMBLE", b"1"),
                    (b"SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", b"1"),
                    (b"SDL_JOYSTICK_HIDAPI_SWITCH_HOME_LED", b"0"),
                    (b"SDL_JOYSTICK_HIDAPI_JOY_CONS", b"1"),
                    (b"SDL_JOYSTICK_HIDAPI_COMBINE_JOY_CONS", b"0"),
                ):
                    sdl.SDL_SetHint(k, v)
                if sdl.SDL_InitSubSystem(0x200 | 0x2000) != 0:
                    return []
                seen: Dict[str, int] = {}
                for i in range(sdl.SDL_NumJoysticks()):
                    raw = bytes(sdl.SDL_JoystickGetDeviceGUID(i).data)
                    if raw == bytes(16):
                        continue
                    guid = str(uuid.UUID(bytes_le=raw))
                    guid = "0000" + guid[4:]
                    idx = seen.get(guid, 0)
                    seen[guid] = idx + 1
                    name = (sdl.SDL_JoystickNameForIndex(i) or b"Gamepad").decode("utf-8", "ignore")
                    result.append({"id": f"{idx}-{guid}", "name": name})
                sdl.SDL_QuitSubSystem(0x200 | 0x2000)
            except Exception:
                return result
        return result

    def test_vibration(self, port: int = 0, duration_ms: int = 350) -> Dict[str, Any]:
        """Triggers rumble motor on an XInput controller to confirm connectivity."""
        if not self._xinput:
            return {"ok": False, "message": "Pilote XInput non disponible."}
        try:
            vib = XINPUT_VIBRATION(45000, 45000)
            if self._xinput.XInputSetState(port, ctypes.byref(vib)) != 0:
                return {"ok": False, "message": f"Aucune manette XInput sur le port {port + 1}."}
            import time

            def _stop():
                time.sleep(duration_ms / 1000.0)
                self._xinput.XInputSetState(port, ctypes.byref(XINPUT_VIBRATION(0, 0)))

            threading.Thread(target=_stop, daemon=True).start()
            return {"ok": True, "message": f"Vibration envoyée à la manette {port + 1}."}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    # ------------------------------------------------------------------ profile management
    def get_active_profile(self) -> Dict[str, Any]:
        prof_id = self.settings.get("active_profile", "xbox_standard")
        profiles = self.settings.get("profiles", DEFAULT_PROFILES)
        return profiles.get(prof_id) or profiles.get("xbox_standard") or DEFAULT_PROFILES["xbox_standard"]

    def update_settings(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Updates the active profile / bindings. Native config files are rewritten by the caller (SettingsManager)."""
        profiles = self.settings["profiles"]
        if payload.get("active_profile") in profiles:
            self.settings["active_profile"] = payload["active_profile"]
        prof = profiles[self.settings["active_profile"]]

        if isinstance(payload.get("keyboard_bindings"), dict):
            for action, key in payload["keyboard_bindings"].items():
                if action in ACTIONS and isinstance(key, str) and key.strip():
                    prof["keyboard_bindings"][action] = key.strip().lower()
        if isinstance(payload.get("gamepad_bindings"), dict):
            for action, btn in payload["gamepad_bindings"].items():
                if action in ACTIONS and str(btn).strip():
                    prof["gamepad_bindings"][action] = str(btn).strip()
        if "swap_ab_xy" in payload:
            swap = bool(payload["swap_ab_xy"])
            prof["swap_ab_xy"] = swap
            src = _GP_POSITION if swap else _GP_LABEL
            for k in ("a", "b", "x", "y"):
                prof["gamepad_bindings"][k] = src[k]
        if "deadzone" in payload:
            try:
                prof["deadzone"] = max(0.0, min(0.6, float(payload["deadzone"])))
            except (TypeError, ValueError):
                pass
        if "vibration_enabled" in payload:
            prof["vibration_enabled"] = bool(payload["vibration_enabled"])
        if "auto_configure_on_launch" in payload:
            self.settings["auto_configure_on_launch"] = bool(payload["auto_configure_on_launch"])
        self._save_settings()
        return {"ok": True, "settings": self.settings, "active_profile": prof}

    def reset_active_profile(self) -> Dict[str, Any]:
        pid = self.settings.get("active_profile", "xbox_standard")
        self.settings["profiles"][pid] = copy.deepcopy(DEFAULT_PROFILES.get(pid, DEFAULT_PROFILES["xbox_standard"]))
        self._save_settings()
        return {"ok": True, "settings": self.settings, "active_profile": self.settings["profiles"][pid],
                "message": "Profil réinitialisé."}

    # ------------------------------------------------------------------ native config writers
    def sync_to_all_emulators(self, lightweight_mode: bool = False) -> Dict[str, Any]:
        """Writes controller mappings for RetroArch, Caprice32, PUAE and Dolphin."""
        adv = self.advanced or {}
        prof = self.get_active_profile()
        kb = prof["keyboard_bindings"]
        gp = prof["gamepad_bindings"]
        targets = []

        targets.append(self._write_retroarch(prof, kb, gp, adv))
        targets.append(self._write_libretro_core_options(adv))
        targets.append(self._write_dolphin(kb, gp, adv))
        return {"ok": True, "profile_name": prof["name"], "targets": targets}

    def _write_retroarch(self, prof, kb, gp, adv) -> str:
        ra_dir = os.path.join(self.emulators_dir, "retroarch")
        os.makedirs(ra_dir, exist_ok=True)
        cfg_path = os.path.join(ra_dir, "retroarch.cfg")
        kv: Dict[str, str] = {}
        if os.path.exists(cfg_path):
            try:
                with open(cfg_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if "=" in line and not line.strip().startswith("#"):
                            k, v = line.split("=", 1)
                            kv[k.strip()] = v.strip().strip('"')
            except Exception:
                pass

        def p(d):
            return os.path.join(ra_dir, d).replace("\\", "/")

        for d in ("cores", "system", "saves", "states", "autoconfig", "screenshots", "config"):
            os.makedirs(os.path.join(ra_dir, d), exist_ok=True)

        kv.update({
            "libretro_directory": p("cores"),
            "libretro_info_path": p("info"),
            "system_directory": p("system"),
            "savefile_directory": p("saves"),
            "savestate_directory": p("states"),
            "screenshot_directory": p("screenshots"),
            "joypad_autoconfig_dir": p("autoconfig"),
            "rgui_config_directory": p("config"),
            "input_joypad_driver": "xinput",
            "input_driver": "dinput",
            "input_autodetect_enable": "true",
            "input_menu_toggle_gamepad_combo": "2",   # L3 + R3 -> menu
            "input_quit_gamepad_combo": "3",           # L1 + R1 + Start + Select -> quit
            "quit_press_twice": "false",
            "pause_nonactive": "false",
            "config_save_on_exit": "false",
            "menu_show_core_updater": "false",
            "network_cmd_enable": "false",
            "input_analog_deadzone": str(prof.get("deadzone", adv.get("left_stick_deadzone", 0.15))),
            "input_rumble_gain": str(int(adv.get("vibration_strength", 85))) if prof.get("vibration_enabled", True) else "0",
        })

        ra_names = {
            "up": "up", "down": "down", "left": "left", "right": "right",
            "a": "a", "b": "b", "x": "x", "y": "y",
            "l1": "l", "r1": "r", "l2": "l2", "r2": "r2", "l3": "l3", "r3": "r3",
            "start": "start", "select": "select",
        }
        # If only DirectInput pads are connected, leave button binds empty so RetroArch's autoconfig
        # profiles (PlayStation, Switch Pro, 8BitDo...) map them correctly. Otherwise use XInput indices.
        only_dinput = self.has_dinput_pad() and not self.has_xinput_pad()
        for action, ra in ra_names.items():
            kv[f"input_player1_{ra}"] = kb.get(action, _DEFAULT_KB[action])
            val = gp.get(action, _GP_LABEL[action])
            btn_key, axis_key = f"input_player1_{ra}_btn", f"input_player1_{ra}_axis"
            if only_dinput:
                kv[btn_key], kv[axis_key] = "nul", "nul"
            elif val.startswith(("+", "-")):
                kv[btn_key], kv[axis_key] = "nul", val
            else:
                kv[btn_key], kv[axis_key] = val, "nul"
        for i in range(2, 5):
            for ra in ra_names.values():
                kv.setdefault(f"input_player{i}_{ra}", "nul")
        kv.update({
            "input_player1_l_x_plus_axis": "+0", "input_player1_l_x_minus_axis": "-0",
            "input_player1_l_y_plus_axis": "-1", "input_player1_l_y_minus_axis": "+1",
            "input_player1_r_x_plus_axis": "+2", "input_player1_r_x_minus_axis": "-2",
            "input_player1_r_y_plus_axis": "-3", "input_player1_r_y_minus_axis": "+3",
            "input_player1_analog_dpad_mode": "1" if adv.get("analog_to_dpad", True) else "0",
        })
        # Player device assignment (index of the joypad, 0-based)
        for i in range(1, 5):
            dev = str(adv.get(f"player{i}_device", "auto" if i <= 2 else "none"))
            if dev.startswith("xinput_") or dev.startswith("dinput_"):
                kv[f"input_player{i}_joypad_index"] = dev.split("_", 1)[1]
            else:
                kv[f"input_player{i}_joypad_index"] = str(i - 1)

        with open(cfg_path, "w", encoding="utf-8") as f:
            for k in sorted(kv):
                f.write(f'{k} = "{kv[k]}"\n')
        return "RetroArch (8 consoles Libretro)"

    def _write_libretro_core_options(self, adv) -> str:
        ra_dir = os.path.join(self.emulators_dir, "retroarch")
        cap32_dir = os.path.join(ra_dir, "config", "cap32")
        os.makedirs(cap32_dir, exist_ok=True)
        amstrad_kb = adv.get("amstrad_input_mode", "joystick") == "keyboard"
        with open(os.path.join(cap32_dir, "cap32.opt"), "w", encoding="utf-8") as f:
            f.write('cap32_model = "6128"\n')
            f.write('cap32_autorun = "enabled"\n')
            f.write('cap32_combokey = "y"\n')
            f.write(f'cap32_retrojoy0 = "{"keyboard" if amstrad_kb else "joystick"}"\n')

        puae_dir = os.path.join(ra_dir, "config", "PUAE")
        os.makedirs(puae_dir, exist_ok=True)
        amiga_mouse = adv.get("amiga_input_mode", "joystick") == "mouse"
        with open(os.path.join(puae_dir, "PUAE.opt"), "w", encoding="utf-8") as f:
            f.write('puae_model = "auto"\n')
            f.write('puae_kickstart = "auto"\n')
            f.write(f'puae_joyport = "{"mouse" if amiga_mouse else "joystick"}"\n')
            f.write('puae_retropad_options = "jump"\n')
            f.write('puae_use_whdload = "files"\n')
        return "Amstrad CPC (Caprice32) + Amiga (PUAE)"

    def _write_dolphin(self, kb, gp, adv) -> str:
        dolphin_dir = os.path.join(self.emulators_dir, "dolphin")
        cfg_dir = os.path.join(dolphin_dir, "User", "Config")
        os.makedirs(cfg_dir, exist_ok=True)
        with open(os.path.join(dolphin_dir, "portable.txt"), "w", encoding="utf-8") as f:
            f.write("")

        pad_dev = "XInput/0/Gamepad"
        kbd = "DInput/0/Keyboard Mouse"

        def m(action: str) -> str:
            """Expression = gamepad control OR keyboard key (fully qualified device)."""
            g = _GP_TO_DOLPHIN.get(gp.get(action, _GP_LABEL[action]), "")
            k = ra_key_to_dolphin(kb.get(action, _DEFAULT_KB[action]))
            parts = []
            if g:
                parts.append(f"`{g}`")
            parts.append(f"`{kbd}:{k}`")
            return " | ".join(parts)

        dz = round(float(adv.get("left_stick_deadzone", 0.15)) * 100, 1)
        gc_ini = f"""[GCPad1]
Device = {pad_dev}
Buttons/A = {m('a')}
Buttons/B = {m('b')}
Buttons/X = {m('x')}
Buttons/Y = {m('y')}
Buttons/Z = {m('r1')}
Buttons/Start = {m('start')}
Main Stick/Up = `Left Y+` | `{kbd}:{ra_key_to_dolphin(kb.get('up', 'up'))}`
Main Stick/Down = `Left Y-` | `{kbd}:{ra_key_to_dolphin(kb.get('down', 'down'))}`
Main Stick/Left = `Left X-` | `{kbd}:{ra_key_to_dolphin(kb.get('left', 'left'))}`
Main Stick/Right = `Left X+` | `{kbd}:{ra_key_to_dolphin(kb.get('right', 'right'))}`
Main Stick/Dead Zone = {dz}
C-Stick/Up = `Right Y+`
C-Stick/Down = `Right Y-`
C-Stick/Left = `Right X-`
C-Stick/Right = `Right X+`
C-Stick/Dead Zone = {dz}
Triggers/L = {m('l2')}
Triggers/R = {m('r2')}
Triggers/L-Analog = `Trigger L`
Triggers/R-Analog = `Trigger R`
D-Pad/Up = `Pad N`
D-Pad/Down = `Pad S`
D-Pad/Left = `Pad W`
D-Pad/Right = `Pad E`
Rumble/Motor = `Motor L` | `Motor R`
"""
        with open(os.path.join(cfg_dir, "GCPadNew.ini"), "w", encoding="utf-8") as f:
            f.write(gc_ini)

        mode = adv.get("wii_controller_type", "wiimote_nunchuk")
        extension = {"wiimote_nunchuk": "Nunchuk", "classic": "Classic"}.get(mode, "None")
        sideways = "True" if mode == "wiimote_horizontal" else "False"
        # In horizontal mode the D-pad is rotated by Dolphin itself; buttons 1/2 become the face buttons.
        wiimote_ini = f"""[Wiimote1]
Device = {pad_dev}
Source = 1
Extension = {extension}
Options/Sideways Wiimote = {sideways}
Buttons/A = {m('a')}
Buttons/B = {m('b') if mode != 'wiimote_horizontal' else m('r1')}
Buttons/1 = {m('x') if mode != 'wiimote_horizontal' else m('b')}
Buttons/2 = {m('y') if mode != 'wiimote_horizontal' else m('a')}
Buttons/- = {m('select')}
Buttons/+ = {m('start')}
Buttons/Home = `Thumb R`
D-Pad/Up = {m('up')}
D-Pad/Down = {m('down')}
D-Pad/Left = {m('left')}
D-Pad/Right = {m('right')}
IR/Up = `Right Y+`
IR/Down = `Right Y-`
IR/Left = `Right X-`
IR/Right = `Right X+`
IR/Auto-Hide = True
Shake/X = `Thumb L`
Shake/Y = `Thumb L`
Shake/Z = `Thumb L`
Rumble/Motor = `Motor L` | `Motor R`
Nunchuk/Buttons/C = {m('l1')}
Nunchuk/Buttons/Z = {m('l2')}
Nunchuk/Stick/Up = `Left Y+`
Nunchuk/Stick/Down = `Left Y-`
Nunchuk/Stick/Left = `Left X-`
Nunchuk/Stick/Right = `Left X+`
Nunchuk/Stick/Dead Zone = {dz}
Classic/Buttons/A = {m('a')}
Classic/Buttons/B = {m('b')}
Classic/Buttons/X = {m('x')}
Classic/Buttons/Y = {m('y')}
Classic/Buttons/ZL = {m('l2')}
Classic/Buttons/ZR = {m('r2')}
Classic/Buttons/- = {m('select')}
Classic/Buttons/+ = {m('start')}
Classic/Buttons/Home = `Thumb R`
Classic/Left Stick/Up = `Left Y+`
Classic/Left Stick/Down = `Left Y-`
Classic/Left Stick/Left = `Left X-`
Classic/Left Stick/Right = `Left X+`
Classic/Right Stick/Up = `Right Y+`
Classic/Right Stick/Down = `Right Y-`
Classic/Right Stick/Left = `Right X-`
Classic/Right Stick/Right = `Right X+`
Classic/Triggers/L = {m('l1')}
Classic/Triggers/R = {m('r1')}
Classic/D-Pad/Up = `Pad N`
Classic/D-Pad/Down = `Pad S`
Classic/D-Pad/Left = `Pad W`
Classic/D-Pad/Right = `Pad E`
[Wiimote2]
Source = 0
[Wiimote3]
Source = 0
[Wiimote4]
Source = 0
[BalanceBoard]
Source = 0
"""
        with open(os.path.join(cfg_dir, "WiimoteNew.ini"), "w", encoding="utf-8") as f:
            f.write(wiimote_ini)
        return "Wii / GameCube (Dolphin : pad GameCube + Wiimote)"

    def ryujinx_input_configs(self) -> List[Dict[str, Any]]:
        """Builds Ryujinx v70 `input_config` entries: SDL gamepad on Player 1 if present, else keyboard."""
        adv = self.advanced or {}
        prof = self.get_active_profile()
        kb = prof["keyboard_bindings"]
        gp = prof["gamepad_bindings"]
        ctype = adv.get("switch_controller_type", "ProController")
        if ctype not in ("ProController", "JoyconPair", "Handheld"):
            ctype = "ProController"

        def rk(action):
            return ra_key_to_ryujinx(kb.get(action, _DEFAULT_KB[action]))

        keyboard_cfg = {
            "left_joycon_stick": {
                "stick_up": "W", "stick_down": "S", "stick_left": "A", "stick_right": "D", "stick_button": "F",
            },
            "right_joycon_stick": {
                "stick_up": "I", "stick_down": "K", "stick_left": "J", "stick_right": "L", "stick_button": "H",
            },
            "left_joycon": {
                "button_minus": rk("select"), "button_l": rk("l1"), "button_zl": rk("l2"),
                "button_sl": "Unbound", "button_sr": "Unbound",
                "dpad_up": rk("up"), "dpad_down": rk("down"), "dpad_left": rk("left"), "dpad_right": rk("right"),
            },
            "right_joycon": {
                "button_plus": rk("start"), "button_r": rk("r1"), "button_zr": rk("r2"),
                "button_sl": "Unbound", "button_sr": "Unbound",
                "button_x": rk("x"), "button_b": rk("b"), "button_y": rk("y"), "button_a": rk("a"),
            },
            "version": 1,
            "backend": "WindowKeyboard",
            "id": "0",
            "name": "Keyboard",
            "controller_type": ctype,
            "player_index": "Player1",
        }

        pads = self.sdl_gamepads()
        if not pads:
            return [keyboard_cfg]

        def rg(action):
            return _GP_TO_RYU.get(gp.get(action, _GP_LABEL[action]), "Unbound")

        dz_l = float(adv.get("left_stick_deadzone", prof.get("deadzone", 0.15)))
        dz_r = float(adv.get("right_stick_deadzone", prof.get("deadzone", 0.15)))
        strength = float(adv.get("vibration_strength", 85)) / 100.0
        configs = []
        for idx, pad in enumerate(pads[:4]):
            configs.append({
                "left_joycon_stick": {
                    "joystick": "Left", "invert_stick_x": False, "invert_stick_y": False,
                    "rotate90_cw": False, "stick_button": "LeftStick",
                },
                "right_joycon_stick": {
                    "joystick": "Right", "invert_stick_x": False, "invert_stick_y": False,
                    "rotate90_cw": False, "stick_button": "RightStick",
                },
                "deadzone_left": round(dz_l, 2),
                "deadzone_right": round(dz_r, 2),
                "range_left": 1.0,
                "range_right": 1.0,
                "trigger_threshold": float(adv.get("trigger_threshold", 0.5)),
                "motion": {
                    "motion_backend": "GamepadDriver", "sensitivity": 100, "gyro_deadzone": 1, "enable_motion": True,
                },
                "rumble": {
                    "strong_rumble": round(strength, 2), "weak_rumble": round(strength, 2),
                    "enable_rumble": bool(adv.get("vibration_enabled", prof.get("vibration_enabled", True))),
                },
                "led": {"enable_led": False, "turn_off_led": False, "use_rainbow": False, "led_color": 0},
                "left_joycon": {
                    "button_minus": rg("select"), "button_l": rg("l1"), "button_zl": rg("l2"),
                    "button_sl": "Unbound", "button_sr": "Unbound",
                    "dpad_up": "DpadUp", "dpad_down": "DpadDown", "dpad_left": "DpadLeft", "dpad_right": "DpadRight",
                },
                "right_joycon": {
                    "button_plus": rg("start"), "button_r": rg("r1"), "button_zr": rg("r2"),
                    "button_sl": "Unbound", "button_sr": "Unbound",
                    "button_x": rg("x"), "button_b": rg("b"), "button_y": rg("y"), "button_a": rg("a"),
                },
                "version": 1,
                "backend": "GamepadSDL2",
                "id": pad["id"],
                "name": pad["name"],
                "controller_type": ctype,
                "player_index": f"Player{idx + 1}",
            })
        return configs
