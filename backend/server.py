"""
OmniConsole Tornado Web/API Backend & Desktop Window Manager.
Exposes REST endpoints for game search, downloading, library management,
live controller polling & auto-configuration, PC hardware monitoring,
native emulator launching, and comprehensive settings management.
"""

import html
import json
import os
import subprocess
import threading
import urllib.parse
import webbrowser
from typing import Dict, Any
import tornado.ioloop
import tornado.web

from .hardware_monitor import HardwareMonitor, CONSOLE_SPECS
from .controller_manager import ControllerManager
from .emulator_manager import EmulatorManager
from .settings_manager import SettingsManager
from .search_engine import GameSearchAndLibraryManager
from .cover_service import CoverArtService


class BaseAPIHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")
        self.set_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.set_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")

    def options(self, *args, **kwargs):
        self.set_status(204)
        self.finish()

    def write_json(self, data: Any, status: int = 200):
        self.set_status(status)
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps(data, ensure_ascii=False))

    def get_json_body(self) -> Dict[str, Any]:
        try:
            return json.loads(self.request.body.decode("utf-8"))
        except Exception:
            return {}


class BootstrapHandler(BaseAPIHandler):
    def initialize(self, ctx: Dict[str, Any]):
        self.ctx = ctx

    def get(self):
        hw: HardwareMonitor = self.ctx["hw"]
        cm: ControllerManager = self.ctx["cm"]
        em: EmulatorManager = self.ctx["em"]
        sm: GameSearchAndLibraryManager = self.ctx["sm"]
        st: SettingsManager = self.ctx["st"]
        app_state = self.ctx["app_state"]

        featured = sm.search_games("", page=1, per_page=60)
        self.write_json({
            "ok": True,
            "system": hw.get_system_profile(),
            "consoles": em.get_all_engines_status(),
            "controllers": {
                "connected": cm.detect_controllers(),
                "settings": cm.settings,
                "active_profile": cm.get_active_profile(),
                "profiles": cm.settings.get("profiles", {}),
            },
            "settings": st.get_settings(),
            "library": sm.get_library(),
            "featured": featured,
            "sources": [
                {"id": "all", "label": "Toutes les sources"},
                {"id": "curated", "label": "Sélection AetherDeck"},
                {"id": "archive_org", "label": "Internet Archive (16 consoles)"},
                {"id": "osc_wii", "label": "Open Shop Channel (Wii Homebrew)"},
                {"id": "switch_hb", "label": "Switch Homebrew App Store"},
                {"id": "smallgames", "label": "SmallGames.ch (Externe - Consentement requis)"},
                {"id": "nxbrew", "label": "NxBrew (Switch NSP/XCI - Consentement requis)"},
            ],
            "legal_compliance": st.settings.get("legal_compliance", {}),
            "tutorial_seen": app_state.get("tutorial_seen", False),
        })


class SearchHandler(BaseAPIHandler):
    def initialize(self, ctx: Dict[str, Any]):
        self.ctx = ctx

    def get(self):
        sm: GameSearchAndLibraryManager = self.ctx["sm"]
        q = self.get_argument("q", "")
        console_filter = self.get_argument("console", "all")
        source_filter = self.get_argument("source", "all")
        weight_filter = self.get_argument("weight", "all")
        try:
            page = int(self.get_argument("page", "1"))
        except ValueError:
            page = 1
        try:
            per_page = int(self.get_argument("per_page", "60"))
        except ValueError:
            per_page = 60

        search_res = sm.search_games(
            query=q,
            console_filter=console_filter,
            source_filter=source_filter,
            weight_filter=weight_filter,
            page=page,
            per_page=per_page,
        )
        search_res["ok"] = True
        self.write_json(search_res)


class GameDetailHandler(BaseAPIHandler):
    def initialize(self, ctx: Dict[str, Any]):
        self.ctx = ctx

    def get(self, game_id: str):
        sm: GameSearchAndLibraryManager = self.ctx["sm"]
        game = sm.get_game_by_id(game_id)
        if not game:
            return self.write_json({"ok": False, "message": "Jeu introuvable."}, 404)
        self.write_json({"ok": True, "game": game})


