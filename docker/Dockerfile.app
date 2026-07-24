FROM python:3.11-slim AS builder

WORKDIR /build

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

COPY requirements.txt .
COPY requirements.runtime.txt .
RUN pip install -r requirements.runtime.txt

COPY pyproject.toml .
COPY src/ src/
COPY config/ config/
COPY scripts/ scripts/
RUN pip install --no-deps .

FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:${PATH}" \
    HOME=/home/poketcg \
    TMPDIR=/tmp/poketcg

RUN useradd --create-home --home-dir /home/poketcg --uid 10001 --shell /usr/sbin/nologin poketcg \
    && mkdir -p /app /tmp/poketcg \
    && chown -R 10001:10001 /app /tmp/poketcg /home/poketcg

COPY --from=builder /opt/venv /opt/venv
COPY --chown=10001:10001 pyproject.toml README.md /app/
COPY --chown=10001:10001 src/ /app/src/
COPY --chown=10001:10001 config/ /app/config/
COPY --chown=10001:10001 scripts/ /app/scripts/

WORKDIR /app
USER 10001:10001

EXPOSE 8000
EXPOSE 8501

CMD ["sh", "-c", "uvicorn pokemon_tcg_rag.api.main:app --host 0.0.0.0 --port 8000 & streamlit run src/pokemon_tcg_rag/ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0"]
