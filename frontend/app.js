/**
 * AetherDeck — Architecture d'Émulation & Préservation Multi-Systèmes
 * Clean, modern desktop client (Zero Emojis, Pure SVG Icons, Vanilla JS)
 */

// --- Global State ---
const state = {
  currentView: "discover",
  searchQuery: "",
  consoleFilter: "all",
  sourceFilter: "all",
  weightFilter: "all",
  page: 1,
  perPage: 60,
  hasMore: false,
  totalResults: 0,
  isLoading: false,

  libraryConsoleFilter: "all",
  activeGameDetail: null,
  controllersPollingTimer: null,
  tasksPollingTimer: null,
  activeRemap: null, // { type: 'keyboard'|'gamepad', action: 'a' }

  bootstrapData: null,
  settings: null,
  legalCompliance: { accepted_external_sources_disclaimer: false, accepted_at: null },
  pendingLegalCallback: null,
  controllers: null,
  library: [],
  gamesList: [],
};

// --- Action Labels Map (English -> French display) ---
const ACTION_LABELS = {
  up: "Haut (D-Pad / Stick)",
  down: "Bas (D-Pad / Stick)",
  left: "Gauche (D-Pad / Stick)",
  right: "Droite (D-Pad / Stick)",
  a: "Bouton A (Action / Saut)",
  b: "Bouton B (Attaque / Annuler)",
  x: "Bouton X (Action 3 / Arme)",
  y: "Bouton Y (Action 4 / Course)",
  l1: "Gâchette L1 / LB",
  r1: "Gâchette R1 / RB",
  l2: "Gâchette L2 / LT",
  r2: "Gâchette R2 / RT",
  l3: "Stick Clic Gauche (L3)",
  r3: "Stick Clic Droit (R3)",
  start: "Start / Pause",
  select: "Select / Pièce",
};

// --- Initialization ---
document.addEventListener("DOMContentLoaded", () => {
  initSearchInput();
  initInfiniteScroll();
  initGlobalKeyboardAndGamepadListeners();
  loadBootstrap();
});

// --- API Helpers ---
async function apiGet(endpoint) {
  try {
    const res = await fetch(endpoint);
    return await res.json();
  } catch (err) {
    console.error("API GET Error:", endpoint, err);
    return { ok: false, message: err.message };
  }
}

async function apiPost(endpoint, body = {}) {
  try {
    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return await res.json();
  } catch (err) {
    console.error("API POST Error:", endpoint, err);
    return { ok: false, message: err.message };
  }
}

// --- Bootstrap Loading ---
async function loadBootstrap() {
  const data = await apiGet("/api/bootstrap");
  if (!data || !data.ok) {
    showToast("Connexion au serveur AetherDeck impossible.", "error");
    return;
  }
  state.bootstrapData = data;
  state.settings = data.settings?.settings || {};
  state.legalCompliance = data.legal_compliance || state.settings.legal_compliance || {
    accepted_external_sources_disclaimer: false,
    accepted_at: null,
  };
  state.controllers = data.controllers || {};
  state.library = data.library || [];

  updateSidebarStatus(data.system, data.consoles, data.controllers);
  updateLibraryBadge();
  updateLegalUI();

  // Populate GPU selector in settings
  populateGpuSelector(data.settings?.available_gpus || ["Auto"]);

  // Render initial featured games
  if (data.featured && data.featured.games) {
    state.gamesList = data.featured.games;
    state.totalResults = data.featured.total || data.featured.games.length;
    state.hasMore = data.featured.has_more || false;
    renderGamesGrid(state.gamesList, false);
    updateResultsCount(state.totalResults);
  }

  // Render Engines & Controllers views data
  renderEnginesView(data.consoles, data.system);
  renderControllersView(data.controllers);
  populateSettingsForm(state.settings);

  // Check Tutorial status
  if (data.tutorial_seen === false) {
    openTutorialModal();
  }

  // Start polling tasks for active downloads/installs
  startTasksPolling();
}

function updateSidebarStatus(system, consoles, controllers) {
  if (system) {
    const tierEl = document.getElementById("sidebar-pc-tier");
    if (tierEl) tierEl.innerText = system.pc_tier_label || "PC Windows";
  }
  if (consoles) {
    const readyEl = document.getElementById("sidebar-engines-ready");
    if (readyEl) {
      const installed = consoles.filter((c) => c.installed).length;
      readyEl.innerText = `${installed} / ${consoles.length}`;
    }
  }
  if (controllers && controllers.connected) {
    const padStatusEl = document.getElementById("sidebar-gamepad-status");
    if (padStatusEl) {
      const hasPhysical = controllers.connected.some((c) => c.type !== "keyboard");
      if (hasPhysical) {
        padStatusEl.innerText = "Manette Connectée";
        padStatusEl.className = "status-value text-success";
      } else {
        padStatusEl.innerText = "Clavier PC Actif";
        padStatusEl.className = "status-value";
      }
    }
  }
}

function updateLibraryBadge() {
  const count = state.library.length;
  const badge = document.getElementById("nav-library-count");
  if (badge) badge.innerText = count.toString();
}

// --- Navigation ---
function switchView(viewName) {
  state.currentView = viewName;

  document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.view === viewName);
  });

  document.querySelectorAll(".view-section").forEach((sec) => {
    sec.classList.toggle("active", sec.id === `view-${viewName}`);
  });

  // Manage timers
  if (viewName === "controllers") {
    startControllersPolling();
  } else {
    stopControllersPolling();
  }

  if (viewName === "library") {
    refreshLibraryView();
  } else if (viewName === "engines") {
    refreshEnginesView();
  }
}

// --- Search & Filters ---
function initSearchInput() {
  const input = document.getElementById("global-search-input");
  const clearBtn = document.getElementById("search-clear-btn");
  let debounceTimeout = null;

  input.addEventListener("input", (e) => {
    const val = e.target.value.trim();
    clearBtn.style.display = val.length > 0 ? "flex" : "none";
    clearTimeout(debounceTimeout);
    debounceTimeout = setTimeout(() => {
      state.searchQuery = val;
      state.page = 1;
      executeSearch(true);
    }, 280);
  });
}

function clearSearch() {
  const input = document.getElementById("global-search-input");
  const clearBtn = document.getElementById("search-clear-btn");
  input.value = "";
  clearBtn.style.display = "none";
  state.searchQuery = "";
  state.page = 1;
  executeSearch(true);
}

function triggerQuickSearch(query) {
  const input = document.getElementById("global-search-input");
  const clearBtn = document.getElementById("search-clear-btn");
  input.value = query;
  clearBtn.style.display = query ? "flex" : "none";
  state.searchQuery = query;
  state.page = 1;
  switchView("discover");
  executeSearch(true);
}

function setConsoleFilter(consoleId) {
  state.consoleFilter = consoleId;
  state.page = 1;
  document.querySelectorAll("#console-filter-chips .chip").forEach((c) => {
    c.classList.toggle("active", c.dataset.console === consoleId);
  });
  executeSearch(true);
}

function setSourceFilter(sourceId) {
  if (
    (sourceId === "nxbrew" || sourceId === "smallgames") &&
    !state.legalCompliance?.accepted_external_sources_disclaimer
  ) {
    const sel = document.getElementById("source-filter-select");
    if (sel) sel.value = state.sourceFilter || "all";
    openLegalConsentModal(() => {
      if (sel) sel.value = sourceId;
      state.sourceFilter = sourceId;
      state.page = 1;
      executeSearch(true);
    });
    return;
  }
  state.sourceFilter = sourceId;
  state.page = 1;
  executeSearch(true);
}

function setWeightFilter(weightId) {
  state.weightFilter = weightId;
  state.page = 1;
  executeSearch(true);
}

