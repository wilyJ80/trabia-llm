"""
Script de avaliação experimental com Top K = 15 (comparativo vs padrão K=5).

Uso:
    uv run python run_evaluation_k15.py

Gera docs/performance_report_k15.md com os mesmos 30 casos testados
contra os 3 embedders (openai, spacy, none) usando K=15.
"""

from run_evaluation import run_k15

if __name__ == "__main__":
    run_k15()
