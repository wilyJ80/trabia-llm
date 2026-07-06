import json
import subprocess
import os
import time

def run_evaluation():
    with open('test_cases.json', 'r') as f:
        cases = json.load(f)

    # Use K=15
    new_env = {**os.environ, 'PYTHONPATH': 'src', 'K': '15'}

    report_content = "# Relatório de Desempenho do RAG - CPMI 8 de Janeiro (K=15)\n\n"
    report_content += "| Prompt | Categoria | Resposta | Score |\n"
    report_content += "| --- | --- | --- | --- |\n"

    for case in cases:
        prompt = case['prompt']
        category = case['category']
        
        # Avoid rate limiting
        time.sleep(1)

        # Execute headless.py with K=15 enforced
        result = subprocess.run(
            ['uv', 'run', 'src/headless.py', prompt],
            env=new_env,
            capture_output=True,
            text=True
        )
        
        response = result.stdout.strip()
        if result.returncode != 0:
            response = f"[ERROR] {result.stderr.strip()}"
        
        # Add empty column for Score
        report_content += f"| {prompt} | {category} | {response} | |\n"
        print(f"Processed: {prompt[:50]}...")

    with open('docs/performance_report_k15.md', 'w') as f:
        f.write(report_content)
    
    print("Report generated in docs/performance_report_k15.md")

if __name__ == "__main__":
    run_evaluation()
