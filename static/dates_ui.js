/* # ╔═════════════════════════════════════════════════════════════════╗ */
/* # ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║ */
/* # ║  ▄█▛▘‾ ‾▝▜█▄  │ Dates Ui – V1.0.0                              │║ */
/* # ║ ██▘       ▝██ │                                                │║ */
/* # ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║ */
/* # ║ ███▄_   _▄███ │ By Ir.On                                       │║ */
/* # ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║ */
/* # ║ ██ ▀ ████████ │ Ultima modificacao: 2026-02-11 - 12:55         │║ */
/* # ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║ */
/* # ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║ */
/* # ║      ██    ▜▛ │ Caminho:                                       │║ */
/* # ║      ▜▛       │ static/dates_ui.js                             │║ */
/* # ║               ├────────────────────────────────────────────────┤║ */
/* # ║               │ Detalhes:                                      │║ */
/* # ║               │ * V1.0.0 - [sem detalhes]                      │║ */
/* # ║               │                                                │║ */
/* # ║               └────────────────────────────────────────────────┘║ */
/* # ╚═════════════════════════════════════════════════════════════════╝ */

const form = document.getElementById("dates-form");
const previewStatus = document.getElementById("preview-status");
const previewSummary = document.getElementById("preview-summary");
const tableBody = document.querySelector("#dates-table tbody");
const normalizeBtn = document.getElementById("btn-normalize");
const normalizeStatus = document.getElementById("normalize-status");

let currentRows = [];

function formatDate(value) {
  if (!value) return "-";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toISOString().slice(0, 10);
}

function diffDays(dates) {
  const valid = dates.filter((d) => d);
  if (valid.length < 2) return 0;
  const timestamps = valid.map((d) => new Date(d).getTime());
  const min = Math.min(...timestamps);
  const max = Math.max(...timestamps);
  return Math.round((max - min) / (1000 * 60 * 60 * 24));
}

function pickDefaultTarget(row) {
  const candidates = [
    { key: "person", date: row.person_add_time },
    { key: "org", date: row.org_add_time },
    { key: "deal", date: row.deal_add_time },
  ].filter((item) => item.date);

  if (!candidates.length) return null;
  candidates.sort((a, b) => new Date(a.date) - new Date(b.date));
  return candidates[0].key;
}

function buildDateCell(row, idx, key, label) {
  const dateValue = row[`${key}_add_time`];
  const safeDate = formatDate(dateValue);
  const radioName = `final_date_${idx}`;
  const disabled = dateValue ? "" : "disabled";

  return `
    <span class="ix-date-cell ${row._highlightClass}">
      <input type="radio" name="${radioName}" value="${key}" ${disabled}>
      <span>${safeDate}</span>
    </span>
  `;
}

function renderTable(rows) {
  tableBody.innerHTML = "";
  currentRows = rows;

  rows.forEach((row, idx) => {
    const delta = diffDays([
      row.person_add_time,
      row.org_add_time,
      row.deal_add_time,
    ]);

    let highlight = "";
    if (delta >= 14) {
      highlight = "ix-date-danger";
    } else if (delta >= 7) {
      highlight = "ix-date-warn";
    }
    row._highlightClass = highlight;

    const personCell = buildDateCell(row, idx, "person");
    const orgCell = buildDateCell(row, idx, "org");
    const dealCell = buildDateCell(row, idx, "deal");

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.person_name || "-"}</td>
      <td>${personCell}</td>
      <td>${row.org_name || "-"}</td>
      <td>${orgCell}</td>
      <td>${row.deal_title || "-"}</td>
      <td>${dealCell}</td>
      <td>${delta}</td>
    `;
    tableBody.appendChild(tr);

    const defaultTarget = pickDefaultTarget(row);
    if (defaultTarget) {
      const radio = tr.querySelector(`input[value="${defaultTarget}"]`);
      if (radio) radio.checked = true;
    }
  });
}

function getSelectedRangeMode() {
  return document.querySelector("input[name=range_mode]:checked")?.value;
}

function getSelectedDateField() {
  return document.querySelector("input[name=date_field]:checked")?.value;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  previewStatus.textContent = "Carregando...";
  normalizeStatus.textContent = "";
  normalizeBtn.disabled = true;

  const payload = {
    range_mode: getSelectedRangeMode(),
    date_field: getSelectedDateField(),
    last_days: document.getElementById("last_days").value,
    after_date: document.getElementById("after_date").value,
    before_date: document.getElementById("before_date").value,
    start_date: document.getElementById("start_date").value,
    end_date: document.getElementById("end_date").value,
  };

  try {
    const res = await fetch("/dates/preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || "Erro ao carregar dados");
    }

    renderTable(data.rows || []);
    previewSummary.textContent = `Encontrados: ${data.rows.length} | Scanned: ${data.scanned}${data.truncated ? " | Limite de scan atingido" : ""}`;
    normalizeBtn.disabled = !data.rows.length;
    previewStatus.textContent = "";
  } catch (err) {
    previewStatus.textContent = err.message;
  }
});

normalizeBtn.addEventListener("click", async () => {
  normalizeStatus.textContent = "Normalizando...";

  const rows = [];
  const trs = Array.from(tableBody.querySelectorAll("tr"));
  trs.forEach((tr, idx) => {
    const selected = tr.querySelector(`input[name=final_date_${idx}]:checked`);
    if (!selected) return;

    const row = currentRows[idx];
    const targetKey = selected.value;
    const targetDate = row[`${targetKey}_add_time`];
    if (!targetDate) return;

    rows.push({
      deal_id: row.deal_id,
      person_id: row.person_id,
      org_id: row.org_id,
      target_date: targetDate,
    });
  });

  if (!rows.length) {
    normalizeStatus.textContent = "Selecione pelo menos uma data.";
    return;
  }

  try {
    const res = await fetch("/dates/normalize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rows }),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || "Erro ao normalizar");
    }

    const ok = data.results.filter((r) => r.deal && r.deal === "ok").length;
    normalizeStatus.textContent = `Normalizacao concluida. Linhas: ${data.results.length}`;
  } catch (err) {
    normalizeStatus.textContent = err.message;
  }
});

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
