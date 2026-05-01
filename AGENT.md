# ix.DealScore · Sync Agent

Este projeto implementa um **agente de sincronização controlada** para Deals do Pipedrive,
com foco em:

- Backfill seguro
- Execução incremental
- Observabilidade
- Controle manual (UI)
- Prevenção de loops infinitos

Este agente **não depende de totals confiáveis do Pipedrive**.
A regra de parada é **determinística** e baseada apenas no retorno real da API.

---

## 🎯 PRINCÍPIO FUNDAMENTAL

> **Enquanto a API retornar deals → continua**  
> **Quando retornar vazio → finaliza**

Essa é a **única regra de parada confiável**.

❌ Não confiar em:
- `pagination.more_items_in_collection`
- `total_items`
- `limit`
- `processed >= total`

---

## 🧠 MODELO MENTAL DO AGENTE

O agente opera em **lotes sequenciais**, com estado explícito:

- `start` → deslocamento atual
- `limit` → tamanho do lote
- `intervalMs` → intervalo entre execuções
- `running / paused` → estado operacional

A UI **não toma decisões de negócio**.  
Ela apenas **reflete e controla o estado do agente**.

---

## 🔁 CICLO DE EXECUÇÃO (CORE LOOP)

1. Chama `/sync/?filter_id=X&start=Y&limit=Z`
2. Recebe `results[]`
3. Se `results.length === 0` → **FIM**
4. Caso contrário:
   - Processa
   - Incrementa `start`
   - Aguarda `intervalMs`
   - Repete

Essa lógica está **concentrada exclusivamente no JS (`sync_ui.js`)**.

---

## 🧯 ANTI-LOOP INFINITO (REGRA DE OURO)

Qualquer alteração futura **DEVE respeitar**:

```js
if (results.length === 0) {
  finishSync();
  return;
}
```

Se isso for removido ou enfraquecido → o agente quebra.

---

## **💾 PERSISTÊNCIA DE ESTADO**

O estado do sync é salvo em:

```
localStorage["ix.dealscore.sync.state"]
```

Isso permite:

* Reload da página
* Recuperação de sessão
* Pausa / retomar manual
---

## **🧪 MODOS DE EXECUÇÃO**

* mode=test → não grava alterações no Pipedrive
* mode=write → grava UTM + DealScore

O cálculo de DealScore **sempre acontece**.

A escrita é que é condicional.

---

## **🧩 RESPONSABILIDADES DOS ARQUIVOS**

* main.py

  * API
  * Integração com Pipedrive
  * Regra de negócio
  * Nunca controla fluxo de loop
* sync_ui.js

  * Controle de execução
  * Loop
  * Pausa / resume
  * Logs e progresso
* sync_ui.html

  * Interface
  * Nenhuma lógica
---

## **⚠️ ALTERAÇÕES FUTURAS**

Antes de alterar qualquer coisa:

1. Verifique se a regra de parada ainda é baseada em results.length
2. Confirme que **nenhuma lógica de total foi reintroduzida**
3. Nunca confie em metadata do Pipedrive para fluxo

⠀
---

## **🧠 CONTINUIDADE PELO CODEX**

Sempre que retomar este projeto:

* Leia este AGENT.md primeiro
* Depois abra o sync_ui.js
* Só então mexa no backend

Este agente já passou pela fase perigosa.

Agora ele é **estável, previsível e controlável**.
