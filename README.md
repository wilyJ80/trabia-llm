# Prerequisites

- Add info to `.env` based on `env.example`

- `uv` installed: [uv](https://docs.astral.sh/uv/getting-started/installation/)

- install dependencies with `uv sync`

- install project as editable with `uv pip install -e .`

- Convenience script for starting DB and migrating located in `./docker/dev.sh`

- To use it:

    - `chmod +x ./docker/dev.sh`

    - `./docker/dev.sh`

    - **Or** use an existing PGVector database and run migrations manually:

        - `uv run src/migrate.py`

- Install CNN embedding model with the command:

    - `uv run spacy download pt_core_news_lg`

# Running

- Ingest with `uv run src/run_ingestion.py`

- Run main with `uv run src/main.py`

# TODO:

- [x] Assert total chunk size for report, add this info in knowledge base section of report

- [x] structured output

- [x] schema validation

- [x] incomplete/invalid answer

- [ ] Report: loading, chunking, overlap, and why

- [ ] Report: embeddings model, if same provider or not, and why

- [ ] Report: how vector DB query was vectorized, how similarity was used, how many snippets were returned, and how snippets were added to prompt in the app

- [ ] Report: validation

- [ ] Report: comparison between versions: RAG/No RAG, comparison between chunking strategies, or top-k, or embedding model

- [ ] 30 case testing: easy cases, medium cases, ambiguous cases, insufficient knowledge base cases, cases that test the limits of the application

- [ ] Report: definicao do problema, base documental, pipeline de ingestao, arquitetura da solucao, modelos e componentes utilizados, protocolo experimental, resultados, analise critica, conclusao, referencias.

- [ ] Slides: problema atacado, arquitetura da solucao, base documental, pipeline de ingestao, recuperacao vetorial, validacao ou mecanismo hibrido, resultados experimentais, principais falhas
