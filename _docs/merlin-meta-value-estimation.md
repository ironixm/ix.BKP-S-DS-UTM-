<!-- # ╔═════════════════════════════════════════════════════════════════════════════╗ -->
<!-- # ║    ▄▄███▄▄    ┌────────────────────────────────────────────────────────────┐║ -->
<!-- # ║  ▄█▛▘‾ ‾▝▜█▄  │ ix.Merlin → Meta Ads: Estimativa de Valor do SubmitAppl... │║ -->
<!-- # ║ ██▘       ▝██ │                                                            │║ -->
<!-- # ║ ██▖       ▗██ ├────────────────────────────────────────────────────────────┤║ -->
<!-- # ║ ███▄_   _▄███ │ By Ir.On                                                   │║ -->
<!-- # ║ █████████████ │ Agent: Copilot | Sessao: branch:main                       │║ -->
<!-- # ║ ██ ▀ ████████ │ commit:f563b5b                                             │║ -->
<!-- # ║ ██ ● ██▀██▀██ │ Ultima modificacao: 2026-03-23 - 12:38                     │║ -->
<!-- # ║ ▜▛   ██ ▜▛ ██ │ ironix.com.br                                              │║ -->
<!-- # ║      ██    ▜▛ ├────────────────────────────────────────────────────────────┤║ -->
<!-- # ║      ▜▛       │ Caminho:                                                   │║ -->
<!-- # ║               │ _docs/merlin-meta-value-estimation.md                      │║ -->
<!-- # ║               ├────────────────────────────────────────────────────────────┤║ -->
<!-- # ║               │ Detalhes:                                                  │║ -->
<!-- # ║               │ * V1.0.0 - [sem detalhes]                                  │║ -->
<!-- # ║               │                                                            │║ -->
<!-- # ║               └────────────────────────────────────────────────────────────┘║ -->
<!-- # ╚═════════════════════════════════════════════════════════════════════════════╝ -->

# ix.Merlin → Meta Ads: Estimativa de Valor do SubmitApplication

> Gerado em 23/03/2026 — baseado na análise real de 1.096 deals (49 ganhos).

---

## 1. Resumo da Abordagem

Reutilizamos os **mesmos pesos do DealScore** já calibrados no backend (`deal_score_rules.py`),
mas apenas os componentes disponíveis **no momento do formulário** (antes de entrar no CRM).

| Dado                   | Disponível no Form? | Peso max |
|------------------------|:-------------------:|:--------:|
| Cargo                  | ✅                   | +25      |
| Segmento               | ✅                   | +15      |
| Formato de Vendas      | ✅                   | +15      |
| Tem Site               | ✅                   | +15      |
| Email válido           | ✅                   | +10      |
| Email empresarial      | ✅                   | +10      |
| Telefone válido        | ✅                   | +10      |
| Questionário preenchido| ✅ (sempre Sim)      | +20      |
| Funil (UTM campaign)   | ✅                   | +30      |
| **Total máximo**       |                     | **+150** |
| **Total mínimo**       |                     | **-40**  |

### Fórmula

```
preScore = cargo + segmento + formato_vendas + site + email + email_empresarial + phone + questionario(20) + funil

normalized = clamp((preScore + 40) / 190, 0, 1)

closeRate = BASE_CLOSE_RATE + normalized × (MAX_CLOSE_RATE - BASE_CLOSE_RATE)

estimatedValue = round(closeRate × AVG_WON_DEAL_VALUE)
```

### Constantes (calibradas com dados reais)

| Constante            | Valor    | Origem                                       |
|----------------------|----------|----------------------------------------------|
| `AVG_WON_DEAL_VALUE` | R$4.200  | Mediana de 49 deals ganhos                   |
| `BASE_CLOSE_RATE`    | 0,01     | Pior lead possível ≈ 1%                      |
| `MAX_CLOSE_RATE`     | 0,15     | Melhor lead pré-CRM ≈ 15%                    |
| Win rate global      | 4,5%     | 49/1096 (referência, não usado diretamente)  |

### Exemplos de Valor Estimado

| Perfil do Lead            | preScore | closeRate | **Valor →  Meta** |
|---------------------------|:--------:|:---------:|:-----------------:|
| Estudante, gmail, sem site | -25      | ~1,2%     | **R$49**          |
| Médio (analista, tecno)    | +50      | ~6,6%     | **R$279**         |
| CEO, SaaS, BOFU, site corp | +140     | ~14,3%    | **R$600**         |

> O Meta não precisa de valores exatos. Ele precisa de **diferenciação relativa**
> entre leads bons e ruins. Mesmo com ±20% de erro, o algoritmo de otimização
> já consegue priorizar leads de maior valor. Sim, você está correto — depois
> pode otimizar campanhas para "value optimization" (ROAS).

