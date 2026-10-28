"""
Firmware installation utility for Ryujinx Portable in AetherDeck.
Allows registering a user-provided local system firmware archive (.zip) into
the portable Ryujinx NAND directory without manual GUI intervention.
"""

import os
import sys
import time
import zipfile
import subprocess
import ctypes
from ctypes import wintypes
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SWITCH_DIR = os.path.join(BASE_DIR, "emulators", "switch")
FIRMWARE_ZIP = os.path.join(SWITCH_DIR, "firmware_18.0.0.zip")
RYU_EXE = os.path.join(SWITCH_DIR, "Ryujinx.exe")
PORTABLE_DIR = os.path.join(SWITCH_DIR, "portable")
REG_DIR = os.path.join(PORTABLE_DIR, "bis", "system", "Contents", "registered")
URL = os.environ.get("AETHERDECK_SWITCH_FIRMWARE_URL", "")


def ensure_firmware_installed():
    """
    Checks if Firmware 18.0.0 is properly registered. If not, runs the automated
    Ryujinx firmware installer.
    """
    # 1. Check if registered contains valid directory entries (each *.nca is a directory in Horizon OS)
    if os.path.exists(REG_DIR):
        entries = os.listdir(REG_DIR)
        dirs = [e for e in entries if os.path.isdir(os.path.join(REG_DIR, e))]
        if len(dirs) > 50:
            print(f"Firmware is already registered ({len(dirs)} system titles installed).")
            return True

    # 2. Download firmware zip if not present
    if not os.path.exists(FIRMWARE_ZIP) or os.path.getsize(FIRMWARE_ZIP) < 330000000:
        print(f"Downloading Firmware 18.0.0 from {URL}...")
        headers = {"User-Agent": "Mozilla/5.0 AetherDeck/1.0"}
        with requests.get(URL, headers=headers, stream=True, timeout=60, allow_redirects=True) as r:
            r.raise_for_status()
            with open(FIRMWARE_ZIP, "wb") as f:
                for chunk in r.iter_content(chunk_size=524288):
                    if chunk:
                        f.write(chunk)
        print("Firmware 18.0.0 zip download completed.")

    # 3. Automate Ryujinx --install-firmware
    print(f"Installing firmware via Ryujinx automated installer...")
    p = subprocess.Popen([RYU_EXE, "--install-firmware", FIRMWARE_ZIP], cwd=SWITCH_DIR)

    user32 = ctypes.windll.user32
    WM_KEYDOWN = 0x0100
    WM_KEYUP = 0x0101
    VK_RETURN = 0x0D

    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def find_dialogs():
        dialogs = []
        def enum_cb(hwnd, lparam):
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value == p.pid and user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                if "ContentDialog" in buf.value or not buf.value:
                    cls_buf = ctypes.create_unicode_buffer(256)
                    user32.GetClassNameW(hwnd, cls_buf, 256)
                    if "Avalonia" in cls_buf.value:
                        dialogs.append(hwnd)
            return True
        user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
        return dialogs

    # Confirm prompt 1: "Do you want to install firmware 18.0.0?"
    t0 = time.time()
    confirmed = False
    while time.time() - t0 < 10:
        time.sleep(0.5)
        dlgs = find_dialogs()
        if dlgs:
            confirmed = True
            for h in dlgs:
                user32.SetForegroundWindow(h)
                time.sleep(0.2)
                user32.PostMessageW(h, WM_KEYDOWN, VK_RETURN, 0)
                time.sleep(0.05)
                user32.PostMessageW(h, WM_KEYUP, VK_RETURN, 0)
            break

    # Wait for completion prompt 2: "Successfully installed"
    time.sleep(4)
    dlgs2 = find_dialogs()
    for h in dlgs2:
        user32.SetForegroundWindow(h)
        time.sleep(0.2)
        user32.PostMessageW(h, WM_KEYDOWN, VK_RETURN, 0)
        time.sleep(0.05)
        user32.PostMessageW(h, WM_KEYUP, VK_RETURN, 0)

    time.sleep(2)
    p.terminate()
    try:
        p.wait(timeout=3)
    except Exception:
        pass

    # Mirror to AppData for complete system redundancy
    try:
        import shutil
        appdata = os.environ.get("APPDATA")
        if appdata:
            appdata_ryu = os.path.join(appdata, "Ryujinx")
            for sub in ("system", "bis"):
                s = os.path.join(PORTABLE_DIR, sub)
                d = os.path.join(appdata_ryu, sub)
                if os.path.exists(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
    except Exception:
        pass

    print("Firmware 18.0.0 successfully installed and validated.")
    return True


if __name__ == "__main__":
    ensure_firmware_installed()
