# Avaliacao da extracao estruturada
- Executado em: 2026-07-13T17:01:48-03:00
- Casos: 30
- Embedder: `spacy`
- Corpus: `data\relatorio-cpmi-versao-consolidada_231017_100010.pdf`
- Chunks no corpus: 1533
- Chunk size/overlap: 2000/200

## Resumo por versao

| Metrica | top_k=0 | top_k=5 |
| --- | ---: | ---: |
| Execucoes concluidas | 30 | 30 |
| JSON/schema validos | 100.0% | 100.0% |
| Campos obrigatorios completos | 60.0% | 46.7% |
| Status de validacao correto | 80.0% | 66.7% |
| Falsos `valid` em casos insuficientes | 0.0% | 0.0% |
| Cobertura dos valores anotados | 71.8% | 54.4% |
| Latencia media (s) | 18.86 | 68.78 |
| Chunks de contexto medios | 0.0 | 5.0 |

## Resultados por categoria

| Versao | Categoria | Casos | Cobertura anotada | Status correto |
| --- | --- | ---: | ---: | ---: |
| top_k=0 | facil | 6 | 80.4% | 50.0% |
| top_k=0 | medio | 7 | 73.4% | 85.7% |
| top_k=0 | ambiguo | 6 | 68.0% | 66.7% |
| top_k=0 | base_insuficiente | 6 | 100.0% | 100.0% |
| top_k=0 | limite | 5 | 62.5% | 100.0% |
| top_k=5 | facil | 6 | 64.7% | 50.0% |
| top_k=5 | medio | 7 | 51.6% | 57.1% |
| top_k=5 | ambiguo | 6 | 54.0% | 66.7% |
| top_k=5 | base_insuficiente | 6 | 100.0% | 100.0% |
| top_k=5 | limite | 5 | 45.0% | 60.0% |

## Criterios

A cobertura compara os valores retornados com as anotacoes versionadas em `extraction_test_cases.json`, apos normalizacao de caixa, acentos e pontuacao. O conjunto nao calcula precisao: valores adicionais exigem revisao humana.

Casos de base insuficiente aceitam `partial` ou `invalid`; qualquer `valid` nesses casos conta como falso positivo. Campos inferidos por regras locais nao contam como campos obrigatorios confirmados.

Erros de execucao: 0. Os resultados completos estao em `docs/extraction_performance_results.json`.