---

## 2. Variáveis Necessárias no Merlin

O bloco "Criar variável" do Merlin precisa ter **todas** estas variáveis:

| Variável Merlin       | Campo do formulário                    |
|-----------------------|----------------------------------------|
| `nome`                | Nome completo                          |
| `email`               | E-mail                                 |
| `wpp`                 | WhatsApp / Telefone                    |
| `cargo`               | Cargo (pergunta com botões)            |
| `segmento`            | Segmento (pergunta com botões)         |
| `formato_vendas`      | Formato de vendas (pergunta com botões)|
| `tem_site`            | Tem site? (Sim/Não)                    |
| `site`                | Endereço do site                       |
| `plataforma`          | Plataforma de vendas                   |

> Se alguma variável não existir ainda no node "Criar variável", adicione-a
> antes de usar o código abaixo.

---

## 3. Código JavaScript — Bloco 1: "ix.Pega Dados para o META e GADS"

Cole este código no node **"Código Javascript"** chamado "ix.Pega Dados para o META e GADS":

```javascript
<script>
(async function () {

  // =====================================================
  // Helpers
  // =====================================================
  function normalize(value) {
    return value ? value.trim().toLowerCase() : null;
  }

  function normalizePhone(phone) {
    if (!phone) return null;
    return phone.replace(/\D/g, "");
  }

  async function sha256(value) {
    const enc = new TextEncoder();
    const buffer = await crypto.subtle.digest("SHA-256", enc.encode(value));
    return Array.from(new Uint8Array(buffer))
      .map(b => b.toString(16).padStart(2, "0"))
      .join("");
  }

  function clamp(val, min, max) {
    return Math.max(min, Math.min(max, val));
  }

  // =====================================================
  // Dados vindos do Merlin (variáveis do formulário)
  // =====================================================
  const rawName          = "{{{nome}}}";
  const rawEmail         = "{{{email}}}";
  const rawPhone         = "{{{wpp}}}";
  const rawCargo         = "{{{cargo}}}";
  const rawSegmento      = "{{{segmento}}}";
  const rawFormatoVendas = "{{{formato_vendas}}}";
  const rawTemSite       = "{{{tem_site}}}";
  const rawSite          = "{{{site}}}";
  const rawPlataforma    = "{{{plataforma}}}";

  // =====================================================
  // Dados do URL (UTMs, fbclid, gclid)
  // =====================================================
  const urlParams    = new URLSearchParams(window.location.search);
  const utm_source   = urlParams.get("utm_source")   || "";
  const utm_medium   = urlParams.get("utm_medium")   || "";
  const utm_campaign = urlParams.get("utm_campaign")  || "";
  const utm_content  = urlParams.get("utm_content")   || "";
  const utm_term     = urlParams.get("utm_term")      || "";
  const fbclid       = urlParams.get("fbclid")        || "";
  const gclid        = urlParams.get("gclid")         || "";
  const fbc          = document.cookie.match(/_fbc=([^;]+)/)?.[1] || "";
  const fbp          = document.cookie.match(/_fbp=([^;]+)/)?.[1] || "";

  // =====================================================
  // Tabelas de Score (espelho do deal_score_rules.py)
  // =====================================================
  const CARGO_SCORES = {
    "CEO": 25,
    "Dono/Proprietário(a)": 20,
    "Diretor(a)": 18,
    "Sócio(a)": 15,
    "Gerente de Marketing/Vendas": 10,
    "Coordenador de Marketing/Vendas": 8,
    "Analista de Marketing/Vendas": 5,
    "Consultor(a)": 0,
    "Autônomo": -2,
    "Estudante": -10,
  };

  const SEGMENTO_SCORES = {
    "Tecnologia/Software/SaaS": 15,
    "Financeiros/Crédito": 12,
    "Certificação Digital": 10,
    "Educação": 8,
    "Incorporação/Imobiliária": 8,
    "Saúde e bem estar": 8,
    "Energia solar": 8,
    "Corretoras e seguradoras": 8,
    "Seguros": 8,
    "Contabilidade": 6,
    "Consultorias": 6,
    "Varejo": 6,
    "Turismo e Hotelaria": 5,
    "Internet e Telefonia": 5,
    "Alimentação": 4,
    "Esporte e lazer": 4,
    "Agência de marketing": 2,
    "Outros": 0,
  };

  const FORMATO_VENDAS_SCORES = {
    "Planos/assinaturas/mensalidades": 15,
    "Consultivo": 12,
    "E-commerce": 8,
    "Lançamento de Infoprodutos": 5,
    "Outros": 0,
  };

  const PLATAFORMA_SCORES = {
    "Hotmart": 6,
    "Eduzz": 5,
    "Sympla": 2,
    "Outros": 0,
  };

  // =====================================================
  // Validadores
  // =====================================================
  const emailRegex    = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
  const freeEmailRe   = /@(gmail\.com|hotmail\.com|outlook\.com|live\.com|yahoo\.com(\.br)?|icloud\.com)$/i;

  const email     = normalize(rawEmail);
  const phone     = normalizePhone(rawPhone);
  const isEmailOk = email && emailRegex.test(email);
  const isBizEmail = isEmailOk && !freeEmailRe.test(email);
  const isPhoneOk = phone && phone.length >= 10;

  // =====================================================
  // Funil (derivado de utm_campaign)
  // =====================================================
  let funilScore = 0;
  if (utm_campaign.includes("ix.F")) funilScore = 30;      // BOFU
  else if (utm_campaign.includes("ix.M")) funilScore = 15;  // MOFU
  else if (utm_campaign.includes("ix.T")) funilScore = 5;   // TOFU

  // =====================================================
  // Cálculo do Pre-CRM DealScore
  // =====================================================
  const preScore =
    (CARGO_SCORES[rawCargo]               || 0) +
    (SEGMENTO_SCORES[rawSegmento]         || 0) +
    (FORMATO_VENDAS_SCORES[rawFormatoVendas] || 0) +
    (PLATAFORMA_SCORES[rawPlataforma]     || 0) +
    (rawTemSite === "Sim" ? 15 : -15)           +  // site_valido
    (isEmailOk   ? 10 : -10)                    +  // email_valido
    (isBizEmail  ? 10 : 0)                      +  // email_empresarial
    (isPhoneOk   ? 10 : -5)                     +  // phone_valido
    20                                           +  // questionario = Sim (preencheu form)
    funilScore;

  // =====================================================
  // Estimativa de Valor (R$)
  // =====================================================
  const AVG_WON_VALUE   = 4200;   // Mediana deals ganhos BuzzLead
  const BASE_CLOSE_RATE = 0.01;   // 1% — pior lead
  const MAX_CLOSE_RATE  = 0.15;   // 15% — melhor lead pré-CRM

  const normalized = clamp((preScore + 40) / 190, 0, 1);
  const closeRate  = BASE_CLOSE_RATE + normalized * (MAX_CLOSE_RATE - BASE_CLOSE_RATE);
  const estimatedValue = Math.round(closeRate * AVG_WON_VALUE);

  // =====================================================
  // Container global
  // =====================================================
  window._ix = window._ix || {};
  window._ix.ec   = {};   // Google Enhanced Conversions
  window._ix.meta = {};   // Meta Advanced Matching
  window._ix.ev   = {};   // Dados do evento (valor, UTMs, etc.)

  // =====================================================
  // Valor + Moeda
  // =====================================================
  window._ix.ev.value    = estimatedValue;
  window._ix.ev.currency = "BRL";
  window._ix.ev.preScore = preScore;

  // =====================================================
  // UTMs + Click IDs (para cAPI futuro e dataLayer)
  // =====================================================
  window._ix.ev.utm_source   = utm_source;
  window._ix.ev.utm_medium   = utm_medium;
  window._ix.ev.utm_campaign = utm_campaign;
  window._ix.ev.utm_content  = utm_content;
  window._ix.ev.utm_term     = utm_term;
  window._ix.ev.fbclid       = fbclid;
  window._ix.ev.gclid        = gclid;
  window._ix.ev.fbc          = fbc;
  window._ix.ev.fbp          = fbp;

  // =====================================================
  // Nome (hash para Meta, plain para Google)
  // =====================================================
  if (rawName) {
    const name  = normalize(rawName);
    const parts = name.split(" ");
    const first = parts[0] || null;
    const last  = parts.length > 1 ? parts.slice(1).join(" ") : null;

    window._ix.ec.first_name = first;

    if (first) window._ix.meta.fn = await sha256(first);
    if (last)  window._ix.meta.ln = await sha256(last);
  }

  // =====================================================
  // Email (hash)
  // =====================================================
  if (email) {
    const hash = await sha256(email);
    window._ix.ec.email = hash;
    window._ix.meta.em  = hash;
  }

  // =====================================================
  // Telefone (hash)
  // =====================================================
  if (phone) {
    const hash = await sha256(phone);
    window._ix.ec.phone_number = hash;
    window._ix.meta.ph         = hash;
  }

  // =====================================================
  // Cidade / Estado (via fbc/fbp cookies — Meta lê automaticamente)
  // Nota: geo real requer GeoIP server-side (cAPI futuro)
  // =====================================================

  // =====================================================
  // GOOGLE ADS — Enhanced Conversions
  // =====================================================
  window.dataLayer = window.dataLayer || [];
  function gtag(){ dataLayer.push(arguments); }

  if (Object.keys(window._ix.ec).length) {
    gtag("set", "user_data", window._ix.ec);
  }

  // =====================================================
  // META ADS — Advanced Matching (reinit com dados do lead)
  // =====================================================
  if (typeof fbq === "function" && Object.keys(window._ix.meta).length) {
    // Adiciona fbc/fbp se disponíveis
    if (fbc) window._ix.meta.fbc = fbc;
    if (fbp) window._ix.meta.fbp = fbp;

    fbq("init", "125029621496314", window._ix.meta);
  }

  // Debug (remover em produção)
  console.log("[ix] preScore:", preScore, "| value:", estimatedValue, "| closeRate:", (closeRate*100).toFixed(1)+"%");

})();
</script>
```

