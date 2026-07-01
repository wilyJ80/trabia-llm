# Prerequisites

# Running

- Add info to `.env` based on `env.example`

## Locally

- Ingest with `uv run src/run_ingestion.py`

# Development

- `uv` installed

- installing dependencies with `uv sync`

- install project as editable with `uv pip install -e .`

- Convenience script for starting DB and migrating located in `./docker/dev.sh`

- To use it:

    - `chmod +x ./docker/dev.sh`

    - `./docker/dev.sh`

- **Or** use an existing database and run migrations manually:

    - `uv run src/migrate.py`

- Install CNN embedding model with the command:

    - `uv run spacy download pt_core_news_lg`