async function executeSearch(reset = false) {
  if (state.isLoading) return;
  state.isLoading = true;

  const url = `/api/search?q=${encodeURIComponent(state.searchQuery)}&console=${state.consoleFilter}&source=${state.sourceFilter}&weight=${state.weightFilter}&page=${state.page}&per_page=${state.perPage}`;
  const data = await apiGet(url);

  state.isLoading = false;
  if (!data || !data.ok) return;

  state.totalResults = data.total || 0;
  state.hasMore = data.has_more || false;

  if (reset) {
    state.gamesList = data.games || [];
  } else {
    state.gamesList = state.gamesList.concat(data.games || []);
  }

  renderGamesGrid(state.gamesList, !reset);
  updateResultsCount(state.totalResults);

  // Manage Load more button
  const loadMoreBox = document.getElementById("load-more-container");
  if (loadMoreBox) {
    loadMoreBox.style.display = state.hasMore ? "flex" : "none";
  }
}

function loadMoreGames() {
  if (!state.hasMore || state.isLoading) return;
  state.page += 1;
  executeSearch(false);
}

function initInfiniteScroll() {
  const btn = document.getElementById("load-more-btn");
  if (!btn || !window.IntersectionObserver) return;
  const observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting && state.hasMore && !state.isLoading) {
      loadMoreGames();
    }
  }, { rootMargin: "300px" });
  observer.observe(btn);
}

function updateResultsCount(total) {
  const badge = document.getElementById("search-results-count");
  const navBadge = document.getElementById("nav-catalog-count");
  const label = total === 1 ? "1 résultat" : `${total} résultats`;
  if (badge) badge.innerText = label;
  if (navBadge) navBadge.innerText = total > 999 ? "999+" : total.toString();
}

// --- Render Games Grid ---
function renderGamesGrid(games, append = false) {
  const grid = document.getElementById("discover-games-grid");
  if (!grid) return;

  if (!append) {
    grid.innerHTML = "";
  }

  if (games.length === 0 && !append) {
    grid.innerHTML = `
      <div class="empty-state" style="grid-column: 1 / -1;">
        <svg class="svg-icon empty-icon"><use href="#icon-search"></use></svg>
        <h3>Aucun jeu trouvé pour ces critères</h3>
        <p>Essayez avec d'autres mots-clés ou sélectionnez « Toutes les consoles ».</p>
      </div>
    `;
    return;
  }

  games.forEach((game) => {
    const card = createGameCardElement(game);
    grid.appendChild(card);
  });
}

function createGameCardElement(game) {
  const card = document.createElement("div");
  card.className = "game-card";
  card.onclick = () => openGameDetailModal(game);

  const fallbackSvgUrl = `/api/cover_svg?title=${encodeURIComponent(game.title)}&console=${encodeURIComponent(game.console_name || "Console")}&accent=${encodeURIComponent(game.console_accent || "#4f46e5")}`;
  const autoCoverUrl = `/api/cover_art?title=${encodeURIComponent(game.title)}&console=${encodeURIComponent(game.console_name || "Console")}&id=${encodeURIComponent(game.console_id || "")}&accent=${encodeURIComponent(game.console_accent || "#4f46e5")}`;
  const posterUrl = (game.cover_url && game.cover_url.startsWith("http")) ? game.cover_url : autoCoverUrl;

  const inLib = game.in_library;
  const isDownloading = game.download_status === "downloading";

  let statusBadge = "";
  if (inLib) {
    statusBadge = `<span class="badge-tag" style="background: rgba(16, 185, 129, 0.2); color: #10b981;">Prêt à jouer</span>`;
  } else if (isDownloading) {
    statusBadge = `<span class="badge-tag" style="background: rgba(79, 70, 229, 0.2); color: #818cf8;">Téléchargement ${game.download_progress}%</span>`;
  } else {
    statusBadge = `<span class="badge-tag" style="background: ${game.console_accent || '#4f46e5'}22; color: ${game.console_accent || '#818cf8'};">${esc(game.console_name)}</span>`;
  }

  card.innerHTML = `
    <img
      src="${esc(posterUrl)}"
      alt="${esc(game.title)}"
      class="game-card-poster"
      loading="lazy"
      data-auto-url="${esc(autoCoverUrl)}"
      data-fallback-url="${esc(fallbackSvgUrl)}"
      onerror="if(!this.dataset.autoTried){ this.dataset.autoTried='1'; this.src=this.dataset.autoUrl; } else { this.onerror=null; this.src=this.dataset.fallbackUrl; }"
    />
    <div class="game-card-info">
      <div class="game-card-tags">
        ${statusBadge}
        <span class="size-label">${esc(game.file_size_label || "")}</span>
      </div>
      <h3 class="game-card-title">${esc(game.title)}</h3>
      <div class="game-card-meta">
        <span>${esc(game.release_year || "Classique")}</span>
        <span>${esc(game.source_label || "AetherDeck")}</span>
      </div>
    </div>
  `;
  return card;
}

// --- Game Detail Modal ---
function openGameDetailModal(game) {
  state.activeGameDetail = game;
  const modal = document.getElementById("game-detail-modal");

  const fallbackSvgUrl = `/api/cover_svg?title=${encodeURIComponent(game.title)}&console=${encodeURIComponent(game.console_name || "Console")}&accent=${encodeURIComponent(game.console_accent || "#4f46e5")}`;
  const autoCoverUrl = `/api/cover_art?title=${encodeURIComponent(game.title)}&console=${encodeURIComponent(game.console_name || "Console")}&id=${encodeURIComponent(game.console_id || "")}&accent=${encodeURIComponent(game.console_accent || "#4f46e5")}`;
  const coverImg = document.getElementById("detail-cover-img");
  coverImg.dataset.autoTried = "0";
  coverImg.src = (game.cover_url && game.cover_url.startsWith("http")) ? game.cover_url : autoCoverUrl;
  coverImg.onerror = () => {
    if (coverImg.dataset.autoTried !== "1") {
      coverImg.dataset.autoTried = "1";
      coverImg.src = autoCoverUrl;
    } else {
      coverImg.src = fallbackSvgUrl;
    }
  };

  document.getElementById("detail-title").innerText = game.title;
  document.getElementById("detail-developer").innerText = game.developer || "Édition Originale";
  document.getElementById("detail-year").innerText = game.release_year || "Classique";
  document.getElementById("detail-genre").innerText = game.genre || "Jeu Vidéo";
  document.getElementById("detail-size").innerText = game.file_size_label || "Taille inconnue";

  const consoleBadge = document.getElementById("detail-console-badge");
  consoleBadge.innerText = game.console_full_name || game.console_name;
  consoleBadge.style.color = game.console_accent || "#818cf8";
  consoleBadge.style.borderColor = (game.console_accent || "#4f46e5") + "66";

  const sourceBadge = document.getElementById("detail-source-badge");
  const sourceText = document.getElementById("detail-source-text");
  sourceText.innerText = `${game.source_label || "Source Vérifiée"} • ${game.trust_note || "Téléchargement sécurisé"}`;

  // Supported controllers list
  const controllersList = document.getElementById("detail-controllers-list");
  controllersList.innerHTML = "";
  const supported = game.supported_controllers || ["Manette Xbox / PlayStation / Switch", "Clavier PC"];
  supported.forEach((ctrl) => {
    const item = document.createElement("div");
    item.className = "controller-badge-item";
    item.innerHTML = `
      <svg class="svg-icon" style="width: 14px; height: 14px;"><use href="#icon-gamepad"></use></svg>
      <span>${esc(ctrl)}</span>
    `;
    controllersList.appendChild(item);
  });

  // PC Compatibility
  const compatBox = document.getElementById("detail-pc-compat");
  if (game.pc_compatibility) {
    compatBox.innerText = `${game.pc_compatibility.status_text} (${game.weight_label || "Poids standard"}) — Moteur ${game.engine_name}`;
    compatBox.style.borderLeft = `4px solid ${game.pc_compatibility.badge_color || "#10b981"}`;
  } else {
    compatBox.innerText = `Émulateur : ${game.engine_name} (Compatible)`;
    compatBox.style.borderLeft = "4px solid #10b981";
  }

  document.getElementById("detail-description").innerText = game.description || game.summary || "";

  const nxbrewSection = document.getElementById("detail-nxbrew-section");
  if (nxbrewSection) {
    if (game.download_kind === "nxbrew") {
      nxbrewSection.style.display = "block";
      loadNxBrewDetails(game);
    } else {
      nxbrewSection.style.display = "none";
      nxbrewSection.innerHTML = "";
    }
  }

  renderDetailActionsRow(game);
  modal.classList.add("active");
}