class DownloadHandler(BaseAPIHandler):
    def initialize(self, ctx: Dict[str, Any]):
        self.ctx = ctx

    def post(self):
        sm: GameSearchAndLibraryManager = self.ctx["sm"]
        body = self.get_json_body()
        game_id = body.get("game_id", "")
        game_payload = body.get("game")
        sync_mode = bool(body.get("sync", False))
        if not game_id:
            return self.write_json({"ok": False, "message": "Paramètre game_id manquant."}, 400)
        if sync_mode:
            res = sm.download_game_sync(game_id, game_payload)
        else:
            res = sm.download_game_async(game_id, game_payload)
        self.write_json(res)


class TasksStatusHandler(BaseAPIHandler):
    def initialize(self, ctx: Dict[str, Any]):
        self.ctx = ctx

    def get(self):
        sm: GameSearchAndLibraryManager = self.ctx["sm"]
        em: EmulatorManager = self.ctx["em"]
        self.write_json({
            "ok": True,
            "downloads": sm.download_tasks,
            "engine_installs": em.install_tasks,
            "library_ids": list(sm.library.keys()),
        })

    def delete(self):
        sm: GameSearchAndLibraryManager = self.ctx["sm"]
        to_del = [k for k, v in sm.download_tasks.items() if v.get("status") in ("error", "done")]
        for k in to_del:
            sm.download_tasks.pop(k, None)
        self.write_json({"ok": True, "cleared": len(to_del)})


class LibraryHandler(BaseAPIHandler):
    def initialize(self, ctx: Dict[str, Any]):
        self.ctx = ctx

    def get(self):
        sm: GameSearchAndLibraryManager = self.ctx["sm"]
        console_filter = self.get_argument("console", "all")
        self.write_json({
            "ok": True,
            "games": sm.get_library(console_filter=console_filter),
        })

    def delete(self):
        sm: GameSearchAndLibraryManager = self.ctx["sm"]
        game_id = self.get_argument("game_id", "")
        if not game_id:
            body = self.get_json_body()
            game_id = body.get("game_id", "")
        res = sm.remove_from_library(game_id)
        self.write_json(res)


class ImportLocalRomHandler(BaseAPIHandler):
    def initialize(self, ctx: Dict[str, Any]):
        self.ctx = ctx

    def post(self):
        sm: GameSearchAndLibraryManager = self.ctx["sm"]
        body = self.get_json_body()
        console_id = body.get("console_id", "nes")
        file_path = body.get("file_path", "")
        custom_title = body.get("title", "")

        if not file_path:
            selected = {"path": ""}

            def _pick():
                try:
                    import tkinter as tk
                    from tkinter import filedialog
                    root = tk.Tk()
                    root.withdraw()
                    root.attributes("-topmost", True)
                    all_supported = (
                        "*.nsp *.xci *.nro *.nca *.nds *.dsi *.3ds *.cia *.cxi "
                        "*.iso *.rvz *.wbfs *.gcm *.dol *.chd *.pbp *.cue *.z64 "
                        "*.n64 *.v64 *.md *.smd *.gen *.gba *.gb *.gbc *.sfc *.smc "
                        "*.nes *.dsk *.adf *.adz *.lha *.zip *.7z"
                    )
                    p = filedialog.askopenfilename(
                        title="Importer un jeu dans OmniConsole (Switch, NDS, 3DS, Wii, Rétro)",
                        filetypes=[
                            ("Tous les jeux compatibles (NSP, NDS, 3DS, ISO, ROMs)", all_supported),
                            ("Nintendo Switch (*.nsp, *.xci, *.nro)", "*.nsp *.xci *.nro *.nca"),
                            ("Nintendo DS (*.nds, *.dsi)", "*.nds *.dsi"),
                            ("Nintendo 3DS (*.3ds, *.cia, *.cxi)", "*.3ds *.cia *.cxi"),
                            ("Nintendo Wii & GameCube (*.iso, *.rvz, *.wbfs)", "*.iso *.rvz *.wbfs *.gcm *.dol"),
                            ("PlayStation 1 (*.chd, *.pbp, *.cue)", "*.chd *.pbp *.cue"),
                            ("Consoles Rétro (NES, SNES, GBA, N64, Mega Drive)", "*.nes *.sfc *.smc *.gba *.n64 *.z64 *.md"),
                            ("Micro-ordinateurs (Amstrad, Amiga)", "*.dsk *.adf *.adz *.lha"),
                            ("Archives compressées (*.zip, *.7z)", "*.zip *.7z"),
                            ("Tous les fichiers", "*.*"),
                        ],
                    )
                    root.destroy()
                    selected["path"] = p or ""
                except Exception:
                    pass

            t = threading.Thread(target=_pick)
            t.start()
            t.join(timeout=60)
            file_path = selected["path"]

        if not file_path:
            return self.write_json({"ok": False, "cancelled": True, "message": "Aucun fichier sélectionné."})

        res = sm.import_local_rom(file_path, console_id, custom_title)
        self.write_json(res)


