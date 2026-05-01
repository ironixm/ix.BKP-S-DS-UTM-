/* # ╔═════════════════════════════════════════════════════════════════╗ */
/* # ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║ */
/* # ║  ▄█▛▘‾ ‾▝▜█▄  │ Ix Delscore Sync – V1.0.0                      │║ */
/* # ║ ██▘       ▝██ │                                                │║ */
/* # ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║ */
/* # ║ ███▄_   _▄███ │ By Ir.On                                       │║ */
/* # ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║ */
/* # ║ ██ ▀ ████████ │ Ultima modificacao: 2026-02-03 - 15:41         │║ */
/* # ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║ */
/* # ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║ */
/* # ║      ██    ▜▛ │ Caminho:                                       │║ */
/* # ║      ▜▛       │ modules/ix-delscore-sync.js                    │║ */
/* # ║               ├────────────────────────────────────────────────┤║ */
/* # ║               │ Detalhes:                                      │║ */
/* # ║               │ * V1.0.0 - [sem detalhes]                      │║ */
/* # ║               │                                                │║ */
/* # ║               └────────────────────────────────────────────────┘║ */
/* # ╚═════════════════════════════════════════════════════════════════╝ */

(function () {
  var timer = null;
  var running = false;
  var total = 0;
  var processed = 0;
  var start = 0;

  function qs(id) {
    return document.getElementById(id);
  }

  function log(msg) {
    qs("log").textContent += msg + "\n";
    qs("log").scrollTop = qs("log").scrollHeight;
  }

  function setProgress() {
    if (!total) return;
    var pct = Math.min(100, Math.round((processed / total) * 100));
    qs("progress-bar").style.width = pct + "%";
    qs("progress-text").textContent =
      processed + " / " + total + " (" + pct + "%)";
  }

  function stop() {
    running = false;
    if (timer) clearInterval(timer);
    log("⏹ Sincronização finalizada");
  }

  function runBatch(cfg) {
    if (!running) return;

    var url =
      "/sync/?filter_id=" +
      cfg.filter_id +
      "&start=" +
      start +
      "&limit=" +
      cfg.limit +
      "&mode=" +
      cfg.mode;

    fetch(url)
      .then(function (r) {
        return r.json();
      })
      .then(function (data) {
        if (!data.processed || data.processed === 0) {
          log("✔ Fim dos dados");
          stop();
          return;
        }

        processed += data.processed;
        start += cfg.limit;

        log("✔ Processados: " + data.processed);
        setProgress();

        if (processed >= total) {
          log("✔ 100% concluído");
          stop();
        }
      })
      .catch(function (e) {
        log("❌ Erro: " + e.message);
        stop();
      });
  }

  function init(e) {
    e.preventDefault();
    if (running) return;

    var cfg = {
      filter_id: qs("filter_id").value,
      limit: parseInt(qs("limit").value, 10),
      mode: qs("mode").value,
      interval: parseInt(qs("interval").value, 10) * 1000,
    };

    start = parseInt(qs("start").value, 10) || 0;
    processed = 0;
    running = true;
    qs("log").textContent = "";

    fetch("/sync/count?filter_id=" + cfg.filter_id)
      .then(function (r) {
        return r.json();
      })
      .then(function (data) {
        total = data.total || 0;
        log("📊 Total de deals: " + total);
        setProgress();

        runBatch(cfg);
        timer = setInterval(function () {
          runBatch(cfg);
        }, cfg.interval);
      });
  }

  document.addEventListener("DOMContentLoaded", function () {
    qs("sync-form").addEventListener("submit", init);
    qs("stop").addEventListener("click", stop);
  });
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
