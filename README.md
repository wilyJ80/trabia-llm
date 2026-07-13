# 🧠 Trabia LLM — RAG API

**Sistema de Perguntas e Respostas sobre o Relatório da CPMI do 8 de Janeiro de 2023**, usando **RAG (Retrieval-Augmented Generation)** com arquitetura **provider-agnostic** (OpenAI-compatível) e suporte a **embedders intercambiáveis** para experimentos comparativos.

---

## ✨ Funcionalidades

- 📄 **Ingestão de PDF** com chunking configurável (tamanho e sobreposição)
- 🔍 **Busca vetorial** via pgvector (similaridade por cosseno)
- 🤖 **LLM intercambiável** — funciona com Ollama, OpenAI, Groq, Gemini, Together AI, etc.
- 🧬 **Embedders múltiplos** — OpenAI-compatível (768d) **ou** spaCy (300d) para experimentos comparativos
- 🚫 **Modo Sem RAG** — consulta o LLM diretamente sem busca vetorial, para comparação
- 🧪 **Tabelas separadas por embedder** — dados não se misturam, comparação justa
- 📋 **Respostas estruturadas** com conteúdo + fontes citadas com páginas
- 📑 **Extração estruturada de documentos** — extrai campos como tipo, título, eventos, atores, organizações, fatos e evidências de PDFs ou texto bruto
- ✅ **Validação em camadas** — parse JSON → repair automático → fallbacks determinísticos → validação de campos obrigatórios
- 🧠 **Pipeline de reparo** — quando o LLM retorna JSON mal formatado, uma segunda chamada tenta corrigi-lo automaticamente
- ⚡ **Async-first** — FastAPI + SQLAlchemy async + AsyncOpenAI
- 🖥️ **Interface web** em `/` com toggle PDF/Texto, acordeão de configurações e health bar
- 🐳 **Docker Compose** — ambiente completo com um comando

---

## 🏗️ Arquitetura

### Hexagonal (Ports & Adapters)

O código segue o padrão de **portas e adaptadores** (hexagonal), onde o domínio (`core/`) define interfaces abstratas e a infraestrutura (`infra/`) as implementa:

```
                    ┌─────────────────┐
                    │   FastAPI App    │
                    │   (api/main.py)  │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │    RAGService   │  ← Orquestrador
                    │  (core/service) │
                    └──┬──────┬──────┬┘
                       │      │      │
              ┌────────┘      │      └────────┐
              ▼               ▼               ▼
      ┌──────────────┐ ┌───────────┐ ┌──────────────┐
      │  EmbedderPort│ │ LLMPort   │ │RepositoryPort│
      │  (interface) │ │(interface)│ │ (interface)  │
      └──┬───────┬───┘ └─────┬─────┘ └──────┬───────┘
         │       │           │              │
         ▼       ▼           ▼              ▼
   ┌────────┐ ┌──────┐ ┌──────────┐ ┌──────────────┐
   │ OpenAI │ │spaCy │ │OpenAI LLM│ │ PgVectorRepo │
   │Embedder│ │Embed │ │(qualquer │ │ (pgvector)   │
   │(768d)  │ │(300d)│ │provider) │ │              │
   └────────┘ └──────┘ └──────────┘ └──────────────┘
```

### Fluxo de uma pergunta (Query)

```
Usuário → POST /api/query
  ├─ 1. Embedder gera vetor da pergunta
  ├─ 2. pgvector busca chunks similares (cosine distance)
  ├─ 3. RAGService monta prompt com contexto recuperado
  ├─ 4. LLM responde com conteúdo + fontes
  └─ 5. Resposta estruturada → usuário
```

### Fluxo de ingestão (Ingest)

```
Upload PDF → POST /api/ingest
  ├─ 1. PDFLoader extrai texto página por página (PyMuPDF)
  ├─ 2. TextChunker divide em chunks (RecursiveCharacterTextSplitter)
  ├─ 3. Embedder gera vetor para cada chunk
  ├─ 4. Repositório armazena chunk + vetor no pgvector
  └─ 5. Confirmação com total de chunks
```