class ScanDownloadsHandler(BaseAPIHandler):
    def initialize(self, ctx: Dict[str, Any]):
        self.ctx = ctx

    def get(self):
        sm: GameSearchAndLibraryManager = self.ctx["sm"]
        files = sm.scan_downloads_folder()
        self.write_json({"ok": True, "files": files, "count": len(files)})


class LaunchGameHandler(BaseAPIHandler):
    def initialize(self, ctx: Dict[str, Any]):
        self.ctx = ctx

    def post(self):
        sm: GameSearchAndLibraryManager = self.ctx["sm"]
        em: EmulatorManager = self.ctx["em"]
        body = self.get_json_body()
        game_id = body.get("game_id", "")
        game = sm.get_game_by_id(game_id)
        if not game:
            return self.write_json({"ok": False, "message": "Jeu introuvable."}, 404)
        if not game.get("in_library"):
            dl_res = sm.download_game_sync(game_id, game)
            if not dl_res.get("ok"):
                return self.write_json(dl_res, 500)
            game = dl_res["game"]

        res = em.launch_game(game)
        if res.get("ok"):
            sm.record_play_session(game_id)
        self.write_json(res)


class ControllersHandler(BaseAPIHandler):
    def initialize(self, ctx: Dict[str, Any]):
        self.ctx = ctx

    def get(self):
        cm: ControllerManager = self.ctx["cm"]
        self.write_json({
            "ok": True,
            "connected": cm.detect_controllers(),
            "settings": cm.settings,
            "active_profile": cm.get_active_profile(),
            "profiles": cm.settings.get("profiles", {}),
        })

    def post(self):
        cm: ControllerManager = self.ctx["cm"]
        st: SettingsManager = self.ctx["st"]
        body = self.get_json_body()
        action = body.get("action", "update")
        if action == "vibrate":
            port = int(body.get("port", 0))
            return self.write_json(cm.test_vibration(port=port))
        elif action == "sync":
            return self.write_json(st.apply_to_all_emulators())
        elif action == "reset_profile":
            reset_res = cm.reset_active_profile()
            st.apply_to_all_emulators()
            return self.write_json(reset_res)
        else:
            upd_res = cm.update_settings(body)
            st.apply_to_all_emulators()
            return self.write_json(upd_res)


class SettingsHandler(BaseAPIHandler):
    def initialize(self, ctx: Dict[str, Any]):
        self.ctx = ctx

    def get(self):
        st: SettingsManager = self.ctx["st"]
        self.write_json({"ok": True, **st.get_settings()})

    def post(self):
        st: SettingsManager = self.ctx["st"]
        body = self.get_json_body()
        action = body.get("action", "")
        if action == "reset":
            return self.write_json(st.reset_to_defaults())
        return self.write_json(st.update_settings(body))


class EnginesHandler(BaseAPIHandler):
    def initialize(self, ctx: Dict[str, Any]):
        self.ctx = ctx

    def get(self):
        em: EmulatorManager = self.ctx["em"]
        hw: HardwareMonitor = self.ctx["hw"]
        self.write_json({
            "ok": True,
            "system": hw.get_system_profile(),
            "consoles": em.get_all_engines_status(),
        })

    def post(self):
        em: EmulatorManager = self.ctx["em"]
        body = self.get_json_body()
        console_id = body.get("console_id", "")
        sync = bool(body.get("sync", False))
        if console_id == "all":
            return self.write_json({"ok": True, "results": em.install_all_essential_cores()})
        if sync:
            return self.write_json(em.install_engine_sync(console_id))
        return self.write_json(em.install_engine_async(console_id))


class EnginesOpenHandler(BaseAPIHandler):
    def initialize(self, ctx: Dict[str, Any]):
        self.ctx = ctx

    def post(self):
        em: EmulatorManager = self.ctx["em"]
        body = self.get_json_body()
        console_id = body.get("console_id", "nes")
        res = em.open_emulator_gui(console_id)
        self.write_json(res)


