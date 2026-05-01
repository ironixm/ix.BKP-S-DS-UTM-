/**
 * PipedrivePull.gs — Puxa deals do Pipedrive para a aba "Oportunidades Pipedrive"
 * 
 * Uso:
 *   1. Cole este arquivo no Apps Script do projeto
 *   2. Rode setupPipedriveKey() uma vez para salvar a API key
 *   3. Rode pullFromPipedrive() para popular a planilha
 *   4. (Opcional) Configure trigger automático via criarTriggerDiario()
 *
 * Planilha: ix.BLZ - Leads Ads: funil mídia paga
 * Sheet ID: 1VzKUC785Y_kkfgeV5ATznpHu5dwhVZMGAf6Rqew4GFA
 */

// ═══════════════════════════════════════════════════════════
// CONFIG
// ═══════════════════════════════════════════════════════════

var PD_CONFIG = {
  BASE_URL: 'https://api.pipedrive.com/v1',
  SHEET_NAME: 'Oportunidades Pipedrive',
  BATCH_LIMIT: 500,
  FILTER_ID: 9870,  // ix.Negócios-EmOuApós-2024(Com Fonte)

  // Colunas (mesma ordem da planilha)
  HEADERS: [
    'ID',
    'Person ID Only',
    'Negócio criado em',
    'Etiqueta',
    'Organization (Name/ID)',
    'Pipeline Stage Name',
    'Canal',
    'Fonte',
    'Campanha',
    'Conteúdo',
    'Status',
    'Fit do Lead',
    'ix.DealScore'
  ],

  // Campo IDs customizados do Pipedrive (deal fields)
  FIELDS: {
    CANAL:      'fceaaacccd265c3fb375d8b573850007456815d2',
    FONTE:      '81701fa45b2f46b8f081320b73741d3232fbf95a',
    CAMPANHA:   '8ba3c6ef23c1678a96c41b51748a7a8bf6fda577',
    CONTEUDO:   'd25a7f0b6998871eecd21ce2a027eba65f5dcb87',
    DEALSCORE:  '6ecee6457426bc4cc8f2fcce89b14baf3793ecfe',
    FIT_LEAD:   '07ed15ffee5c467fa58f2b0c1b8dd54c1bd9e93e'
  },

  // Label IDs → nomes
  LABELS: {
    199: 'OPORTUNIDADE FRACA',
    195: 'Oportunidades Quentes',
    198: 'CONTRATO ENVIADO',
    205: 'Reagendar',
    229: 'Reagendado',
    230: 'Reaquecer',
    231: 'Programa de Indicação',
    232: 'Prospecção Ativa',
    233: 'Quente',
    234: 'Frio',
    235: 'Pendencia',
    236: 'Lead Leandro',
    237: 'Morna',
    238: 'Lead Ouro',
    239: 'Lead Prata',
    240: 'Lead Bronze',
    250: 'COM',
    251: 'LIGHT'
  }
};

// Cache de stages (pipeline_id → {stage_id: name})
var _stagesCache = {};

// ═══════════════════════════════════════════════════════════
// SETUP — Rodar 1x para salvar a API key
// ═══════════════════════════════════════════════════════════

/**
 * Salva a API key do Pipedrive no PropertiesService.
 * Rode esta função UMA VEZ pelo editor do Apps Script.
 */
function setupPipedriveKey() {
  var ui = SpreadsheetApp.getUi();
  var result = ui.prompt(
    'Pipedrive API Key',
    'Cole sua API key do Pipedrive:',
    ui.ButtonSet.OK_CANCEL
  );
  if (result.getSelectedButton() === ui.Button.OK) {
    var key = result.getResponseText().trim();
    if (key) {
      PropertiesService.getScriptProperties().setProperty('PIPEDRIVE_API_KEY', key);
      ui.alert('API key salva com sucesso!');
    }
  }
}

/**
 * Alternativa: configura a API key diretamente (pode rodar do editor GAS).
 * Rode UMA VEZ e depois pode apagar a key daqui.
 */