async function loadNxBrewDetails(game) {
  const container = document.getElementById("detail-nxbrew-section");
  if (!container) return;
  container.innerHTML = `
    <div class="detail-section-title">Packages &amp; Téléchargements NxBrew (Résolution Playwright) :</div>
    <div style="padding: 12px; text-align: center; color: var(--text-secondary); background: var(--bg-surface); border-radius: var(--radius-sm); border: 1px solid var(--border-subtle); margin-top: 6px;">
      <svg class="svg-icon spin" style="width: 16px; height: 16px; margin-right: 6px;"><use href="#icon-cpu"></use></svg>
      Chargement des packages et hébergeurs disponibles...
    </div>
  `;

  try {
    const res = await fetch(`/api/nxbrew/details?url=${encodeURIComponent(game.page_url || game.download_url)}`);
    const data = await res.json();
    if (!data.ok || !data.packages || data.packages.length === 0) {
      container.innerHTML = `
        <div class="detail-section-title">Packages &amp; Téléchargements NxBrew :</div>
        <div style="padding: 12px; color: var(--text-secondary); background: var(--bg-surface); border-radius: var(--radius-sm); border: 1px solid var(--border-subtle); margin-top: 6px;">
          Impossible d'analyser automatiquement les packages. Utilisez le bouton ci-dessous pour ouvrir directement la page du jeu.
        </div>
      `;
      return;
    }

    let html = `
      <div class="detail-section-title">Packages &amp; Hébergeurs Disponibles (Sans redirection via Playwright) :</div>
      <div class="nxbrew-packages-container">
    `;

    data.packages.forEach((pkg, pIdx) => {
      html += `
        <div class="nxbrew-pkg-card">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; flex-wrap: wrap; gap: 8px;">
            <div class="nxbrew-pkg-title">
              <svg class="svg-icon" style="width: 15px; height: 15px;"><use href="#icon-download"></use></svg>
              <span>${esc(pkg.name)}</span>
            </div>
            <button class="pill-btn primary" style="padding: 5px 12px; font-size: 12px;" onclick="downloadNxBrewPackage('${esc(game.id)}', '${esc(pkg.name)}', '${esc(pkg.hosts[0]?.url || '')}', '${esc(pkg.hosts[0]?.host || '1Fichier')}')">
              <svg class="svg-icon" style="width: 12px; height: 12px;"><use href="#icon-download"></use></svg>
              <span>Télécharger ce package (Playwright)</span>
            </button>
          </div>
          <div class="nxbrew-hosts-grid">
      `;
      (pkg.hosts || []).forEach((h, hIdx) => {
        const uniqueId = `nxb-host-${pIdx}-${hIdx}`;
        html += `
          <button class="nxbrew-host-chip" onclick="resolveNxBrewHost('${esc(h.url)}', '${esc(h.host)}', '${uniqueId}')">
            <span>${esc(h.host)}</span>
            <svg class="svg-icon" style="width: 12px; height: 12px;"><use href="#icon-chevron-right"></use></svg>
          </button>
        `;
      });
      html += `
          </div>
          <div id="nxb-resolved-area-${pIdx}" style="margin-top: 8px;"></div>
        </div>
      `;
    });

    html += `</div>`;
    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = `
      <div class="detail-section-title">Packages NxBrew :</div>
      <div style="padding: 10px; color: var(--accent-danger);">Erreur lors de la récupération : ${esc(err.message)}</div>
    `;
  }
}

async function resolveNxBrewHost(ouoUrl, hostName, hostBtnId) {
  showToast(`Résolution Playwright en cours pour ${hostName} (anti-redirection)...`, "info");

  try {
    const res = await fetch("/api/nxbrew/resolve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: ouoUrl })
    });
    const data = await res.json();
    if (data.ok && data.resolved_url) {
      showToast(`Lien direct résolu avec succès (${data.host || hostName}) !`, "success");

      let existingCard = document.getElementById("nxbrew-active-resolved-card");
      if (!existingCard) {
        existingCard = document.createElement("div");
        existingCard.id = "nxbrew-active-resolved-card";
        existingCard.className = "nxbrew-resolved-card";
        document.getElementById("detail-nxbrew-section").appendChild(existingCard);
      }
      existingCard.innerHTML = `
        <div class="nxbrew-resolved-title">
          <svg class="svg-icon" style="width: 14px; height: 14px;"><use href="#icon-check"></use></svg>
          <span>Lien Direct Résolu (Playwright sans redirection) :</span>
        </div>
        <div class="nxbrew-resolved-url">${esc(data.resolved_url)}</div>
        <div style="display: flex; gap: 8px; margin-top: 8px; flex-wrap: wrap;">
          <button class="pill-btn primary" style="padding: 6px 14px; font-size: 12px;" onclick="downloadResolvedUrl('${esc(state.activeGameDetail?.id)}', '${esc(data.resolved_url)}', '${esc(data.host || hostName)}')">
            <svg class="svg-icon" style="width: 13px; height: 13px;"><use href="#icon-download"></use></svg>
            <span>Télécharger directement dans AetherDeck</span>
          </button>
          <button class="pill-btn" style="padding: 6px 12px; font-size: 12px;" onclick="openExternalUrl('${esc(data.resolved_url)}')">
            <svg class="svg-icon" style="width: 13px; height: 13px;"><use href="#icon-external"></use></svg>
            <span>Ouvrir (${esc(data.host || hostName)})</span>
          </button>
          <button class="pill-btn" style="padding: 6px 12px; font-size: 12px;" onclick="navigator.clipboard.writeText('${esc(data.resolved_url)}'); showToast('Lien copié dans le presse-papier !', 'success');">
            <span>Copier</span>
          </button>
        </div>
      `;
      existingCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
    } else {
      showToast(data.message || "Impossible de résoudre automatiquement le lien.", "error");
      openExternalUrl(ouoUrl);
    }
  } catch (err) {
    showToast(`Erreur : ${err.message}`, "error");
    openExternalUrl(ouoUrl);
  }
}

async function downloadNxBrewPackage(gameId, pkgName, pkgUrl, hostName) {
  showToast(`Démarrage du téléchargement (${pkgName})...`, "info");
  const res = await apiPost("/api/download", {
    game_id: gameId,
    game: {
      package_name: pkgName,
      package_url: pkgUrl,
      host_name: hostName,
      download_kind: "nxbrew",
      console_id: "switch",
    }
  });
  if (res && res.ok) {
    showToast("Téléchargement lancé en arrière-plan. Suivi en temps réel activé.", "success");
    if (state.activeGameDetail && state.activeGameDetail.id === gameId) {
      state.activeGameDetail.download_status = "downloading";
      state.activeGameDetail.download_progress = 2;
      state.activeGameDetail.download_message = `Initialisation (${pkgName})...`;
      renderDetailActionsRow(state.activeGameDetail);
    }
  } else {
    showToast(res?.message || "Erreur de téléchargement.", "error");
  }
}

async function downloadResolvedUrl(gameId, resolvedUrl, hostName) {
  showToast(`Téléchargement en arrière-plan depuis ${hostName}...`, "info");
  const res = await apiPost("/api/download", {
    game_id: gameId,
    game: {
      package_url: resolvedUrl,
      host_name: hostName,
      download_kind: "nxbrew",
      console_id: "switch",
    }
  });
  if (res && res.ok) {
    showToast("Téléchargement démarré dans AetherDeck !", "success");
    if (state.activeGameDetail && state.activeGameDetail.id === gameId) {
      state.activeGameDetail.download_status = "downloading";
      state.activeGameDetail.download_progress = 5;
      state.activeGameDetail.download_message = `Connexion à ${hostName}...`;
      renderDetailActionsRow(state.activeGameDetail);
    }
  } else {
    showToast(res?.message || "Erreur de téléchargement.", "error");
  }
}