### Fluxo de extração (Extract)

```
PDF ou texto → POST /api/extract
  ├─ 1. PDFLoader extrai texto (se PDF) ou usa texto enviado
  ├─ 2. (Opcional) Embedder busca chunks similares como contexto externo
  ├─ 3. LLM extrai campos estruturados (json_mode)
  ├─ 4. Parse do JSON → reparo se necessário
  ├─ 5. Fallbacks determinísticos para campos óbvios
  ├─ 6. Validação de campos obrigatórios
  └─ 7. ExtractedDocument com status (valid/partial/invalid) + confidence

```

---

## 🔌 Provider-Agnostic

O sistema usa **exclusivamente** o SDK `openai` da OpenAI, que se conecta a **qualquer provedor compatível com a API da OpenAI**:

| Provedor | Exemplo de `LLM_BASE_URL` | Chave |
|----------|---------------------------|-------|
| **Ollama** (local) | `http://localhost:11434/v1` | `ollama` (ignorada) |
| **OpenAI** | `https://api.openai.com/v1` | `sk-...` |
| **Gemini** (Google) | `https://generativelanguage.googleapis.com/v1beta/openai/` | Chave do AI Studio |
| **Groq** | `https://api.groq.com/openai/v1` | `gsk_...` |
| **Together AI** | `https://api.together.xyz/v1` | Chave do Together |

### Embedders disponíveis

| Embedder | Dimensões | Modelo | Tipo |
|----------|-----------|--------|------|
| `openai` (padrão) | **768d** | `nomic-embed-text` (Ollama) ou `text-embedding-3-small` (OpenAI) | Transformer |
| `spacy` | **300d** | `pt_core_news_lg` (local, 541MB) | Word2Vec estático |

Cada embedder usa **sua própria tabela no banco** (`chunk` para 768d, `chunk_spacy` para 300d), permitindo comparar a qualidade da RAG com diferentes embeddings sem conflito.

---

## 🚀 Começando

### Pré-requisitos

- Docker e Docker Compose
- ~4GB de RAM disponível (Ollama + pgvector + API)

### Configuração

```bash
# 1. Clone o repositório
git clone <repo-url>
cd trabia-llm

# 2. Copie o arquivo de ambiente
cp env.example .env

# 3. Edite .env se necessário (valores padrão já funcionam com Docker)
```

### Subindo o ambiente

```bash
# Build + start + baixar modelos do Ollama + migrações automáticas
make dev

# Ou manualmente:
docker compose up -d
make pull-models
```

Acesse:
- **Interface web:** http://localhost:8000/
- **API:** http://localhost:8000
- **Swagger UI:** http://localhost:8000/docs

### Fluxo recomendado pela interface

A tela principal em `/` atende a demonstração do projeto 2.

1. Selecione um PDF.
2. Clique em **Ingerir e extrair PDF**.
3. A interface envia o mesmo arquivo para `POST /api/ingest` e depois para `POST /api/extract`.
4. O resultado mostra campos extraídos, fontes, status de validação, confiança e quantidade de chunks usados como contexto.

Use **Extrair sem ingestão** para texto bruto ou para analisar um PDF sem atualizar a base vetorial. A área de consulta RAG fica abaixo do fluxo principal e usa os chunks já armazenados no banco.

### Parando

```bash
make down               # Apenas para os containers
make clean              # Remove containers + volumes + imagens
make reset              # Clean + build + up (reset completo)
```

---

## 🌐 Endpoints da API

### `POST /api/ingest` — Ingerir PDF

Faz upload de um PDF, extrai texto, chunkifica, gera embeddings e armazena no banco.

