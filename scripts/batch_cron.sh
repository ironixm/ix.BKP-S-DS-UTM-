#!/bin/bash
# batch_cron.sh — wrapper auto-destrutivo para batch_enrich.py
# Remove-se do crontab quando o batch completa (progress file some).
# Adicionado por: Copilot em 2026-04-21

PROJ='/Users/IronMascarenhas_1/Projects/ix.BLZ-S(DS+UTM)'
PROGRESS="$PROJ/scripts/.batch_progress.txt"
LOG="$PROJ/tmp/batch_$(date +%Y%m%d_%H%M).log"
VENV="$PROJ/.venv/bin/python3"
PYTHON=$([ -f "$VENV" ] && echo "$VENV" || echo "python3")

# Se não há mais progresso pendente, batch concluído → remove cron e sai
if [ ! -f "$PROGRESS" ]; then
  echo "[batch_cron] Batch concluído. Removendo crontab entry..."
  crontab -l 2>/dev/null | grep -v "batch_cron.sh" | crontab -
  echo "[batch_cron] Crontab limpo. Tudo pronto!" >> "$PROJ/tmp/batch_cron.done"
  exit 0
fi

echo "[batch_cron] Iniciando rodada — $(date)" >> "$LOG"
cd "$PROJ" || exit 1
PYTHONUNBUFFERED=1 "$PYTHON" scripts/batch_enrich.py all >> "$LOG" 2>&1
echo "[batch_cron] Rodada encerrada — $(date)" >> "$LOG"

# Checa de novo: se terminou nesta rodada, limpa o cron
if [ ! -f "$PROGRESS" ]; then
  echo "[batch_cron] Última rodada completa. Removendo crontab entry..."
  crontab -l 2>/dev/null | grep -v "batch_cron.sh" | crontab -
  echo "[batch_cron] Crontab limpo. Batch 100% concluído!" >> "$PROJ/tmp/batch_cron.done"
fi
