/* ══════════════════════════════════════════════════════
   Air intérieur — Application logic
   ══════════════════════════════════════════════════════ */

const state = {
  data: null,
  filters: {
    search: "",
    author: "",
    category: "",
    type: "",
    status: "",
    themes: new Set(),
    chapter: "",
  },
  selectedKey: null,
  selectedPage: null,
};

/* ─── DOM refs ─── */
const els = {
  title: document.getElementById("site-title"),
  abstract: document.getElementById("site-abstract"),
  noteDownload: document.getElementById("note-download"),
  metaEntryCount: document.getElementById("meta-entry-count"),
  metaFulltextCount: document.getElementById("meta-fulltext-count"),
  metaPdfCount: document.getElementById("meta-pdf-count"),
  chapterNav: document.getElementById("chapter-nav"),
  authorSelect: document.getElementById("author-select"),
  searchInput: document.getElementById("search-input"),
  categoryFilters: document.getElementById("category-filters"),
  themeFilters: document.getElementById("theme-filters"),
  typeFilters: document.getElementById("type-filters"),
  statusFilters: document.getElementById("status-filters"),
  resetFilters: document.getElementById("reset-filters"),
  resultsCount: document.getElementById("results-count"),
  sourceList: document.getElementById("source-list"),
  chapterSummary: document.getElementById("chapter-summary"),
  detailEmpty: document.getElementById("detail-empty"),
  detailCard: document.getElementById("detail-card"),
  detailCitation: document.getElementById("detail-citation"),
  detailTitle: document.getElementById("detail-title"),
  detailBadges: document.getElementById("detail-badges"),
  detailKey: document.getElementById("detail-key"),
  detailBase: document.getElementById("detail-base"),
  detailActions: document.getElementById("detail-actions"),
  detailChapters: document.getElementById("detail-chapters"),
  detailPages: document.getElementById("detail-pages"),
  detailSynthesis: document.getElementById("detail-synthesis"),
  detailReperesSection: document.getElementById("detail-reperes-section"),
  detailReperes: document.getElementById("detail-reperes"),
  detailQuotesSection: document.getElementById("detail-quotes-section"),
  detailQuotes: document.getElementById("detail-quotes"),
  viewerSection: document.getElementById("viewer-section"),
  viewerActions: document.getElementById("viewer-actions"),
  pdfFrame: document.getElementById("pdf-frame"),
};

/* ─── Label maps ─── */
const CATEGORY_LABELS = {
  "theorie": "Cadre théorique",
  "air-interieur": "Air intérieur",
  "source-institutionnelle": "Source institutionnelle",
};

const THEME_LABELS = {
  "publicisation": "Publicisation",
  "imputation": "Imputation",
  "instruments": "Instruments",
  "inegalites": "Inégalités",
  "cadre-theorique": "Cadre théorique",
  "source-institutionnelle": "Institutionnel",
  "responsabilisation": "Responsabilisation",
  "risque-politique": "Risque politique",
  "medias": "Médias",
  "etiquetage": "Étiquetage",
  "ventilation": "Ventilation",
  "logement": "Logement",
  "expertise": "Expertise",
};

const TYPE_LABELS = {
  "book": "Livre",
  "article": "Article",
  "incollection": "Chapitre",
  "report": "Rapport",
  "online": "En ligne",
  "misc": "Autre",
};

const STATUS_LABELS = {
  "FULLTEXT": "Full text",
  "FULLTEXT-CIBLE": "Full text ciblé",
  "PARTIAL": "Partiel",
  "INDIRECT": "Indirect",
  "UNKNOWN": "Statut inconnu",
};

/* ─── Markdown helper ─── */
function renderMarkdown(src) {
  if (!src) return "";
  try {
    if (window.marked && typeof marked.parse === "function") {
      return marked.parse(src);
    }
    if (window.marked && typeof marked === "function") {
      return marked(src);
    }
  } catch (_) {
    /* fallback below */
  }
  // Minimal fallback: escape HTML and convert line breaks
  return src
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\n{2,}/g, "</p><p>")
    .replace(/\n/g, "<br>")
    .replace(/^/, "<p>")
    .replace(/$/, "</p>");
}

/* ─── Init ─── */
init();

