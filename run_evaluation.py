import json
import os
import subprocess
import time


def run_evaluation():
    with open("test_cases.json", "r") as f:
        cases = json.load(f)

    report_content = "# Relatório de Desempenho do RAG - CPMI 8 de Janeiro\n\n"
    report_content += "| Prompt | Categoria | Resposta |\n"
    report_content += "| --- | --- | --- |\n"

    for case in cases:
        prompt = case["prompt"]
        category = case["category"]

        # Avoid rate limiting
        time.sleep(1)

        # Execute headless.py
        result = subprocess.run(
            ["uv", "run", "src/headless.py", prompt],
            env={**os.environ, "PYTHONPATH": "src"},
            capture_output=True,
            text=True,
        )

        response = result.stdout.strip()
        if result.returncode != 0:
            response = f"[ERROR] {result.stderr.strip()}"

        report_content += f"| {prompt} | {category} | {response} |\n"
        print(f"Processed: {prompt[:50]}...")

    with open("docs/performance_report.md", "w") as f:
        f.write(report_content)

    print("Report generated in docs/performance_report.md")


if __name__ == "__main__":
    run_evaluation()