**Parâmetros (multipart/form-data):**

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `file` | `File` | obrigatório | Arquivo PDF |
| `chunk_size` | `int` | `2000` | Tamanho de cada chunk (500–8000) |
| `chunk_overlap` | `int` | `200` | Sobreposição entre chunks (0–1000) |
| `reset_collection` | `bool` | `false` | Limpa a coleção do embedder antes da ingestão |
| `embedder` | `string` | `"openai"` | `"openai"` (768d) ou `"spacy"` (300d) |

```bash
curl -X POST http://localhost:8000/api/ingest \
  -F "file=@relatorio.pdf" \
  -F "chunk_size=1000" \
  -F "chunk_overlap=200" \
  -F "reset_collection=true" \
  -F "embedder=openai"
```

Resposta:
```json
{
  "chunks_stored": 4230,
  "message": "Ingestão concluída: 4230 chunks armazenados de 'relatorio.pdf'.",
  "params_used": {
    "filename": "relatorio.pdf",
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "reset_collection": true,
    "embedder": "openai"
  }
}
```

### `POST /api/query` — Perguntar

Faz uma pergunta sobre o documento usando RAG ou consulta o LLM diretamente.

**Parâmetros (JSON body):**

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `question` | `string` | obrigatório | Pergunta do usuário |
| `top_k` | `int` | `5` | Número de trechos a recuperar (1–50) |
| `embedder` | `string` | `"none"` | `"openai"` (768d), `"spacy"` (300d) ou `"none"` (sem RAG) |

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "O relatório menciona Jair Bolsonaro?",
    "top_k": 5,
    "embedder": "openai"
  }'
```

Resposta:
```json
{
  "answer": {
    "content": "Sim, o relatório menciona Jair Bolsonaro...",
    "sources": [
      { "claim": "Incentivou a manutenção de acampamento", "page": 486 },
      { "claim": "Conversa com Walter Delgatti Neto", "page": 1281 }
    ]
  },
  "embedder_used": "openai"
}
```

### `POST /api/extract` — Extrair dados estruturados

Extrai campos estruturados de um PDF ou texto bruto usando LLM com validação em múltiplas camadas.

**Parâmetros (multipart/form-data):**

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `file` | `File` | opcional | Arquivo PDF para extração |
| `text` | `string` | `""` | Texto bruto para extração |
| `top_k` | `int` | `5` | Chunks de contexto externo (0 = sem RAG) |
| `embedder` | `string` | `"openai"` | `"openai"` (768d) ou `"spacy"` (300d) |

> Envie pelo menos um dos dois: `file` (PDF) **ou** `text` (texto bruto), ou ambos.

```bash
# Extrair de um PDF
curl -X POST http://localhost:8000/api/extract \
  -F "file=@relatorio.pdf" \
  -F "top_k=5" \
  -F "embedder=openai"

# Extrair de texto bruto
curl -X POST http://localhost:8000/api/extract \
  -F "text=O relatório trata da CPMI do 8 de Janeiro..." \
  -F "top_k=3"
