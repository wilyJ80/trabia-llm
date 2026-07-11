# Pré-requisitos

- Adicione as informações ao arquivo `.env` com base no `env.example`

- `uv` instalado: [uv](https://docs.astral.sh/uv/getting-started/installation/)

- Instale as dependências com `uv sync`

- Instale o projeto em modo editável com `uv pip install -e .`

- Script de conveniência para iniciar o banco de dados e realizar migrações localizado em `./docker/dev.sh`

- Para utilizá-lo:

    - `chmod +x ./docker/dev.sh`

    - `./docker/dev.sh`

    - **Ou** utilize um banco de dados PGVector existente e execute as migrações manualmente:

        - `uv run src/migrate.py`

- Instale o modelo de *embeddings* com o comando:

    - `uv run spacy download pt_core_news_lg`

# Execução

- Realize a ingestão com `uv run src/run_ingestion.py`

- Execute o programa principal com `uv run src/main.py`

# TODO:

- [x] Verificar tamanho total dos *chunks* para o relatório; adicionar essa informação à seção de base de conhecimento do relatório

- [x] Saída estruturada

- [x] Validação de esquema

- [x] Resposta incompleta/inválida

- [x] Relatório: carregamento, divisão em *chunks* (chunking), sobreposição (*overlap*) e justificativa

- [x] Relatório: modelo de *embeddings*, se é o mesmo provedor ou não, e justificativa

- [x] Relatório: como a consulta ao banco vetorial foi vetorizada, como a similaridade foi utilizada, quantos trechos (*snippets*) foram retornados e como eles foram adicionados ao *prompt* na aplicação

- [x] Relatório: validação

- [x] Relatório: comparação entre versões (RAG vs. sem RAG), comparação entre estratégias de divisão em *chunks*, parâmetros *top-k* ou modelos de *embeddings*

- [x] Testes com 30 casos: casos simples, casos médios, casos ambíguos, casos com base de conhecimento insuficiente, casos que testam os limites da aplicação

- [x] Relatório: 
    - [x] definição do problema, 
    - [x] base documental, 
    - [x] *pipeline* de ingestão, 
    - [x] arquitetura da solução, 
    - [x] modelos e componentes utilizados, 
    - [x] protocolo experimental, 
    - [x] resultados, 
    - [x] analisar criticamente, 
    - [x] conclusão, 
    - [x] referências.

- [x] Slides: 
    - [x] problema atacado, 
    - [x] arquitetura da solução, 
    - [x] documental base, 
    - [x] pipeline de ingestão, 
    - [x] recuperação vetorial, 
    - [x] validação ou mecanismo híbrido, 
    - [x] resultados experimentais, 
    - [x] principais falhas
