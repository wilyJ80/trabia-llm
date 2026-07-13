"""
Script de avaliação experimental — compara os 3 modos de consulta:
  • RAG com OpenAI (embedder="openai")
  • RAG com spaCy   (embedder="spacy")
  • Sem RAG         (embedder="none")
"""

import asyncio
import json
from datetime import datetime

import httpx

API_BASE = "http://localhost:8000/api"

EMBEDDERS = [
    ("openai", "RAG c/ OpenAI", "Busca vetorial 768d + LLM"),
    ("spacy", "RAG c/ spaCy", "Busca vetorial 300d + LLM"),
    ("none", "Apenas LLM", "Sem contexto — LLM direto"),
]

REPORT_PATH = "docs/performance_report.md"
REPORT_K15_PATH = "docs/performance_report_k15.md"


async def query(client: httpx.AsyncClient, question: str, embedder: str, top_k: int = 5) -> dict:
    """Call the /api/query endpoint and return a result dict."""
    payload = {"question": question, "top_k": top_k, "embedder": embedder}
    try:
        resp = await client.post("/query", json=payload, timeout=120)
        if resp.status_code == 200:
            data = resp.json()
            answer = data.get("answer", {})
            return {
                "response": (answer.get("content") or "").strip(),
                "sources": answer.get("sources", []),
                "embedder_used": data.get("embedder_used", embedder),
                "error": False,
            }
        elif resp.status_code == 400:
            detail = resp.json().get("detail", "Request invalido")
            return {"response": f"[ERRO] {detail}", "sources": [], "error": True}
        else:
            return {
                "response": f"[ERRO HTTP {resp.status_code}]",
                "sources": [],
                "error": True,
            }
    except httpx.ConnectError:
        return {
            "response": "[ERRO] API nao disponivel — execute 'make dev' primeiro",
            "sources": [],
            "error": True,
        }
    except Exception as exc:
        return {"response": f"[EXCEPTION] {exc}", "sources": [], "error": True}


async def evaluate(top_k: int = 5, report_path: str = REPORT_PATH) -> None:
    """Run all test cases against all embedders and generate a report."""
    with open("test_cases.json") as f:
        cases = json.load(f)

    total = len(cases)
    results = {key: [] for key, _, _ in EMBEDDERS}

    print(f"🧪 Avaliando {total} casos com {len(EMBEDDERS)} embedders (top_k={top_k})")
    print(f"   Conectando em {API_BASE} ...\n")

    async with httpx.AsyncClient(base_url=API_BASE) as client:
        for i, case in enumerate(cases, 1):
            prompt = case["prompt"]
            category = case["category"]

            for key, label, _ in EMBEDDERS:
                print(f"  [{i}/{total}] {label:<16s} {prompt[:55]}...")
                result = await query(client, prompt, key, top_k)
                result["prompt"] = prompt
                result["category"] = category
                result["embedder"] = key
                results[key].append(result)
                await asyncio.sleep(0.3)  # gentle rate limiting

            print()

    # Generate report
    _write_report(top_k, results, report_path)
    _print_summary(results)


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------


def _write_report(top_k: int, results: dict, path: str) -> None:
    lines: list[str] = []
    k15_suffix = " (K=15)" if top_k == 15 else ""

    lines.append(f"# Relatório de Desempenho — RAG{k15_suffix}\n")
    lines.append(f"**Gerado em:** {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
    lines.append(f"**Top K:** {top_k}  |  **Embedders:** {', '.join(k for k, _, _ in EMBEDDERS)}\n")
    lines.append(f"**Total de casos:** {len(next(iter(results.values())))}\n")
    lines.append("---\n")

    # Per-embedder tables
    for key, label, description in EMBEDDERS:
        items = results[key]
        errors = sum(1 for r in items if r.get("error"))
        ok = len(items) - errors

        lines.append(f"## {label}\n")
        lines.append(f"{description}\n\n")
        lines.append(f"**OK:** {ok}/{len(items)}  |  **Erros:** {errors}\n")

        # Source count stats
        with_sources = sum(1 for r in items if not r.get("error") and r.get("sources"))
        lines.append(f"**Com fontes citadas:** {with_sources}\n\n")

        # Table
        lines.append("| # | Prompt | Categoria | Resposta (inicio) | Fontes |\n")
        lines.append("|---|--------|-----------|-------------------|--------|\n")

        for idx, r in enumerate(items, 1):
            response_preview = (r.get("response") or "")[:80].replace("\n", " ")
            source_count = len(r.get("sources") or [])
            lines.append(
                f"| {idx} | {r['prompt'][:60]} | {r['category']} "
                f"| {response_preview} | {source_count} |\n"
            )

        lines.append("\n---\n")

    # Comparison summary
    lines.append("## Comparação entre versões\n\n")
    lines.append("| Métrica | " + " | ".join(label for _, label, _ in EMBEDDERS) + " |\n")
    lines.append("|---------|" + "|".join("---" for _ in EMBEDDERS) + "|\n")

    for metric, extract_fn in [
        ("Casos OK", lambda r: sum(1 for x in r if not x.get("error"))),
        ("Com fontes", lambda r: sum(1 for x in r if not x.get("error") and x.get("sources"))),
        ("Total fontes", lambda r: sum(len(x.get("sources", [])) for x in r if not x.get("error"))),
    ]:
        vals = [str(extract_fn(results[k])) for k, _, _ in EMBEDDERS]
        lines.append(f"| {metric} | " + " | ".join(vals) + " |\n")

    with open(path, "w") as f:
        f.writelines(lines)

    print(f"📄 Relatorio salvo em: {path}")


def _print_summary(results: dict) -> None:
    print("\n" + "=" * 60)
    print("  RESUMO DA AVALIACAO")
    print("=" * 60)
    for key, label, _ in EMBEDDERS:
        items = results[key]
        errors = sum(1 for r in items if r.get("error"))
        ok = len(items) - errors
        with_sources = sum(1 for r in items if not r.get("error") and r.get("sources"))
        print(
            f"  {label:<18s}  OK: {ok:2d}/{len(items)}  Erros: {errors:2d}  Fontes: {with_sources:2d}"
        )
    print("=" * 60)


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------


def run_default() -> None:
    """Top K = 5 (padrão)."""
    asyncio.run(evaluate(top_k=5, report_path=REPORT_PATH))


def run_k15() -> None:
    """Top K = 15 (comparativo)."""
    asyncio.run(evaluate(top_k=15, report_path=REPORT_K15_PATH))


if __name__ == "__main__":
    run_default()
