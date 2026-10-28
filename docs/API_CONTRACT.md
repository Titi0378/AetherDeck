# AetherDeck — Contrat d'API (backend Tornado <-> frontend)

Toutes les routes renvoient du JSON `{"ok": bool, ...}`. Le frontend est servi en statique depuis `frontend/`
(index.html, styles.css, app.js) sur `http://127.0.0.1:<port>/`. Pas de framework, pas de build : JS vanilla.

## Objet `Game` (renvoyé par search / library / game)
```json
{
  "id": "ia_nes_ab12cd34ef",
  "title": "Super Mario Bros.",
  "full_rom_name": "Super Mario Bros. (World)",
  "console_id": "nes",                // amstrad_cpc | amiga | nes | snes | gba | megadrive | n64 | ps1 | wii | switch
  "console_name": "NES",
  "console_full_name": "Nintendo Entertainment System (NES)",
  "console_accent": "#dc2626",
  "cover_url": "https://thumbnails.libretro.com/....png",   // peut être vide ou 404 -> utiliser /api/cover_svg
  "file_size_label": "40 Ko",
  "size_bytes": 40960,
  "release_year": 1985,
  "developer": "...", "genre": "...", "players": "...", "region": "USA",
  "summary": "...", "description": "...",
  "source_id": "archive_org",         // archive_org | osc_wii | switch_hb | smallgames | curated | local
  "source_label": "Internet Archive",
  "trust_level": "verified",          // verified | external
  "trust_note": "Téléchargement direct HTTPS depuis archive.org",
  "download_kind": "direct",          // direct = téléchargé par l'app ; external = ouvre la page dans le navigateur
  "page_url": "https://...",          // page web d'origine (pour external)
  "engine_name": "FCEUmm (Libretro NES)",
  "weight_category": "leger", "weight_label": "Très Léger",
  "pc_compatibility": {"status": "optimal|compatible|demanding", "status_text": "...", "badge_color": "#10b981"},
  "supported_controllers": ["Manette Xbox / PlayStation / Switch / USB", "Clavier PC"],
  "console_controllers": [{"id": "xbox_ps_switch", "name": "...", "icon": "gamepad|keyboard|mouse|joystick|motion", "recommended": true}],
  "in_library": false,
  "local_path": null,
  "play_count": 0, "last_played": null,
  "download_status": "idle|queued|downloading|extracting|downloaded|error",
  "download_progress": 0,
  "download_message": "Prêt à télécharger"
}
```

## Routes
| Méthode | Route | Corps / Query | Réponse |
|---|---|---|---|
| GET | `/api/bootstrap` | – | `{system, consoles[], controllers:{connected[], settings, active_profile}, settings:{settings, available_gpus[], available_backends[]}, library[], featured:{games[], total}, sources[], tutorial_seen}` |
| GET | `/api/search` | `q, console=all, source=all, weight=all, page=1, per_page=60` | `{query, page, per_page, total, has_more, games[], sources_status:{source_id:{label, count, ready}}}` |
| GET | `/api/game/<id>` | – | `{game}` |
| POST | `/api/download` | `{game_id, game?}` | `{status:"started"|"queued"}` (asynchrone, suivre via /api/tasks) |
| GET | `/api/tasks` | – | `{downloads:{game_id:{status, progress, message, title, speed_label}}, engine_installs:{}, library_ids[]}` |
| GET | `/api/library` | `console=all` | `{games[]}` |
| DELETE | `/api/library?game_id=` | – | `{message}` |
| POST | `/api/library/import` | `{console_id, file_path?}` (sans file_path => sélecteur Windows) | `{game}` |
| GET | `/api/library/scan_downloads` | – | `{files:[{path, name, size_label, console_id}]}` (fichiers jeux trouvés dans le dossier Téléchargements Windows) |
| POST | `/api/launch` | `{game_id}` | `{engine, message, pid}` |
| GET | `/api/controllers` | – | `{connected[], settings, active_profile, profiles}` |
| POST | `/api/controllers` | `{action:"update", active_profile?, swap_ab_xy?, keyboard_bindings?:{action:key}, gamepad_bindings?:{action:"btn index"}, deadzone?, vibration_enabled?}` | `{settings, synced}` |
| POST | `/api/controllers` | `{action:"vibrate", port}` / `{action:"sync"}` / `{action:"reset_profile"}` | `{message}` |
| GET | `/api/settings` | – | `{settings, available_gpus[], available_backends[]}` |
| POST | `/api/settings` | `{graphics?:{}, performance_audio?:{}, controllers_advanced?:{}, search_sources?:{}}` (sections partielles) | `{settings, synced}` |
| POST | `/api/settings/reset` | – | `{settings}` |
| GET | `/api/engines` | – | `{system, consoles[]}` |
| POST | `/api/engines` | `{console_id}` ou `{console_id:"all"}` | installe le moteur |
| POST | `/api/engines/open` | `{console_id}` | ouvre l'interface native (retroarch.exe / Dolphin.exe / Ryujinx.exe) |
| POST | `/api/engines/test` | `{console_id}` | lance le jeu de test de la console (`{ok, message, engine}`) |
| POST | `/api/open_external` | `{url}` | ouvre l'URL dans le navigateur par défaut |
| POST | `/api/open_folder` | `{kind:"roms"|"emulators"|"downloads", console_id?}` | ouvre l'explorateur |
| GET | `/api/cover_svg` | `title, console, accent` | image SVG de pochette de secours |
| POST | `/api/tutorial` | `{tutorial_seen}` | – |

### Actions de manette (remapping)
Actions : `up, down, left, right, a, b, x, y, l1, r1, l2, r2, l3, r3, start, select`.
- `keyboard_bindings` : noms de touches au format RetroArch (`up`, `down`, `left`, `right`, `a`..`z`, `num0`..`num9`, `enter`, `space`, `rshift`, `lshift`, `rctrl`, `ctrl`, `alt`, `tab`, `backspace`, `escape`, `f1`..`f12`, `keypad0`..`keypad9`).
- `gamepad_bindings` : valeurs au format RetroArch / XInput :
  - boutons : `"0"`=A/Croix, `"1"`=B/Rond, `"2"`=X/Carré, `"3"`=Y/Triangle, `"4"`=LB/L1, `"5"`=RB/R1, `"6"`=Back/Select, `"7"`=Start, `"8"`=L3, `"9"`=R3
  - croix directionnelle : `"h0up"`, `"h0down"`, `"h0left"`, `"h0right"`
  - gâchettes analogiques : `"+4"` (LT/L2), `"+5"` (RT/R2)
  - Conversion depuis l'API Gamepad du navigateur (mapping "standard") : 0→"0", 1→"1", 2→"2", 3→"3", 4→"4", 5→"5", 6→"+4", 7→"+5", 8→"6", 9→"7", 10→"8", 11→"9", 12→"h0up", 13→"h0down", 14→"h0left", 15→"h0right".
- `profiles` (GET /api/controllers) : dict `{profile_id: {id, name, description, swap_ab_xy, deadzone, vibration_enabled, keyboard_bindings, gamepad_bindings}}` ; `settings.active_profile` = id du profil actif.

### Objet `settings` (global_settings.json)
Voir `backend/settings_manager.py` `DEFAULT_GLOBAL_SETTINGS` : sections `graphics`, `performance_audio`, `controllers_advanced` (dont `hotkeys`), `search_sources`.
