# 🧠 Trabia LLM — RAG API

**Sistema de Perguntas e Respostas sobre o Relatório da CPMI do 8 de Janeiro de 2023**, usando **RAG (Retrieval-Augmented Generation)** com arquitetura **provider-agnostic** (OpenAI-compatível) e suporte a **embedders intercambiáveis** para experimentos comparativos.

---

## ✨ Funcionalidades

- 📄 **Ingestão de PDF** com chunking configurável (tamanho e sobreposição)
- 🔍 **Busca vetorial** via pgvector (similaridade por cosseno)
- 🤖 **LLM intercambiável** — funciona com Ollama, OpenAI, Groq, Gemini, Together AI, etc.
- 🧬 **Embedders múltiplos** — OpenAI-compatível (768d) **ou** spaCy (300d) para experimentos comparativos
- 🧪 **Tabelas separadas por embedder** — dados não se misturam, comparação justa
- 📋 **Respostas estruturadas** com conteúdo + fontes citadas com páginas
- ⚡ **Async-first** — FastAPI + SQLAlchemy async + AsyncOpenAI
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
- **API:** http://localhost:8000
- **Swagger UI:** http://localhost:8000/docs

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
| `embedder` | `string` | `"openai"` | `"openai"` (768d) ou `"spacy"` (300d) |

```bash
curl -X POST http://localhost:8000/api/ingest \
  -F "file=@relatorio.pdf" \
  -F "chunk_size=1000" \
  -F "chunk_overlap=200" \
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
    "embedder": "openai"
  }
}
```

### `POST /api/query` — Perguntar

Faz uma pergunta sobre o documento usando RAG.

**Parâmetros (JSON body):**

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `question` | `string` | obrigatório | Pergunta do usuário |
| `top_k` | `int` | `5` | Número de trechos a recuperar (1–50) |
| `embedder` | `string` | `"openai"` | `"openai"` para tabela 768d, `"spacy"` para tabela 300d |

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

### `GET /api/health` — Status

```bash
curl http://localhost:8000/api/health
```

```json
{
  "status": "ok",
  "chunks_count": 4230,
  "llm_connected": true
}
```

---

## 🧪 Experimentos Comparativos

A arquitetura foi projetada para permitir experimentos controlados comparando diferentes configurações.

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
│   │   │   └── ingest.py      # POST /api/ingest, GET /api/health
│   │   └── schemas/
│   │       ├── query.py       # QueryRequest / QueryResponse
│   │       └── ingest.py      # IngestResponse / HealthResponse
│   │
│   ├── core/                  # Domínio (Ports & Models)
│   │   ├── models.py          # Chunk, ChunkResult, Source, AIAnswer
│   │   ├── prompt.py          # System prompt + build_rag_prompt()
│   │   ├── service.py         # RAGService (orquestrador)
│   │   └── port/
│   │       ├── repository_port.py  # Interface do banco vetorial
│   │       ├── embedder_port.py    # Interface do embedder
│   │       └── llm_port.py         # Interface do LLM
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
├── docker-compose.yaml        # PostgreSQL + Ollama + API
├── Dockerfile                 # Imagem da API (uv-based, slim)
├── Makefile                   # Comandos úteis
├── pyproject.toml             # Dependências e metadados
├── env.example                # Template de configuração
└── alembic.ini                # Config do Alembic
```

---

## ⚙️ Configuração

Todas as configurações são feitas via **variáveis de ambiente** (arquivo `.env`).

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
| `make clean` | Remove containers + volumes + imagens |
| `make reset` | Clean + build + up |

---

## 🧪 Testes

```bash
# Dentro do container (recomendado)
make test

# Localmente (requer PostgreSQL + Ollama rodando)
make test-local
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
| **Container** | Docker Compose (uv-based slim image) |

---

## 📄 Licença

MPL-2.0