function setupPipedriveKeyDirect() {
  PropertiesService.getScriptProperties().setProperty(
    'PIPEDRIVE_API_KEY',
    '9787c5d97a9d039c4f5d06398e52da3f07d6bb44'
  );
  Logger.log('API key configurada com sucesso!');
}

// ═══════════════════════════════════════════════════════════
// API HELPERS
// ═══════════════════════════════════════════════════════════

function _getApiKey() {
  var key = PropertiesService.getScriptProperties().getProperty('PIPEDRIVE_API_KEY');
  if (!key) throw new Error('PIPEDRIVE_API_KEY não configurada. Rode setupPipedriveKey() primeiro.');
  return key;
}

function _pdRequest(path, params) {
  var apiKey = _getApiKey();
  params = params || {};
  params['api_token'] = apiKey;

  var qs = Object.keys(params).map(function(k) {
    return encodeURIComponent(k) + '=' + encodeURIComponent(params[k]);
  }).join('&');

  var url = PD_CONFIG.BASE_URL + path + '?' + qs;
  var resp = UrlFetchApp.fetch(url, { muteHttpExceptions: true });
  var code = resp.getResponseCode();
  if (code !== 200) {
    throw new Error('Pipedrive API ' + code + ': ' + resp.getContentText().substring(0, 200));
  }
  return JSON.parse(resp.getContentText());
}

// ═══════════════════════════════════════════════════════════
// STAGE NAME RESOLVER
// ═══════════════════════════════════════════════════════════

function _getStageName(pipelineId, stageId) {
  if (!pipelineId || !stageId) return '';
  var key = String(pipelineId);
  if (!_stagesCache[key]) {
    _stagesCache[key] = {};
    try {
      var r = _pdRequest('/stages', { pipeline_id: pipelineId });
      var data = r.data || [];
      for (var i = 0; i < data.length; i++) {
        _stagesCache[key][String(data[i].id)] = data[i].name;
      }
    } catch (e) {
      Logger.log('Erro ao buscar stages: ' + e.message);
    }
  }
  return _stagesCache[key][String(stageId)] || '';
}

// ═══════════════════════════════════════════════════════════
// LABEL RESOLVER
// ═══════════════════════════════════════════════════════════

function _getLabelName(labelIds) {
  if (!labelIds) return '';
  var ids = String(labelIds).split(',');
  var names = [];
  for (var i = 0; i < ids.length; i++) {
    var id = parseInt(ids[i].trim(), 10);
    if (PD_CONFIG.LABELS[id]) {
      names.push(PD_CONFIG.LABELS[id]);
    }
  }
  return names.join(', ');
}

// ═══════════════════════════════════════════════════════════
// EXTRAI DADOS DE 1 DEAL
// ═══════════════════════════════════════════════════════════

function _dealToRow(deal) {
  var personId = '';
  var p = deal.person_id;
  if (p && typeof p === 'object') {
    personId = p.value || '';
  } else if (p) {
    personId = p;
  }

  var orgName = '';
  var org = deal.org_id;
  if (org && typeof org === 'object') {
    orgName = org.name || '';
  } else if (org) {
    orgName = org;
  }

  var stageName = _getStageName(deal.pipeline_id, deal.stage_id);
  var labelName = _getLabelName(deal.label);

  return [
    deal.id,                                          // ID
    personId,                                         // Person ID Only
    deal.add_time || '',                              // Negócio criado em
    labelName,                                        // Etiqueta
    orgName,                                          // Organization
    stageName,                                        // Pipeline Stage Name
    deal[PD_CONFIG.FIELDS.CANAL] || '',               // Canal
    deal[PD_CONFIG.FIELDS.FONTE] || '',               // Fonte
    deal[PD_CONFIG.FIELDS.CAMPANHA] || '',            // Campanha
    deal[PD_CONFIG.FIELDS.CONTEUDO] || '',            // Conteúdo
    deal.status || '',                                // Status
    deal[PD_CONFIG.FIELDS.FIT_LEAD] || '',            // Fit do Lead
    deal[PD_CONFIG.FIELDS.DEALSCORE] || ''            // ix.DealScore
  ];
}

