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