class EnginesTestHandler(BaseAPIHandler):
    def initialize(self, ctx: Dict[str, Any]):
        self.ctx = ctx

    def post(self):
        em: EmulatorManager = self.ctx["em"]
        sm: GameSearchAndLibraryManager = self.ctx["sm"]
        body = self.get_json_body()
        console_id = body.get("console_id", "nes")

        # Find existing game in library or first curated game for that console
        game_to_launch = None
        for g in sm.get_library(console_filter=console_id):
            if g.get("local_path") and os.path.exists(g["local_path"]):
                game_to_launch = g
                break
        if not game_to_launch:
            search_res = sm.search_games("", console_filter=console_id, page=1, per_page=5)
            games = search_res.get("games", [])
            if games:
                game_to_launch = games[0]

        if not game_to_launch:
            return self.write_json({"ok": False, "message": f"Aucun jeu disponible pour tester {console_id}."}, 404)

        if not game_to_launch.get("in_library"):
            dl_res = sm.download_game_sync(game_to_launch["id"], game_to_launch)
            if not dl_res.get("ok"):
                return self.write_json(dl_res, 500)
            game_to_launch = dl_res["game"]

        res = em.launch_game(game_to_launch)
        self.write_json(res)


class OpenExternalHandler(BaseAPIHandler):
    def post(self):
        body = self.get_json_body()
        url = body.get("url", "")
        if url.startswith(("http://", "https://")):
            try:
                webbrowser.open(url)
                return self.write_json({"ok": True, "message": f"Ouverture de {url} dans le navigateur."})
            except Exception as e:
                return self.write_json({"ok": False, "message": str(e)}, 500)
        self.write_json({"ok": False, "message": "URL non sécurisée ou invalide."}, 400)


class OpenFolderHandler(BaseAPIHandler):
    def initialize(self, ctx: Dict[str, Any]):
        self.ctx = ctx

    def post(self):
        body = self.get_json_body()
        kind = body.get("kind", "roms")
        target_path = self.ctx.get("base_dir", "")

        if kind == "roms":
            target_path = self.ctx.get("roms_dir", "")
        elif kind == "emulators":
            target_path = self.ctx.get("emulators_dir", "")
        elif kind == "downloads":
            target_path = os.path.join(os.path.expanduser("~"), "Downloads")

        if os.path.exists(target_path):
            try:
                os.startfile(target_path)
                return self.write_json({"ok": True, "path": target_path})
            except Exception as e:
                return self.write_json({"ok": False, "message": str(e)}, 500)
        self.write_json({"ok": False, "message": "Dossier introuvable."}, 404)


class LegalComplianceHandler(BaseAPIHandler):
    """Manages explicit legal disclaimer consent for external/third-party game indexers."""

    def initialize(self, ctx: Dict[str, Any]):
        self.ctx = ctx

    def get(self):
        st: SettingsManager = self.ctx["st"]
        legal = st.settings.get("legal_compliance", {})
        self.write_json({
            "ok": True,
            "legal_compliance": legal,
            "sources_classification": {
                "official_homebrew_open": ["osc_wii", "switch_hb"],
                "digital_preservation_archive": ["archive_org", "curated"],
                "third_party_external_consent_required": ["nxbrew", "smallgames"],
            },
            "legal_notice_fr": (
                "AetherDeck est un frontal d'émulation et de gestion matérielle open-source. "
                "Il ne contient, n'héberge et ne distribue aucun fichier ROM, ISO, BIOS, firmware ou clé cryptographique protégé par le droit d'auteur. "
                "L'accès aux index tiers (tels que NxBrew ou SmallGames) est désactivé par défaut et nécessite l'acceptation explicite de l'utilisateur, "
                "qui certifie posséder légalement l'œuvre originale (exception de copie privée, art. L122-5 du CPI / DMCA) et assume l'entière responsabilité de ses téléchargements."
            ),
        })

    def post(self):
        import time
        st: SettingsManager = self.ctx["st"]
        body = self.get_json_body()
        accepted = bool(body.get("accepted", False))
        ts = time.strftime("%Y-%m-%d %H:%M:%S") if accepted else None
        st.update_settings({
            "legal_compliance": {
                "accepted_external_sources_disclaimer": accepted,
                "accepted_at": ts,
            },
            "search_sources": {
                "enable_nxbrew": accepted,
                "enable_smallgames": accepted,
            },
        })
        self.write_json({
            "ok": True,
            "legal_compliance": st.settings.get("legal_compliance", {}),
            "search_sources": st.settings.get("search_sources", {}),
        })


