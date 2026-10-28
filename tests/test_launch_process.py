import os
import subprocess
import time

BASE_DIR = r"C:\Users\timot\Documents\Programmation\Emulation_All_console"
dolphin_exe = os.path.join(BASE_DIR, "emulators", "dolphin", "Dolphin.exe")
ryujinx_exe = os.path.join(BASE_DIR, "emulators", "switch", "Ryujinx.exe")
retroarch_exe = os.path.join(BASE_DIR, "emulators", "retroarch", "retroarch.exe")
nsp_path = os.path.join(BASE_DIR, "roms", "switch", "Pokémon™ Legends\ua789 Arceus [01001F5010DFA000][v0][Base].nsp")

# 1. Test Dolphin launch
if os.path.exists(dolphin_exe):
    p_dol = subprocess.Popen([dolphin_exe, "--help"], cwd=os.path.dirname(dolphin_exe), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(1)
    p_dol.terminate()
    print("Dolphin launch test: OK (PID:", p_dol.pid, ")")

# 2. Test RetroArch version launch
if os.path.exists(retroarch_exe):
    p_ra = subprocess.Popen([retroarch_exe, "--version"], cwd=os.path.dirname(retroarch_exe), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, _ = p_ra.communicate(timeout=5)
    print("RetroArch launch test: OK -", out.decode(errors="replace").strip()[:60])

# 3. Test Ryujinx game launch with real NSP and Firmware 18.0.0 validation
if os.path.exists(ryujinx_exe) and os.path.exists(nsp_path):
    p_ryu = subprocess.Popen([ryujinx_exe, nsp_path], cwd=os.path.dirname(ryujinx_exe))
    time.sleep(4)
    p_ryu.terminate()
    try:
        p_ryu.wait(timeout=3)
    except Exception:
        pass
    
    # Check latest Ryujinx log
    logs_dir = os.path.join(BASE_DIR, "emulators", "switch", "portable", "Logs")
    log_files = sorted(
        [os.path.join(logs_dir, f) for f in os.listdir(logs_dir) if f.endswith(".log")],
        key=os.path.getmtime,
        reverse=True
    )
    if log_files:
        with open(log_files[0], "r", encoding="utf-8", errors="replace") as f:
            log_content = f.read()
        assert "Using Firmware Version: 18.0.0" in log_content, "Firmware 18.0.0 was not recognized!"
        assert ("Loading as NSP." in log_content or "Application Loaded:" in log_content), "Application was not loaded!"
        assert "RYU-0002" not in log_content, "RYU-0002 popup occurred!"
        print("Ryujinx Switch Game Launch: OK - Successfully running on Firmware 18.0.0 without errors.")
