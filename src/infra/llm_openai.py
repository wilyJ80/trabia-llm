"""OpenAI-compatible LLM adapter — implements LLMPort using the OpenAI Python client.

Works with any provider that exposes an OpenAI-compatible chat completions endpoint:
- Ollama (local) — http://localhost:11434/v1
- OpenAI — https://api.openai.com/v1
- Groq — https://api.groq.com/openai/v1
- Together AI — https://api.together.xyz/v1
- etc.
"""

import re

import httpx
from openai import AsyncOpenAI

from core.models import AIAnswer, Source
from core.port.llm_port import LLMPort


class OpenAILLM(LLMPort):
    """LLM adapter that calls any OpenAI-compatible chat completions endpoint.

    The full prompt (system instructions + context + question) is assembled
    upstream by ``build_rag_prompt()`` and passed as a single user message.
    """

    def __init__(
        self,
        model: str = "phi4-mini:latest",
        base_url: str = "http://localhost:11434/v1",
        api_key: str = "ollama",
    ):
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._client = AsyncOpenAI(base_url=base_url, api_key=api_key)

    async def ask(self, prompt: str) -> AIAnswer:
        """Send the assembled prompt and parse the structured reply."""
        content = await self.ask_text(prompt)
        answer, sources = self._parse_response(content)
        return AIAnswer(content=answer, sources=sources)

    async def ask_text(
        self,
        prompt: str,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> str:
        """Send the assembled prompt and return the raw text response."""
        request = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": max_tokens,
        }
        if json_mode:
            request["response_format"] = {"type": "json_object"}

        try:
            response = await self._client.chat.completions.create(**request)
        except Exception:
            if not json_mode:
                raise
            request.pop("response_format", None)
            response = await self._client.chat.completions.create(**request)

        return response.choices[0].message.content or ""

    async def is_reachable(self) -> bool:
        """Return whether the configured OpenAI-compatible provider responds."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    f"{self._base_url}/models",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                )
                response.raise_for_status()
        except Exception:
            return False
        return True

    # ------------------------------------------------------------------
    # Response parsing — shared with the old OllamaLLM adapter
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_response(content: str) -> tuple[str, list[Source]]:
        """Split the LLM response into answer text and structured sources.

        Handles multiple formats:
        - ``Fontes:`` / ``Fonte:`` header with bullet list
        - ``Fonte:`` with inline description (e.g. ``Trechos das páginas 810, 1106``)
        - ``Sources:`` / ``References:`` headers (the model occasionally mixes languages)
        """
        sources: list[Source] = []
        answer_lines: list[str] = []
        in_sources = False

        sources_header = re.compile(
            r"^(?:fontes?|sources?|referências?|references?)\s*:?",
            re.IGNORECASE,
        )

        for line in content.split("\n"):
            stripped = line.strip()
            if not stripped:
                if in_sources:
                    continue
                answer_lines.append("")
                continue

            if sources_header.match(stripped):
                in_sources = True
                header_body = sources_header.sub("", stripped).strip()
                if header_body:
                    sources.extend(OpenAILLM._extract_inline_pages(header_body))
                continue

            if in_sources:
                if stripped.startswith("-") or stripped.startswith("*"):
                    source = OpenAILLM._parse_source_line(stripped)
                    if source is not None:
                        sources.append(source)
                else:
                    inline_sources = OpenAILLM._extract_inline_pages(stripped)
                    if inline_sources:
                        sources.extend(inline_sources)
                    else:
                        answer_lines.append(stripped)
                        in_sources = False
            else:
                answer_lines.append(stripped)

        answer = "\n".join(answer_lines).strip()

        if answer.lower().startswith("resposta:"):
            answer = answer[len("Resposta:") :].strip()

        return answer, sources

    @staticmethod
    def _extract_inline_pages(text: str) -> list[Source]:
        m = re.search(
            r"(?:p[áa]ginas?|pages?|p\.)\s*((?:\d+[,\s]*)+)",
            text,
            re.IGNORECASE,
        )
        if m:
            pages = re.findall(r"\d+", m.group(1))
            claim = (
                re.sub(
                    r"(?:p[áa]ginas?|pages?|p\.)\s*((?:\d+[,\s]*)+).*$",
                    "",
                    text,
                    flags=re.IGNORECASE,
                )
                .strip()
                .strip(":-")
                .strip()
            )
            if not claim:
                claim = "Trecho citado"
            return [Source(claim=claim, page=int(p)) for p in pages]
        return []

    @staticmethod
    def _parse_source_line(line: str) -> Source | None:
        text = line.lstrip("-* ").strip()

        for separator in [" — ", "— ", " – ", "– "]:
            if separator in text:
                parts = text.split(separator, 1)
                claim = parts[0].strip()
                page_part = parts[1].strip()
                digits = re.sub(r"[^\d]", "", page_part)
                if digits:
                    return Source(claim=claim.strip("[]"), page=int(digits))
                return Source(claim=text.strip("[]"), page=0)

        m = re.search(r"\([^)]*?(?:p[áa]gina|page|p\.?)\s*(\d+)", text, re.IGNORECASE)
        if m:
            claim = re.sub(r"\s*\([^)]*\)", "", text).strip()
            return Source(claim=claim, page=int(m.group(1)))

        return Source(claim=text, page=0)
