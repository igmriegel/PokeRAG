FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
COPY requirements.runtime.txt .
RUN pip install --no-cache-dir -r requirements.runtime.txt

COPY pyproject.toml .
COPY src/ src/
COPY config/ config/
COPY tests/ tests/

RUN pip install --no-cache-dir -e .

EXPOSE 8000
EXPOSE 8501

CMD ["sh", "-c", "uvicorn pokemon_tcg_rag.api.main:app --host 0.0.0.0 --port 8000 & streamlit run src/pokemon_tcg_rag/ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0"]
