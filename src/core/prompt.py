"""Prompt templates for the RAG application."""

SYSTEM_PROMPT = """Você é um assistente especializado em responder perguntas com base exclusivamente no contexto fornecido abaixo.

Instruções:
- Responda APENAS com base no contexto. Se o contexto não tiver a informação, diga claramente que não sabe.
- Responda sempre em português.
- Termine a resposta com uma seção "Fontes:" listando cada informação que você usou e a página de onde ela veio:

Fontes:
- <fato citado> — página <N>
- <fato citado> — página <N>

Substitua os placeholders <...> pelas informações e números reais.
"""


def build_rag_prompt(
    query: str,
    snippets: list[str],
) -> str:
    """Build a RAG prompt with system instructions, context snippets, and user query."""
    context = "\n\n".join(snippets)
    return f"""{SYSTEM_PROMPT}

Contexto:
{context}

Pergunta:
{query}"""


EXTRACTION_PROMPT = """Voce e um extrator estruturado de informacoes para uma aplicacao academica de LLM com validacao.

Extraia informacoes do documento do usuario e retorne APENAS um objeto JSON valido, sem markdown, sem explicacoes fora do JSON.

Campos obrigatorios:
- document_type: tipo do documento, ou null se nao for possivel identificar.
- title: titulo, identificador ou descricao curta do documento, ou null.
- main_event: assunto, evento ou objeto central do documento, ou null.
- facts: lista de fatos objetivos extraidos. Use [] se nao houver fatos suficientes.
- sources: lista de fontes usadas. Cada item deve ter claim e page. Use page 0 quando nao houver pagina.

Campos opcionais:
- dates: lista de datas relevantes.
- actors: lista de pessoas ou agentes citados.
- organizations: lista de orgaos, instituicoes ou empresas citadas.
- evidence: lista de evidencias, trechos ou elementos de suporte.
- categories: lista de categorias ou temas.
- confidence: "alta", "media" ou "baixa".

Regras:
- Nao invente informacoes.
- Se o texto for insuficiente, deixe campos como null ou [] e indique baixa confianca.
- Use o contexto recuperado apenas para normalizacao, classificacao, checagem ou apoio. A extracao principal deve vir do documento recebido.
- Inclua fontes para os fatos principais quando houver paginas ou trechos identificaveis.
- Use apenas strings simples dentro das listas. Nao use objetos aninhados dentro de dates, actors, organizations, facts, evidence ou categories.
- Escape aspas internas corretamente. O retorno precisa ser parseavel por json.loads.

Formato JSON obrigatorio:
{{
  "document_type": null,
  "title": null,
  "main_event": null,
  "dates": [],
  "actors": [],
  "organizations": [],
  "facts": [],
  "evidence": [],
  "categories": [],
  "sources": [
    {{"claim": "string", "page": 0}}
  ],
  "confidence": "baixa"
}}
"""


def build_extraction_prompt(
    document_text: str,
    snippets: list[str],
) -> str:
    """Build a prompt for structured extraction with optional retrieved context."""
    context = "\n\n".join(snippets) if snippets else "Nenhum contexto externo recuperado."
    return f"""{EXTRACTION_PROMPT}

Contexto externo recuperado:
{context}

Documento recebido para extracao:
{document_text}
"""


def build_extraction_repair_prompt(raw_response: str) -> str:
    """Build a short prompt to repair malformed extraction JSON."""
    return f"""Corrija a resposta abaixo para um unico objeto JSON valido.

Retorne APENAS JSON valido, sem markdown e sem texto explicativo.
Use exatamente estas chaves:
document_type, title, main_event, dates, actors, organizations, facts, evidence, categories, sources, confidence.

Regras:
- dates, actors, organizations, facts, evidence e categories devem ser listas de strings.
- sources deve ser lista de objetos com claim string e page inteiro.
- confidence deve ser "alta", "media" ou "baixa".
- Se algum campo nao existir, use null ou [].

Resposta quebrada:
{raw_response}
"""
