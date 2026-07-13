"""Reproducible evaluation for the Project 2 structured extraction workflow."""

import argparse
import asyncio
import json
import time
import unicodedata
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

API_BASE = "http://localhost:8000/api"
CASES_PATH = Path("extraction_test_cases.json")
REPORT_PATH = Path("docs/extraction_performance_report.md")
RESULTS_PATH = Path("docs/extraction_performance_results.json")
PARTIAL_RESULTS_PATH = Path("docs/extraction_performance_results.partial.json")
DEFAULT_CORPUS = Path("data/relatorio-cpmi-versao-consolidada_231017_100010.pdf")
LIST_FIELDS = ("dates", "actors", "organizations", "facts", "evidence", "categories")
REQUIRED_FIELDS = ("document_type", "title", "main_event", "facts")


def normalize(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode()
    return " ".join("".join(char if char.isalnum() else " " for char in text.lower()).split())


def contains(actual: object, expected: str) -> bool:
    return normalize(expected) in normalize(actual)


def is_schema_valid(extraction: object) -> bool:
    if not isinstance(extraction, dict):
        return False
    if any(not isinstance(extraction.get(field, []), list) for field in LIST_FIELDS):
        return False
    if not isinstance(extraction.get("sources", []), list):
        return False
    if extraction.get("validation_status") not in {"valid", "partial", "invalid"}:
        return False
    return all(
        isinstance(source, dict)
        and isinstance(source.get("claim"), str)
        and isinstance(source.get("page"), int)
        and source["page"] >= 0
        for source in extraction.get("sources", [])
    )


def score_expected_values(extraction: dict[str, Any], expected: dict[str, list[str]]) -> tuple[int, int]:
    hits = 0
    total = 0
    for field, expected_values in expected.items():
        if not expected_values:
            continue
        actual = extraction.get(field)
        if field == "document_type":
            total += 1
            hits += int(any(contains(actual, value) for value in expected_values))
            continue
        actual_values = actual if isinstance(actual, list) else [actual]
        for value in expected_values:
            total += 1
            hits += int(any(contains(item, value) for item in actual_values if item is not None))
    return hits, total


def status_matches(actual: str | None, expected: str) -> bool:
    if expected == "partial":
        return actual in {"partial", "invalid"}
    return actual == expected


def required_complete(extraction: dict[str, Any]) -> bool:
    inferred = set(extraction.get("inferred_fields", []))
    return all(extraction.get(field) not in (None, "", []) and field not in inferred for field in REQUIRED_FIELDS)


async def prepare_corpus(
    client: httpx.AsyncClient,
    corpus_path: Path,
    embedder: str,
    chunk_size: int,
    chunk_overlap: int,
) -> dict[str, Any]:
    with corpus_path.open("rb") as corpus_file:
        response = await client.post(
            "/ingest",
            files={"file": (corpus_path.name, corpus_file, "application/pdf")},
            data={
                "chunk_size": str(chunk_size),
                "chunk_overlap": str(chunk_overlap),
                "embedder": embedder,
                "reset_collection": "true",
            },
            timeout=1800,
        )
    response.raise_for_status()
    return response.json()


async def evaluate_case(
    client: httpx.AsyncClient,
    case: dict[str, Any],
    top_k: int,
    embedder: str,
    request_timeout: float,
) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        response = await client.post(
            "/extract",
            data={"text": case["text"], "top_k": str(top_k), "embedder": embedder},
            timeout=request_timeout,
        )
        payload = response.json()
    except Exception as exc:
        return {
            "case_id": case["id"],
            "category": case["category"],
            "top_k": top_k,
            "error": f"{type(exc).__name__}: {exc}",
            "latency_seconds": round(time.perf_counter() - started, 3),
        }

    latency = round(time.perf_counter() - started, 3)
    if response.status_code != 200:
        return {
            "case_id": case["id"],
            "category": case["category"],
            "top_k": top_k,
            "error": payload.get("detail", f"HTTP {response.status_code}"),
            "latency_seconds": latency,
        }

    extraction = payload.get("extraction", {})
    hits, total = score_expected_values(extraction, case.get("expected", {}))
    actual_status = extraction.get("validation_status")
    return {
        "case_id": case["id"],
        "category": case["category"],
        "top_k": top_k,
        "error": None,
        "latency_seconds": latency,
        "context_chunks_used": payload.get("context_chunks_used", 0),
        "schema_valid": is_schema_valid(extraction),
        "required_complete": required_complete(extraction),
        "status_match": status_matches(actual_status, case["expected_status"]),
        "false_valid": case["expected_status"] == "partial" and actual_status == "valid",
        "expected_hits": hits,
        "expected_total": total,
        "expected_coverage": round(hits / total, 4) if total else None,
        "extraction": extraction,
    }


def summarize(items: list[dict[str, Any]]) -> dict[str, Any]:
    completed = [item for item in items if item.get("error") is None]
    annotated = [item for item in completed if item.get("expected_total")]
    insufficient = [item for item in completed if item["category"] == "base_insuficiente"]
    total_hits = sum(item.get("expected_hits", 0) for item in annotated)
    total_expected = sum(item.get("expected_total", 0) for item in annotated)
    return {
        "cases": len(items),
        "completed": len(completed),
        "schema_valid_rate": sum(item.get("schema_valid", False) for item in completed)
        / max(len(completed), 1),
        "required_complete_rate": sum(item.get("required_complete", False) for item in completed)
        / max(len(completed), 1),
        "status_match_rate": sum(item.get("status_match", False) for item in completed)
        / max(len(completed), 1),
        "false_valid_rate": sum(item.get("false_valid", False) for item in insufficient)
        / max(len(insufficient), 1),
        "annotated_values": total_expected,
        "expected_coverage": total_hits / max(total_expected, 1),
        "average_latency_seconds": sum(item["latency_seconds"] for item in completed)
        / max(len(completed), 1),
        "average_context_chunks": sum(item.get("context_chunks_used", 0) for item in completed)
        / max(len(completed), 1),
    }


def percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def write_report(metadata: dict[str, Any], results: list[dict[str, Any]]) -> None:
    by_top_k: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for item in results:
        by_top_k[item["top_k"]].append(item)

    summaries = {top_k: summarize(items) for top_k, items in sorted(by_top_k.items())}
    lines = [
        "# Avaliacao da extracao estruturada\n",
        f"- Executado em: {metadata['executed_at']}\n",
        f"- Casos: {metadata['case_count']}\n",
        f"- Embedder: `{metadata['embedder']}`\n",
        f"- Corpus: `{metadata['corpus']}`\n",
        f"- Chunks no corpus: {metadata['chunks_stored']}\n",
        f"- Chunk size/overlap: {metadata['chunk_size']}/{metadata['chunk_overlap']}\n\n",
        "## Resumo por versao\n\n",
        "| Metrica | " + " | ".join(f"top_k={top_k}" for top_k in summaries) + " |\n",
        "| --- | " + " | ".join("---:" for _ in summaries) + " |\n",
    ]
    metrics = (
        ("Execucoes concluidas", "completed", lambda value: str(int(value))),
        ("JSON/schema validos", "schema_valid_rate", percent),
        ("Campos obrigatorios completos", "required_complete_rate", percent),
        ("Status de validacao correto", "status_match_rate", percent),
        ("Falsos `valid` em casos insuficientes", "false_valid_rate", percent),
        ("Cobertura dos valores anotados", "expected_coverage", percent),
        ("Latencia media (s)", "average_latency_seconds", lambda value: f"{value:.2f}"),
        ("Chunks de contexto medios", "average_context_chunks", lambda value: f"{value:.1f}"),
    )
    for label, key, formatter in metrics:
        lines.append(
            f"| {label} | "
            + " | ".join(formatter(summary[key]) for summary in summaries.values())
            + " |\n"
        )

    lines.append("\n## Resultados por categoria\n\n")
    lines.append("| Versao | Categoria | Casos | Cobertura anotada | Status correto |\n")
    lines.append("| --- | --- | ---: | ---: | ---: |\n")
    for top_k, items in sorted(by_top_k.items()):
        categories: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in items:
            categories[item["category"]].append(item)
        for category, category_items in categories.items():
            category_summary = summarize(category_items)
            coverage = (
                percent(category_summary["expected_coverage"])
                if category_summary["annotated_values"]
                else "n/a"
            )
            lines.append(
                f"| top_k={top_k} | {category} | {len(category_items)} | "
                f"{coverage} | "
                f"{percent(category_summary['status_match_rate'])} |\n"
            )

    errors = [item for item in results if item.get("error") is not None]
    lines.extend(
        [
            "\n## Criterios\n\n",
            "A cobertura compara os valores retornados com as anotacoes versionadas em "
            "`extraction_test_cases.json`, apos normalizacao de caixa, acentos e pontuacao. "
            "O conjunto nao calcula precisao: valores adicionais exigem revisao humana.\n\n",
            "Casos de base insuficiente aceitam `partial` ou `invalid`; qualquer `valid` nesses "
            "casos conta como falso positivo. Campos inferidos por regras locais nao contam como "
            "campos obrigatorios confirmados.\n\n",
            f"Erros de execucao: {len(errors)}. Os resultados completos estao em "
            "`docs/extraction_performance_results.json`.\n",
        ]
    )
    REPORT_PATH.write_text("".join(lines), encoding="utf-8")


async def run(args: argparse.Namespace) -> None:
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    if args.limit:
        cases = cases[: args.limit]
    top_k_values = [int(value) for value in args.top_k.split(",")]

    timeout = httpx.Timeout(1800, connect=30)
    async with httpx.AsyncClient(base_url=args.api_base, timeout=timeout) as client:
        chunks_stored = 0
        if args.prepare_corpus:
            print(f"Preparing corpus with {args.embedder}...", flush=True)
            ingest = await prepare_corpus(
                client,
                args.corpus,
                args.embedder,
                args.chunk_size,
                args.chunk_overlap,
            )
            chunks_stored = ingest["chunks_stored"]
        else:
            health = (await client.get(f"/health?embedder={args.embedder}")).json()
            chunks_stored = health.get("chunks_count", 0)

        if any(top_k > 0 for top_k in top_k_values) and chunks_stored == 0:
            raise RuntimeError("A versao com RAG exige uma colecao ingerida. Use --prepare-corpus.")

        results: list[dict[str, Any]] = []
        if args.resume:
            resume_path = (
                PARTIAL_RESULTS_PATH if PARTIAL_RESULTS_PATH.exists() else RESULTS_PATH
            )
            if resume_path.exists():
                previous = json.loads(resume_path.read_text(encoding="utf-8"))["results"]
                results = [item for item in previous if item.get("error") is None]
        completed_keys = {(item["top_k"], item["case_id"]) for item in results}
        pending = [
            (top_k, case)
            for top_k in top_k_values
            for case in cases
            if (top_k, case["id"]) not in completed_keys
        ]
        total = len(cases) * len(top_k_values)
        for index, (top_k, case) in enumerate(pending, start=len(results) + 1):
            print(f"[{index}/{total}] top_k={top_k} {case['id']}", flush=True)
            results.append(
                await evaluate_case(
                    client,
                    case,
                    top_k,
                    args.embedder,
                    args.request_timeout,
                )
            )
            PARTIAL_RESULTS_PATH.write_text(
                json.dumps({"results": results}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    metadata = {
        "executed_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "api_base": args.api_base,
        "case_count": len(cases),
        "embedder": args.embedder,
        "top_k": top_k_values,
        "corpus": str(args.corpus),
        "chunks_stored": chunks_stored,
        "chunk_size": args.chunk_size,
        "chunk_overlap": args.chunk_overlap,
    }
    RESULTS_PATH.write_text(
        json.dumps({"metadata": metadata, "results": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_report(metadata, results)
    PARTIAL_RESULTS_PATH.unlink(missing_ok=True)
    print(f"Wrote {REPORT_PATH} and {RESULTS_PATH}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-base", default=API_BASE)
    parser.add_argument("--embedder", choices=("openai", "spacy"), default="openai")
    parser.add_argument("--top-k", default="0,5")
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--chunk-size", type=int, default=2000)
    parser.add_argument("--chunk-overlap", type=int, default=200)
    parser.add_argument("--prepare-corpus", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--request-timeout", type=float, default=900)
    parser.add_argument("--limit", type=int)
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(run(parse_args()))