function renderDetailActionsRow(game) {
  const actionsRow = document.getElementById("detail-actions-row");
  if (!actionsRow) return;
  actionsRow.innerHTML = "";

  const inLib = game.in_library;
  const isDownloading = game.download_status === "downloading";

  if (inLib) {
    actionsRow.innerHTML = `
      <button class="pill-btn primary" onclick="launchGame('${esc(game.id)}')">
        <svg class="svg-icon"><use href="#icon-play"></use></svg>
        <span>Lancer le jeu</span>
      </button>
      <button class="pill-btn danger" onclick="removeGameFromLibrary('${esc(game.id)}')">
        <svg class="svg-icon"><use href="#icon-trash"></use></svg>
        <span>Supprimer</span>
      </button>
    `;
    return;
  }

  if (isDownloading) {
    const pct = game.download_progress || 0;
    const msg = game.download_message || `Téléchargement en cours (${pct}%)...`;
    actionsRow.innerHTML = `
      <div style="width: 100%; background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); padding: 10px 14px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; font-size: 13px; font-weight: 600;">
          <span style="color: var(--text-primary);">${esc(msg)}</span>
          <span style="color: var(--accent-primary);">${pct}%</span>
        </div>
        <div style="width: 100%; height: 8px; background: rgba(255,255,255,0.08); border-radius: 4px; overflow: hidden;">
          <div style="width: ${pct}%; height: 100%; background: var(--accent-primary); transition: width 0.3s ease;"></div>
        </div>
      </div>
    `;
    return;
  }

  let errBanner = "";
  if (game.download_status === "error" && game.download_message) {
    errBanner = `
      <div style="width: 100%; padding: 8px 12px; margin-bottom: 8px; border-radius: var(--radius-sm); background: rgba(239,68,68,0.12); border: 1px solid rgba(239,68,68,0.4); color: #ef4444; font-size: 12px;">
        ${esc(game.download_message)}
      </div>
    `;
  }

  if (game.download_kind === "nxbrew") {
    actionsRow.innerHTML = `
      ${errBanner}
      <button class="pill-btn primary" onclick="downloadGame('${esc(game.id)}')">
        <svg class="svg-icon"><use href="#icon-download"></use></svg>
        <span>Télécharger avec Playwright (NSP)</span>
      </button>
      <button class="pill-btn" onclick="openExternalUrl('${esc(game.page_url || game.download_url)}')">
        <svg class="svg-icon"><use href="#icon-external"></use></svg>
        <span>Page NxBrew</span>
      </button>
      <button class="pill-btn" onclick="openScanDownloadsModal()">
        <svg class="svg-icon"><use href="#icon-scan"></use></svg>
        <span>Scanner Téléchargements</span>
      </button>
    `;
    return;
  }

  if (game.download_kind === "external") {
    actionsRow.innerHTML = `
      ${errBanner}
      <button class="pill-btn primary" onclick="openExternalUrl('${esc(game.page_url || game.download_url)}')">
        <svg class="svg-icon"><use href="#icon-external"></use></svg>
        <span>Ouvrir la page de téléchargement</span>
      </button>
      <button class="pill-btn" onclick="openScanDownloadsModal()">
        <svg class="svg-icon"><use href="#icon-scan"></use></svg>
        <span>Scanner mes Téléchargements</span>
      </button>
    `;
    return;
  }

  actionsRow.innerHTML = `
    ${errBanner}
    <button class="pill-btn primary" onclick="downloadGame('${esc(game.id)}')">
      <svg class="svg-icon"><use href="#icon-download"></use></svg>
      <span>Télécharger (${esc(game.file_size_label)})</span>
    </button>
  `;
}

function closeGameDetailModal(e) {
  if (e && e.target.classList.contains("modal-card")) return;
  const modal = document.getElementById("game-detail-modal");
  modal.classList.remove("active");
  state.activeGameDetail = null;
}

// --- Game Actions: Download, Launch, Remove ---
async function downloadGame(gameId) {
  const res = await apiPost("/api/download", { game_id: gameId });
  if (res && res.ok) {
    showToast("Téléchargement démarré en arrière-plan.", "info");
    if (state.activeGameDetail && state.activeGameDetail.id === gameId) {
      state.activeGameDetail.download_status = "downloading";
      state.activeGameDetail.download_progress = 2;
      state.activeGameDetail.download_message = "Initialisation du téléchargement...";
      renderDetailActionsRow(state.activeGameDetail);
    }
  } else {
    showToast(res?.message || "Erreur de téléchargement.", "error");
  }
}

async function launchGame(gameId) {
  showToast("Préparation des contrôles et démarrage de l'émulateur...", "info");
  const res = await apiPost("/api/launch", { game_id: gameId });
  if (res && res.ok) {
    showToast(res.message || "Jeu lancé avec succès !", "success");
    closeGameDetailModal();
  } else {
    showToast(res?.message || "Impossible de lancer le jeu.", "error");
  }
}

async function removeGameFromLibrary(gameId) {
  const res = await fetch(`/api/library?game_id=${encodeURIComponent(gameId)}`, { method: "DELETE" });
  const data = await res.json();
  if (data && data.ok) {
    showToast("Jeu supprimé de la bibliothèque.", "info");
    closeGameDetailModal();
    refreshLibraryView();
    // Also update discover items
    const game = state.gamesList.find((g) => g.id === gameId);
    if (game) game.in_library = false;
    renderGamesGrid(state.gamesList, false);
  } else {
    showToast(data?.message || "Erreur lors de la suppression.", "error");
  }
}

// --- Tasks Polling (Downloads & Installs) ---
function startTasksPolling() {
  if (state.tasksPollingTimer) clearInterval(state.tasksPollingTimer);
  state.tasksPollingTimer = setInterval(async () => {
    const data = await apiGet("/api/tasks");
    if (!data || !data.ok) return;

    const downloads = data.downloads || {};
    const taskList = Object.values(downloads);
    const activeTasks = taskList.filter((t) => t.status === "downloading");
    const errorTasks = taskList.filter((t) => t.status === "error");

    const sidebarBox = document.getElementById("sidebar-downloads-box");
    const barFill = document.getElementById("sidebar-downloads-bar");
    const pctEl = document.getElementById("sidebar-downloads-pct");
    const titleEl = document.getElementById("sidebar-downloads-title");
    const msgEl = document.getElementById("sidebar-downloads-msg");

    if (activeTasks.length > 0) {
      const first = activeTasks[0];
      if (sidebarBox) {
        sidebarBox.style.display = "block";
        sidebarBox.style.borderLeft = "3px solid #6366f1";
        sidebarBox.style.cursor = "default";
        sidebarBox.onclick = null;
        sidebarBox.title = "";
      }
      if (barFill) {
        barFill.style.width = `${first.progress || 0}%`;
        barFill.style.backgroundColor = "#6366f1";
      }
      if (pctEl) pctEl.innerText = `${first.progress || 0}%`;
      if (titleEl) titleEl.innerText = first.title || "Téléchargement";
      if (msgEl) {
        msgEl.style.color = "var(--text-secondary)";
        msgEl.innerText = first.message || "En cours...";
      }
    } else if (errorTasks.length > 0) {
      const first = errorTasks[0];
      if (sidebarBox) {
        sidebarBox.style.display = "block";
        sidebarBox.style.borderLeft = "3px solid #ef4444";
        sidebarBox.style.cursor = "pointer";
        sidebarBox.title = "Cliquer pour masquer l'erreur";
        sidebarBox.onclick = async () => {
          await fetch("/api/tasks", { method: "DELETE" });
          sidebarBox.style.display = "none";
        };
      }
      if (barFill) {
        barFill.style.width = "100%";
        barFill.style.backgroundColor = "#ef4444";
      }
      if (pctEl) pctEl.innerText = "Erreur";
      if (titleEl) titleEl.innerText = first.title || "Téléchargement";
      if (msgEl) {
        msgEl.style.color = "#ef4444";
        msgEl.innerText = `${first.message || "Échec du téléchargement"} (Cliquer pour fermer)`;
      }
    } else {
      if (sidebarBox) {
        sidebarBox.style.display = "none";
        sidebarBox.onclick = null;
      }
    }

    // Live-update open Game Detail Modal if it matches a tracked download task
    const newLibIds = data.library_ids || [];
    const newLibSet = new Set(newLibIds);
    if (state.activeGameDetail) {
      const activeId = state.activeGameDetail.id;
      const taskForModal = downloads[activeId];
      if (taskForModal) {
        const prevStatus = state.activeGameDetail.download_status;
        const prevPct = state.activeGameDetail.download_progress;
        const prevMsg = state.activeGameDetail.download_message;
        state.activeGameDetail.download_status = taskForModal.status;
        state.activeGameDetail.download_progress = taskForModal.progress || 0;
        state.activeGameDetail.download_message = taskForModal.message || "";
        if (taskForModal.status === "downloaded" || newLibSet.has(activeId)) {
          state.activeGameDetail.in_library = true;
        }
        if (
          prevStatus !== taskForModal.status ||
          prevPct !== state.activeGameDetail.download_progress ||
          prevMsg !== state.activeGameDetail.download_message
        ) {
          renderDetailActionsRow(state.activeGameDetail);
        }
      } else if (!state.activeGameDetail.in_library && newLibSet.has(activeId)) {
        state.activeGameDetail.in_library = true;
        state.activeGameDetail.download_status = "downloaded";
        renderDetailActionsRow(state.activeGameDetail);
      }
    }

    // Refresh library & discover badges if library membership changed
    const currentLibIds = new Set(state.library.map((g) => g.id));
    let libChanged = newLibIds.length !== currentLibIds.size;
    if (!libChanged) {
      for (const id of newLibIds) {
        if (!currentLibIds.has(id)) {
          libChanged = true;
          break;
        }
      }
    }
    if (libChanged) {
      refreshLibraryView();
      if (state.gamesList && state.gamesList.length > 0) {
        state.gamesList.forEach((g) => {
          if (newLibSet.has(g.id)) g.in_library = true;
        });
        renderGamesGrid(state.gamesList, false);
      }
    }
  }, 900);
}

