"""
Curated Multi-Console Game Catalog & Archive.org Collection Index for OmniConsole.
Includes comprehensive Mario titles across NES, SNES, GBA, N64, Wii/GameCube, Switch,
as well as iconic classics on Amstrad CPC, Commodore Amiga, Sega Mega Drive, and PlayStation 1.
"""

from typing import List, Dict, Any

# Archive.org verified ROM collection identifiers for live dynamic search
ARCHIVE_COLLECTIONS_BY_CONSOLE = {
    "nes": ("roms-bestset-nintendo-entertainment-system", "Nintendo - Nintendo Entertainment System"),
    "snes": ("roms-bestset-super-nintendo-entertainment-system", "Nintendo - Super Nintendo Entertainment System"),
    "gba": ("roms-bestset-nintendo-game-boy-advance", "Nintendo - Game Boy Advance"),
    "n64": ("roms-bestset-nintendo-64", "Nintendo - Nintendo 64"),
    "megadrive": ("roms-bestset-sega-megadrive", "Sega - Mega Drive - Genesis"),
    "amstrad_cpc": ("ACPC-Arquivista", "Amstrad - CPC"),
    "amiga": ("commodore-amiga-floppy-disk-images", "Commodore - Amiga"),
    "ps1": ("tekken-usa", "Sony - PlayStation"),
    "wii": ("Wii_ISO", "Nintendo - Wii"),
    "nds": ("nds-collection", "Nintendo - Nintendo DS"),
    "3ds": ("3ds-decrypted-roms321com", "Nintendo - Nintendo 3DS"),
    "atari2600": ("atari-2600-roms-ultra", "Atari - 2600"),
    "arcade": ("neo-geo-aes-romset", "SNK - Neo Geo"),
    "dreamcast": ("DreamcastSelfBoot", "Sega - Dreamcast"),
    "psp": ("psp-chd-zstd-redump-part1", "Sony - PlayStation Portable"),
}

# Verified comprehensive Nintendo Wii archive collections (3,850+ titles across Redump sets + top ISOs)
WII_ARCHIVE_COLLECTIONS = [
    ("Wii_ISO", "Nintendo - Wii", "iso"),
    ("Wii-Redump-2024-Individual-Games-Part1", "Nintendo - Wii", "rvz"),
    ("Wii-Redump-2024-Individual-Games-Part2", "Nintendo - Wii", "rvz"),
    ("Wii-Redump-2024-Individual-Games-Part3", "Nintendo - Wii", "rvz"),
    ("Wii-Redump-2024-Individual-Games-Part4", "Nintendo - Wii", "rvz"),
    ("Wii-Redump-2024-Individual-Games-Part5", "Nintendo - Wii", "rvz"),
    ("Wii-Redump-2024-Individual-Games-Part6", "Nintendo - Wii", "rvz"),
]

# Standalone verified open Wii archive items (direct HTTPS without login)
WII_STANDALONE_ARCHIVE_ITEMS = [
    {
        "identifier": "rmgr-01",
        "title": "Super Mario Galaxy",
        "filename": "RMGR01.wbfs",
        "size_bytes": 3682598912,
        "release_year": 2007,
        "developer": "Nintendo EAD Tokyo",
        "genre": "Plateforme 3D / Gravité",
        "cover_name": "Super Mario Galaxy (Europe) (En,Fr,De,Es,It)",
    },
    {
        "identifier": "mario-kart_202107",
        "title": "Mario Kart Wii",
        "filename": "Mario Kart Wii.wbfs",
        "size_bytes": 2992635904,
        "release_year": 2008,
        "developer": "Nintendo EAD",
        "genre": "Course Arcade",
        "cover_name": "Mario Kart Wii (Europe) (En,Fr,De,Es,It)",
    },
    {
        "identifier": "super-smash-bros-brawl-wbfs-rom",
        "title": "Super Smash Bros. Brawl",
        "filename": "Super Smash Bros Brawl.zip",
        "size_bytes": 2503278592,
        "release_year": 2008,
        "developer": "Ad hoc Development / Sora Ltd.",
        "genre": "Combat / Multijoueur",
        "cover_name": "Super Smash Bros. Brawl (Europe) (En,Fr,De,Es,It)",
    },
    {
        "identifier": "sp2p01",
        "title": "Wii Sports + Wii Sports Resort",
        "filename": "SP2P01.wbfs",
        "size_bytes": 1549803520,
        "release_year": 2009,
        "developer": "Nintendo EAD",
        "genre": "Sport / Party-Game",
        "cover_name": "Wii Sports + Wii Sports Resort (Europe)",
    },
    {
        "identifier": "nsmbwwbfs",
        "title": "Newer Super Mario Bros. Wii",
        "filename": "SMNP03.wbfs",
        "size_bytes": 910163968,
        "release_year": 2013,
        "developer": "Newer Team / Nintendo",
        "genre": "Plateforme 2D",
        "cover_name": "New Super Mario Bros. Wii (Europe) (En,Fr,De,Es,It)",
    },
    {
        "identifier": "supermarioallstarswii",
        "title": "Super Mario All-Stars (Wii 25th Anniversary)",
        "filename": "Super Mario All-Stars.wbfs",
        "size_bytes": 18874368,
        "release_year": 2010,
        "developer": "Nintendo EAD",
        "genre": "Plateforme Compilation",
        "cover_name": "Super Mario All-Stars - 25th Anniversary Edition (Europe)",
    },
    {
        "identifier": "kirbys-adventure-wii-europe-en-fr-de-es-it",
        "title": "Kirby's Adventure Wii",
        "filename": "Kirby's Adventure Wii (Europe) (En,Fr,De,Es,It).zip",
        "size_bytes": 598544384,
        "release_year": 2011,
        "developer": "HAL Laboratory",
        "genre": "Plateforme 2D",
        "cover_name": "Kirby's Adventure Wii (Europe)",
    },
    {
        "identifier": "wii-play-europe-rev-1",
        "title": "Wii Play",
        "filename": "Wii Play (Europe) (En,Fr,De,Es,It) (Rev 1).wbfs",
        "size_bytes": 109051904,
        "release_year": 2006,
        "developer": "Nintendo EAD",
        "genre": "Mini-jeux Arcade",
        "cover_name": "Wii Play (Europe) (En,Fr,De,Es,It) (Rev 1)",
    },
]