```

Resposta:
```json
{
  "extraction": {
    "document_type": "relatorio",
    "title": "Relatório da CPMI",
    "main_event": "Comissão Parlamentar Mista de Inquérito",
    "dates": ["2023-01-08"],
    "actors": ["Jair Bolsonaro", "Walter Delgatti"],
    "organizations": ["CPMI", "Polícia Federal"],
    "facts": [
      "Relatório aponta omissão do ex-presidente",
      "Documento sugere conduta criminosa"
    ],
    "evidence": [
      "Trecho da página 486"
    ],
    "categories": ["político", "investigação"],
    "sources": [
      {"claim": "Relatório aponta omissão", "page": 486}
    ],
    "missing_required_fields": [],
    "validation_status": "valid",
    "validation_errors": [],
    "confidence": "alta"
  },
  "context_chunks_used": 5,
  "embedder_used": "openai",
  "params_used": {
    "sources": ["relatorio.pdf"],
    "top_k": 5,
    "embedder": "openai"
  }
}
```

### `GET /api/health` — Status

Retorna o status da aplicação e contagem de chunks por embedder.

**Parâmetros (query string):**

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `embedder` | `string` | `"openai"` | Embedder usado para o campo `chunks_count` |

```bash
curl http://localhost:8000/api/health?embedder=openai
```

```json
{
  "status": "ok",
  "chunks_count": 1533,
  "llm_connected": true,
  "embedder_used": "openai",
  "chunks_by_embedder": {
    "openai": 1533,
    "spacy": 0
  }
}
```

---

## 🧪 Experimentos Comparativos

A arquitetura foi projetada para permitir experimentos controlados comparando diferentes configurações.

### Avaliação principal do projeto 2

O conjunto `extraction_test_cases.json` contém 30 documentos anotados. O comando abaixo
recria a coleção spaCy e compara a extração sem RAG (`top_k=0`) com a extração apoiada
por cinco chunks (`top_k=5`):

```bash
uv run python run_extraction_evaluation.py \
  --prepare-corpus --embedder spacy --top-k 0,5
```

O script gera `docs/extraction_performance_report.md` e
`docs/extraction_performance_results.json`.

### Exemplo: Comparar chunk_size com o mesmo embedder

```bash
# Experimento A: chunks grandes (2000 caracteres)
curl -X POST http://localhost:8000/api/ingest -F "file=@relatorio.pdf" -F "chunk_size=2000" -F "embedder=openai"
# → ~1.900 chunks no banco 'chunk'

# Experimento B: chunks pequenos (500 caracteres)
# ⚠️ Zere o banco primeiro: docker compose down -v && docker compose up -d
curl -X POST http://localhost:8000/api/ingest -F "file=@relatorio.pdf" -F "chunk_size=500" -F "embedder=openai"
# → ~6.800 chunks no banco 'chunk'
```

### Exemplo: Comparar embedder (OpenAI vs spaCy)

```bash
# Ingestão com OpenAI (768d)
curl -X POST http://localhost:8000/api/ingest -F "file=@relatorio.pdf" -F "embedder=openai"
# → chunks na tabela 'chunk'

# Ingestão com spaCy (300d) — mesma chunk_size, tabela diferente
curl -X POST http://localhost:8000/api/ingest -F "file=@relatorio.pdf" -F "embedder=spacy"
# → chunks na tabela 'chunk_spacy'

# Consulta cada tabela com o embedder correspondente
curl -X POST http://localhost:8000/api/query -H "Content-Type: application/json" \
  -d '{"question": "O que diz sobre Bolsonaro?", "embedder": "openai"}'

curl -X POST http://localhost:8000/api/query -H "Content-Type: application/json" \
  -d '{"question": "O que diz sobre Bolsonaro?", "embedder": "spacy"}'