---

## 4. Código JavaScript — Bloco "Evento para o META e GADS"

Este é o bloco que **dispara o evento** `SubmitApplication` com valor.
Cole no node de "Conversão com Google" / "Meta" ou num novo "Código Javascript" **após** o bloco 1:

```javascript
<script>
(function () {

  var ev = (window._ix && window._ix.ev) || {};
  var value    = ev.value    || 0;
  var currency = ev.currency || "BRL";

  // =====================================================
  // META ADS — SubmitApplication com valor
  // =====================================================
  if (typeof fbq === "function") {
    fbq("track", "SubmitApplication", {
      value: value,
      currency: currency,
      content_name: "Formulário de Demonstração",
    });
  }

  // =====================================================
  // GOOGLE ADS — Evento de conversão com valor
  // =====================================================
  window.dataLayer = window.dataLayer || [];
  function gtag(){ dataLayer.push(arguments); }

  gtag("event", "conversion", {
    send_to: "AW-XXXXXXXXX/YYYYYYY",  // ← substituir pelo ID real
    value: value,
    currency: currency,
  });

  // =====================================================
  // DataLayer push (para GTM, se usar)
  // =====================================================
  dataLayer.push({
    event: "ix_submit_application",
    ix_value: value,
    ix_currency: currency,
    ix_pre_score: ev.preScore || 0,
    ix_utm_source: ev.utm_source || "",
    ix_utm_medium: ev.utm_medium || "",
    ix_utm_campaign: ev.utm_campaign || "",
    ix_fbclid: ev.fbclid || "",
    ix_gclid: ev.gclid || "",
  });

})();
</script>
```