class TutorialStateHandler(BaseAPIHandler):
    def initialize(self, ctx: Dict[str, Any]):
        self.ctx = ctx

    def post(self):
        body = self.get_json_body()
        seen = bool(body.get("tutorial_seen", True))
        self.ctx["app_state"]["tutorial_seen"] = seen
        state_file = self.ctx["state_file"]
        try:
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump(self.ctx["app_state"], f, indent=2)
        except Exception:
            pass
        self.write_json({"ok": True, "tutorial_seen": seen})


class NxBrewDetailsHandler(BaseAPIHandler):
    def initialize(self, ctx: Dict[str, Any]):
        self.ctx = ctx

    def get(self):
        sm: GameSearchAndLibraryManager = self.ctx["sm"]
        url = self.get_argument("url", "")
        if not url:
            return self.write_json({"ok": False, "message": "Paramètre url manquant."}, 400)
        details = sm.get_nxbrew_details(url)
        self.write_json(details)


class NxBrewResolveHandler(BaseAPIHandler):
    def initialize(self, ctx: Dict[str, Any]):
        self.ctx = ctx

    def post(self):
        sm: GameSearchAndLibraryManager = self.ctx["sm"]
        body = self.get_json_body()
        url = body.get("url", "")
        if not url:
            return self.write_json({"ok": False, "message": "Paramètre url manquant."}, 400)
        resolved = sm.resolve_nxbrew_link(url)
        self.write_json(resolved)


class CoverArtHandler(tornado.web.RequestHandler):
    """Automatically searches, caches, and serves official boxart images with fallback to dynamic SVG."""

    def initialize(self, ctx: Dict[str, Any]):
        self.ctx = ctx

    def get(self):
        cs: CoverArtService = self.ctx["cs"]
        title = self.get_argument("title", "").strip()
        console = self.get_argument("console", "").strip()
        console_id = self.get_argument("id", "").strip()
        accent = self.get_argument("accent", "#4f46e5")

        if title:
            cached_path = cs.get_or_fetch_cover(title=title, console_name=console, console_id=console_id)
            if cached_path and os.path.exists(cached_path):
                ext = os.path.splitext(cached_path)[1].lower()
                mime = "image/png" if ext == ".png" else "image/webp" if ext == ".webp" else "image/jpeg"
                self.set_header("Content-Type", mime)
                self.set_header("Cache-Control", "public, max-age=604800")
                with open(cached_path, "rb") as f:
                    self.write(f.read())
                return

        # Fallback to dynamic SVG
        svg_url = f"/api/cover_svg?title={urllib.parse.quote(title or 'Jeu')}&console={urllib.parse.quote(console or 'Console')}&accent={urllib.parse.quote(accent)}"
        self.redirect(svg_url)


class CoverSvgFallbackHandler(tornado.web.RequestHandler):
    """Generates a crisp, dynamic SVG cover art when an external boxart URL is unavailable."""

    def get(self):
        title = html.escape(self.get_argument("title", "Jeu Rétro"))
        console = html.escape(self.get_argument("console", "Console"))
        accent = self.get_argument("accent", "#4f46e5")
        if not accent.startswith("#") or len(accent) not in (4, 7):
            accent = "#4f46e5"

        words = title.split()
        lines = []
        curr = ""
        for w in words:
            if len(curr) + len(w) + 1 <= 16:
                curr = f"{curr} {w}".strip()
            else:
                if curr:
                    lines.append(curr)
                curr = w
        if curr:
            lines.append(curr)
        lines = lines[:3]

        text_elems = ""
        start_y = 195 - (len(lines) - 1) * 18
        for idx, line in enumerate(lines):
            y = start_y + idx * 36
            text_elems += f'<text x="150" y="{y}" text-anchor="middle" fill="#f8fafc" font-family="Segoe UI, Inter, sans-serif" font-weight="700" font-size="22">{line}</text>'

        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 400" width="300" height="400">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{accent}"/>
      <stop offset="55%" stop-color="#111827"/>
      <stop offset="100%" stop-color="#030712"/>
    </linearGradient>
  </defs>
  <rect width="300" height="400" rx="12" fill="url(#bg)"/>
  <circle cx="240" cy="70" r="95" fill="#ffffff" fill-opacity="0.04"/>
  <circle cx="50" cy="340" r="110" fill="{accent}" fill-opacity="0.12"/>
  <rect x="18" y="18" width="264" height="364" rx="10" fill="none" stroke="#ffffff" stroke-opacity="0.12" stroke-width="1.5"/>
  <rect x="32" y="34" width="130" height="26" rx="5" fill="#000000" fill-opacity="0.4"/>
  <text x="97" y="52" text-anchor="middle" fill="#cbd5e1" font-family="Segoe UI, sans-serif" font-weight="700" font-size="11" letter-spacing="1">{console.upper()}</text>
  {text_elems}
  <text x="150" y="350" text-anchor="middle" fill="#64748b" font-family="Segoe UI, sans-serif" font-weight="600" font-size="10" letter-spacing="1.5">AETHERDECK</text>
