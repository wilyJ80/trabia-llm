.PHONY: up down build pull pull-models logs shell dev test revision ingest clean help

# ── Services ──────────────────────────────────────────────────────

up: ## Start all services (PostgreSQL + Ollama + API)
	docker compose -f docker-compose.yaml up -d

down: ## Stop and remove all services
	docker compose -f docker-compose.yaml down

build: ## Build (or rebuild) the API image
	docker compose -f docker-compose.yaml build

pull: pull-models ## Pull base images + Ollama models
	docker compose -f docker-compose.yaml pull

pull-models: ## Baixar modelos do Ollama (LLM + embedding) — necessário na primeira vez
	docker compose -f docker-compose.yaml up -d ollama
	@echo "Baixando phi4-mini:latest (~2.5GB)..."
	docker compose -f docker-compose.yaml exec -T ollama ollama pull phi4-mini:latest
	@echo "Baixando nomic-embed-text:latest (~137MB)..."
	docker compose -f docker-compose.yaml exec -T ollama ollama pull nomic-embed-text:latest
	@echo "Modelos baixados!"

logs: ## Tail logs from all services
	docker compose -f docker-compose.yaml logs -f

# ── Development ──────────────────────────────────────────────────

dev: ## Full dev startup: build → start → (migrations automáticas na API)
	@docker compose -f docker-compose.yaml down --remove-orphans
	@docker compose -f docker-compose.yaml build
	@docker compose -f docker-compose.yaml up -d ollama postgres
	@uv run python -c "import time; time.sleep(2)"
	@$(MAKE) pull-models
	@docker compose -f docker-compose.yaml up -d api
	@echo "API pronta em http://localhost:8000"
	@echo "Swagger docs em http://localhost:8000/docs"

shell-api: ## Abrir shell no container da API
	docker compose -f docker-compose.yaml exec api /bin/bash

shell-db: ## Abrir psql no banco
	docker compose -f docker-compose.yaml exec postgres psql -U $$POSTGRES_USER -d $$POSTGRES_DB

# ── Tests ─────────────────────────────────────────────────────────

test: ## Rodar testes (requer serviços rodando)
	docker compose -f docker-compose.yaml exec api uv run pytest

test-local: ## Rodar testes localmente (requer PostgreSQL + Ollama rodando)
	PYTHONPATH=src uv run pytest

# ── Database ──────────────────────────────────────────────────────

revision: ## Criar nova migration (uso: make revision msg="descricao")
	docker compose -f docker-compose.yaml exec api uv run alembic revision --autogenerate -m "$(msg)"

# ── Ingestion ─────────────────────────────────────────────────────

ingest: ## Rodar pipeline de ingestão do PDF
	docker compose -f docker-compose.yaml exec api uv run python -m src.scripts.ingest

# ── Cleanup ───────────────────────────────────────────────────────

clean: ## Remover containers, volumes e imagens
	docker compose -f docker-compose.yaml down -v --rmi all --remove-orphans

reset: clean build up ## Reset completo: limpa tudo, reconstrói e sobe

# ── Help ──────────────────────────────────────────────────────────

help: ## Mostrar esta ajuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