async function init() {
  // 1. Try window.__SITE_DATA__ (loaded via data.js — works on file://)
  // 2. Fallback to fetch (works on HTTP servers / GitHub Pages)
  if (window.__SITE_DATA__) {
    state.data = window.__SITE_DATA__;
  } else {
    try {
      const response = await fetch("data.json");
      state.data = await response.json();
    } catch (err) {
      console.error("Failed to load data.json:", err);
      document.body.innerHTML =
        '<div style="padding:40px;font-family:sans-serif;color:#e03131">' +
        "<h2>Erreur de chargement</h2>" +
        "<p>Impossible de charger les données. Vérifie que <code>data.js</code> " +
        "ou <code>data.json</code> est bien présent à côté de <code>index.html</code>.</p></div>";
      return;
    }
  }

  // Configure marked (v4 API) — wrapped for safety
  try {
    if (window.marked && marked.setOptions) {
      marked.setOptions({ mangle: false, headerIds: false });
    }
  } catch (_) {
    /* ignore — renderMarkdown will handle it */
  }

  hydrateHeader();
  buildStaticControls();
  bindEvents();
  render();
}

/* ─── Header ─── */
function hydrateHeader() {
  const { note } = state.data;
  els.title.textContent = note.title || "Corpus air intérieur";
  els.abstract.textContent = note.abstract || "";

  const entryCount = state.data.entries.length;
  const fulltextCount = state.data.entries.filter(
    (e) => ["FULLTEXT", "FULLTEXT-CIBLE"].includes(e.access_status)
  ).length;
  const pdfCount =
    state.data.entries.filter((e) => e.pdf_file).length +
    (note.pdf_file ? 1 : 0);

  els.metaEntryCount.textContent = entryCount;
  els.metaFulltextCount.textContent = fulltextCount;
  els.metaPdfCount.textContent = pdfCount;

  if (note.pdf_file) {
    els.noteDownload.href = note.pdf_file;
  } else {
    els.noteDownload.classList.add("is-hidden");
  }
}

/* ─── Controls ─── */
function buildStaticControls() {
  buildChapterNav();
  buildAuthorSelect();
  buildChipGroup(
    els.categoryFilters,
    [...new Set(state.data.entries.map((e) => e.category).filter(Boolean))],
    "category"
  );
  buildChipGroup(
    els.typeFilters,
    [...new Set(state.data.entries.map((e) => e.type).filter(Boolean))],
    "type"
  );
  buildChipGroup(
    els.statusFilters,
    [...new Set(state.data.entries.map((e) => e.access_status).filter(Boolean))],
    "status"
  );
  buildChipGroup(
    els.themeFilters,
    [...new Set(state.data.entries.flatMap((e) => e.themes || []).filter(Boolean))],
    "theme"
  );
}

function buildChapterNav() {
  const frag = document.createDocumentFragment();
  frag.appendChild(
    createChapterButton(
      { slug: "", title: "Toutes les sources", summary: "" },
      true
    )
  );
  for (const ch of state.data.chapters) {
    frag.appendChild(createChapterButton(ch, false));
  }
  els.chapterNav.replaceChildren(frag);
}

function createChapterButton(chapter, isAll) {
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "chapter-button";
  btn.dataset.chapter = chapter.slug;
  btn.innerHTML = `<strong>${esc(chapter.title)}</strong>${
    chapter.summary
      ? `<small>${esc(
          chapter.summary.length > 120
            ? chapter.summary.slice(0, 120) + "…"
            : chapter.summary
        )}</small>`
      : ""
  }`;
  if (isAll) btn.classList.add("is-active");
  return btn;
}

function buildAuthorSelect() {
  const names = [
    ...new Set(
      state.data.entries.flatMap((e) => e.author_surnames || [])
    ),
  ].sort((a, b) => a.localeCompare(b, "fr"));
  for (const name of names) {
    const opt = document.createElement("option");
    opt.value = name;
    opt.textContent = name;
    els.authorSelect.appendChild(opt);
  }
}

function buildChipGroup(container, values, kind) {
  const sorted = values.sort((a, b) => a.localeCompare(b, "fr"));
  const frag = document.createDocumentFragment();
  for (const val of sorted) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "chip";
    btn.dataset.kind = kind;
    btn.dataset.value = val;
    btn.textContent = chipLabel(kind, val);
    frag.appendChild(btn);
  }
  container.replaceChildren(frag);
}

