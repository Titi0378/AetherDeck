"""
Comprehensive End-to-End Test Suite for AetherDeck.
Verifies hardware monitoring, controller centralization & config generation,
all 16 emulator engines (RetroArch, Dolphin, Ryujinx, Caprice32, PUAE, Stella, FBNeo, Flycast, PPSSPP),
multi-source search, real game downloading, library persistence,
settings panel with GPU selection, legal compliance API, and HTTP APIs.
"""

import json
import os
import sys
import threading
import time
import unittest
import requests
import tornado.httpserver
import tornado.ioloop

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from backend.hardware_monitor import HardwareMonitor, CONSOLE_SPECS
from backend.controller_manager import ControllerManager
from backend.emulator_manager import EmulatorManager
from backend.search_engine import GameSearchAndLibraryManager
from backend.server import create_tornado_app


class TestAetherDeckEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import asyncio
        cls.port = 18765
        ready_evt = threading.Event()

        def _run_server():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            cls.app = create_tornado_app(BASE_DIR)
            cls.server = cls.app.listen(cls.port, address="127.0.0.1")
            cls.ioloop = tornado.ioloop.IOLoop.current()
            ready_evt.set()
            cls.ioloop.start()

        cls.loop_thread = threading.Thread(target=_run_server, daemon=True)
        cls.loop_thread.start()
        ready_evt.wait(timeout=10)
        cls.base_url = f"http://127.0.0.1:{cls.port}"

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "ioloop"):
            cls.ioloop.add_callback(cls.ioloop.stop)

    def test_01_hardware_monitor_and_lightweight_pc_support(self):
        r = requests.get(f"{self.base_url}/api/bootstrap", timeout=10)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data["ok"])
        sys_prof = data["system"]
        self.assertIn("cpu_name", sys_prof)
        self.assertGreater(sys_prof["ram_total_gb"], 0)
        self.assertIn(sys_prof["pc_tier"], ("leger", "moyen", "puissant"))

        compat = sys_prof["console_compatibility"]
        for light_cid in ("amstrad_cpc", "amiga", "nes", "snes", "gba", "megadrive"):
            self.assertEqual(compat[light_cid]["weight_category"], "leger")
            self.assertEqual(compat[light_cid]["status"], "optimal")
        self.assertEqual(compat["wii"]["weight_category"], "lourd")
        self.assertEqual(compat["switch"]["weight_category"], "lourd")

    def test_02_all_16_emulator_engines_installed_and_ready(self):
        r = requests.get(f"{self.base_url}/api/engines", timeout=10)
        self.assertEqual(r.status_code, 200)
        consoles = {c["console_id"]: c for c in r.json()["consoles"]}
        expected = [
            "amstrad_cpc", "amiga", "nes", "snes", "gba", "megadrive",
            "n64", "ps1", "wii", "switch", "nds", "3ds",
            "atari2600", "arcade", "dreamcast", "psp",
        ]
        for cid in expected:
            self.assertIn(cid, consoles, f"Missing console {cid}")
            self.assertTrue(consoles[cid]["installed"], f"Engine for {cid} should be installed")

        self.assertTrue(os.path.exists(os.path.join(BASE_DIR, "emulators", "retroarch", "retroarch.exe")))
        self.assertTrue(os.path.exists(os.path.join(BASE_DIR, "emulators", "dolphin", "Dolphin.exe")))
        self.assertTrue(os.path.exists(os.path.join(BASE_DIR, "emulators", "switch", "Ryujinx.exe")))
        self.assertTrue(os.path.exists(os.path.join(BASE_DIR, "emulators", "retroarch", "cores", "melonds_libretro.dll")))
        self.assertTrue(os.path.exists(os.path.join(BASE_DIR, "emulators", "retroarch", "cores", "citra_libretro.dll")))
        self.assertTrue(os.path.exists(os.path.join(BASE_DIR, "emulators", "retroarch", "cores", "stella2014_libretro.dll")))
        self.assertTrue(os.path.exists(os.path.join(BASE_DIR, "emulators", "retroarch", "cores", "fbneo_libretro.dll")))
        self.assertTrue(os.path.exists(os.path.join(BASE_DIR, "emulators", "retroarch", "cores", "flycast_libretro.dll")))
        self.assertTrue(os.path.exists(os.path.join(BASE_DIR, "emulators", "retroarch", "cores", "ppsspp_libretro.dll")))

    def test_03_centralized_controllers_and_config_injection(self):
        r = requests.get(f"{self.base_url}/api/controllers", timeout=10)
        self.assertEqual(r.status_code, 200)
        c_data = r.json()
        self.assertTrue(c_data["ok"])
        self.assertGreaterEqual(len(c_data["connected"]), 1)

        # Switch to Nintendo layout
        r_post = requests.post(
            f"{self.base_url}/api/controllers",
            json={"active_profile": "nintendo_layout"},
            timeout=10,
        )
        self.assertEqual(r_post.status_code, 200)
        self.assertTrue(r_post.json()["ok"])

        # Switch back to xbox_standard
        requests.post(
            f"{self.base_url}/api/controllers",
            json={"active_profile": "xbox_standard"},
            timeout=10,
        )

        # Verify generated configuration files exist for RetroArch, Amstrad, Amiga, Dolphin, and Switch
        self.assertTrue(os.path.exists(os.path.join(BASE_DIR, "emulators", "retroarch", "retroarch.cfg")))
        self.assertTrue(os.path.exists(os.path.join(BASE_DIR, "emulators", "retroarch", "config", "cap32", "cap32.opt")))
        self.assertTrue(os.path.exists(os.path.join(BASE_DIR, "emulators", "retroarch", "config", "PUAE", "PUAE.opt")))
        self.assertTrue(os.path.exists(os.path.join(BASE_DIR, "emulators", "dolphin", "User", "Config", "GCPadNew.ini")))
        self.assertTrue(os.path.exists(os.path.join(BASE_DIR, "emulators", "dolphin", "User", "Config", "WiimoteNew.ini")))
        self.assertTrue(os.path.exists(os.path.join(BASE_DIR, "emulators", "switch", "portable", "Config.json")))

    def test_04_search_mario_across_consoles(self):
        r = requests.get(f"{self.base_url}/api/search?q=Mario", timeout=10)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data["ok"])
        games = data["games"]
        self.assertGreaterEqual(len(games), 6, "Searching 'Mario' should return multiple Mario games across consoles")

        consoles_found = {g["console_id"] for g in games}
        for expected_cid in ("nes", "snes", "gba", "n64"):
            self.assertIn(expected_cid, consoles_found, f"Mario search should include {expected_cid}")

    def test_05_real_download_and_library_flow(self):
        for gid in ("nes_super_mario_bros", "cpc_prince_of_persia"):
            r = requests.post(
                f"{self.base_url}/api/download",
                json={"game_id": gid, "sync": True},
                timeout=60,
            )
            self.assertEqual(r.status_code, 200)
            res = r.json()
            self.assertTrue(res["ok"], f"Download failed for {gid}: {res}")
            self.assertTrue(os.path.exists(res["local_path"]))
            self.assertGreater(os.path.getsize(res["local_path"]), 1024)

        r_lib = requests.get(f"{self.base_url}/api/library", timeout=10)
        self.assertEqual(r_lib.status_code, 200)
        lib_games = r_lib.json()["games"]
        lib_ids = {g["id"] for g in lib_games}
        self.assertIn("nes_super_mario_bros", lib_ids)
        self.assertIn("cpc_prince_of_persia", lib_ids)

    def test_06_frontend_assets_and_svg_cover_fallback(self):
        for path in ("/", "/styles.css", "/app.js", "/api/cover_svg?title=Super+Mario&console=NES"):
            r = requests.get(f"{self.base_url}{path}", timeout=10)
            self.assertEqual(r.status_code, 200)

    def test_07_settings_panel_and_gpu_configuration(self):
        r = requests.get(f"{self.base_url}/api/settings", timeout=10)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data["ok"])
        self.assertIn("available_gpus", data)
        self.assertIn("available_backends", data)

        # Update GPU and graphics backend
        r_post = requests.post(
            f"{self.base_url}/api/settings",
            json={
                "graphics": {
                    "video_backend": "vulkan",
                    "internal_resolution_scale": 2,
                    "vsync": True,
                },
                "performance_audio": {
                    "audio_volume": 85,
                    "audio_latency_ms": 64,
                },
            },
            timeout=10,
        )
        self.assertEqual(r_post.status_code, 200)
        res = r_post.json()
        self.assertTrue(res["ok"])
        self.assertEqual(res["settings"]["graphics"]["video_backend"], "vulkan")
        self.assertEqual(res["settings"]["performance_audio"]["audio_volume"], 85)

        # Verify Ryujinx Config.json v70 received the update
        with open(os.path.join(BASE_DIR, "emulators", "switch", "portable", "Config.json"), "r", encoding="utf-8") as f:
            ryu_cfg = json.load(f)
            self.assertEqual(ryu_cfg["version"], 70)
            self.assertEqual(ryu_cfg["graphics_backend"], "Vulkan")

    def test_08_multi_source_search_and_pagination(self):
        # Test pagination
        r = requests.get(f"{self.base_url}/api/search?page=1&per_page=10", timeout=10)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data["ok"])
        self.assertLessEqual(len(data["games"]), 10)
        self.assertIn("sources_status", data)

        # Test source filter
        r_src = requests.get(f"{self.base_url}/api/search?source=curated", timeout=10)
        self.assertEqual(r_src.status_code, 200)
        src_data = r_src.json()
        self.assertTrue(src_data["ok"])
        self.assertGreater(len(src_data["games"]), 0)

    def test_09_scan_downloads_and_tasks_status(self):
        r_scan = requests.get(f"{self.base_url}/api/library/scan_downloads", timeout=10)
        self.assertEqual(r_scan.status_code, 200)
        self.assertTrue(r_scan.json()["ok"])

        r_tasks = requests.get(f"{self.base_url}/api/tasks", timeout=10)
        self.assertEqual(r_tasks.status_code, 200)
        self.assertTrue(r_tasks.json()["ok"])

        # Test DELETE /api/tasks to clear completed/errored tasks
        r_del = requests.delete(f"{self.base_url}/api/tasks", timeout=10)
        self.assertEqual(r_del.status_code, 200)
        self.assertTrue(r_del.json()["ok"])

    def test_10_interactive_per_button_remapping(self):
        r_remap = requests.post(
            f"{self.base_url}/api/controllers",
            json={
                "action": "update",
                "keyboard_bindings": {"a": "space", "b": "c"},
                "gamepad_bindings": {"a": "0", "b": "1"},
            },
            timeout=10,
        )
        self.assertEqual(r_remap.status_code, 200)
        data = r_remap.json()
        self.assertTrue(data["ok"])
        active_prof = data.get("active_profile") or data.get("settings", {}).get("profiles", {}).get("xbox_standard", {})
        self.assertEqual(active_prof.get("keyboard_bindings", {}).get("a"), "space")

    def test_11_nsp_and_nds_3ds_import_and_keys(self):
        # 1. Verify Switch authentic prod.keys, title.keys, and full Nintendo Switch Firmware (18.0.0)
        prod_keys_path = os.path.join(BASE_DIR, "emulators", "switch", "portable", "system", "prod.keys")
        title_keys_path = os.path.join(BASE_DIR, "emulators", "switch", "portable", "system", "title.keys")
        reg_dir = os.path.join(BASE_DIR, "emulators", "switch", "portable", "bis", "system", "Contents", "registered")

        self.assertTrue(os.path.exists(prod_keys_path), "prod.keys must exist")
        self.assertTrue(os.path.exists(title_keys_path), "title.keys must exist")
        self.assertGreater(os.path.getsize(prod_keys_path), 5000, "prod.keys must contain authentic master keys, not a 79-byte dummy")
        self.assertTrue(os.path.exists(reg_dir), "Firmware registered contents directory must exist")
        self.assertGreaterEqual(len(os.listdir(reg_dir)), 200, "Firmware must contain at least 200 registered NCAs")

        # Verify engine status reports firmware installed
        r_eng = requests.get(f"{self.base_url}/api/engines", timeout=10)
        sw_info = next((c for c in r_eng.json()["consoles"] if c["console_id"] == "switch"), {})
        self.assertTrue(sw_info.get("firmware_installed"), "Switch engine status must report firmware installed")

        # 2. Test auto-detection of NSP files on import
        test_tmp_dir = os.path.join(BASE_DIR, "tests", "_test_roms_tmp")
        os.makedirs(test_tmp_dir, exist_ok=True)
        nsp_path = os.path.join(test_tmp_dir, "Super_Mario_Test.nsp")
        with open(nsp_path, "wb") as f:
            f.write(b"HEAD" + b"\x00" * 1024)

        r_import = requests.post(
            f"{self.base_url}/api/library/import",
            json={"file_path": nsp_path, "console_id": "auto"},
            timeout=10,
        )
        self.assertEqual(r_import.status_code, 200)
        res_import = r_import.json()
        self.assertTrue(res_import["ok"])
        self.assertEqual(res_import["game"]["console_id"], "switch", "NSP must auto-route to switch console")

        # 3. Test auto-detection of NDS and 3DS files on import
        nds_path = os.path.join(test_tmp_dir, "Mario_Kart_DS_Test.nds")
        with open(nds_path, "wb") as f:
            f.write(b"NDS_TEST" + b"\x00" * 512)
        r_nds = requests.post(f"{self.base_url}/api/library/import", json={"file_path": nds_path, "console_id": "auto"}, timeout=10)
        self.assertEqual(r_nds.json()["game"]["console_id"], "nds")

        ds3_path = os.path.join(test_tmp_dir, "Mario_3D_Land_Test.3ds")
        with open(ds3_path, "wb") as f:
            f.write(b"3DS_TEST" + b"\x00" * 512)
        r_3ds = requests.post(f"{self.base_url}/api/library/import", json={"file_path": ds3_path, "console_id": "auto"}, timeout=10)
        self.assertEqual(r_3ds.json()["game"]["console_id"], "3ds")

        # Clean up temporary test entries from library and roms
        for imported_res in (res_import, r_nds.json(), r_3ds.json()):
            gid = imported_res.get("game", {}).get("id")
            lpath = imported_res.get("game", {}).get("local_path")
            if gid:
                requests.delete(f"{self.base_url}/api/library?game_id={gid}", timeout=10)
            if lpath and os.path.exists(lpath):
                try:
                    os.remove(lpath)
                except Exception:
                    pass

        # Clean up temporary test files
        import shutil
        shutil.rmtree(test_tmp_dir, ignore_errors=True)

    def test_12_wii_verified_sources_and_dolphin_launch(self):
        # 1. Search for Wii games
        r = requests.get(f"{self.base_url}/api/search?q=Mario&console=wii", timeout=10)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data["ok"])
        wii_games = data["games"]
        self.assertGreater(len(wii_games), 0, "Wii search must return games")

        titles = [g["title"] for g in wii_games]
        # Verify presence of iconic Wii games
        has_galaxy = any("galaxy" in t.lower() for t in titles)
        has_kart = any("kart" in t.lower() for t in titles)
        self.assertTrue(has_galaxy or has_kart, f"Expected Super Mario Galaxy or Mario Kart Wii in results: {titles}")

        # 2. Check that direct download link returns HTTP 200/206
        reachable = False
        for w_game in wii_games[:4]:
            dl_url = w_game.get("download_url", "")
            if not dl_url:
                continue
            try:
                r_chk = requests.get(
                    dl_url,
                    headers={"User-Agent": "Mozilla/5.0", "Range": "bytes=0-63"},
                    allow_redirects=True,
                    timeout=10,
                    stream=True,
                )
                r_chk.close()
                if r_chk.status_code in (200, 206):
                    reachable = True
                    break
            except Exception:
                pass
        self.assertTrue(reachable, "At least one Wii download URL must respond with HTTP 200/206")

    def test_13_nxbrew_search_details_and_playwright_resolver(self):
        # 1. Test NxBrew live search
        r_search = requests.get(f"{self.base_url}/api/search?q=Mario&source=nxbrew", timeout=15)
        self.assertEqual(r_search.status_code, 200)
        s_data = r_search.json()
        self.assertTrue(s_data["ok"])
        self.assertGreater(len(s_data["games"]), 0, "NxBrew search must return games for query 'Mario'")
        first_game = s_data["games"][0]
        self.assertEqual(first_game["console_id"], "switch")
        self.assertEqual(first_game["source_id"], "nxbrew")
        self.assertTrue(first_game["download_url"].startswith("http"))

        # 2. Test NxBrew details extraction
        detail_target_url = "https://nxbrew.net/mario-kart-live-home-circuit-switch-nsp-eshop/"
        r_det = requests.get(f"{self.base_url}/api/nxbrew/details?url={detail_target_url}", timeout=15)
        self.assertEqual(r_det.status_code, 200)
        d_data = r_det.json()
        self.assertTrue(d_data["ok"], f"NxBrew details should succeed: {d_data}")
        self.assertGreater(len(d_data["packages"]), 0, "NxBrew details must parse at least 1 package")
        first_pkg = d_data["packages"][0]
        self.assertGreater(len(first_pkg["hosts"]), 0, "Package must contain host links")

        # 3. Test Playwright direct link resolution (anti-redirection)
        test_ouo = first_pkg["hosts"][0]["url"]
        r_resolve = requests.post(f"{self.base_url}/api/nxbrew/resolve", json={"url": test_ouo}, timeout=35)
        self.assertEqual(r_resolve.status_code, 200)
        res_data = r_resolve.json()
        self.assertTrue(res_data["ok"], f"Link resolution failed: {res_data}")
        self.assertIn("resolved_url", res_data)
        self.assertNotIn("ouo.io", res_data["resolved_url"].lower())

    def test_14_cover_art_service_and_endpoint(self):
        # 1. Test automated cover search for Wii game
        r_cover = requests.get(f"{self.base_url}/api/cover_art?title=Super+Mario+Galaxy&console=Wii&id=wii", timeout=12)
        self.assertEqual(r_cover.status_code, 200)
        self.assertTrue(r_cover.headers.get("Content-Type", "").startswith("image/"))
        self.assertGreater(len(r_cover.content), 2048, "Cover image must contain real image bytes")

        # 2. Test automated cover search for Switch game
        r_cover_sw = requests.get(f"{self.base_url}/api/cover_art?title=Pokemon+Legends+Arceus&console=Switch&id=switch", timeout=12)
        self.assertEqual(r_cover_sw.status_code, 200)
        self.assertTrue(r_cover_sw.headers.get("Content-Type", "").startswith("image/"))
        self.assertGreater(len(r_cover_sw.content), 2048, "Switch cover image must contain real image bytes")

    def test_15_wii_comprehensive_catalog(self):
        # Test searching for Wii titles across the extensive Redump catalog
        for query in ["Animal Crossing", "Star Wars", "Super Paper Mario"]:
            r = requests.get(f"{self.base_url}/api/search?q={requests.utils.quote(query)}&console=wii", timeout=10)
            self.assertEqual(r.status_code, 200)
            data = r.json()
            self.assertTrue(data["ok"])
            games = data["games"]
            self.assertGreater(len(games), 0, f"Expected search results for Wii query '{query}'")
            first = games[0]
            self.assertEqual(first["console_id"], "wii")
            self.assertTrue(first["download_url"].startswith("https://archive.org/download/"))

    def test_16_new_consoles_search_and_legal_compliance_api(self):
        # 1. Verify search results for Atari 2600, Arcade/Neo Geo, Dreamcast, and PSP
        for cid in ("atari2600", "arcade", "dreamcast", "psp"):
            r = requests.get(f"{self.base_url}/api/search?console={cid}", timeout=10)
            self.assertEqual(r.status_code, 200)
            data = r.json()
            self.assertTrue(data["ok"])
            self.assertGreater(len(data["games"]), 0, f"Expected games for {cid}")
            self.assertEqual(data["games"][0]["console_id"], cid)

        # 2. Verify Legal Compliance API (/api/legal and /api/legal/consent)
        r_leg = requests.get(f"{self.base_url}/api/legal", timeout=10)
        self.assertEqual(r_leg.status_code, 200)
        self.assertTrue(r_leg.json()["ok"])

        # Accept consent
        r_accept = requests.post(f"{self.base_url}/api/legal/consent", json={"accepted": True}, timeout=10)
        self.assertEqual(r_accept.status_code, 200)
        self.assertTrue(r_accept.json()["legal_compliance"]["accepted_external_sources_disclaimer"])

        # Revoke consent back to strict default
        r_revoke = requests.post(f"{self.base_url}/api/legal/consent", json={"accepted": False}, timeout=10)
        self.assertEqual(r_revoke.status_code, 200)
        self.assertFalse(r_revoke.json()["legal_compliance"]["accepted_external_sources_disclaimer"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