```

### Estimativas de chunks para o relatório (1.333 páginas, ~2.1M caracteres)

| chunk_size | chunk_overlap | Chunks estimados | Média/página |
|-----------|:-----------:|:--------------:|:-----------:|
| 2000 | 200 | ~1.900 | ~1,4 |
| 1000 | 200 | ~3.400 | ~2,6 |
| **500** | **200** | **~6.800** | **~5,1** |
| 300 | 100 | ~13.000 | ~9,8 |

---

## 🗂️ Estrutura do Projeto

```
trabia-llm/
├── alembic/                   # Migrations (SQLAlchemy/Alembic)
│   ├── env.py
│   └── versions/
│       ├── 001_initial_schema.py
│       └── 002_add_chunk_spacy.py
├── data/                      # PDFs fonte
│   └── relatorio-cpmi-*.pdf
├── docs/                      # Documentação acadêmica
├── src/
│   ├── api/                   # Camada de apresentação (FastAPI)
│   │   ├── main.py            # App factory + lifespan (auto-migrate)
│   │   ├── dependencies.py    # DI: build_service(), get_service()
│   │   ├── routes/
│   │   │   ├── query.py       # POST /api/query
│   │   │   ├── ingest.py      # POST /api/ingest, GET /api/health
│   │   │   └── extract.py     # POST /api/extract
│   │   ├── static/            # Interface web servida em /
│   │   └── schemas/
│   │       ├── query.py       # QueryRequest / QueryResponse
│   │       ├── ingest.py      # IngestResponse / HealthResponse
│   │       └── extract.py     # ExtractResponse
│   │
│   ├── core/                  # Domínio (Ports & Models)
│   │   ├── models.py          # Chunk, ChunkResult, Source, AIAnswer, ExtractedDocument
│   │   ├── prompt.py          # System prompt + build_rag_prompt() + build_extraction_prompt()
│   │   ├── service.py         # RAGService (query + extract + embed_and_store)
│   │   └── port/
│   │       ├── repository_port.py  # Interface do banco vetorial
│   │       ├── embedder_port.py    # Interface do embedder
│   │       └── llm_port.py         # Interface do LLM (ask + ask_text)
│   │
│   ├── infra/                 # Adaptadores (implementações concretas)
│   │   ├── database.py        # Async engine + session factory
│   │   ├── models.py          # ORM: ChunkModel (768d), ChunkSpacyModel (300d)
│   │   ├── repository.py      # PgVectorRepository (pgvector + SQLAlchemy)
│   │   ├── llm_openai.py      # OpenAILLM — qualquer provider compatível
│   │   ├── embedder_openai.py # OpenAIEmbedder — 768d
│   │   └── embedder_spacy.py  # SpacyEmbedder — 300d (auto-download)
│   │
│   ├── ingest/                # Pipeline de ingestão
│   │   ├── loader.py          # PDFLoader (PyMuPDF)
│   │   └── chunker.py         # TextChunker (LangChain RecursiveCharacter)
│   │
│   └── settings.py            # Config (pydantic-settings, env vars)
│
├── tests/                     # Testes com pytest
│   ├── conftest.py             # Fixtures compartilhadas
│   ├── test_extract.py         # Testes unitários de extração (no_db)
│   ├── test_api.py             # Testes HTTP da API (health, ingest, query)
│   ├── test_chunks.py          # Testes de chunking
│   ├── test_repository.py      # Testes do repositório
│   └── test_static_ui.py       # Testes da interface web
├── test_cases.json             # Casos de teste para avaliação experimental
├── docker-compose.yaml         # PostgreSQL + Ollama + API
├── Dockerfile                  # Imagem da API (uv-based, slim)
├── Makefile                    # Comandos úteis
├── pyproject.toml              # Dependências, ruff, pytest config
├── .env                        # Config ativa (gitignorado)
├── env.example                 # Template de configuração
├── .gitignore                  # Arquivos ignorados pelo git
└── alembic.ini                 # Config do Alembic
```

---

## ⚙️ Configuração

Todas as configurações são feitas via **variáveis de ambiente** (arquivo `.env`).

`.dockerignore` exclui `.env` e `env` para impedir que configurações locais e segredos entrem na imagem da API. No Docker Compose, a API usa `PG_HOST=postgres` e aponta `LLM_BASE_URL`/`EMBED_BASE_URL` para `ollama`.

### Variáveis

| Variável | Padrão (Docker) | Descrição |
|----------|:--------------:|-----------|
| `POSTGRES_USER` | `postgres` | Usuário do PostgreSQL |
| `POSTGRES_PASSWORD` | `mysecretpassword` | Senha do PostgreSQL |
| `POSTGRES_DB` | `postgres` | Nome do banco |
| `PG_HOST` | `postgres` | Host do PostgreSQL (Docker) |
| `PG_PORT` | `5432` | Porta do PostgreSQL |
| `K` | `5` | Número de chunks recuperados |
| `LLM_BASE_URL` | `http://ollama:11434/v1` | Endpoint OpenAI-compatível para o LLM |
| `LLM_API_KEY` | `ollama` | API key do LLM |
| `LLM_MODEL` | `phi4-mini:latest` | Modelo de geração de texto |
| `EMBED_BASE_URL` | `http://ollama:11434/v1` | Endpoint OpenAI-compatível para embeddings |
| `EMBED_API_KEY` | `ollama` | API key para embeddings |
| `EMBED_MODEL` | `nomic-embed-text:latest` | Modelo de embedding |