/* ─── Events ─── */
function bindEvents() {
  els.searchInput.addEventListener("input", (e) => {
    state.filters.search = e.target.value.trim().toLowerCase();
    render();
  });

  els.authorSelect.addEventListener("change", (e) => {
    state.filters.author = e.target.value;
    render();
  });

  document.querySelectorAll(".chips").forEach((group) => {
    group.addEventListener("click", (e) => {
      const chip = e.target.closest(".chip");
      if (!chip) return;
      const { kind, value } = chip.dataset;
      if (kind === "theme") {
        state.filters.themes.has(value)
          ? state.filters.themes.delete(value)
          : state.filters.themes.add(value);
      } else {
        state.filters[kind] =
          state.filters[kind] === value ? "" : value;
      }
      render();
    });
  });

  els.chapterNav.addEventListener("click", (e) => {
    const btn = e.target.closest(".chapter-button");
    if (!btn) return;
    state.filters.chapter = btn.dataset.chapter || "";
    render();
  });

  els.resetFilters.addEventListener("click", () => {
    state.filters = {
      search: "",
      author: "",
      category: "",
      type: "",
      status: "",
      themes: new Set(),
      chapter: "",
    };
    els.searchInput.value = "";
    els.authorSelect.value = "";
    render();
  });
}

/* ─── Render loop ─── */
function render() {
  syncActiveControls();
  const filtered = getFilteredEntries();
  renderResultsCount(filtered.length);
  renderChapterSummary();
  syncSelection(filtered);
  renderSourceList(filtered);
  renderDetail();
}

function syncActiveControls() {
  document.querySelectorAll(".chip").forEach((chip) => {
    const { kind, value } = chip.dataset;
    const active =
      kind === "theme"
        ? state.filters.themes.has(value)
        : state.filters[kind] === value;
    chip.classList.toggle("is-active", active);
  });

  document.querySelectorAll(".chapter-button").forEach((btn) => {
    btn.classList.toggle(
      "is-active",
      (btn.dataset.chapter || "") === state.filters.chapter
    );
  });
}

function getFilteredEntries() {
  return state.data.entries.filter((entry) => {
    if (
      state.filters.chapter &&
      !(entry.used_in_chapters || []).includes(state.filters.chapter)
    )
      return false;
    if (
      state.filters.author &&
      !(entry.author_surnames || []).includes(state.filters.author)
    )
      return false;
    if (state.filters.category && entry.category !== state.filters.category)
      return false;
    if (state.filters.type && entry.type !== state.filters.type) return false;
    if (state.filters.status && entry.access_status !== state.filters.status)
      return false;
    if (state.filters.themes.size > 0) {
      const et = new Set(entry.themes || []);
      for (const t of state.filters.themes) if (!et.has(t)) return false;
    }
    if (state.filters.search) {
      const hay = [
        entry.key,
        entry.title,
        ...(entry.author || []),
        entry.synthesis_md,
        ...(entry.repere_bullets || []),
        ...(entry.quote_bullets || []),
      ]
        .join(" ")
        .toLowerCase();
      if (!hay.includes(state.filters.search)) return false;
    }
    return true;
  });
}

function renderResultsCount(count) {
  els.resultsCount.textContent = `${count} source${count > 1 ? "s" : ""}`;
}

function renderChapterSummary() {
  if (!state.filters.chapter) {
    els.chapterSummary.classList.add("is-hidden");
    els.chapterSummary.innerHTML = "";
    return;
  }
  const ch = state.data.chapters.find(
    (c) => c.slug === state.filters.chapter
  );
  if (!ch) {
    els.chapterSummary.classList.add("is-hidden");
    return;
  }
  els.chapterSummary.classList.remove("is-hidden");
  const isCollapsed = els.chapterSummary.classList.contains("is-collapsed");
  els.chapterSummary.innerHTML = `
    <button type="button" class="accordion-toggle" id="chapter-toggle">
      <p class="eyebrow">Fil de l'argument</p>
      <svg class="accordion-chevron${isCollapsed ? " is-collapsed" : ""}" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
    </button>
    <div class="accordion-body${isCollapsed ? " is-hidden" : ""}">
      <h3>${esc(ch.title)}</h3>
      <p>${esc(ch.summary || "")}</p>
      <p class="muted">${ch.citation_count} référence${ch.citation_count > 1 ? "s" : ""} mobilisée${ch.citation_count > 1 ? "s" : ""}</p>
    </div>
  `;
  document.getElementById("chapter-toggle")?.addEventListener("click", () => {
    els.chapterSummary.classList.toggle("is-collapsed");
    const body = els.chapterSummary.querySelector(".accordion-body");
    const chevron = els.chapterSummary.querySelector(".accordion-chevron");
    body?.classList.toggle("is-hidden");
    chevron?.classList.toggle("is-collapsed");
  });
}