// --- Library View ---
async function refreshLibraryView() {
  const data = await apiGet(`/api/library?console=${state.libraryConsoleFilter}`);
  if (!data || !data.ok) return;
  state.library = data.games || [];
  updateLibraryBadge();

  const grid = document.getElementById("library-games-grid");
  const emptyState = document.getElementById("library-empty-state");
  if (!grid || !emptyState) return;

  grid.innerHTML = "";
  if (state.library.length === 0) {
    emptyState.style.display = "flex";
  } else {
    emptyState.style.display = "none";
    state.library.forEach((game) => {
      const card = createGameCardElement(game);
      grid.appendChild(card);
    });
  }
}

function setLibraryConsoleFilter(consoleId) {
  state.libraryConsoleFilter = consoleId;
  document.querySelectorAll("#library-console-chips .chip").forEach((c) => {
    c.classList.toggle("active", c.dataset.console === consoleId);
  });
  refreshLibraryView();
}

// --- Scan Downloads Modal ---
async function openScanDownloadsModal() {
  const modal = document.getElementById("scan-downloads-modal");
  const listEl = document.getElementById("scanned-files-list");
  modal.classList.add("active");
  listEl.innerHTML = `<div style="text-align: center; padding: 30px; color: var(--text-secondary);">Analyse de votre dossier Téléchargements en cours...</div>`;

  const data = await apiGet("/api/library/scan_downloads");
  if (!data || !data.ok || !data.files || data.files.length === 0) {
    listEl.innerHTML = `
      <div class="empty-state" style="padding: 24px;">
        <svg class="svg-icon empty-icon"><use href="#icon-scan"></use></svg>
        <h3>Aucun fichier de jeu trouvé dans Téléchargements</h3>
        <p>Les fichiers d'extension .nsp, .xci, .nds, .3ds, .cia, .iso, .rvz, .zip, .nes, .sfc, .gba, .n64, .dsk, .adf sont détectés automatiquement.</p>
      </div>
    `;
    return;
  }

  listEl.innerHTML = "";
  data.files.forEach((file) => {
    const item = document.createElement("div");
    item.className = "scanned-file-item";
    item.innerHTML = `
      <div>
        <strong style="font-size: 13.5px;">${esc(file.title)}</strong>
        <div style="font-size: 11.5px; color: var(--text-muted); margin-top: 2px;">
          <span>${esc(file.console_name)}</span> • <span>${esc(file.size_label)}</span> • <span style="font-family: monospace;">${esc(file.filename)}</span>
        </div>
      </div>
      <button class="pill-btn primary" onclick="importScannedFile('${esc(file.file_path)}', '${esc(file.console_id)}', '${esc(file.title)}')">
        <span>Importer</span>
      </button>
    `;
    listEl.appendChild(item);
  });
}

async function importScannedFile(filePath, consoleId, title) {
  showToast("Importation du jeu en cours...", "info");
  const res = await apiPost("/api/library/import", {
    file_path: filePath,
    console_id: consoleId,
    title: title,
  });
  if (res && res.ok) {
    showToast(`« ${title} » ajouté à votre bibliothèque !`, "success");
    closeScanDownloadsModal();
    refreshLibraryView();
  } else {
    showToast(res?.message || "Erreur d'importation.", "error");
  }
}

function closeScanDownloadsModal() {
  document.getElementById("scan-downloads-modal").classList.remove("active");
}

async function openImportDialog() {
  showToast("Sélectionnez votre jeu (NSP, NDS, 3DS, ISO, ROM) dans la boîte de dialogue Windows...", "info");
  const cid = state.libraryConsoleFilter !== "all" ? state.libraryConsoleFilter : "auto";
  const res = await apiPost("/api/library/import", { console_id: cid });
  if (res && res.ok) {
    showToast(`« ${res.game?.title || "Jeu"} » importé avec succès pour ${res.game?.console_name || ""} !`, "success");
    refreshLibraryView();
  } else if (!res?.cancelled) {
    showToast(res?.message || "Importation annulée.", "info");
  }
}

// --- Engines & PC Overview View ---
async function refreshEnginesView() {
  const data = await apiGet("/api/engines");
  if (data && data.ok) {
    renderEnginesView(data.consoles, data.system);
  }
}

function renderEnginesView(consoles, system) {
  if (system) {
    document.getElementById("hw-cpu-name").innerText = `${system.cpu_name} (${system.cpu_logical_cores} cœurs)`;
    document.getElementById("hw-gpu-name").innerText = system.gpus ? system.gpus.join(" / ") : "Carte Graphique Direct3D";
    document.getElementById("hw-ram-metric").innerText = `${system.ram_total_gb} Go (${system.ram_available_gb} Go disponibles)`;
    document.getElementById("hw-cores-metric").innerText = `${system.cpu_physical_cores} physiques / ${system.cpu_logical_cores} logiques`;
    document.getElementById("hw-tier-badge").innerText = system.pc_tier_label || "PC Polyvalent";
    document.getElementById("hw-advice-metric").innerText = system.pc_tier_description || "Parfait pour tous les jeux.";
  }

  const grid = document.getElementById("engines-grid");
  if (!grid || !consoles) return;
  grid.innerHTML = "";

  consoles.forEach((c) => {
    const card = document.createElement("div");
    card.className = "engine-card";

    let statusText = c.installed ? "Moteur Prêt & Configuré" : "Prêt à installer";
    let statusClass = c.installed ? "text-success" : "";

    card.innerHTML = `
      <div class="engine-card-header">
        <div>
          <h3 class="engine-card-title">${esc(c.name)}</h3>
          <div class="engine-card-engine">${esc(c.engine_name)}</div>
        </div>
        <span class="badge-tag" style="color: ${c.accent_color || '#818cf8'}; border: 1px solid ${c.accent_color || '#4f46e5'}44;">
          ${esc(c.weight_label)}
        </span>
      </div>

      <div class="engine-compat-row">
        <span class="${statusClass}">● ${statusText}</span>
        <span>•</span>
        <span>${esc(c.compatibility?.status_text || "Fluide")}</span>
      </div>

      <p style="font-size: 12.5px; color: var(--text-secondary); line-height: 1.5;">${esc(c.description)}</p>

      <div class="engine-actions-row">
        <button class="pill-btn primary" onclick="testEngine('${esc(c.console_id)}')">
          <svg class="svg-icon"><use href="#icon-play"></use></svg>
          <span>Tester</span>
        </button>
        <button class="pill-btn" onclick="openEngineGui('${esc(c.console_id)}')">
          <svg class="svg-icon"><use href="#icon-external"></use></svg>
          <span>Ouvrir l'émulateur</span>
        </button>
      </div>
    `;
    grid.appendChild(card);
  });
}

