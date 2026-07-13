# Modificações realizadas no projeto

Este documento registra as mudanças feitas para alinhar o código e o relatório do
grupo 4 ao projeto 2 da especificação do T3. Foram modificados 23 arquivos e
criados 6 arquivos. As alterações ainda estão no working tree, sem commit.

## 1. Validação da extração

### `src/core/models.py`

Foi adicionado o campo:

```python
inferred_fields: list[str]
```

Esse campo informa quais valores foram preenchidos por heurísticas locais, e não
confirmados pelo LLM.

### `src/core/service.py`

A ordem da validação foi corrigida. Antes, os fallbacks preenchiam campos
obrigatórios antes da validação, o que podia transformar uma resposta incompleta
do LLM em uma saída `valid`.

Agora o fluxo é:

1. Interpretar e normalizar a resposta do LLM.
2. Tentar reparar o JSON, quando necessário.
3. Validar a resposta original do LLM.
4. Aplicar fallbacks somente para melhorar a exibição.
5. Registrar os campos preenchidos pelos fallbacks em `inferred_fields`.

Campos inferidos continuam presentes em `missing_required_fields` e não tornam a
extração válida.

### `src/core/prompt.py`

O prompt de extração passou a instruir o modelo a:

- usar um cabeçalho explícito como título;
- derivar um tipo documental curto;
- identificar a ação ou o assunto central do documento;
- não deixar campos obrigatórios vazios quando a informação estiver no texto;
- usar o contexto recuperado somente como apoio, sem substituir o documento
  enviado.

## 2. Tratamento de documentos longos

O sistema anteriormente enviava apenas os primeiros 12.000 caracteres do
documento ao LLM. Isso introduzia um viés forte para as primeiras páginas.

O novo comportamento em `src/core/service.py`:

- aceita até 24.000 caracteres para a extração;
- seleciona até 24 blocos distribuídos pelo documento;
- preserva conteúdo do início, do meio e do fim;
- quando não existem marcadores de página, cria três segmentos equivalentes;
- limita a consulta vetorial a 3.000 caracteres, também combinando início, meio e
  fim.

Essa amostragem reduz a chance de ignorar fatos localizados nas últimas páginas,
mas não equivale a uma leitura exaustiva do documento inteiro.

## 3. Ingestão e armazenamento vetorial

### Numeração de páginas

Em `src/ingest/loader.py`, a numeração das páginas foi alterada de base zero para
base um:

- antes: a primeira página era `0`;
- agora: a primeira página é `1`.

A rota de extração também passou a usar `1` como valor padrão nos marcadores de
página.

### Inserção em lote

Foi acrescentado `insert_chunks` em:

- `src/core/port/repository_port.py`;
- `src/infra/repository.py`.

Os chunks de cada lote de embeddings agora são inseridos em uma única transação.
O método `insert_chunk` continua disponível e delega para a operação em lote.

Antes, cada chunk provocava um `commit` separado. A alteração reduz a quantidade
de transações durante a ingestão do PDF completo.

## 4. Reinicialização controlada da coleção

A rota `POST /api/ingest` recebeu o parâmetro:

```text
reset_collection: bool = false
```

Quando esse parâmetro é `true`, a aplicação:

1. identifica a coleção correspondente ao embedder selecionado;
2. remove os chunks existentes dessa coleção;
3. ingere o novo documento.

A coleção do outro embedder não é afetada. Esse comportamento impede que
reexecuções do experimento acumulem chunks duplicados.

## 5. Saúde da API e configuração Docker

### Verificação real do LLM

O endpoint `/api/health` retornava `llm_connected=true` de forma fixa.

Foi implementado `OpenAILLM.is_reachable()` em `src/infra/llm_openai.py`. O método
consulta o endpoint `/models` do provedor OpenAI-compatível, com timeout de cinco
segundos. O valor de `llm_connected` agora representa o estado real do Ollama.

### URLs internas do Compose

Em `docker-compose.yaml`, as URLs internas foram fixadas como:

```yaml
LLM_BASE_URL: http://ollama:11434/v1
EMBED_BASE_URL: http://ollama:11434/v1
```

Isso impede que valores `localhost` vindos do `.env` sejam usados dentro do
container da API. Dentro do Docker, `localhost` apontaria para o próprio container
da API, e não para o Ollama.

### Cache do spaCy

Em `src/api/dependencies.py`, o `SpacyEmbedder` passou a usar `lru_cache`. O modelo
`pt_core_news_lg` agora é carregado uma vez por processo da API, em vez de ser
recarregado a cada requisição.

