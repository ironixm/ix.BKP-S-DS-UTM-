FROM python:3.11-slim

WORKDIR /app

# Dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Dependências Python
COPY pyproject.toml ./
RUN pip install --no-cache-dir flask flask-login gunicorn requests google-ads "psycopg[binary,pool]>=3.2"

# Código da aplicação
COPY main.py logger.py mappings.py parsers.py pd_api.py agendor_api.py \
     notes_builder.py product_match.py ltv.py conversions.py ./
COPY dealscore/ dealscore/
COPY enrichment/ enrichment/
COPY modules/ modules/
COPY scripts/ scripts/
COPY templates/ templates/
COPY static/ static/

# Porta
EXPOSE 5000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -sf http://localhost:5000/ || exit 1

# Rodar com gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "main:app"]
