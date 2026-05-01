/* # ╔═════════════════════════════════════════════════════════════════╗ */
/* # ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║ */
/* # ║  ▄█▛▘‾ ‾▝▜█▄  │ Sync Ui – V1.0.0                               │║ */
/* # ║ ██▘       ▝██ │                                                │║ */
/* # ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║ */
/* # ║ ███▄_   _▄███ │ By Ir.On                                       │║ */
/* # ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║ */
/* # ║ ██ ▀ ████████ │ Ultima modificacao: 2026-02-03 - 15:57         │║ */
/* # ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║ */
/* # ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║ */
/* # ║      ██    ▜▛ │ Caminho:                                       │║ */
/* # ║      ▜▛       │ static/sync_ui.js                              │║ */
/* # ║               ├────────────────────────────────────────────────┤║ */
/* # ║               │ Detalhes:                                      │║ */
/* # ║               │ * V1.0.0 - [sem detalhes]                      │║ */
/* # ║               │                                                │║ */
/* # ║               └────────────────────────────────────────────────┘║ */
/* # ╚═════════════════════════════════════════════════════════════════╝ */

(function () {
  "use strict";

  /* =====================================================
     CONFIG
     ===================================================== */

  const STORAGE_KEY = "ix.dealscore.sync.state";
  const DEAL_URL_BASE = "https://buzzlead.pipedrive.com/deal/";

  /* =====================================================
     ESTADO GLOBAL
     ===================================================== */

  const syncState = {
    running: false,
    paused: false,
    timer: null,

    filterId: null,
    start: 0,
    limit: 50,
    maxDeals: null,
    mode: "test",
    intervalMs: 30000,

    total: null,        // pode ser null (desconhecido)
    processed: 0,

    startedAt: null,
  };

  /* =====================================================
     ELEMENTOS DE UI
     ===================================================== */

  const formEl = document.getElementById("sync-form");
  const logEl = document.getElementById("log");
  const progressWrapperEl = document.getElementById("progress-wrapper");
  const progressBarEl = document.getElementById("progress-bar");
  const statsEl = document.getElementById("sync-stats");

  const btnStart = document.getElementById("btn-start");
  const btnPause = document.getElementById("btn-pause");
  const btnResume = document.getElementById("btn-resume");

  /* =====================================================
     LOCAL STORAGE
     ===================================================== */

  function saveState() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(syncState));
  }

  function loadState() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return;
      Object.assign(syncState, JSON.parse(raw));
    } catch (_) {}
  }

  function clearTimer() {
    if (syncState.timer) {
      clearTimeout(syncState.timer);
      syncState.timer = null;
    }
  }

  /* =====================================================
     UI HELPERS
     ===================================================== */

  function lockForm(lock) {
    formEl.querySelectorAll("input, select").forEach(el => {
      el.disabled = lock;
    });
  }

  function setRunningUI() {
    btnStart.classList.add("hidden");
    btnPause.classList.remove("hidden");
    btnResume.classList.add("hidden");
    lockForm(true);
  }

  function setPausedUI() {
    btnPause.classList.add("hidden");
    btnResume.classList.remove("hidden");
  }

  function setFinishedUI() {
    btnStart.classList.remove("hidden");
    btnPause.classList.add("hidden");
    btnResume.classList.add("hidden");
    lockForm(false);
  }

  function appendLog(msg) {
    const ts = new Date().toLocaleTimeString();
    logEl.innerHTML += `[${ts}] ${msg}<br>`;
    logEl.scrollTop = logEl.scrollHeight;
  }

  function appendDealLog(results) {
    if (!Array.isArray(results)) return;

    results.forEach(d => {
      if (!d || !d.deal_id) return;

      const title = d.deal_title || "Sem título";
      const url = d.deal_url || `${DEAL_URL_BASE}${d.deal_id}`;
      const score =
        Number.isFinite(d.deal_score) ? ` -> ${d.deal_score}pts` : "";

      appendLog(
        `→ <a href="${url}" target="_blank">${title} (#${d.deal_id})</a>${score}`
      );
    });
  }

  function formatTime(seconds) {
    if (!isFinite(seconds) || seconds <= 0) return "—";
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}m ${s}s`;
  }

  function updateStats() {
    if (!syncState.startedAt) return;

    if (!syncState.total) {
      statsEl.innerHTML = "<em>Total desconhecido</em>";
      return;
    }

    const elapsed = (Date.now() - syncState.startedAt) / 1000;
    const rate = elapsed > 0 ? syncState.processed / elapsed : 0;
    const remaining = syncState.total - syncState.processed;
    const eta = rate > 0 ? remaining / rate : null;

    statsEl.innerHTML = `
      <strong>Processados:</strong> ${syncState.processed} / ${syncState.total}<br>
      <strong>Velocidade:</strong> ${(rate * 60).toFixed(1)} deals/min<br>
      <strong>ETA:</strong> ${formatTime(eta)}
    `;
  }

  function updateProgress() {
    if (!syncState.total) return;
    const pct = Math.min(
      100,
      Math.round((syncState.processed / syncState.total) * 100)
    );
    progressBarEl.style.width = pct + "%";
    updateStats();
  }

  /* =====================================================
     API
     ===================================================== */

  async function fetchTotalDeals(filterId) {
    try {
      const r = await fetch(`/sync/count?filter_id=${filterId}`);
      const j = await r.json();
      return Number.isFinite(j.total) && j.total > 0 ? j.total : null;
    } catch {
      return null;
    }
  }

  async function fetchBatch(limitOverride) {
    const qs = new URLSearchParams({
      filter_id: syncState.filterId,
      start: syncState.start,
      limit: limitOverride ?? syncState.limit,
      mode: syncState.mode,
    });
    const r = await fetch(`/sync/?${qs.toString()}`);
    return r.json();
  }

  /* =====================================================
     LOOP PRINCIPAL (CORRETO E À PROVA DE LOOP)
     ===================================================== */

  async function runBatch() {
    if (!syncState.running || syncState.paused) return;

    if (
      Number.isFinite(syncState.maxDeals) &&
      syncState.maxDeals > 0 &&
      syncState.processed >= syncState.maxDeals
    ) {
      appendLog("✅ Limite de rolagens atingido");
      finishSync();
      return;
    }

    appendLog(`⏳ Processando start=${syncState.start}`);

    let batchLimit = syncState.limit;
    if (Number.isFinite(syncState.maxDeals) && syncState.maxDeals > 0) {
      const remaining = syncState.maxDeals - syncState.processed;
      if (remaining <= 0) {
        appendLog("✅ Limite de rolagens atingido");
        finishSync();
        return;
      }
      batchLimit = Math.min(syncState.limit, remaining);
    }

    const data = await fetchBatch(batchLimit);
    const results = Array.isArray(data.results) ? data.results : [];

    // ✅ ÚNICA REGRA DE PARADA CONFIÁVEL
    if (results.length === 0) {
      appendLog("✅ Sync finalizado (nenhum deal retornado)");
      finishSync();
      return;
    }

    appendDealLog(results);

    syncState.processed += results.length;
    syncState.start += batchLimit;

    updateProgress();
    saveState();

    syncState.timer = setTimeout(runBatch, syncState.intervalMs);
  }

  function finishSync() {
    syncState.running = false;
    clearTimeout(syncState.timer);
    saveState();
    setFinishedUI();
    updateStats();
  }

  /* =====================================================
     CONTROLES
     ===================================================== */

  formEl.addEventListener("submit", async (e) => {
    e.preventDefault();

    clearTimer();

    syncState.filterId = Number(document.getElementById("filter_id").value);
    syncState.start = Number(document.getElementById("start").value);
    syncState.limit = Number(document.getElementById("limit").value);
    const maxDealsRaw = Number(document.getElementById("max_deals").value);
    syncState.maxDeals =
      Number.isFinite(maxDealsRaw) && maxDealsRaw > 0 ? maxDealsRaw : null;
    syncState.mode = document.getElementById("mode").value;
    syncState.intervalMs =
      Number(document.getElementById("interval").value) * 1000;

    syncState.running = true;
    syncState.paused = false;
    syncState.processed = 0;
    syncState.startedAt = Date.now();

    logEl.innerHTML = "";
    progressWrapperEl.classList.remove("hidden");
    progressBarEl.style.width = "0%";
    statsEl.innerHTML = "";

    setRunningUI();
    appendLog("▶ Sync iniciado");

    syncState.total = await fetchTotalDeals(syncState.filterId);
    if (Number.isFinite(syncState.maxDeals) && syncState.maxDeals > 0) {
      syncState.total = syncState.total
        ? Math.min(syncState.total, syncState.maxDeals)
        : syncState.maxDeals;
    }
    appendLog(
      syncState.total
        ? `ℹ Total de deals no filtro: ${syncState.total}`
        : "ℹ Total de deals desconhecido"
    );

    saveState();
    runBatch();
  });

  btnPause.addEventListener("click", () => {
    syncState.paused = true;
    clearTimer();
    saveState();
    appendLog("⏸ Sync pausado");
    setPausedUI();
  });

  btnResume.addEventListener("click", () => {
    if (!syncState.running) return;
    syncState.paused = false;
    appendLog("▶ Sync retomado");
    setRunningUI();
    runBatch();
  });

  /* =====================================================
     RESTORE AUTOMÁTICO
     ===================================================== */

  loadState();

  if (syncState.running && !syncState.paused) {
    progressWrapperEl.classList.remove("hidden");
    setRunningUI();
    appendLog("♻ Restaurando sync em andamento...");
    updateProgress();
    runBatch();
  }

})();

/*
  ▗▅▅▖   
▄▛▘‾‾▝▜▄ 
█▖    ▗█   © 2026 Copyright
███▅▅███   Ir.On
██●█████ 
▜▛  █▜▛█   "Feito com muito carinho."
    █  ▀ 
    ▀    
*/
