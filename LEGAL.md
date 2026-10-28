# Charte Légale, Droit d'Auteur & Conformité DMCA / Legal Disclaimer & Copyright Policy

Ce document définit le cadre juridique strict du projet **AetherDeck** (anciennement *OmniConsole*), les garanties de conformité au droit d'auteur (Code de la propriété intellectuelle français, Directive Européenne 2009/24/CE et Digital Millennium Copyright Act — DMCA), ainsi que la responsabilité exclusive de l'utilisateur final.

---

## Partie I — Version Française

### 1. Légalité de l'Émulation Logicielle et de l'Interopérabilité
**AetherDeck** est une interface logicielle open-source (distribuée sous licence MIT) d'orchestration matérielle, de configuration de périphériques d'entrée (XInput / SDL2) et de gestion de moteurs d'émulation multi-systèmes.

Conformément au droit français et européen (**Article L122-6-1 du Code de la propriété intellectuelle** et **Directive 2009/24/CE du Parlement européen** concernant la protection juridique des programmes d'ordinateur), ainsi qu'à la jurisprudence américaine constante (*Sony Computer Entertainment, Inc. v. Connectix Corp.*, 203 F.3d 596 ; **17 U.S.C. § 117**), la conception et l'utilisation d'un logiciel d'émulation permettant l'interopérabilité matérielle et logicielle sont **strictement légales**.

### 2. Absence Totale de Fichiers Protégés par le Droit d'Auteur
Le dépôt officiel du projet **AetherDeck** :
- **Ne contient, n'héberge et ne distribue aucun jeu commercial** (aucun fichier `.nsp`, `.xci`, `.rvz`, `.iso`, `.wbfs`, `.3ds`, `.nds`, `.chd`, `.z64`, `.sfc`, `.nes`, `.gba`, `.dsk`, `.adf`).
- **Ne contient, n'héberge et ne distribue aucun BIOS propriétaire ni aucun micrologiciel (firmware) sous licence.**
- **Ne contient et ne fournit aucune clé cryptographique propriétaire** (telles que `prod.keys` ou `title.keys`).

Le fichier [`.gitignore`](.gitignore) du dépôt exclut de manière permanente les répertoires locaux `roms/` et `emulators/` ainsi que toutes les extensions de fichiers d'images disques, de cartouches et de clés cryptographiques.

### 3. Exception de Copie Privée et Dépôts Homebrew Officiels
Par défaut, **AetherDeck** active uniquement les dépôts communautaires d'applications libres, homebrew et d'archives publiques de préservation :
1. **Open Shop Channel (Wii)** : applications et jeux homebrew libres de droits au format `.dol`.
2. **Switch Homebrew App Store** : applications et portages open-source au format `.nro`.
3. **Internet Archive** : archives publiques de préservation numérique et logiciels du domaine public / TOSEC.

Conformément à l'**Article L122-5 du Code de la propriété intellectuelle** (exception de copie privée et de sauvegarde), l'utilisateur n'est autorisé à importer ou télécharger la copie de sauvegarde d'une œuvre commerciale que s'il possède légalement et personnellement un exemplaire original (physique ou numérique) de ladite œuvre.

### 4. Non-Affiliation et Désactivation par Défaut des Indexeurs Tiers Externes
L'application comporte un mécanisme technique générique de recherche web pouvant interroger des indexeurs tiers externes indépendants (tels que `NxBrew` ou `SmallGames.ch`).
- **Aucune affiliation** : Les auteurs et contributeurs d'**AetherDeck** n'hébergent, n'administrent, ne contrôlent et n'approuvent aucun site tiers externe.
- **Désactivation stricte par défaut** : Ces sources externes tierces sont **désactivées par défaut** dans la configuration du logiciel (`enable_nxbrew: false`, `enable_smallgames: false` dans [`backend/settings_manager.py`](backend/settings_manager.py)).
- **Consentement explicite obligatoire** : Toute tentative de sélection ou d'activation d'un indexeur externe déclenche l'ouverture obligatoire de la **Charte Légale & Clause de Responsabilité** dans l'interface ([`frontend/index.html`](frontend/index.html)). Tant que l'utilisateur n'a pas expressément certifié prendre l'entière responsabilité juridique de la vérification de la légalité des contenus dans sa juridiction, ces sources demeurent inactives.
- **Limitation de responsabilité** : L'auteur du projet décline toute responsabilité civile ou pénale quant à l'utilisation détournée que pourrait faire un utilisateur final de sites web tiers accessibles sur Internet.

### 5. Marques Déposées
Toutes les dénominations de systèmes et de marques mentionnées à titre purement descriptif d'interopérabilité technique (notamment *Nintendo*, *NES*, *SNES*, *Game Boy Advance*, *Nintendo 64*, *GameCube*, *Wii*, *Nintendo DS*, *Nintendo 3DS*, *Nintendo Switch*, *Sony PlayStation*, *PSP*, *Sega Mega Drive*, *Dreamcast*, *Atari 2600*, *SNK Neo Geo*, *Amstrad CPC*, *Commodore Amiga*, *Microsoft Xbox*) appartiennent à leurs propriétaires respectifs. **AetherDeck** n'est affilié à aucun de ces constructeurs.

---

## Part II — English Version (International & DMCA Compliance)

### 1. Legality of Emulation Software
**AetherDeck** is an open-source multi-system emulation frontend, hardware diagnostic tool, and controller configuration manager released under the MIT License. Under international copyright law, including **EU Directive 2009/24/EC** and **17 U.S.C. § 117 / DMCA interoperability exemptions** (*Sony Computer Entertainment, Inc. v. Connectix Corp.*), software emulators are completely legal.

### 2. Zero Copyrighted Content Policy
This repository **does not contain, host, or distribute**:
- Any copyrighted game ROMs, ISOs, or encrypted packages (`.nsp`, `.xci`, `.rvz`, `.iso`, `.3ds`, `.nds`, `.chd`, etc.).
- Any proprietary console BIOS files or system firmware.
- Any proprietary cryptographic keys (`prod.keys`, `title.keys`, etc.).

### 3. Third-Party Indexers Disabled by Default & User Responsibility
- Optional third-party web indexers (`NxBrew`, `SmallGames.ch`) are **independent external websites** that have no affiliation whatsoever with **AetherDeck** or its developers.
- In strict compliance with copyright law, third-party external indexers are **disabled by default** (`enable_nxbrew: false`, `enable_smallgames: false`).
- Accessing or enabling external third-party sources requires the user to explicitly accept the in-app **Legal Disclaimer & Copyright Responsibility Charter**, certifying that they will only use the software with homebrew titles or legal private backup copies of games they legitimately own.
- The developers of **AetherDeck** assume zero liability for any misuse of the software or any third-party websites accessed by the end user.