O comentário de `src/infra/embedder_spacy.py` também foi corrigido. O modelo é
baixado no primeiro uso e permanece disponível enquanto o container existir; ele
não é pré-instalado durante o build da imagem.

## 6. Interface web

### `src/api/static/index.html`

Foi adicionado o controle **Substituir base**, marcado por padrão no fluxo
principal. O controle corresponde ao parâmetro `reset_collection`.

As versões de `styles.css` e `app.js` foram atualizadas para evitar que o navegador
continue usando arquivos antigos em cache.

### `src/api/static/app.js`

O JavaScript agora:

- envia `reset_collection=true` ou `false` para `/api/ingest`;
- exibe a seção **Campos inferidos por regra** quando `inferred_fields` não está
  vazio.

### `src/api/static/styles.css`

Foram adicionados os estilos do checkbox, incluindo alinhamento e cor de destaque.

## 7. Conjunto de avaliação

Foi criado `extraction_test_cases.json` com 30 documentos curtos anotados:

| Categoria | Casos |
| --- | ---: |
| Fácil | 6 |
| Médio | 7 |
| Ambíguo | 6 |
| Base insuficiente | 6 |
| Limite | 5 |
| **Total** | **30** |

Cada caso contém:

- identificador;
- categoria;
- texto de entrada;
- status de validação esperado;
- valores esperados por campo.

O conjunto inclui documentos administrativos, textos incompletos, ambiguidades,
prompt injection, fragmentos de JSON e variações de idioma e formato.

## 8. Avaliador reproduzível

Foi criado `run_extraction_evaluation.py`. O script:

- pode limpar e ingerir novamente o corpus da CPMI;
- executa os mesmos casos com `top_k=0` e `top_k=5`;
- usa o mesmo embedder, LLM, prompt, temperatura e corpus nas duas versões;
- calcula métricas por execução e por categoria;
- grava resultados completos em JSON;
- gera um resumo em Markdown;
- grava checkpoint após cada caso;
- aceita `--resume` para continuar uma execução interrompida;
- usa timeout padrão de 900 segundos por extração;
- registra o tipo da exceção quando ocorre um erro.

As métricas implementadas são:

- validade do JSON e do schema;
- completude dos quatro campos obrigatórios;
- correspondência do status retornado com o esperado;
- falsos `valid` nos casos de informação insuficiente;
- cobertura dos valores anotados;
- latência;
- quantidade de chunks usados.

A cobertura normaliza caixa, acentos e pontuação. Ela mede a recuperação dos
valores anotados, mas não mede a precisão dos valores adicionais produzidos pelo
LLM.

### Correção de timeout

Na primeira execução, cinco casos atingiram o timeout antigo de 180 segundos. A
exceção `httpx.ReadTimeout` possuía mensagem vazia e estava sendo contabilizada
incorretamente como execução concluída.

O avaliador foi corrigido para:

- distinguir `error=None` de uma string de erro vazia;
- registrar o nome da exceção;
- usar timeout configurável, com padrão de 900 segundos;
- carregar resultados anteriores ao executar com `--resume`;
- repetir apenas casos incompletos ou com erro.

Os cinco casos foram reexecutados. O resultado final possui 60 execuções únicas e
zero erros.

## 9. Artefatos experimentais

Foram gerados:

- `docs/extraction_performance_results.json`: respostas e métricas das 60
  execuções;
- `docs/extraction_performance_report.md`: resumo automático das métricas.

O corpus foi recriado com:

- embedder spaCy;
- 1.333 páginas;
- 1.533 chunks;
- `chunk_size=2000`;
- overlap de 200 caracteres;
- modelo `phi4-mini:latest`;
- temperatura 0,1.

## 10. Resultados do experimento

| Métrica | `top_k=0` | `top_k=5` |
| --- | ---: | ---: |
| Execuções concluídas | 30 | 30 |
| JSON/schema válidos | 100,0% | 100,0% |
| Campos obrigatórios completos | 60,0% | 46,7% |
| Status de validação correto | 80,0% | 66,7% |
| Falsos `valid` em casos insuficientes | 0,0% | 0,0% |
| Cobertura dos valores anotados | 71,8% | 54,4% |
| Latência média | 18,86 s | 68,78 s |
| Chunks de contexto médios | 0,0 | 5,0 |

Todas as respostas finais atenderam ao schema. A validação também evitou falsos
`valid` nos seis casos de informação insuficiente.

O contexto RAG reduziu completude, correspondência de status e cobertura, além de
aumentar a latência em aproximadamente 3,6 vezes. A causa observada é a diferença
de domínio: a base vetorial contém a CPMI, enquanto os documentos curtos abrangem
outros domínios administrativos.