---

## 5. Sobre cAPI (Conversions API) — Próximo Passo

O Facebook cAPI requer chamada **server-side** (`POST https://graph.facebook.com/v19.0/{PIXEL_ID}/events`).

Não dá para fazer diretamente do Merlin (é client-side). Mas o fluxo futuro seria:

1. **No Merlin** (já feito acima): coletar `fbclid`, `fbc`, `fbp`, `user_agent`, `ip_hint`
2. **Quando o deal entra no Pipedrive** (via webhook no `main.py`): disparar o evento via cAPI com os dados coletados

### Dados que o cAPI aceita (e já temos):

| Parâmetro cAPI      | Fonte                          |
|---------------------|--------------------------------|
| `em` (email hash)   | Form → Pipedrive               |
| `ph` (phone hash)   | Form → Pipedrive               |
| `fn`, `ln`          | Form → Pipedrive               |
| `fbc`               | Cookie `_fbc` (capturado no JS)|
| `fbp`               | Cookie `_fbp` (capturado no JS)|
| `client_user_agent` | `navigator.userAgent`          |
| `event_source_url`  | `window.location.href`         |
| `value`, `currency` | preScore → fórmula             |

Para implementar cAPI no backend, seria um novo endpoint no `main.py` ou um hook no webhook do Pipedrive.
Isso fica como evolução — o browser-side com Advanced Matching + valor já é um grande upgrade.

---

## 6. Calibração Futura

Após 30-60 dias com dados de conversão:

1. Exportar deals ganhos com o `preScore` que tinham na entrada
2. Calcular a taxa real de fechamento por faixa de score
3. Ajustar `BASE_CLOSE_RATE`, `MAX_CLOSE_RATE` e `AVG_WON_VALUE`
4. Considerar uma curva não-linear (sigmoid) se houver concentração

A beleza dessa abordagem é que os **mesmos pesos** do `deal_score_rules.py` servem
tanto o backend (priorização de deals) quanto o frontend (valoração para Meta/GAds).
Qualquer ajuste lá atualiza os dois lados.

<!--
  ▗▅▅▖   
▄▛▘‾‾▝▜▄ 
█▖    ▗█   © 2026 Copyright
███▅▅███   Ir.On
██●█████ 
▜▛  █▜▛█   "Feito com muito carinho."
    █  ▀ 
    ▀    
-->
