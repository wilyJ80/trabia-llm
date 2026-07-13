FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim

WORKDIR /app

# Install system dependencies (for psycopg binary)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./

RUN uv sync --no-install-project --no-dev

COPY . .

RUN uv sync --no-dev

CMD ["uv", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