async function openEngineGui(consoleId) {
  showToast("Ouverture de l'interface de l'émulateur...", "info");
  const res = await apiPost("/api/engines/open", { console_id: consoleId });
  if (res && res.ok) {
    showToast(res.message || "Émulateur ouvert.", "success");
  } else {
    showToast(res?.message || "Impossible d'ouvrir l'émulateur.", "error");
  }
}

async function testEngine(consoleId) {
  showToast(`Lancement du test pour la console...`, "info");
  const res = await apiPost("/api/engines/test", { console_id: consoleId });
  if (res && res.ok) {
    showToast(res.message || "Test lancé avec succès !", "success");
  } else {
    showToast(res?.message || "Échec du test de l'émulateur.", "error");
  }
}

// --- Controllers & Interactive Remapper View ---
function startControllersPolling() {
  if (state.controllersPollingTimer) clearInterval(state.controllersPollingTimer);
  pollControllersOnce();
  state.controllersPollingTimer = setInterval(pollControllersOnce, 1500);
}

function stopControllersPolling() {
  if (state.controllersPollingTimer) {
    clearInterval(state.controllersPollingTimer);
    state.controllersPollingTimer = null;
  }
}

async function pollControllersOnce() {
  const data = await apiGet("/api/controllers");
  if (!data || !data.ok) return;
  state.controllers = data;
  renderControllersView(data);
}

function renderControllersView(data) {
  if (!data) return;
  const connected = data.connected || [];
  const listEl = document.getElementById("connected-controllers-list");
  if (listEl) {
    listEl.innerHTML = "";
    connected.forEach((dev) => {
      const item = document.createElement("div");
      item.className = "controller-device-item";

      let pressedText = "";
      if (dev.buttons_pressed && dev.buttons_pressed.length > 0) {
        pressedText = ` • Boutons pressés: ${dev.buttons_pressed.join(", ")}`;
      }

      let vibBtn = "";
      if (dev.supports_vibration) {
        vibBtn = `<button class="pill-btn" onclick="testVibration(${dev.port || 0})">Tester Vibration</button>`;
      }

      item.innerHTML = `
        <div>
          <div class="device-name">${esc(dev.name)}</div>
          <div class="device-api-tag">${esc(dev.api)} • Statut : ${esc(dev.status)}${esc(pressedText)}</div>
        </div>
        ${vibBtn}
      `;
      listEl.appendChild(item);
    });
  }

  // Active Profile Dropdown
  const profSelect = document.getElementById("controller-profile-select");
  const descEl = document.getElementById("profile-description");
  const swapCb = document.getElementById("swap-ab-xy-checkbox");
  const activeProf = data.active_profile;

  if (activeProf) {
    if (profSelect) profSelect.value = activeProf.id || "xbox_standard";
    if (descEl) descEl.innerText = activeProf.description || "";
    if (swapCb) swapCb.checked = activeProf.swap_ab_xy || false;
    renderRemapperTable(activeProf);
  }
}

