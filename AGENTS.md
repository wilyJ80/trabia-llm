# Repository Guidelines

## Project Context

This is an academic Python 3.12 FastAPI project about RAG, LLMs, structured
document extraction, and validation. Requirements are in
`docs/T3_Especificacao_LLMs_RAG_Validacao.pdf`; group 4 works on project 2.

The main demonstration flow is the web interface at `http://localhost:8000/`.
The primary button, **Ingerir e extrair PDF**, sends the same PDF to
`POST /api/ingest` and then to `POST /api/extract`. This populates pgvector
first, then runs structured extraction with retrieved context. The secondary
button, **Extrair sem ingestao**, calls `POST /api/extract` without adding new
chunks to the vector database.

The API still exposes Swagger at `http://localhost:8000/docs`.

## Project Structure & Module Organization

The code uses ports and adapters.

- `src/api/`: FastAPI app, routes, schemas, dependency wiring, and static UI.
- `src/api/static/`: vanilla HTML/CSS/JS interface served at `/`.
- `src/core/`: domain models, prompts, service orchestration, and port interfaces.
- `src/infra/`: concrete adapters for PostgreSQL/pgvector, OpenAI-compatible LLMs, and embedders.
- `src/ingest/`: PDF loading and text chunking.
- `src/scripts/`: CLI entry points for migrations and ingestion.
- `alembic/`: database migrations.
- `tests/`: pytest test suite.
- `docs/` and `data/`: academic documents, reports, slides, static assets, and sample PDFs.

## Build, Test, and Development Commands

- `make dev`: rebuilds and starts PostgreSQL, Ollama, downloads models, then starts the API.
- `make up`: starts all Docker Compose services.
- `make down`: stops and removes services.
- `make build`: rebuilds the API image.
- `make pull-models`: downloads the Ollama LLM and embedding models.
- `make test`: runs pytest inside the API container.
- `make test-local`: runs tests locally with `uv`; requires PostgreSQL and Ollama running.
- `python -m compileall src tests`: quick syntax/import sanity check.

For UI-only changes, run:

```bash
uv run pytest tests/test_static_ui.py -q
python -m compileall src tests
```

The Docker image copies source files at build time. Rebuild and recreate `api`
after changing static assets:

```bash
docker compose -f docker-compose.yaml build api
docker compose -f docker-compose.yaml up -d api
```

## API and UI Behavior

- `POST /api/ingest`: accepts a PDF, chunks it, embeds chunks, and stores them.
- `POST /api/extract`: accepts a PDF or text, extracts structured fields, and may use retrieved chunks when `top_k > 0`.
- `POST /api/query`: asks questions against the stored vector base.
- `GET /api/health`: reports chunk count and LLM reachability.
- `/`: serves the project UI from `src/api/static/`.

If `context_chunks_used` is `0`, extraction still ran on the submitted PDF or
text, but the vector database had no matching stored chunks or no chunks at all.
Run ingestion first when the demonstration needs RAG context.

## Coding Style & Naming Conventions

Use Python type hints and keep code async-first where the surrounding module is async. Follow layered naming: route handlers in `src/api/routes`, request/response DTOs in `src/api/schemas`, orchestration in `src/core/service.py`, adapters in `src/infra`.

Ruff is configured in `pyproject.toml` with Python 3.12, 100-character lines, double quotes, space indentation, and import sorting. Prefer clear snake_case names for functions, variables, and modules.

Keep UI code dependency-free unless the user asks for a frontend framework. The
current UI uses plain HTML, CSS, and JavaScript in `src/api/static/`.

## Testing Guidelines

Tests use `pytest` with `pytest-asyncio`. Name test files `test_*.py` and keep focused unit tests close to the behavior being changed. Mark tests that do not require database cleanup with `@pytest.mark.no_db`.

Run targeted tests during development, for example:

```bash
uv run pytest tests/test_extract.py -q
```

Run the full suite before submitting changes when the database and Ollama services are available.

## Docker and Configuration Notes

Do not commit real secrets in `.env`; use `env.example` for defaults. `.dockerignore`
excludes `.env` and `env` so local secrets and host-specific config do not enter
the API image.

Inside Docker, service URLs must use Compose hostnames:

- PostgreSQL: `postgres`
- Ollama: `ollama`

Do not use `localhost` from inside the API container for Postgres or Ollama.
`localhost` points back to the API container and causes connection refused errors.

`Settings` ignores extra keys in `.env` so shared local files can contain settings
from experiments or older scripts without breaking API startup.

## Commit & Pull Request Guidelines

Use short, imperative commit subjects such as `Add extract endpoint validation` or `Fix Docker env defaults`.

Pull requests should include a concise description, affected endpoints or modules, test results, and any configuration changes. For API behavior changes, include example requests or Swagger notes.
