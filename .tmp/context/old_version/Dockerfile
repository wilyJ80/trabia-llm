FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --no-install-project

COPY . .

RUN uv sync

RUN uv pip install -e .