</svg>"""
        self.set_header("Content-Type", "image/svg+xml; charset=utf-8")
        self.set_header("Cache-Control", "public, max-age=86400")
        self.write(svg)


def create_tornado_app(base_dir: str) -> tornado.web.Application:
    data_dir = os.path.join(base_dir, "data")
    emulators_dir = os.path.join(base_dir, "emulators")
    roms_dir = os.path.join(base_dir, "roms")
    frontend_dir = os.path.join(base_dir, "frontend")

    for d in (data_dir, emulators_dir, roms_dir, frontend_dir):
        os.makedirs(d, exist_ok=True)

    state_file = os.path.join(data_dir, "app_state.json")
    app_state = {"tutorial_seen": False}
    if os.path.exists(state_file):
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                app_state.update(json.load(f))
        except Exception:
            pass

    hw = HardwareMonitor()
    cm = ControllerManager(data_dir, emulators_dir)
    em = EmulatorManager(base_dir, emulators_dir, hw, cm)
    st = SettingsManager(data_dir, emulators_dir, hw, cm)
    sm = GameSearchAndLibraryManager(data_dir, roms_dir, hw)
    cs = CoverArtService(data_dir)

    # Initial emulator config generation
    st.apply_to_all_emulators()

    ctx = {
        "base_dir": base_dir,
        "data_dir": data_dir,
        "emulators_dir": emulators_dir,
        "roms_dir": roms_dir,
        "state_file": state_file,
        "app_state": app_state,
        "hw": hw,
        "cm": cm,
        "em": em,
        "st": st,
        "sm": sm,
        "cs": cs,
    }

    return tornado.web.Application(
        [
            (r"/api/bootstrap", BootstrapHandler, {"ctx": ctx}),
            (r"/api/search", SearchHandler, {"ctx": ctx}),
            (r"/api/game/([^/]+)", GameDetailHandler, {"ctx": ctx}),
            (r"/api/nxbrew/details", NxBrewDetailsHandler, {"ctx": ctx}),
            (r"/api/nxbrew/resolve", NxBrewResolveHandler, {"ctx": ctx}),
            (r"/api/download", DownloadHandler, {"ctx": ctx}),
            (r"/api/tasks", TasksStatusHandler, {"ctx": ctx}),
            (r"/api/library", LibraryHandler, {"ctx": ctx}),
            (r"/api/library/import", ImportLocalRomHandler, {"ctx": ctx}),
            (r"/api/library/scan_downloads", ScanDownloadsHandler, {"ctx": ctx}),
            (r"/api/launch", LaunchGameHandler, {"ctx": ctx}),
            (r"/api/controllers", ControllersHandler, {"ctx": ctx}),
            (r"/api/settings", SettingsHandler, {"ctx": ctx}),
            (r"/api/engines", EnginesHandler, {"ctx": ctx}),
            (r"/api/engines/open", EnginesOpenHandler, {"ctx": ctx}),
            (r"/api/engines/test", EnginesTestHandler, {"ctx": ctx}),
            (r"/api/open_external", OpenExternalHandler),
            (r"/api/open_folder", OpenFolderHandler, {"ctx": ctx}),
            (r"/api/tutorial", TutorialStateHandler, {"ctx": ctx}),
            (r"/api/legal", LegalComplianceHandler, {"ctx": ctx}),
            (r"/api/legal/consent", LegalComplianceHandler, {"ctx": ctx}),
            (r"/api/cover_art", CoverArtHandler, {"ctx": ctx}),
            (r"/api/cover_svg", CoverSvgFallbackHandler),
            (
                r"/(.*)",
                tornado.web.StaticFileHandler,
                {"path": frontend_dir, "default_filename": "index.html"},
            ),
        ],
        debug=False,
    )