> **Nota:** `LLM_BASE_URL` e `EMBED_BASE_URL` podem apontar para provedores **diferentes**. Ex: LLM no Gemini (nuvem) e Embedding no Ollama (local).

### Exemplo: Usando Gemini como LLM + Ollama para embeddings

```env
# .env
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_API_KEY=SUA_CHAVE_DO_GEMINI
LLM_MODEL=gemini-2.0-flash

EMBED_BASE_URL=http://localhost:11434/v1
EMBED_API_KEY=ollama
EMBED_MODEL=nomic-embed-text:latest
```

---

## 📦 Comandos (Makefile)

| Comando | Descrição |
|---------|-----------|
| `make up` | Sobe todos os serviços |
| `make down` | Para e remove os containers |
| `make build` | Reconstrói a imagem da API |
| `make pull-models` | Baixa modelos do Ollama |
| `make dev` | Build + start + modelos (full setup) |
| `make logs` | Logs em tempo real |
| `make shell-api` | Shell dentro do container da API |
| `make shell-db` | Conexão psql com o banco |
| `make test` | Roda testes no container |
| `make test-local` | Roda testes localmente |
| `make revision msg="descrição"` | Cria nova migration Alembic |
| `make ingest` | Roda pipeline de ingestão do PDF |
| `make clean` | Remove containers + volumes + imagens |
| `make reset` | Clean + build + up |

---

## 🧪 Testes

O projeto usa **pytest** com suporte a async e marker `no_db` para testes que não precisam de banco.

| Arquivo | Descrição | Marcação |
|---------|-----------|----------|
| `tests/test_extract.py` | Testes unitários de extração (parse, repair, fallbacks, confidence) | `no_db` |
| `tests/test_api.py` | Testes HTTP contra a API rodando (health, ingest, query) | — |
| `tests/test_chunks.py` | Testes de chunking | — |
| `tests/test_repository.py` | Testes do repositório pgvector | — |

```bash
# Dentro do container (recomendado)
make test

# Localmente (requer PostgreSQL + Ollama rodando)
make test-local

# Testes sem banco (rápidos, não precisam de containers)
PYTHONPATH=src uv run pytest tests/test_extract.py -v
```

---

## 🐳 Docker

### Serviços

| Serviço | Imagem | Porta |
|---------|--------|:----:|
| **postgres** | `pgvector/pgvector:pg17` | 5432 |
| **ollama** | `ollama/ollama` | 11434 |
| **api** | Build local (uv-based) | 8000 |

### Migrações automáticas

As migrações do banco (Alembic) rodam **automaticamente na inicialização da API**, durante o `lifespan` do FastAPI. Não é necessário executar manualmente.

---

## 📚 Stack

| Componente | Tecnologia |
|-----------|-----------|
| **API** | FastAPI (Python 3.12 + Async) |
| **LLM** | OpenAI-compatível (Ollama, Gemini, Groq, etc.) |
| **Embeddings** | OpenAI-compatível (768d) **ou** spaCy (300d) |
| **Vector DB** | PostgreSQL 17 + pgvector |
| **PDF Loader** | PyMuPDF |
| **Chunking** | LangChain RecursiveCharacterTextSplitter |
| **ORM** | SQLAlchemy 2.0 (async) |
| **Migrações** | Alembic |
| **Linter/Formatter** | Ruff (F, E, W, I + format) |
| **Container** | Docker Compose (uv-based slim image) |

---

## 📄 Licença

MPL-2.0