// ═══════════════════════════════════════════════════════════
// PULL PRINCIPAL
// ═══════════════════════════════════════════════════════════

/**
 * Puxa todos os deals do Pipedrive (>= 2024-01-01) e grava na aba.
 * Substitui todos os dados existentes (exceto cabeçalho).
 */
function pullFromPipedrive() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(PD_CONFIG.SHEET_NAME);
  if (!sheet) {
    sheet = ss.insertSheet(PD_CONFIG.SHEET_NAME);
  }

  // Cabeçalho
  var headerRange = sheet.getRange(1, 1, 1, PD_CONFIG.HEADERS.length);
  headerRange.setValues([PD_CONFIG.HEADERS]);
  headerRange.setFontWeight('bold');

  var allRows = [];
  var start = 0;
  var hasMore = true;

  Logger.log('=== PULL PIPEDRIVE → SHEETS ===');
  Logger.log('Filtro: ' + PD_CONFIG.FILTER_ID);

  while (hasMore) {
    var resp = _pdRequest('/deals', {
      filter_id: PD_CONFIG.FILTER_ID,
      start: start,
      limit: PD_CONFIG.BATCH_LIMIT,
      sort: 'id DESC'
    });

    var deals = resp.data || [];
    if (deals.length === 0) break;

    for (var i = 0; i < deals.length; i++) {
      allRows.push(_dealToRow(deals[i]));
    }

    var pagination = (resp.additional_data || {}).pagination || {};
    hasMore = pagination.more_items_in_collection === true;
    start = pagination.next_start || (start + PD_CONFIG.BATCH_LIMIT);

    Logger.log('Processados: ' + allRows.length + ' deals (offset=' + start + ')');
  }

  // Limpa dados antigos (mantém header)
  if (sheet.getLastRow() > 1) {
    sheet.getRange(2, 1, sheet.getLastRow() - 1, sheet.getLastColumn()).clearContent();
  }

  // Grava tudo de uma vez
  if (allRows.length > 0) {
    sheet.getRange(2, 1, allRows.length, PD_CONFIG.HEADERS.length).setValues(allRows);
  }

  Logger.log('=== CONCLUÍDO: ' + allRows.length + ' deals gravados ===');

  // Notifica
  SpreadsheetApp.getActiveSpreadsheet().toast(
    allRows.length + ' deals importados do Pipedrive!',
    'Pull Completo',
    10
  );
}

// ═══════════════════════════════════════════════════════════
// MENU CUSTOMIZADO
// ═══════════════════════════════════════════════════════════

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('ix.Pipedrive')
    .addItem('Pull from Pipedrive', 'pullFromPipedrive')
    .addItem('Configurar API Key', 'setupPipedriveKey')
    .addSeparator()
    .addItem('Criar Trigger Diário', 'criarTriggerDiario')
    .addToUi();
}

// ═══════════════════════════════════════════════════════════
// TRIGGER AUTOMÁTICO (OPCIONAL)
// ═══════════════════════════════════════════════════════════

/**
 * Cria trigger para rodar pullFromPipedrive() 1x por dia às 3h.
 */
function criarTriggerDiario() {
  // Remove triggers antigos desta função
  var triggers = ScriptApp.getProjectTriggers();
  for (var i = 0; i < triggers.length; i++) {
    if (triggers[i].getHandlerFunction() === 'pullFromPipedrive') {
      ScriptApp.deleteTrigger(triggers[i]);
    }
  }

  ScriptApp.newTrigger('pullFromPipedrive')
    .timeBased()
    .everyDays(1)
    .atHour(3)
    .create();

  Logger.log('Trigger diário criado! Vai rodar todo dia às 3h.');
}