function renderRemapperTable(prof) {
  const tbody = document.getElementById("remapper-table-body");
  if (!tbody || !prof) return;

  const kb = prof.keyboard_bindings || {};
  const gp = prof.gamepad_bindings || {};

  tbody.innerHTML = "";
  Object.keys(ACTION_LABELS).forEach((action) => {
    const tr = document.createElement("tr");

    const kbVal = kb[action] || "--";
    const gpVal = gp[action] || "--";

    tr.innerHTML = `
      <td><strong>${esc(ACTION_LABELS[action])}</strong></td>
      <td>
        <button
          class="remap-key-btn ${state.activeRemap?.action === action && state.activeRemap?.type === 'keyboard' ? 'listening' : ''}"
          onclick="startRemap('keyboard', '${action}')"
        >
          ${esc(kbVal.toUpperCase())}
        </button>
      </td>
      <td>
        <button
          class="remap-key-btn ${state.activeRemap?.action === action && state.activeRemap?.type === 'gamepad' ? 'listening' : ''}"
          onclick="startRemap('gamepad', '${action}')"
        >
          Bouton ${esc(gpVal)}
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function startRemap(type, action) {
  state.activeRemap = { type, action };
  const hint = document.getElementById("remap-active-hint");
  if (hint) {
    hint.style.display = "block";
    hint.innerText = type === "keyboard"
      ? `Appuyez sur une touche du clavier pour : ${ACTION_LABELS[action]}...`
      : `Appuyez sur un bouton de votre manette pour : ${ACTION_LABELS[action]}...`;
  }
  if (state.controllers?.active_profile) {
    renderRemapperTable(state.controllers.active_profile);
  }
}

function cancelRemap() {
  state.activeRemap = null;
  const hint = document.getElementById("remap-active-hint");
  if (hint) hint.style.display = "none";
  if (state.controllers?.active_profile) {
    renderRemapperTable(state.controllers.active_profile);
  }
}

function initGlobalKeyboardAndGamepadListeners() {
  // 1. Keyboard capture
  window.addEventListener("keydown", async (e) => {
    if (!state.activeRemap || state.activeRemap.type !== "keyboard") return;
    e.preventDefault();

    if (e.key === "Escape") {
      cancelRemap();
      return;
    }

    let keyName = e.key.toLowerCase();
    if (e.code.startsWith("Key")) keyName = e.code.replace("Key", "").toLowerCase();
    else if (e.code.startsWith("Digit")) keyName = `num${e.code.replace("Digit", "")}`;
    else if (e.code.startsWith("Numpad")) keyName = `keypad${e.code.replace("Numpad", "")}`;
    else if (e.key === "ArrowUp") keyName = "up";
    else if (e.key === "ArrowDown") keyName = "down";
    else if (e.key === "ArrowLeft") keyName = "left";
    else if (e.key === "ArrowRight") keyName = "right";
    else if (e.key === "Enter") keyName = "enter";
    else if (e.key === " ") keyName = "space";
    else if (e.key === "Shift") keyName = e.location === 2 ? "rshift" : "lshift";
    else if (e.key === "Control") keyName = e.location === 2 ? "rctrl" : "ctrl";

    const action = state.activeRemap.action;
    state.activeRemap = null;

    showToast(`Touche « ${keyName.toUpperCase()} » assignée à ${ACTION_LABELS[action]}.`, "info");
    const payload = {
      action: "update",
      keyboard_bindings: { [action]: keyName },
    };
    const res = await apiPost("/api/controllers", payload);
    if (res && res.ok) {
      state.controllers.active_profile = res.active_profile;
      cancelRemap();
    }
  });

  // 2. HTML5 Gamepad polling for remapping button
  function pollGamepadsForRemap() {
    if (state.activeRemap && state.activeRemap.type === "gamepad") {
      const gamepads = navigator.getGamepads ? navigator.getGamepads() : [];
      for (let gp of gamepads) {
        if (!gp) continue;
        for (let bIdx = 0; bIdx < gp.buttons.length; bIdx++) {
          if (gp.buttons[bIdx].pressed) {
            assignGamepadButton(bIdx);
            return;
          }
        }
      }
    }
    requestAnimationFrame(pollGamepadsForRemap);
  }
  requestAnimationFrame(pollGamepadsForRemap);
}

async function assignGamepadButton(buttonIndex) {
  if (!state.activeRemap) return;
  const action = state.activeRemap.action;
  state.activeRemap = null;

  showToast(`Bouton ${buttonIndex} assigné à ${ACTION_LABELS[action]}.`, "info");
  const payload = {
    action: "update",
    gamepad_bindings: { [action]: buttonIndex.toString() },
  };
  const res = await apiPost("/api/controllers", payload);
  if (res && res.ok) {
    state.controllers.active_profile = res.active_profile;
    cancelRemap();
  }
}

async function changeControllerProfile(profileId) {
  showToast("Application du profil de manette...", "info");
  const res = await apiPost("/api/controllers", { active_profile: profileId });
  if (res && res.ok) {
    state.controllers.active_profile = res.active_profile;
    renderControllersView(state.controllers);
    showToast("Profil de manette activé et synchronisé.", "success");
  }
}

async function toggleSwapButtons(isSwapped) {
  const res = await apiPost("/api/controllers", { swap_ab_xy: isSwapped });
  if (res && res.ok) {
    state.controllers.active_profile = res.active_profile;
    renderControllersView(state.controllers);
    showToast(isSwapped ? "Disposition Nintendo activée." : "Disposition Xbox standard activée.", "info");
  }
}

async function testVibration(port = 0) {
  const res = await apiPost("/api/controllers", { action: "vibrate", port });
  if (res && res.ok) {
    showToast(res.message || "Vibration envoyée !", "success");
  } else {
    showToast(res?.message || "Manette incompatible ou non détectée.", "error");
  }
}

async function resetControllerProfile() {
  const res = await apiPost("/api/controllers", { action: "reset_profile" });
  if (res && res.ok) {
    state.controllers.active_profile = res.active_profile;
    renderControllersView(state.controllers);
    showToast("Profil de manette réinitialisé.", "info");
  }
}

async function syncControllers() {
  showToast("Synchronisation des manettes vers tous les émulateurs...", "info");
  const res = await apiPost("/api/controllers", { action: "sync" });
  if (res && res.ok) {
    showToast("Fichiers de configuration manette générés avec succès !", "success");
  }
}

// --- Complete Settings Panel Management ---
function switchSettingsTab(tabId) {
  document.querySelectorAll(".settings-tabs-bar .tab-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.tab === tabId);
  });
  document.querySelectorAll(".settings-tab-pane").forEach((pane) => {
    pane.classList.toggle("active", pane.id === tabId);
  });
}

function populateGpuSelector(availableGpus) {
  const sel = document.getElementById("setting-preferred-gpu");
  if (!sel) return;
  sel.innerHTML = "";
  availableGpus.forEach((gpu) => {
    const opt = document.createElement("option");
    opt.value = gpu;
    opt.innerText = gpu === "Auto" ? "Sélection Automatique (Recommandé)" : gpu;
    sel.appendChild(opt);
  });
}

function populateSettingsForm(s) {
  if (!s) return;
  const gfx = s.graphics || {};
  const perf = s.performance_audio || {};
  const cAdv = s.controllers_advanced || {};
  const src = s.search_sources || {};

  // Graphics
  setVal("setting-preferred-gpu", gfx.preferred_gpu || "Auto");
  setVal("setting-video-backend", gfx.video_backend || "vulkan");
  setVal("setting-internal-res", gfx.internal_resolution_scale || 2);
  setVal("setting-aspect-ratio", gfx.aspect_ratio || "auto");
  setVal("setting-anti-aliasing", gfx.anti_aliasing || "None");
  setVal("setting-anisotropic", gfx.anisotropic_filtering || 4);
  setVal("setting-texture-filtering", gfx.texture_filtering || "bilinear");
  setVal("setting-window-res", gfx.window_resolution || "1280x720");
  setChk("setting-vsync", gfx.vsync ?? true);
  setChk("setting-fullscreen", gfx.fullscreen_on_boot ?? false);
  setChk("setting-fps-osd", gfx.show_fps_osd ?? false);
  setChk("setting-shader-cache", gfx.shader_cache ?? true);

  // Performance & Audio
  setVal("setting-power-profile", perf.power_profile || "auto");
  setVal("setting-cpu-jit", perf.cpu_jit_mode || "fast");
  setVal("setting-frame-limit", perf.frame_limit || 100);
  setVal("setting-audio-backend", perf.audio_backend || "xaudio2");
  setVal("setting-audio-volume", perf.audio_volume ?? 90);
  document.getElementById("setting-audio-volume-val").innerText = perf.audio_volume ?? 90;
  setVal("setting-audio-latency", perf.audio_latency_ms || 64);
  setChk("setting-audio-mute", perf.audio_mute ?? false);
  setChk("setting-threaded-video", perf.threaded_video ?? false);

  // Advanced Inputs
  setVal("setting-deadzone-left", Math.round((cAdv.left_stick_deadzone || 0.15) * 100));
  document.getElementById("setting-deadzone-left-val").innerText = Math.round((cAdv.left_stick_deadzone || 0.15) * 100);
  setVal("setting-deadzone-right", Math.round((cAdv.right_stick_deadzone || 0.15) * 100));
  document.getElementById("setting-deadzone-right-val").innerText = Math.round((cAdv.right_stick_deadzone || 0.15) * 100);
  setVal("setting-vibration-strength", cAdv.vibration_strength || 85);
  document.getElementById("setting-vibration-strength-val").innerText = cAdv.vibration_strength || 85;
  setVal("setting-trigger-threshold", cAdv.trigger_threshold || 0.50);
  setChk("setting-vibration-enabled", cAdv.vibration_enabled ?? true);
  setChk("setting-analog-to-dpad", cAdv.analog_to_dpad ?? true);
  setVal("setting-wii-mode", cAdv.wii_controller_type || "wiimote_nunchuk");
  setVal("setting-switch-mode", cAdv.switch_controller_type || "ProController");
  setVal("setting-amstrad-mode", cAdv.amstrad_input_mode || "joystick");
  setVal("setting-amiga-mode", cAdv.amiga_input_mode || "joystick");

  // Sources
  setChk("setting-src-archive", src.enable_archive_org ?? true);
  setChk("setting-src-osc", src.enable_wii_osc ?? true);
  setChk("setting-src-switch-hb", src.enable_switch_hb ?? true);
  setChk("setting-src-nxbrew", src.enable_nxbrew ?? Boolean(state.legalCompliance?.accepted_external_sources_disclaimer));
  setChk("setting-src-smallgames", src.enable_smallgames ?? Boolean(state.legalCompliance?.accepted_external_sources_disclaimer));
}

function collectSettingsPayload() {
  return {
    graphics: {
      preferred_gpu: getVal("setting-preferred-gpu"),
      video_backend: getVal("setting-video-backend"),
      internal_resolution_scale: parseInt(getVal("setting-internal-res"), 10),
      aspect_ratio: getVal("setting-aspect-ratio"),
      anti_aliasing: getVal("setting-anti-aliasing"),
      anisotropic_filtering: parseInt(getVal("setting-anisotropic"), 10),
      texture_filtering: getVal("setting-texture-filtering"),
      window_resolution: getVal("setting-window-res"),
      vsync: getChk("setting-vsync"),
      fullscreen_on_boot: getChk("setting-fullscreen"),
      show_fps_osd: getChk("setting-fps-osd"),
      shader_cache: getChk("setting-shader-cache"),
    },
    performance_audio: {
      power_profile: getVal("setting-power-profile"),
      cpu_jit_mode: getVal("setting-cpu-jit"),
      frame_limit: parseInt(getVal("setting-frame-limit"), 10),
      audio_backend: getVal("setting-audio-backend"),
      audio_volume: parseInt(getVal("setting-audio-volume"), 10),
      audio_latency_ms: parseInt(getVal("setting-audio-latency"), 10),
      audio_mute: getChk("setting-audio-mute"),
      threaded_video: getChk("setting-threaded-video"),
    },
    controllers_advanced: {
      left_stick_deadzone: parseInt(getVal("setting-deadzone-left"), 10) / 100.0,
      right_stick_deadzone: parseInt(getVal("setting-deadzone-right"), 10) / 100.0,
      vibration_strength: parseInt(getVal("setting-vibration-strength"), 10),
      trigger_threshold: parseFloat(getVal("setting-trigger-threshold")),
      vibration_enabled: getChk("setting-vibration-enabled"),
      analog_to_dpad: getChk("setting-analog-to-dpad"),
      wii_controller_type: getVal("setting-wii-mode"),
      switch_controller_type: getVal("setting-switch-mode"),
      amstrad_input_mode: getVal("setting-amstrad-mode"),
      amiga_input_mode: getVal("setting-amiga-mode"),
    },
    search_sources: {
      enable_archive_org: getChk("setting-src-archive"),
      enable_wii_osc: getChk("setting-src-osc"),
      enable_switch_hb: getChk("setting-src-switch-hb"),
      enable_nxbrew: getChk("setting-src-nxbrew"),
      enable_smallgames: getChk("setting-src-smallgames"),
    },
  };
}

async function saveAllSettings() {
  const payload = collectSettingsPayload();
  showToast("Enregistrement et application des réglages...", "info");
  const res = await apiPost("/api/settings", payload);
  if (res && res.ok) {
    state.settings = res.settings;
    showToast("Paramètres sauvegardés et appliqués aux émulateurs !", "success");
  } else {
    showToast(res?.message || "Erreur de sauvegarde.", "error");
  }
}

async function resetAllSettings() {
  if (!confirm("Voulez-vous rétablir tous les paramètres d'origine d'AetherDeck ?")) return;
  const res = await apiPost("/api/settings", { action: "reset" });
  if (res && res.ok) {
    state.settings = res.settings;
    populateSettingsForm(state.settings);
    showToast("Paramètres d'origine restaurés.", "info");
  }
}

async function openFolder(kind) {
  const res = await apiPost("/api/open_folder", { kind });
  if (res && res.ok) {
    showToast(`Dossier ouvert : ${res.path}`, "info");
  } else {
    showToast(res?.message || "Impossible d'ouvrir le dossier.", "error");
  }
}

function openExternalUrl(url) {
  apiPost("/api/open_external", { url });
}

// --- Legal Compliance & Third-Party Sources Consent Modal ---
function updateLegalUI() {
  const accepted = Boolean(state.legalCompliance?.accepted_external_sources_disclaimer);
  const cb = document.getElementById("legal-consent-checkbox");
  if (cb) cb.checked = accepted;

  const statusText = document.getElementById("legal-status-text");
  if (statusText) {
    statusText.innerText = accepted
      ? "Statut actuel : Consentement utilisateur enregistré — Sources externes tierces autorisées"
      : "Statut actuel : Sources externes tierces désactivées (Mode strict par défaut)";
    statusText.style.color = accepted ? "var(--accent-success)" : "var(--text-muted)";
  }

  const headerBtn = document.getElementById("header-legal-btn");
  if (headerBtn) {
    headerBtn.style.borderColor = accepted ? "rgba(16, 185, 129, 0.4)" : "";
  }
}

function openLegalConsentModal(pendingCallback = null) {
  state.pendingLegalCallback = typeof pendingCallback === "function" ? pendingCallback : null;
  updateLegalUI();
  const modal = document.getElementById("legal-consent-modal");
  if (modal) modal.classList.add("active");
}

function closeLegalConsentModal(e) {
  if (e && e.target.classList.contains("modal-card")) return;
  const modal = document.getElementById("legal-consent-modal");
  if (modal) modal.classList.remove("active");
  state.pendingLegalCallback = null;
}

function onToggleExternalSource(checkboxEl, sourceKey) {
  if (checkboxEl.checked && !state.legalCompliance?.accepted_external_sources_disclaimer) {
    checkboxEl.checked = false;
    openLegalConsentModal(() => {
      checkboxEl.checked = true;
    });
  }
}

async function submitLegalConsent(accepted) {
  const cb = document.getElementById("legal-consent-checkbox");
  if (accepted && cb && !cb.checked) {
    showToast("Veuillez cocher la case de certification légale avant d'activer les sources externes.", "error");
    return;
  }

  const res = await apiPost("/api/legal/consent", { accepted: Boolean(accepted) });
  if (res && res.ok) {
    state.legalCompliance = res.legal_compliance || {
      accepted_external_sources_disclaimer: Boolean(accepted),
    };
    if (state.settings && state.settings.search_sources) {
      state.settings.search_sources.enable_nxbrew = Boolean(accepted);
      state.settings.search_sources.enable_smallgames = Boolean(accepted);
    }
    setChk("setting-src-nxbrew", Boolean(accepted));
    setChk("setting-src-smallgames", Boolean(accepted));
    updateLegalUI();

    const modal = document.getElementById("legal-consent-modal");
    if (modal) modal.classList.remove("active");

    showToast(res.message || (accepted ? "Sources externes activées." : "Mode strict activé."), "success");

    if (accepted && typeof state.pendingLegalCallback === "function") {
      const fn = state.pendingLegalCallback;
      state.pendingLegalCallback = null;
      fn();
    } else {
      state.pendingLegalCallback = null;
      if (!accepted && (state.sourceFilter === "nxbrew" || state.sourceFilter === "smallgames")) {
        const sel = document.getElementById("source-filter-select");
        if (sel) sel.value = "all";
        state.sourceFilter = "all";
        state.page = 1;
        executeSearch(true);
      }
    }
  } else {
    showToast(res?.message || "Erreur lors de l'enregistrement du consentement légal.", "error");
  }
}

// --- Interactive Tutorial Modal ---
let currentTutorialStep = 1;

function openTutorialModal() {
  currentTutorialStep = 1;
  updateTutorialStepView();
  document.getElementById("tutorial-modal").classList.add("active");
}

function closeTutorialModal() {
  document.getElementById("tutorial-modal").classList.remove("active");
  apiPost("/api/tutorial", { tutorial_seen: true });
}

function nextTutorialStep() {
  if (currentTutorialStep < 5) {
    currentTutorialStep += 1;
    updateTutorialStepView();
  } else {
    closeTutorialModal();
  }
}

function prevTutorialStep() {
  if (currentTutorialStep > 1) {
    currentTutorialStep -= 1;
    updateTutorialStepView();
  }
}

function updateTutorialStepView() {
  for (let i = 1; i <= 5; i++) {
    const el = document.getElementById(`tutorial-step-${i}`);
    if (el) el.style.display = i === currentTutorialStep ? "block" : "none";
  }

  const prevBtn = document.getElementById("tutorial-prev-btn");
  const nextBtn = document.getElementById("tutorial-next-btn");
  if (prevBtn) prevBtn.style.visibility = currentTutorialStep > 1 ? "visible" : "hidden";
  if (nextBtn) nextBtn.innerText = currentTutorialStep === 5 ? "Commencer à jouer" : "Suivant";

  const dots = document.querySelectorAll(".tutorial-dots .dot");
  dots.forEach((d, idx) => {
    d.classList.toggle("active", idx + 1 === currentTutorialStep);
  });
}

// --- UI Helpers: Toast & Escape ---
function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;

  let iconName = "icon-check";
  if (type === "error") iconName = "icon-close";
  else if (type === "info") iconName = "icon-console";

  toast.innerHTML = `
    <svg class="svg-icon" style="width: 16px; height: 16px;"><use href="#${iconName}"></use></svg>
    <span>${esc(message)}</span>
  `;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
    toast.style.transition = "all 0.25s ease";
    setTimeout(() => toast.remove(), 250);
  }, 3200);
}

function esc(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function getVal(id) {
  const el = document.getElementById(id);
  return el ? el.value : "";
}

function setVal(id, val) {
  const el = document.getElementById(id);
  if (el) el.value = val;
}

function getChk(id) {
  const el = document.getElementById(id);
  return el ? el.checked : false;
}

function setChk(id, val) {
  const el = document.getElementById(id);
  if (el) el.checked = Boolean(val);
}