A conclusão não é que RAG seja prejudicial em geral. O resultado demonstra que
contexto fora do domínio pode introduzir ruído. Uma implantação real deve separar
coleções por domínio ou aplicar um limiar de similaridade antes de adicionar
chunks ao prompt.

## 11. Alterações no relatório acadêmico

O conteúdo de `docs/report.md` foi atualizado para refletir o comportamento real
do código e o protocolo executado.

Foram removidos:

- a comparação antiga entre `top_k=5` e `top_k=15`;
- os resultados antigos de 20/30 e 23/30;
- as contagens não controladas de 1.995 e 1.519 chunks;
- conclusões qualitativas sem um protocolo reproduzível;
- a afirmação de que aumentar `top_k` melhorava o resultado geral.

Foram adicionados:

- protocolo com 30 documentos e 60 execuções;
- descrição da reinicialização controlada da coleção;
- corpus fixo com 1.333 páginas e 1.533 chunks;
- tabelas com os resultados reais;
- métricas por categoria;
- explicação sobre `inferred_fields`;
- limitações da cobertura automática;
- discussão sobre contexto fora do domínio;
- comandos para reprodução;
- referências para casos e resultados completos;
- descrição do uso de IA generativa e da revisão humana.

## 12. Geração do PDF

Foi criado `docs/report.css` para formatar o relatório em A4. O CSS define:

- margens;
- numeração de páginas;
- tipografia;
- hierarquia de títulos;
- formatação de tabelas;
- blocos de código;
- controle de quebras de página;
- agrupamento da introdução com o exemplo JSON;
- início da seção de resultados em uma página própria.

O `docs/report.pdf` foi regenerado a partir do Markdown. O arquivo final possui
sete páginas. Todas foram renderizadas e inspecionadas visualmente para verificar:

- texto cortado;
- sobreposições;
- tabelas divididas incorretamente;
- títulos isolados;
- numeração;
- legibilidade dos blocos de código.

## 13. README

O `README.md` passou a documentar:

- o parâmetro `reset_collection`;
- um exemplo de ingestão com reinicialização da coleção;
- o valor retornado em `params_used`;
- o comando da avaliação principal do projeto 2;
- os arquivos de resultados gerados.

## 14. Testes alterados e adicionados

### `tests/test_extract.py`

Foram adicionados testes para garantir que:

- fallbacks não transformem uma resposta incompleta em válida;
- campos preenchidos por regras apareçam em `inferred_fields`;
- a amostragem de documentos longos contenha início, meio e fim;
- a consulta vetorial distribuída respeite o limite esperado.

### `tests/test_chunks.py`

O teste agora confirma que a primeira página carregada é `1`.

### `tests/test_repository.py`

Foi adicionado um teste de inserção em lote. Os vetores existentes nos testes
também foram corrigidos de 300 para 768 dimensões, pois o fixture usa
`ChunkModel`, destinado ao embedder OpenAI-compatível.

### `tests/test_extraction_evaluation.py`

Foi criado um arquivo de testes para:

- normalização de caixa e acentos;
- validade do schema;
- validação das fontes;
- exclusão de campos inferidos da completude;
- comparação de status;
- exclusão de timeouts com mensagem vazia da contagem de execuções concluídas.

### `tests/test_static_ui.py`

O teste agora confirma que o JavaScript servido contém `reset_collection`.

### `tests/conftest.py`

O fixture de limpeza passou a criar seu próprio engine e repositório, executando a
limpeza antes e depois do teste e encerrando o engine no `finally`. Isso evita
conflitos entre event loops do `pytest-asyncio`.

## 15. Verificações realizadas

Foram executados:

```bash
uv run pytest tests/test_extract.py tests/test_extraction_evaluation.py \
  tests/test_repository.py tests/test_static_ui.py tests/test_chunks.py -q

uv run ruff check src tests run_extraction_evaluation.py

python -m compileall src tests run_extraction_evaluation.py
```

Resultados:

- 21 testes aprovados;
- 1 aviso de depreciação do Starlette, sem falha;
- Ruff sem erros;
- compilação concluída;
- imagem Docker reconstruída;
- API respondendo em `http://localhost:8000/`;
- `llm_connected=true`;
- 1.533 chunks spaCy presentes;
- 60 execuções experimentais concluídas sem erro.

A suíte HTTP completa não foi executada porque ela reingere o PDF integral várias
vezes. Os endpoints reais `/api/ingest` e `/api/extract` foram exercitados pelas
60 execuções do protocolo experimental.