function syncSelection(filtered) {
  const keys = new Set(filtered.map((e) => e.key));
  if (!state.selectedKey || !keys.has(state.selectedKey)) {
    state.selectedKey = filtered[0]?.key || null;
    state.selectedPage = null;
  }
}

function renderSourceList(entries) {
  const frag = document.createDocumentFragment();
  for (const entry of entries) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "source-card";
    if (entry.key === state.selectedKey) btn.classList.add("is-selected");
    btn.addEventListener("click", () => {
      state.selectedKey = entry.key;
      state.selectedPage = null;
      // Update selection highlight without rebuilding the list
      els.sourceList.querySelectorAll(".source-card").forEach((card, i) => {
        card.classList.toggle("is-selected", card === btn);
      });
      renderDetail();
      // Scroll detail into view on mobile
      if (window.innerWidth <= 1280) {
        document
          .getElementById("detail-pane")
          ?.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    });
    btn.innerHTML = `
      <p class="source-card__citation">${esc(fmtCitation(entry))}</p>
      <h3 class="source-card__title">${esc(entry.title)}</h3>
      <div class="badges">${renderBadges(entry)}</div>
    `;
    frag.appendChild(btn);
  }
  els.sourceList.replaceChildren(frag);
}

/* ─── Detail rendering ─── */
function renderDetail() {
  const entry = state.data.entries.find((e) => e.key === state.selectedKey);
  if (!entry) {
    els.detailEmpty.classList.remove("is-hidden");
    els.detailCard.classList.add("is-hidden");
    return;
  }

  els.detailEmpty.classList.add("is-hidden");
  els.detailCard.classList.remove("is-hidden");

  els.detailCitation.textContent = fmtCitation(entry);
  els.detailTitle.textContent = entry.title;
  els.detailBadges.innerHTML = renderBadges(entry);
  els.detailKey.textContent = entry.key;

  els.detailBase.textContent = entry.base_de_lecture
    ? `Base de lecture : ${entry.base_de_lecture}`
    : "";
  els.detailBase.classList.toggle("is-hidden", !entry.base_de_lecture);

  els.detailSynthesis.innerHTML = renderMarkdown(entry.synthesis_md);

  renderDetailActions(entry);
  renderDetailLinks(entry);
  renderBulletSection(
    entry.repere_bullets,
    els.detailReperesSection,
    els.detailReperes
  );
  renderBulletSection(
    entry.quote_bullets,
    els.detailQuotesSection,
    els.detailQuotes
  );
  renderViewer(entry);
}

function renderDetailActions(entry) {
  const parts = [];
  if (entry.pdf_file) {
    parts.push(
      `<a class="btn btn--sm" href="${attr(entry.pdf_file)}" target="_blank" rel="noopener">` +
        `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>` +
        `Ouvrir</a>`
    );
    parts.push(
      `<a class="btn btn--sm" href="${attr(entry.pdf_file)}" download>` +
        `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>` +
        `Télécharger</a>`
    );
  }
  if (entry.url) {
    parts.push(
      `<a class="btn btn--sm" href="${attr(entry.url)}" target="_blank" rel="noopener">Lien source</a>`
    );
  }
  els.detailActions.innerHTML = parts.join("");
}