CURATED_GAMES: List[Dict[str, Any]] = [
    # ======================= SAGA MARIO (MULTI-CONSOLES) =======================
    {
        "id": "nes_super_mario_bros",
        "title": "Super Mario Bros.",
        "console_id": "nes",
        "console_name": "NES",
        "release_year": 1985,
        "developer": "Nintendo EAD (Shigeru Miyamoto)",
        "genre": "Plateforme",
        "players": "1 - 2 Joueurs",
        "rating": "9.8/10",
        "file_size_label": "40 Ko",
        "cover_url": "https://thumbnails.libretro.com/Nintendo%20-%20Nintendo%20Entertainment%20System/Named_Boxarts/Super%20Mario%20Bros.%20%28World%29.png",
        "download_url": "https://archive.org/download/roms-bestset-nintendo-entertainment-system/Super%20Mario%20Bros.%20%28World%29.zip",
        "filename": "Super Mario Bros. (World).zip",
        "summary": "Le jeu de plateforme légendaire qui a révolutionné l'histoire du jeu vidéo sur NES.",
        "description": (
            "Incarnez Mario (ou Luigi en mode 2 joueurs) à travers les 8 mondes du Royaume Champignon pour "
            "sauver la Princesse Toadstool des griffes du roi Bowser. Ce chef-d'œuvre de Shigeru Miyamoto "
            "tourne à 60 FPS constants sur absolument tous les PC et prend en charge toutes les manettes."
        ),
        "supported_controllers": [
            "Manette Xbox (One / Series / 360)",
            "Manette PlayStation (DualShock 4 / DualSense)",
            "Manette Nintendo Switch Pro / Joy-Con",
            "Manette USB Générique & Clavier PC",
        ],
    },
    {
        "id": "nes_super_mario_bros_3",
        "title": "Super Mario Bros. 3",
        "console_id": "nes",
        "console_name": "NES",
        "release_year": 1988,
        "developer": "Nintendo R&D4",
        "genre": "Plateforme / Aventure",
        "players": "1 - 2 Joueurs",
        "rating": "9.9/10",
        "file_size_label": "230 Ko",
        "cover_url": "https://thumbnails.libretro.com/Nintendo%20-%20Nintendo%20Entertainment%20System/Named_Boxarts/Super%20Mario%20Bros.%203%20%28USA%29.png",
        "download_url": "https://archive.org/download/roms-bestset-nintendo-entertainment-system/Super%20Mario%20Bros.%203%20%28USA%29%20%28Rev%20A%29.zip",
        "filename": "Super Mario Bros. 3 (USA) (Rev A).zip",
        "summary": "L'apogée de la NES : carte du monde interactive, costume Tanooki et 8 mondes géants.",
        "description": (
            "Considéré comme l'un des meilleurs jeux de tous les temps, Super Mario Bros. 3 introduit la "
            "Super Feuille pour voler, le costume de Grenouille, le costume Tanooki et des cartes du monde "
            "remplies de secrets et de bateaux volants gardés par les Koopalings."
        ),
        "supported_controllers": [
            "Manette Xbox (One / Series / 360)",
            "Manette PlayStation (DualShock 4 / DualSense)",
            "Manette Nintendo Switch Pro / Joy-Con",
            "Clavier PC",
        ],
    },
    {
        "id": "snes_super_mario_world",
        "title": "Super Mario World",
        "console_id": "snes",
        "console_name": "Super Nintendo",
        "release_year": 1990,
        "developer": "Nintendo EAD",
        "genre": "Plateforme",
        "players": "1 - 2 Joueurs",
        "rating": "10/10",
        "file_size_label": "512 Ko",
        "cover_url": "https://thumbnails.libretro.com/Nintendo%20-%20Super%20Nintendo%20Entertainment%20System/Named_Boxarts/Super%20Mario%20World%20%28USA%29.png",
        "download_url": "https://archive.org/download/super-mario-world-usa_202406/Super%20Mario%20World%20%28USA%29.sfc",
        "filename": "Super Mario World (USA).sfc",
        "summary": "Le joyau 16-bit de la Super Nintendo marquant la première apparition de Yoshi !",
        "description": (
            "Explorez Dinosaur Land avec Mario, Luigi et leur nouveau compagnon Yoshi ! Grâce à la plume "
            "Cape et aux différents Yoshis colorés, découvrez 96 sorties secrètes, la Star Road et les "
            "châteaux de Bowser dans une réalisation 16-bit d'une fluidité exemplaire."
        ),
        "supported_controllers": [
            "Manette Xbox / PlayStation / Switch Pro",
            "Manette SNES USB / 8BitDo",
            "Clavier PC",
        ],
    },
    {
        "id": "snes_super_mario_kart",
        "title": "Super Mario Kart",
        "console_id": "snes",
        "console_name": "Super Nintendo",
        "release_year": 1992,
        "developer": "Nintendo EAD",
        "genre": "Course Arcade (Mode 7)",
        "players": "1 - 2 Joueurs",
        "rating": "9.5/10",
        "file_size_label": "380 Ko",
        "cover_url": "https://thumbnails.libretro.com/Nintendo%20-%20Super%20Nintendo%20Entertainment%20System/Named_Boxarts/Super%20Mario%20Kart%20%28USA%29.png",
        "download_url": "https://archive.org/download/roms-bestset-super-nintendo-entertainment-system/Super%20Mario%20Kart%20%28USA%29.zip",
        "filename": "Super Mario Kart (USA).zip",
        "summary": "Le fondateur de la série Mario Kart en Mode 7 avec 8 pilotes et le mode Bataille.",
        "description": (
            "Choisissez parmi Mario, Luigi, Peach, Yoshi, Bowser, Donkey Kong Jr., Koopa Troopa et Toad "
            "dans 4 coupes survoltées ! Maîtrisez le dérapage, lancez des carapaces rouges et affrontez "
            "vos amis dans le célèbre Battle Mode aux ballons."
        ),
        "supported_controllers": [
            "Manette Xbox / PlayStation / Switch Pro",
            "Manette USB Générique & Clavier PC",
        ],
    },
    {
        "id": "snes_super_mario_all_stars",
        "title": "Super Mario All-Stars",
        "console_id": "snes",
        "console_name": "Super Nintendo",
        "release_year": 1993,
        "developer": "Nintendo EAD",
        "genre": "Compilation Plateforme",
        "players": "1 - 2 Joueurs",
        "rating": "9.7/10",
        "file_size_label": "1.2 Mo",
        "cover_url": "https://thumbnails.libretro.com/Nintendo%20-%20Super%20Nintendo%20Entertainment%20System/Named_Boxarts/Super%20Mario%20All-Stars%20%28USA%29.png",
        "download_url": "https://archive.org/download/roms-bestset-super-nintendo-entertainment-system/Super%20Mario%20All-Stars%20%28USA%29.zip",
        "filename": "Super Mario All-Stars (USA).zip",
        "summary": "Les 4 premiers épisodes de Super Mario entièrement refaits en graphismes 16-bit SNES.",
        "description": (
            "Retrouvez Super Mario Bros., Super Mario Bros.: The Lost Levels, Super Mario Bros. 2 et "
            "Super Mario Bros. 3 entièrement remasterisés en 16-bit avec musiques orchestrées et sauvegarde intégrée."
        ),
        "supported_controllers": [
            "Manette Xbox / PlayStation / Switch Pro",
            "Manette USB Générique & Clavier PC",
        ],
    },
    {
        "id": "gba_super_mario_advance",
        "title": "Super Mario Advance",
        "console_id": "gba",
        "console_name": "Game Boy Advance",
        "release_year": 2001,
        "developer": "Nintendo R&D2",
        "genre": "Plateforme",
        "players": "1 - 4 Joueurs",
        "rating": "9.2/10",
        "file_size_label": "3.1 Mo",
        "cover_url": "https://thumbnails.libretro.com/Nintendo%20-%20Game%20Boy%20Advance/Named_Boxarts/Super%20Mario%20Advance%20%28USA%2C%20Europe%29.png",
        "download_url": "https://archive.org/download/roms-bestset-nintendo-game-boy-advance/Super%20Mario%20Advance%20%28USA%2C%20Europe%29.zip",
        "filename": "Super Mario Advance (USA, Europe).zip",
        "summary": "Version enrichie sur Game Boy Advance avec voix digitalisées, boss géants et Mario Bros. Arcade.",
        "description": (
            "Incarnez Mario, Luigi, Peach ou Toad avec leurs capacités uniques (saut plané de Peach, force de Toad, "
            "saut vertical de Luigi) dans cette édition 32-bit ultra-colorée et très légère pour votre PC."
        ),
        "supported_controllers": [
            "Manette Xbox / PlayStation / Switch Pro",
            "Clavier PC",
        ],
    },
    {
        "id": "gba_mario_kart_super_circuit",
        "title": "Mario Kart: Super Circuit",
        "console_id": "gba",
        "console_name": "Game Boy Advance",
        "release_year": 2001,
        "developer": "Intelligent Systems",
        "genre": "Course Arcade",
        "players": "1 - 4 Joueurs",
        "rating": "9.3/10",
        "file_size_label": "2.4 Mo",
        "cover_url": "https://thumbnails.libretro.com/Nintendo%20-%20Game%20Boy%20Advance/Named_Boxarts/Mario%20Kart%20-%20Super%20Circuit%20%28USA%29.png",
        "download_url": "https://archive.org/download/roms-bestset-nintendo-game-boy-advance/Mario%20Kart%20-%20Super%20Circuit%20%28USA%29.zip",
        "filename": "Mario Kart - Super Circuit (USA).zip",
        "summary": "40 circuits au total (20 inédits + les 20 circuits de Super Mario Kart déblocables) !",
        "description": (
            "Un concentré de fun et de vitesse en 32-bit sur Game Boy Advance. Très peu gourmand en ressources, "
            "il tourne à la perfection sur n'importe quel ordinateur portable."
        ),
        "supported_controllers": [
            "Manette Xbox / PlayStation / Switch Pro",
            "Clavier PC",
        ],
    },
    {
        "id": "n64_super_mario_64",
        "title": "Super Mario 64",
        "console_id": "n64",
        "console_name": "Nintendo 64",
        "release_year": 1996,
        "developer": "Nintendo EAD",
        "genre": "Plateforme 3D",
        "players": "1 Joueur",
        "rating": "10/10",
        "file_size_label": "6.1 Mo",
        "cover_url": "https://thumbnails.libretro.com/Nintendo%20-%20Nintendo%2064/Named_Boxarts/Super%20Mario%2064%20%28USA%29.png",
        "download_url": "https://archive.org/download/roms-bestset-nintendo-64/Super%20Mario%2064%20%28USA%29.n64.zip",
        "filename": "Super Mario 64 (USA).n64.zip",
        "summary": "La révolution de la plateforme 3D : explorez le château de Peach et récoltez les 120 étoiles !",
        "description": (
            "Sautez à travers les tableaux magiques du château de la Princesse Peach dans le titre qui a défini "
            "les contrôles caméra et stick analogique 3D modernes. Triple saut, saut mural, casquette ailée : "
            "un monument incontournable."
        ),
        "supported_controllers": [
            "Manette avec Stick Analogique (Xbox, PlayStation, Switch Pro)",
            "Clavier PC (Stick analogique émulé sur flèches)",
        ],
    },
    {
        "id": "n64_mario_kart_64",
        "title": "Mario Kart 64",
        "console_id": "n64",
        "console_name": "Nintendo 64",
        "release_year": 1996,
        "developer": "Nintendo EAD",
        "genre": "Course 3D",
        "players": "1 - 4 Joueurs",
        "rating": "9.6/10",
        "file_size_label": "8.4 Mo",
        "cover_url": "https://thumbnails.libretro.com/Nintendo%20-%20Nintendo%2064/Named_Boxarts/Mario%20Kart%2064%20%28USA%29.png",
        "download_url": "https://archive.org/download/roms-bestset-nintendo-64/Mario%20Kart%2064%20%28USA%29.n64.zip",
        "filename": "Mario Kart 64 (USA).n64.zip",
        "summary": "Le passage mythique de Mario Kart à la 3D avec la carapace bleue à épines et la Route Arc-en-Ciel.",
        "description": (
            "Affrontez Wario, Donkey Kong, Mario et Bowser sur 16 circuits en 3D intégrale (Autodrome Royal, "
            "Montagne Choco, Château de Bowser, Route Arc-en-Ciel). Utilisez le stick analogique pour maîtriser le mini-turbo !"
        ),
        "supported_controllers": [
            "Manette Xbox / PlayStation / Switch Pro (Stick Analogique)",
            "Clavier PC",
        ],
    },
    {
        "id": "wii_smw_war",
        "title": "Super Mario War Wii",
        "console_id": "wii",
        "console_name": "Wii / GameCube",
        "release_year": 2009,
        "developer": "72dpi Army / Florian Bitterlich",
        "genre": "Plateforme / Combat Multijoueur",
        "players": "1 - 4 Joueurs",
        "rating": "9.6/10",
        "file_size_label": "3.6 Mo",
        "cover_url": "https://hbb1.oscwii.org/api/contents/smw-wiigii/icon.png",
        "download_url": "https://hbb1.oscwii.org/api/contents/smw-wiigii/smw-wiigii.zip",
        "filename": "smw-wiigii.zip",
        "summary": "Jeu de plateforme / affrontement multijoueur Mario culte pour Nintendo Wii avec des dizaines d'arènes.",
        "description": (
            "Affrontez jusqu'à 4 joueurs ou bots dans l'univers de Super Mario sur le moteur Dolphin Portable. "
            "Sautez sur la tête de vos adversaires, ramassez des carapaces et des power-ups. "
            "Fonctionne immédiatement sur Dolphin avec vos manettes préconfigurées."
        ),
        "supported_controllers": [
            "Manette Xbox / PlayStation / Switch (Pad GC / Wiimote émulée)",
            "Wiimote Originale Bluetooth",
            "Clavier PC",
        ],
    },
    {
        "id": "gc_super_mario_sunshine",
        "title": "Super Mario Sunshine (GameCube / Dolphin)",
        "console_id": "wii",
        "console_name": "Wii / GameCube",
        "release_year": 2002,
        "developer": "Nintendo EAD",
        "genre": "Plateforme 3D",
        "players": "1 Joueur",
        "rating": "9.8/10",
        "file_size_label": "1.28 Go (.zip)",
        "cover_url": "https://thumbnails.libretro.com/Nintendo%20-%20GameCube/Named_Boxarts/Super%20Mario%20Sunshine%20%28USA%29.png",
        "download_url": "https://archive.org/download/super-mario-sunshine-europe-en-fr-de-es-it/Super%20Mario%20Sunshine%20%28Europe%29%20%28En%2CFr%2CDe%2CEs%2CIt%29.zip",
        "filename": "Super Mario Sunshine (Europe) (En,Fr,De,Es,It).zip",
        "summary": "Mario sur l'Île Delphino avec J.E.T. en résolution HD optimisée sur Dolphin.",
        "description": (
            "Explorez l'Île Delphino avec le pistolet à eau J.E.T., nettoyez les graffitis de Bowser Jr. "
            "et collectez les Soleils. Format RVZ compressé sans perte, prêt à lancer dans Dolphin Portable."
        ),
        "supported_controllers": [
            "Manette Xbox / PlayStation / Switch Pro (GCPad préconfiguré)",
            "Clavier PC",
        ],
    },
    {
        "id": "wii_super_mario_galaxy",
        "title": "Super Mario Galaxy",
        "console_id": "wii",
        "console_name": "Wii / GameCube",
        "release_year": 2007,
        "developer": "Nintendo EAD Tokyo (Yoshiaki Koizumi)",
        "genre": "Plateforme 3D / Gravité",
        "players": "1 - 2 Joueurs",
        "rating": "9.9/10",
        "file_size_label": "3.5 Go (.wbfs)",
        "cover_url": "https://thumbnails.libretro.com/Nintendo%20-%20Wii/Named_Boxarts/Super%20Mario%20Galaxy%20%28Europe%29%20%28En%2CFr%2CDe%2CEs%2CIt%29.png",
        "download_url": "https://archive.org/download/rmgr-01/RMGR01.wbfs",
        "filename": "Super Mario Galaxy.wbfs",
        "summary": "Le chef-d'œuvre cosmique de Mario explorant des planètes aux physiques gravitationnelles uniques !",
        "description": (
            "Parcourez les galaxies à travers le cosmos pour sauver la Princesse Peach des griffes de Bowser "
            "avec l'aide d'Harmonie et des Lumas. Ce chef-d'œuvre légendaire tourne à 60 FPS constants en haute résolution "
            "dans le moteur Dolphin Portable avec vos manettes préconfigurées."
        ),
        "supported_controllers": [
            "Manette Xbox / PlayStation / Switch (Wiimote émulée sur Stick droit / Gâchettes)",
            "Wiimote Originale Bluetooth",
            "Clavier PC",
        ],
    },
    {
        "id": "wii_mario_kart_wii",
        "title": "Mario Kart Wii",
        "console_id": "wii",
        "console_name": "Wii / GameCube",
        "release_year": 2008,
        "developer": "Nintendo EAD",
        "genre": "Course Arcade",
        "players": "1 - 4 Joueurs",
        "rating": "9.8/10",
        "file_size_label": "2.9 Go (.wbfs)",
        "cover_url": "https://thumbnails.libretro.com/Nintendo%20-%20Wii/Named_Boxarts/Mario%20Kart%20Wii%20%28Europe%29%20%28En%2CFr%2CDe%2CEs%2CIt%29.png",
        "download_url": "https://archive.org/download/mario-kart_202107/Mario%20Kart%20Wii.wbfs",
        "filename": "Mario Kart Wii.wbfs",
        "summary": "32 circuits cultes, motos, figures acrobatiques et fun immédiat jusqu'à 4 joueurs !",
        "description": (
            "Pilotez karts et motos sur des circuits mythiques (Gorge Champignon, Bois Vermeil, Route Arc-en-Ciel). "
            "Prêt à lancer immédiatement dans Dolphin Portable avec contrôles GameCube et Wiimote intégrés."
        ),
        "supported_controllers": [
            "Manette Xbox / PlayStation / Switch (Manette GameCube / Wiimote émulée)",
            "Wiimote Originale Bluetooth",
            "Clavier PC",
        ],
    },
    {
        "id": "wii_super_smash_bros_brawl",
        "title": "Super Smash Bros. Brawl",
        "console_id": "wii",
        "console_name": "Wii / GameCube",
        "release_year": 2008,
        "developer": "Sora Ltd. / Game Arts (Masahiro Sakurai)",
        "genre": "Combat / Multijoueur",
        "players": "1 - 4 Joueurs",
        "rating": "9.7/10",
        "file_size_label": "2.4 Go (.zip)",
        "cover_url": "https://thumbnails.libretro.com/Nintendo%20-%20Wii/Named_Boxarts/Super%20Smash%20Bros.%20Brawl%20%28Europe%29%20%28En%2CFr%2CDe%2CEs%2CIt%29.png",
        "download_url": "https://archive.org/download/super-smash-bros-brawl-wbfs-rom/Super%20Smash%20Bros%20Brawl.zip",
        "filename": "Super Smash Bros Brawl.zip",
        "summary": "39 combattants dont Sonic et Snake, le mode aventure L'Émissaire Subspatial et le Final Smash !",
        "description": (
            "Le mastodonte du combat Nintendo sur Wii. Affrontez vos amis ou plongez dans l'immense campagne "
            "solo avec cinématiques orchestrées. Entièrement compatible manettes Xbox, PS et Switch."
        ),
        "supported_controllers": [
            "Manette Xbox / PlayStation / Switch (Mappage Pad GameCube recommandé)",
            "Wiimote Originale",
            "Clavier PC",
        ],
    },
    {
        "id": "wii_wii_sports_resort",
        "title": "Wii Sports + Wii Sports Resort",
        "console_id": "wii",
        "console_name": "Wii / GameCube",
        "release_year": 2009,
        "developer": "Nintendo EAD",
        "genre": "Sport / Party-Game",
        "players": "1 - 4 Joueurs",
        "rating": "9.6/10",
        "file_size_label": "1.5 Go (.wbfs)",
        "cover_url": "https://thumbnails.libretro.com/Nintendo%20-%20Wii/Named_Boxarts/Wii%20Sports%20%2B%20Wii%20Sports%20Resort%20%28Europe%29.png",
        "download_url": "https://archive.org/download/sp2p01/SP2P01.wbfs",
        "filename": "Wii Sports Resort.wbfs",
        "summary": "La compilation ultime regroupant Tennis, Bowling, Golf, Sabre, Tir à l'arc, Wakeboard sur l'Île Wuhu !",
        "description": (
            "Découvrez ou revivez les sensations légendaires de la Wii sur l'Île Wuhu. Profitez de tous les sports "
            "cultes directement émulés dans Dolphin Portable."
        ),
        "supported_controllers": [
            "Manette avec Gyroscope / Wiimote Originale Bluetooth",
            "Manette Xbox / PlayStation (Pointeur et mouvements émulés sur les sticks)",
            "Souris + Clavier PC",
        ],
    },
    {
        "id": "wii_newer_super_mario_bros",
        "title": "Newer Super Mario Bros. Wii",
        "console_id": "wii",
        "console_name": "Wii / GameCube",
        "release_year": 2013,
        "developer": "Newer Team / Nintendo",
        "genre": "Plateforme 2D",
        "players": "1 - 4 Joueurs",
        "rating": "9.8/10",
        "file_size_label": "868 Mo (.wbfs)",
        "cover_url": "https://thumbnails.libretro.com/Nintendo%20-%20Wii/Named_Boxarts/New%20Super%20Mario%20Bros.%20Wii%20%28Europe%29%20%28En%2CFr%2CDe%2CEs%2CIt%29.png",
        "download_url": "https://archive.org/download/nsmbwwbfs/SMNP03.wbfs",
        "filename": "Newer Super Mario Bros Wii.wbfs",
        "summary": "128 niveaux inédits, nouvelles musiques, boss originaux et nouveaux costumes Mario !",
        "description": (
            "La suite non officielle ultime de New Super Mario Bros. Wii conçue avec passion par la communauté. "
            "8 mondes complets plus 4 mondes secrets, entièrement jouable de 1 à 4 simultanément."
        ),
        "supported_controllers": [
            "Manette Xbox / PlayStation / Switch Pro",
            "Wiimote Originale Bluetooth",
            "Clavier PC",
        ],
    },
    {
        "id": "wii_super_mario_all_stars",
        "title": "Super Mario All-Stars (Wii 25th Anniversary)",
        "console_id": "wii",
        "console_name": "Wii / GameCube",
        "release_year": 2010,
        "developer": "Nintendo EAD",
        "genre": "Plateforme Compilation",
        "players": "1 - 2 Joueurs",
        "rating": "9.5/10",
        "file_size_label": "18 Mo (.wbfs)",
        "cover_url": "https://thumbnails.libretro.com/Nintendo%20-%20Wii/Named_Boxarts/Super%20Mario%20All-Stars%20-%2025th%20Anniversary%20Edition%20%28Europe%29.png",
        "download_url": "https://archive.org/download/supermarioallstarswii/Super%20Mario%20All-Stars.wbfs",
        "filename": "Super Mario All-Stars Wii.wbfs",
        "summary": "L'édition collector 25e anniversaire de Super Mario sur Wii au format WBFS ultra-léger !",
        "description": (
            "Comprend Super Mario Bros. 1, 2, 3 et The Lost Levels remasterisés avec prise en charge intégrale "
            "des manettes modernes dans Dolphin Portable."
        ),
        "supported_controllers": [
            "Manette Xbox / PlayStation / Switch",
            "Clavier PC",
        ],
    },
    {
        "id": "switch_mario_bros_nx",
        "title": "MarioBrosNX (Nintendo Switch)",
        "console_id": "switch",
        "console_name": "Nintendo Switch",
        "release_year": 2020,
        "developer": "Superfamicon / Switch Homebrew Community",
        "genre": "Arcade / Plateforme HD",
        "players": "1 - 2 Joueurs",
        "rating": "9.5/10",
        "file_size_label": "1.8 Mo (.nro)",
        "cover_url": "https://thumbnails.libretro.com/Nintendo%20-%20Nintendo%20Entertainment%20System/Named_Boxarts/Mario%20Bros.%20%28World%29.png",
        "download_url": "https://switch.cdn.fortheusers.org/zips/MarioBrosNX.zip",
        "filename": "MarioBrosNX.zip",
        "summary": "Portage Switch natif (.nro) de Mario Bros avec graphismes haute définition et 60 FPS sur Ryujinx.",
        "description": (
            "Testez immédiatement le moteur Nintendo Switch Ryujinx Portable avec ce portage arcade natif. "
            "Le fichier s'installe directement dans la carte SD virtuelle de Ryujinx avec contrôles Pro Controller configurés."
        ),
        "supported_controllers": [
            "Nintendo Switch Pro Controller / Joy-Con",
            "Manette Xbox Series / One & DualSense (Mappage automatique)",
            "Clavier PC",
        ],
    },
    {
        "id": "switch_sonic_cd",
        "title": "Sonic CD (Switch Port)",
        "console_id": "switch",
        "console_name": "Nintendo Switch",
        "release_year": 2021,
        "developer": "Rubberduckycooly / Christian Whitehead",
        "genre": "Plateforme Haute Vitesse",
        "players": "1 Joueur",
        "rating": "9.6/10",
        "file_size_label": "4.2 Mo (.nro)",
        "cover_url": "https://thumbnails.libretro.com/Sega%20-%20Mega%20Drive%20-%20Genesis/Named_Boxarts/Sonic%20The%20Hedgehog%20%28USA%2C%20Europe%29.png",
        "download_url": "https://switch.cdn.fortheusers.org/zips/Sonic-CD.zip",
        "filename": "Sonic-CD.zip",
        "summary": "Le chef-d'œuvre de Sonic porté sur Nintendo Switch en 60 FPS plein écran natif.",
        "description": (
            "Voyagez dans le Passé, le Présent et le Futur de Little Planet avec Sonic et Amy Rose sur le moteur Ryujinx."
        ),
        "supported_controllers": [
            "Nintendo Switch Pro Controller / Joy-Con",
            "Manette Xbox / PlayStation",
            "Clavier PC",
        ],
    },

    # ======================= AMSTRAD CPC (464 / 6128) =======================
    {
        "id": "cpc_prince_of_persia",
        "title": "Prince of Persia (Amstrad CPC)",
        "console_id": "amstrad_cpc",
        "console_name": "Amstrad CPC",
        "release_year": 1990,
        "developer": "Jordan Mechner / Broderbund",
        "genre": "Action / Plateforme Cinématique",
        "players": "1 Joueur",
        "rating": "9.6/10",
        "file_size_label": "190 Ko (.dsk)",
        "cover_url": "https://thumbnails.libretro.com/Commodore%20-%20Amiga/Named_Boxarts/Prince%20of%20Persia%20%28Europe%29.png",
        "download_url": "https://archive.org/download/ACPC-Arquivista/Prince%20of%20Persia.dsk",
        "filename": "Prince of Persia.dsk",
        "summary": "La célèbre version Amstrad CPC 6128 avec animations rotoscopées fluides et lancement automatique.",
        "description": (
            "Vous disposez de 60 minutes pour vous échapper des cachots du Grand Vizir Jaffar et sauver la Princesse. "
            "Cette version disquette (.dsk) pour Amstrad CPC 6128 se lance automatiquement grâce au moteur Caprice32 préconfiguré !"
        ),
        "supported_controllers": [
            "Joystick Rétro / Manette Xbox, PlayStation, Switch (Port Joystick 1)",
            "Clavier Amstrad CPC émulé",
        ],
    },
    {
        "id": "cpc_rick_dangerous",
        "title": "Rick Dangerous (Amstrad CPC)",
        "console_id": "amstrad_cpc",
        "console_name": "Amstrad CPC",
        "release_year": 1989,
        "developer": "Core Design / Firebird",
        "genre": "Action / Plateforme",
        "players": "1 Joueur",
        "rating": "9.4/10",
        "file_size_label": "190 Ko (.dsk)",
        "cover_url": "https://thumbnails.libretro.com/Amstrad%20-%20CPC/Named_Boxarts/Arkanoid.png",
        "download_url": "https://archive.org/download/ACPC-Arquivista/Rick%20Dangerous.dsk",
        "filename": "Rick Dangerous.dsk",
        "summary": "L'Indiana Jones de l'Amstrad CPC ! Évitez les pièges avec votre bâton de dynamite et votre pistolet.",
        "description": (
            "Explorez le temple sud-américain, la pyramide d'Égypte et le château de Schwarzendumpf dans l'un "
            "des jeux les plus cultes de l'Amstrad CPC. Ultra-léger, il démarre instantanément sans taper de commande BASIC."
        ),
        "supported_controllers": [
            "Joystick / Manette Xbox, PlayStation, Switch",
            "Clavier PC",
        ],
    },
    {
        "id": "cpc_sorcery_plus",
        "title": "Sorcery+ (Amstrad CPC)",
        "console_id": "amstrad_cpc",
        "console_name": "Amstrad CPC",
        "release_year": 1985,
        "developer": "Virgin Games / Gang of Five",
        "genre": "Action / Aventure",
        "players": "1 Joueur",
        "rating": "9.3/10",
        "file_size_label": "190 Ko (.dsk)",
        "cover_url": "https://thumbnails.libretro.com/Amstrad%20-%20CPC/Named_Boxarts/Barbarian%20-%20The%20Ultimate%20Warrior.png",
        "download_url": "https://archive.org/download/ACPC-Arquivista/Sorcery%20Plus.dsk",
        "filename": "Sorcery Plus.dsk",
        "summary": "Le jeu d'aventure magique emblématique des publicités Amstrad CPC des années 80.",
        "description": (
            "Incarnez un jeune apprenti sorcier volant de salle en salle pour délivrer ses 8 confrères retenus "
            "prisonniers par le Nécromancien. Un monument absolu de l'histoire de l'Amstrad CPC en France."
        ),
        "supported_controllers": [
            "Joystick / Manette Xbox, PlayStation, Switch",
            "Clavier PC",
        ],
    },
    {
        "id": "cpc_gryzor",
        "title": "Gryzor / Contra (Amstrad CPC)",
        "console_id": "amstrad_cpc",
        "console_name": "Amstrad CPC",
        "release_year": 1987,
        "developer": "Ocean Software / Konami",
        "genre": "Run and Gun / Arcade",
        "players": "1 - 2 Joueurs",
        "rating": "9.5/10",
        "file_size_label": "190 Ko (.dsk)",
        "cover_url": "https://thumbnails.libretro.com/Amstrad%20-%20CPC/Named_Boxarts/Fruity%20Frank.png",
        "download_url": "https://archive.org/download/ACPC-Arquivista/Gryzor.dsk",
        "filename": "Gryzor.dsk",
        "summary": "L'adaptation spectaculaire de Contra par Ocean Software sur Amstrad CPC.",
        "description": (
            "Considéré comme l'une des meilleures conversions d'arcade jamais réalisées sur Amstrad CPC, "
            "Gryzor affiche des graphismes Mode 0 flamboyants et une action frénétique à la manette."
        ),
        "supported_controllers": [
            "Joystick / Manette Xbox, PlayStation, Switch",
            "Clavier PC",
        ],
    },

    # ======================= COMMODORE AMIGA (500 / 1200) =======================
    {
        "id": "amiga_lemmings",
        "title": "All New World of Lemmings (Amiga)",
        "console_id": "amiga",
        "console_name": "Amiga",
        "release_year": 1991,
        "developer": "DMA Design / Psygnosis",
        "genre": "Réflexion / Stratégie",
        "players": "1 - 2 Joueurs",
        "rating": "9.7/10",
        "file_size_label": "650 Ko (.adz)",
        "cover_url": "https://thumbnails.libretro.com/Commodore%20-%20Amiga/Named_Boxarts/Lemmings%20%28Europe%29%20%28Amiga%20500%20Bundle%20-%20Cartoon%20Classics%29.png",
        "download_url": "https://archive.org/download/commodore-amiga-floppy-disk-images/disks-agadisks-aga/All%20New%20World%20Of%20Lemmings%20AGA/All%20New%20World%20Of%20Lemmings%20AGA_Disk1.adz",
        "filename": "All New World Of Lemmings AGA_Disk1.adz",
        "summary": "Sauvez les petits Lemmings aux cheveux verts dans ce classique immortel du Commodore Amiga !",
        "description": (
            "Assignez des rôles (Grimpeur, Parachutiste, Constructeur, Foreur, Bloqueur) à votre colonie de "
            "Lemmings pour les guider vers la sortie. Compatible à la fois Souris PC et Manette !"
        ),
        "supported_controllers": [
            "Souris + Clavier PC (Recommandé pour le curseur)",
            "Manette Xbox / PlayStation / Switch (Curseur sur Stick gauche)",
        ],
    },
    {
        "id": "amiga_turrican_2",
        "title": "Turrican II: The Final Fight (Amiga)",
        "console_id": "amiga",
        "console_name": "Amiga",
        "release_year": 1991,
        "developer": "Factor 5 / Rainbow Arts",
        "genre": "Action / Run & Gun",
        "players": "1 Joueur",
        "rating": "9.8/10",
        "file_size_label": "720 Ko (.adz)",
        "cover_url": "https://thumbnails.libretro.com/Commodore%20-%20Amiga/Named_Boxarts/Turrican.png",
        "download_url": "https://archive.org/download/commodore-amiga-floppy-disk-images/disks-multidisks-multi/Turrican%20II%20-%20The%20Final%20Fight/Turrican%20II%20-%20The%20Final%20Fight_Disk1.adz",
        "filename": "Turrican II - The Final Fight_Disk1.adz",
        "summary": "La vitrine technologique de l'Amiga avec la bande-son légendaire de Chris Huelsbeck !",
        "description": (
            "Niveaux gigantesques, armement dévastateur (rayon rebondissant, transformation en roue blindée, "
            "phases de shoot'em up) et musiques anthologiques : Turrican II est le roi de l'action sur Amiga 500."
        ),
        "supported_controllers": [
            "Manette Xbox / PlayStation / Switch (Bouton Saut préconfiguré)",
            "Joystick Rétro & Clavier PC",
        ],
    },
    {
        "id": "amiga_lotus_3",
        "title": "Lotus III: The Ultimate Challenge (Amiga)",
        "console_id": "amiga",
        "console_name": "Amiga",
        "release_year": 1992,
        "developer": "Magnetic Fields / Gremlin",
        "genre": "Course Arcade",
        "players": "1 - 2 Joueurs",
        "rating": "9.4/10",
        "file_size_label": "680 Ko (.adz)",
        "cover_url": "https://thumbnails.libretro.com/Commodore%20-%20Amiga/Named_Boxarts/Prince%20of%20Persia%20%28Europe%29.png",
        "download_url": "https://archive.org/download/commodore-amiga-floppy-disk-images/disks-multidisks-multi/Lotus%20III%20-%20The%20Ultimate%20Challenge/Lotus%20III%20-%20The%20Ultimate%20Challenge_Disk1.adz",
        "filename": "Lotus III - The Ultimate Challenge_Disk1.adz",
        "summary": "Course ultra-rapide sur Amiga avec générateur de circuits RECS et musiques électro cultes.",
        "description": (
            "Prenez le volant de la Lotus Esprit Turbo SE ou du concept-car Lotus M200 à travers tempêtes de neige, "
            "nuit, brouillard et autoroutes dans l'un des meilleurs jeux de course 16-bit."
        ),
        "supported_controllers": [
            "Manette Xbox / PlayStation / Switch",
            "Clavier PC",
        ],
    },

    # ======================= SEGA MEGA DRIVE & AUTRES CLASSIQUES =======================
    {
        "id": "md_sonic_1",
        "title": "Sonic the Hedgehog",
        "console_id": "megadrive",
        "console_name": "Mega Drive",
        "release_year": 1991,
        "developer": "Sonic Team / Sega",
        "genre": "Plateforme Haute Vitesse",
        "players": "1 Joueur",
        "rating": "9.6/10",
        "file_size_label": "360 Ko",
        "cover_url": "https://thumbnails.libretro.com/Sega%20-%20Mega%20Drive%20-%20Genesis/Named_Boxarts/Sonic%20The%20Hedgehog%20%28USA%2C%20Europe%29.png",
        "download_url": "https://archive.org/download/roms-bestset-sega-megadrive/Sonic%20the%20Hedgehog%20%28USA%2C%20Europe%29.zip",
        "filename": "Sonic the Hedgehog (USA, Europe).zip",
        "summary": "Foncez à travers Green Hill Zone contre le Dr. Robotnik sur Sega Mega Drive !",
        "description": (
            "La mascotte supersonique de Sega dans son aventure originale 16-bit. Loopings, anneaux d'or "
            "et Émeraudes du Chaos avec une fluidité totale sur tous les PC."
        ),
        "supported_controllers": [
            "Manette Xbox / PlayStation / Switch / Sega USB",
            "Clavier PC",
        ],
    },
    {
        "id": "md_streets_of_rage_2",
        "title": "Streets of Rage 2",
        "console_id": "megadrive",
        "console_name": "Mega Drive",
        "release_year": 1992,
        "developer": "Sega / Ancient (Yuzo Koshiro)",
        "genre": "Beat 'em All",
        "players": "1 - 2 Joueurs",
        "rating": "9.8/10",
        "file_size_label": "1.4 Mo",
        "cover_url": "https://thumbnails.libretro.com/Sega%20-%20Mega%20Drive%20-%20Genesis/Named_Boxarts/Streets%20of%20Rage%202%20%28USA%29.png",
        "download_url": "https://archive.org/download/roms-bestset-sega-megadrive/Streets%20of%20Rage%202%20%28USA%29.zip",
        "filename": "Streets of Rage 2 (USA).zip",
        "summary": "La référence absolue du Beat'em All 16-bit avec Axel, Blaze, Max et Skate.",
        "description": (
            "Affrontez le syndicat de Mr. X au rythme des compositions électroniques légendaires de Yuzo Koshiro. "
            "Jouable seul ou à deux manettes simultanément !"
        ),
        "supported_controllers": [
            "Manette Xbox / PlayStation / Switch (1 ou 2 joueurs)",
            "Clavier PC",
        ],
    },
    {
        "id": "snes_zelda_alttp",
        "title": "The Legend of Zelda: A Link to the Past",
        "console_id": "snes",
        "console_name": "Super Nintendo",
        "release_year": 1991,
        "developer": "Nintendo EAD",
        "genre": "Action / Aventure",
        "players": "1 Joueur",
        "rating": "10/10",
        "file_size_label": "680 Ko",
        "cover_url": "https://thumbnails.libretro.com/Nintendo%20-%20Super%20Nintendo%20Entertainment%20System/Named_Boxarts/Legend%20of%20Zelda%2C%20The%20-%20A%20Link%20to%20the%20Past%20%28USA%29.png",
        "download_url": "https://archive.org/download/roms-bestset-super-nintendo-entertainment-system/Legend%20of%20Zelda%2C%20The%20-%20A%20Link%20to%20the%20Past%20%28USA%29.zip",
        "filename": "Legend of Zelda, The - A Link to the Past (USA).zip",
        "summary": "Voyagez entre le Monde de la Lumière et le Monde des Ténèbres pour brandir l'Épée de Légende.",
        "description": (
            "Explorez des donjons ingénieux, trouvez le Grappin, les Bottes de Pégase et l'Épée Excalibur "
            "pour sauver la Princesse Zelda et vaincre Ganon."
        ),
        "supported_controllers": [
            "Manette Xbox / PlayStation / Switch Pro",
            "Clavier PC",
        ],
    },
    {
        "id": "ps1_adventures_of_lomax",
        "title": "The Adventures of Lomax",
        "console_id": "ps1",
        "console_name": "PlayStation 1",
        "release_year": 1996,
        "developer": "Psygnosis",
        "genre": "Plateforme 2D / Aventure",
        "players": "1 Joueur",
        "rating": "9.5/10",
        "file_size_label": "380 Mo (.chd)",
        "cover_url": "https://thumbnails.libretro.com/Sony%20-%20PlayStation/Named_Boxarts/Adventures%20of%20Lomax%2C%20The%20%28USA%29.png",
        "download_url": "https://archive.org/download/tekken-usa/Adventures%20of%20Lomax%2C%20The%20%28USA%29.chd",
        "filename": "Adventures of Lomax, The (USA).chd",
        "summary": "Merveille graphique 2D sur PS1 dans l'univers des Lemmings avec Lomax le chevalier.",
        "description": (
            "Considéré comme l'un des plus beaux jeux de plateforme 2D de la PlayStation 1. "
            "Tourne impeccablement sur PCSX-ReARMed / SwanStation sans nécessiter de BIOS externe."
        ),
        "supported_controllers": [
            "Manette PlayStation DualSense / DualShock 4",
            "Manette Xbox / Switch Pro & Clavier PC",
        ],
    },
    {
        "id": "ps1_crash_warped",
        "title": "Crash Bandicoot 3: Warped",
        "console_id": "ps1",
        "console_name": "PlayStation 1",
        "release_year": 1998,
        "developer": "Naughty Dog / Sony",
        "genre": "Plateforme 3D",
        "players": "1 Joueur",
        "rating": "9.8/10",
        "file_size_label": "102 Mo (.chd)",
        "cover_url": "https://thumbnails.libretro.com/Sony%20-%20PlayStation/Named_Boxarts/Crash%20Bandicoot%20-%20Warped%20%28USA%29.png",
        "download_url": "https://archive.org/download/tekken-usa/Crash%20Bandicoot%20-%20Warped%20%28USA%29.chd",
        "filename": "Crash Bandicoot - Warped (USA).chd",
        "summary": "L'apogée de la trilogie Crash Bandicoot sur PS1 avec voyage dans le temps, moto et bazooka.",
        "description": (
            "Traversez les époques avec Crash et Coco pour vaincre le Dr Neo Cortex et Uka Uka. "
            "Format CHD compressé haute performance avec lancement direct."
        ),
        "supported_controllers": [
            "Manette PlayStation DualSense / DualShock 4 (Vibration supportée)",
            "Manette Xbox / Switch Pro & Clavier PC",
        ],
    },
    # ======================= NINTENDO DS & 3DS =======================
    {
        "id": "nds_new_super_mario_bros",
        "title": "New Super Mario Bros. (DS)",
        "console_id": "nds",
        "console_name": "Nintendo DS",
        "release_year": 2006,
        "developer": "Nintendo EAD",
        "genre": "Plateforme 2D",
        "players": "1 - 2 Joueurs",
        "rating": "9.7/10",
        "file_size_label": "32 Mo (.nds)",
        "cover_url": "https://thumbnails.libretro.com/Nintendo%20-%20Nintendo%20DS/Named_Boxarts/New%20Super%20Mario%20Bros.%20%28USA%29.png",
        "download_url": "https://archive.org/download/nds-collection/New%20Super%20Mario%20Bros..zip",
        "filename": "New Super Mario Bros..zip",
        "summary": "Le grand retour de Mario au format 2D sur Nintendo DS avec le Méga Champi et mini-jeux tactiles.",
        "description": (
            "Le jeu le plus vendu de la Nintendo DS (plus de 30 millions d'exemplaires). "
            "Graphismes 3D sur plan 2D, power-ups légendaires et jouabilité parfaite émulée à 60 FPS avec MelonDS."
        ),
        "supported_controllers": [
            "Manette Xbox / PlayStation / Switch Pro",
            "Écran Tactile émulé à la Souris",
            "Clavier PC",
        ],
    },
    {
        "id": "nds_mario_kart_ds",
        "title": "Mario Kart DS",
        "console_id": "nds",
        "console_name": "Nintendo DS",
        "release_year": 2005,
        "developer": "Nintendo EAD",
        "genre": "Course / Kart",
        "players": "1 - 8 Joueurs",
        "rating": "9.8/10",
        "file_size_label": "25 Mo (.nds)",
        "cover_url": "https://thumbnails.libretro.com/Nintendo%20-%20Nintendo%20DS/Named_Boxarts/Mario%20Kart%20DS%20%28USA%29.png",
        "download_url": "https://archive.org/download/nds-collection/Mario%20Kart%20DS.zip",
        "filename": "Mario Kart DS.zip",
        "summary": "L'un des meilleurs Mario Kart avec les circuits rétro, le mode Missions et le double écran carte/course.",
        "description": (
            "Pilotez 12 personnages emblématiques sur 32 circuits mythiques. "
            "Le double écran affiche la course en haut et la carte dynamique avec les objets en bas."
        ),
        "supported_controllers": [
            "Manette Xbox / PlayStation / Switch Pro",
            "Clavier PC",
        ],
    },
    {
        "id": "nds_pokemon_platine",
        "title": "Pokémon Version Platine (DS)",
        "console_id": "nds",
        "console_name": "Nintendo DS",
        "release_year": 2008,
        "developer": "Game Freak / Nintendo",
        "genre": "RPG / Aventure",
        "players": "1 - 2 Joueurs",
        "rating": "9.9/10",
        "file_size_label": "48.5 Mo (.zip)",
        "cover_url": "https://thumbnails.libretro.com/Nintendo%20-%20Nintendo%20DS/Named_Boxarts/Pokemon%20-%20Platinum%20Version%20%28USA%29.png",
        "download_url": "https://archive.org/download/nds-collection/Pokemon%20Platinum%20Version.zip",
        "filename": "Pokemon Platinum Version.zip",
        "summary": "L'aventure ultime de Sinnoh avec Giratina et le Monde Distorsion sur Nintendo DS.",
        "description": (
            "L'un des épisodes les plus acclamés de la série Pokémon. "
            "Compatible tactile pour la Pokémontre et navigation fluide avec MelonDS."
        ),
        "supported_controllers": [
            "Manette Xbox / PlayStation / Switch Pro",
            "Écran Tactile à la Souris",
            "Clavier PC",
        ],
    },
    {
        "id": "nds_zelda_phantom_hourglass",
        "title": "The Legend of Zelda: Phantom Hourglass (DS)",
        "console_id": "nds",
        "console_name": "Nintendo DS",
        "release_year": 2007,
        "developer": "Nintendo EAD",
        "genre": "Action / Aventure",
        "players": "1 - 2 Joueurs",
        "rating": "9.6/10",
        "file_size_label": "52 Mo (.nds)",
        "cover_url": "https://thumbnails.libretro.com/Nintendo%20-%20Nintendo%20DS/Named_Boxarts/Legend%20of%20Zelda%2C%20The%20-%20Phantom%20Hourglass%20%28USA%29.png",
        "download_url": "https://archive.org/download/nds-collection/Legend%20of%20Zelda%2C%20The%20-%20Phantom%20Hourglass.zip",
        "filename": "Legend of Zelda, The - Phantom Hourglass.zip",
        "summary": "Suite directe de The Wind Waker, exploitant avec brio l'écran tactile et le micro de la Nintendo DS.",
        "description": (
            "Explorez les mers avec Link et Linebeck. Tracé des trajectoires du boomerang au stylet et énigmes ingénieuses."
        ),
        "supported_controllers": [
            "Écran Tactile à la Souris (Essentiel)",
            "Manette Xbox / PlayStation / Switch Pro",
            "Clavier PC",
        ],
    },
    {
        "id": "3ds_super_mario_3d_land",
        "title": "Super Mario 3D Land (3DS)",
        "console_id": "3ds",
        "console_name": "Nintendo 3DS",
        "release_year": 2011,
        "developer": "Nintendo EAD Tokyo",
        "genre": "Plateforme 3D",
        "players": "1 Joueur",
        "rating": "9.8/10",
        "file_size_label": "315 Mo (.3ds)",
        "cover_url": "https://thumbnails.libretro.com/Nintendo%20-%20Nintendo%203DS/Named_Boxarts/Super%20Mario%203D%20Land%20%28USA%29.png",
        "download_url": "https://archive.org/download/3ds-decrypted-roms321com/all/Super%20Mario%203D%20Land%20%28USA%29%20%28En%2CFr%2CEs%29.zip",
        "filename": "Super Mario 3D Land (USA).zip",
        "summary": "Le chef-d'œuvre de la 3DS alliant la précision du Mario 2D à la profondeur de la 3D, avec le costume Tanuki.",
        "description": (
            "Une inventivité permanente dans le level design. "
            "Émulation ultra-précise avec le cœur Citra haute résolution 1080p / 4K et gestion des sticks analogiques."
        ),
        "supported_controllers": [
            "Manette avec Stick Analogique (Xbox, PlayStation, Switch Pro)",
            "Souris pour écran tactile",
            "Clavier PC",
        ],
    },
    {
        "id": "3ds_mario_kart_7",
        "title": "Mario Kart 7 (3DS)",
        "console_id": "3ds",
        "console_name": "Nintendo 3DS",
        "release_year": 2011,
        "developer": "Nintendo EAD / Retro Studios",
        "genre": "Course / Kart",
        "players": "1 - 8 Joueurs",
        "rating": "9.7/10",
        "file_size_label": "672 Mo (.3ds)",
        "cover_url": "https://thumbnails.libretro.com/Nintendo%20-%20Nintendo%203DS/Named_Boxarts/Mario%20Kart%207%20%28USA%29.png",
        "download_url": "https://archive.org/download/3ds-decrypted-roms321com/all/Mario%20Kart%207%20%28Europe%29%20%28En%2CFr%2CDe%2CEs%2CIt%2CNl%2CPt%2CRu%29%20%28Rev%202%29.zip",
        "filename": "Mario Kart 7 (Europe) (Rev 2).zip",
        "summary": "Le grand Mario Kart portable introduisant les deltaplanes dans les airs et les hélices sous l'eau.",
        "description": (
            "Customisation des karts, 32 circuits spectaculaires et graphismes rehaussés en haute définition via Citra."
        ),
        "supported_controllers": [
            "Manette avec Stick Analogique (Xbox, PS, Switch Pro)",
            "Clavier PC",
        ],
    },
    {
        "id": "3ds_zelda_a_link_between_worlds",
        "title": "The Legend of Zelda: A Link Between Worlds (3DS)",
        "console_id": "3ds",
        "console_name": "Nintendo 3DS",
        "release_year": 2013,
        "developer": "Nintendo EAD",
        "genre": "Action / Aventure",
        "players": "1 Joueur",
        "rating": "9.9/10",
        "file_size_label": "594 Mo (.3ds)",
        "cover_url": "https://thumbnails.libretro.com/Nintendo%20-%20Nintendo%203DS/Named_Boxarts/Legend%20of%20Zelda%2C%20The%20-%20A%20Link%20Between%20Worlds%20%28USA%29.png",
        "download_url": "https://archive.org/download/3ds-decrypted-roms321com/all/Legend%20of%20Zelda%2C%20The%20-%20A%20Link%20Between%20Worlds%20%28USA%29%20%28En%2CFr%2CEs%29.zip",
        "filename": "Legend of Zelda, The - A Link Between Worlds (USA) (En,Fr,Es).zip",
        "summary": "La suite spirituelle de A Link to the Past avec la capacité de Link de fusionner avec les murs en peinture.",
        "description": (
            "Un des meilleurs Zelda de tous les temps, tournant à 60 FPS constants. Donjons non-linéaires et bande-son orchestrée."
        ),
        "supported_controllers": [
            "Manette Xbox / PlayStation / Switch Pro",
            "Souris pour écran tactile",
            "Clavier PC",
        ],
    },

    # ======================= ATARI 2600 / ARCADE / DREAMCAST / PSP =======================
    {
        "id": "atari2600_river_raid",
        "title": "River Raid (Atari 2600)",
        "console_id": "atari2600",
        "console_name": "Atari 2600",
        "release_year": 1982,
        "developer": "Activision (Carol Shaw)",
        "genre": "Shoot 'em up Vertical",
        "players": "1 - 2 Joueurs",
        "rating": "9.4/10",
        "file_size_label": "4 Ko (.bin)",
        "cover_url": "https://thumbnails.libretro.com/Atari%20-%202600/Named_Boxarts/River%20Raid%20%28USA%29.png",
        "download_url": "https://archive.org/download/atari-2600-roms-ultra/Bermuda%20%28AKA%20River%20Raid%29%20%281983%29%20%28Quelle%29%20%28322.913%205%29%20%28PAL%29.bin",
        "filename": "River Raid (Atari 2600).bin",
        "summary": "Le chef-d'œuvre d'Activision conçu par Carol Shaw sur Atari 2600, pionnier du shoot 'em up à défilement continu.",
        "description": (
            "Pilotez votre avion de chasse au-dessus du fleuve sans manquer de carburant tout en détruisant les ponts, "
            "hélicoptères et navires ennemis. Émulation instantanée via Stella 2014."
        ),
        "supported_controllers": [
            "Joystick Atari / Manette Xbox, PlayStation, Switch",
            "Clavier PC",
        ],
    },
    {
        "id": "arcade_metal_slug",
        "title": "Metal Slug: Super Vehicle-001 (Neo Geo)",
        "console_id": "arcade",
        "console_name": "Arcade / Neo Geo",
        "release_year": 1996,
        "developer": "Nazca Corporation / SNK",
        "genre": "Run and Gun Arcade",
        "players": "1 - 2 Joueurs",
        "rating": "9.8/10",
        "file_size_label": "13.2 Mo (.zip)",
        "cover_url": "https://thumbnails.libretro.com/SNK%20-%20Neo%20Geo/Named_Boxarts/Metal%20Slug%20-%20Super%20Vehicle-001.png",
        "download_url": "https://archive.org/download/neo-geo-aes-romset/mslug.zip",
        "filename": "mslug.zip",
        "summary": "Le sommet du pixel-art 2D sur borne d'arcade SNK Neo Geo MVS/AES.",
        "description": (
            "Action frénétique en coop à 2 joueurs, animations dessinées image par image d'une richesse inégalée "
            "et pilotage du légendaire char Metal Slug sous FinalBurn Neo."
        ),
        "supported_controllers": [
            "Stick Arcade / Manette 6 boutons (Xbox, PS, Switch)",
            "Clavier PC",
        ],
    },
    {
        "id": "dreamcast_sonic_adventure_2",
        "title": "Sonic Adventure 2 (Dreamcast)",
        "console_id": "dreamcast",
        "console_name": "Dreamcast",
        "release_year": 2001,
        "developer": "Sonic Team / Sega",
        "genre": "Plateforme 3D Haute Vitesse",
        "players": "1 - 2 Joueurs",
        "rating": "9.6/10",
        "file_size_label": "680 Mo (.zip)",
        "cover_url": "https://thumbnails.libretro.com/Sega%20-%20Dreamcast/Named_Boxarts/Sonic%20Adventure%202%20%28USA%29.png",
        "download_url": "https://archive.org/download/DreamcastSelfBoot/S/Sonic%20Adventure%202%20%28USA%29.zip",
        "filename": "Sonic Adventure 2 (USA).zip",
        "summary": "L'affrontement mythique entre la campagne Hero (Sonic, Tails, Knuckles) et Dark (Shadow, Eggman, Rouge) sur Sega Dreamcast.",
        "description": (
            "Première apparition de Shadow the Hedgehog, descente de City Escape à 60 FPS et Jardin Chao complet "
            "propulsé par le moteur Flycast HLE sans besoin de BIOS externe."
        ),
        "supported_controllers": [
            "Manette avec Stick Analogique & Gâchettes (Xbox, PS, Switch Pro)",
            "Clavier PC",
        ],
    },
    {
        "id": "psp_007_from_russia_with_love",
        "title": "007: Bons Baisers de Russie (PSP)",
        "console_id": "psp",
        "console_name": "Sony PSP",
        "release_year": 2006,
        "developer": "EA Redwood Shores / Rebellion",
        "genre": "Action / Espionnage 3D",
        "players": "1 - 4 Joueurs",
        "rating": "9.1/10",
        "file_size_label": "512 Mo (.chd)",
        "cover_url": "https://thumbnails.libretro.com/Sony%20-%20PlayStation%20Portable/Named_Boxarts/007%20-%20From%20Russia%20with%20Love%20%28USA%29.png",
        "download_url": "https://archive.org/download/psp-chd-zstd-redump-part1/psp-chd-zstd/007%20-%20From%20Russia%20with%20Love%20%28Europe%2C%20Australia%29%20%28En%2CFr%2CDe%2CEs%2CIt%29.chd",
        "filename": "007 - From Russia with Love (Europe).chd",
        "summary": "Incarnez Sean Connery dans cette adaptation 16:9 sur Sony PSP avec jetpack, gadgets Q et doublages français.",
        "description": (
            "Format compressé sans perte Redump CHD directement pris en charge par le cœur PPSSPP HLE "
            "avec mise à l'échelle haute définition 1080p/4K."
        ),
        "supported_controllers": [
            "Manette DualShock / DualSense / Xbox / Switch Pro",
            "Clavier PC",
        ],
    },
]