function renderDetailLinks(entry) {
  // Chapter links
  const chLinks = (entry.used_in_chapters || [])
    .map((slug) => {
      const ch = state.data.chapters.find((c) => c.slug === slug);
      if (!ch) return "";
      return `<button type="button" class="link-pill" data-jump-chapter="${attr(slug)}">${esc(ch.title)}</button>`;
    })
    .join("");
  els.detailChapters.innerHTML = chLinks
    ? `<strong>Utilisé dans</strong>${chLinks}`
    : "";

  // Page links
  const pgLinks = (entry.page_refs || [])
    .map((ref) => {
      if (entry.pdf_file && entry.pdf_kind === "pdf") {
        return `<button type="button" class="link-pill" data-page="${ref.page}">${esc(ref.label)}</button>`;
      }
      return `<span class="link-pill">${esc(ref.label)}</span>`;
    })
    .join("");
  els.detailPages.innerHTML = pgLinks
    ? `<strong>Pages utiles</strong>${pgLinks}`
    : "";

  // Bind chapter jump
  els.detailChapters
    .querySelectorAll("[data-jump-chapter]")
    .forEach((btn) => {
      btn.addEventListener("click", () => {
        state.filters.chapter = btn.dataset.jumpChapter;
        render();
      });
    });

  // Bind page jump
  els.detailPages.querySelectorAll("[data-page]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.selectedPage = Number(btn.dataset.page);
      renderViewer(entry);
    });
  });
}

function renderBulletSection(items, sectionEl, listEl) {
  if (!items || items.length === 0) {
    sectionEl.classList.add("is-hidden");
    listEl.innerHTML = "";
    return;
  }
  sectionEl.classList.remove("is-hidden");
  listEl.innerHTML = items
    .map((item) => `<li>${esc(item)}</li>`)
    .join("");
}

function renderViewer(entry) {
  const canEmbed = entry.pdf_file && entry.pdf_kind === "pdf";
  if (!canEmbed) {
    els.viewerSection.classList.add("is-hidden");
    els.pdfFrame.removeAttribute("src");
    els.viewerActions.innerHTML = "";
    return;
  }

  const defaultPage = entry.page_refs?.[0]?.page || 1;
  const page = state.selectedPage || defaultPage;
  const src = `${entry.pdf_file}#page=${page}`;

  els.viewerSection.classList.remove("is-hidden");
  els.pdfFrame.src = src;
  els.viewerActions.innerHTML = `
    <button type="button" class="btn btn--sm" id="fullscreen-btn">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/><line x1="21" y1="3" x2="14" y2="10"/><line x1="3" y1="21" x2="10" y2="14"/></svg>
      Plein écran</button>
    <a class="btn btn--sm" href="${attr(entry.pdf_file)}" download>Télécharger</a>
  `;
  document.getElementById("fullscreen-btn")?.addEventListener("click", () => {
    const frame = els.pdfFrame;
    if (frame.requestFullscreen) {
      frame.requestFullscreen();
    } else if (frame.webkitRequestFullscreen) {
      frame.webkitRequestFullscreen();
    } else if (frame.msRequestFullscreen) {
      frame.msRequestFullscreen();
    }
  });
}

/* ─── Helpers ─── */
function fmtCitation(entry) {
  const authors =
    (entry.author || []).join(" · ") || "Référence sans auteur";
  const year = entry.year ? `, ${entry.year}` : "";
  return `${authors}${year}`;
}

function renderBadges(entry) {
  const p = [];
  if (entry.access_status) {
    p.push(
      `<span class="badge badge--status-${slugify(entry.access_status)}">${esc(STATUS_LABELS[entry.access_status] || entry.access_status)}</span>`
    );
  }
  if (entry.category) {
    p.push(
      `<span class="badge badge--category">${esc(CATEGORY_LABELS[entry.category] || entry.category)}</span>`
    );
  }
  if (entry.type) {
    p.push(
      `<span class="badge badge--type">${esc(TYPE_LABELS[entry.type] || entry.type)}</span>`
    );
  }
  for (const t of entry.themes || []) {
    p.push(
      `<span class="badge badge--theme">${esc(THEME_LABELS[t] || t)}</span>`
    );
  }
  return p.join("");
}

function chipLabel(kind, value) {
  if (kind === "category") return CATEGORY_LABELS[value] || value;
  if (kind === "type") return TYPE_LABELS[value] || value;
  if (kind === "status") return STATUS_LABELS[value] || value;
  if (kind === "theme") return THEME_LABELS[value] || value;
  return value;
}

function esc(v = "") {
  return String(v)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function attr(v = "") {
  return esc(v);
}

function slugify(v = "") {
  return String(v)
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}
