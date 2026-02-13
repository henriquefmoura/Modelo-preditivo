# Reformas-Momento-Ideal

Sistema omnichannel anônimo (LGPD-safe) para detectar o "momento ideal" de abordagem para reformas, a partir de eventos internos (web/app/loja/whatsapp), gerando um score de prontidão (0-100).

## 📋 Descrição

Este projeto implementa um sistema de scoring que:
- Analisa eventos anônimos de múltiplos canais (web, app, loja, WhatsApp)
- Calcula features de engajamento (recência, frequência, intenção, diversidade)
- Gera um score "Ready-to-Reform" de 0-100
- Classifica usuários em: **MOMENTO IDEAL** (≥70), **NUTRIR** (40-69), **NÃO ABORDAR** (<40)
- Fornece API REST para consulta de scores
- Dashboard interativo para visualização
- Job automatizado via GitHub Actions

**✅ 100% LGPD-safe**: Não utiliza dados pessoais (sem nome, CPF, telefone, endereço). Apenas identificadores anônimos e eventos comportamentais.

## 🏗️ Arquitetura

```
reformas-momento-ideal/
├── README.md
├── requirements.txt
├── .gitignore
├── data/
│   └── sample/                 # Dados fake para demo
│       └── events_sample.csv
├── sql/
│   └── bigquery_events.sql     # DDL BigQuery
├── src/
│   ├── config.py               # Configurações
│   ├── event_schema.py         # Schemas de eventos
│   ├── features.py             # Feature engineering
│   ├── scoring.py              # Cálculo de scores
│   ├── bq_io.py               # I/O BigQuery
│   ├── generate_sample_data.py # Gerador de dados fake
│   └── run_daily_score.py     # Job batch diário
├── api/
│   └── app.py                 # FastAPI
├── dashboard/
│   └── streamlit_app.py       # Dashboard Streamlit
└── .github/workflows/
    └── daily_score.yml        # GitHub Actions

```

## 🚀 Stack Tecnológica

- **BigQuery**: Data lake para eventos e scores
- **Python 3.10+**: Processamento e feature engineering
- **FastAPI**: API REST para consulta de scores
- **Streamlit**: Dashboard interativo
- **GitHub Actions**: Automação do job diário
- **Pandas/NumPy**: Manipulação de dados

## 📊 Schema BigQuery

### Tabela `events`
```sql
- event_time: TIMESTAMP (quando o evento ocorreu)
- channel: STRING (web|app|store|whatsapp)
- anon_id: STRING (identificador anônimo)
- event_name: STRING (nome do evento)
- event_props: STRING (JSON com propriedades)
- ingestion_time: TIMESTAMP
```

Particionada por `DATE(event_time)` e clusterizada por `(anon_id, event_name)`.

### Tabela `scores_ready`
```sql
- anon_id: STRING
- score: FLOAT64 (0-100)
- class_label: STRING (MOMENTO IDEAL|NUTRIR|NÃO ABORDAR)
- score_date: DATE
- top_drivers: STRING (JSON com top 3 componentes)
- created_at: TIMESTAMP
```

## 🔧 Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/henriquefmoura/Modelo-preditivo.git
cd Modelo-preditivo
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. (Opcional) Configure BigQuery

Se for usar BigQuery em produção:

```bash
# Defina as variáveis de ambiente
export BQ_PROJECT_ID="seu-projeto-gcp"
export BQ_DATASET="reformas"
export BQ_CREDENTIALS_JSON="/caminho/para/credentials.json"
```

### 4. Crie as tabelas no BigQuery

```bash
# Execute o SQL no BigQuery Console ou via bq CLI
bq query --use_legacy_sql=false < sql/bigquery_events.sql
```

## 💻 Uso

### Modo Local (com dados de exemplo)

#### 1. Gerar dados de exemplo

```bash
python src/generate_sample_data.py
```

Isso criará `data/sample/events_sample.csv` com 100 usuários e 30 dias de eventos fake.

#### 2. Executar o job de scoring

```bash
python src/run_daily_score.py --local_sample
```

Output:
- Scores salvos em `data/processed/scores_YYYYMMDD.csv`
- Console mostra: total de eventos, usuários, distribuição de classes, top 5 scores

#### 3. Iniciar a API

```bash
uvicorn api.app:app --reload
```

Acesse:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs

Exemplo de request:
```bash
curl -X POST "http://localhost:8000/score" \
  -H "Content-Type: application/json" \
  -d '{"use_sample": true}'
```

#### 4. Iniciar o Dashboard

```bash
streamlit run dashboard/streamlit_app.py
```

Acesse: http://localhost:8501

### Modo Produção (com BigQuery)

#### 1. Configure as credenciais

```bash
export BQ_PROJECT_ID="seu-projeto"
export BQ_DATASET="reformas"
export BQ_CREDENTIALS_JSON="/path/to/credentials.json"
```

#### 2. Execute o job

```bash
python src/run_daily_score.py --lookback_days 30
```

#### 3. API com BigQuery

A API automaticamente detecta as credenciais do BigQuery e permite consultas:

```bash
curl -X POST "http://localhost:8000/score" \
  -H "Content-Type: application/json" \
  -d '{"anon_ids": ["anon_00001", "anon_00002"]}'
```

## 📈 Features Calculadas

O sistema calcula as seguintes features por `anon_id`:

1. **recency_days**: Dias desde o último evento relevante
2. **freq_7d, freq_14d, freq_30d**: Frequência de eventos em janelas de tempo
3. **high_intent_7d**: Eventos de alta intenção nos últimos 7 dias
   - submit_quote, whatsapp_quote_request, scan_qr_service, talk_to_consultant, begin_checkout
4. **category_diversity_14d**: Número de categorias distintas acessadas
5. **cart_abandon_7d**: Carrinhos abandonados (add_to_cart sem begin_checkout em 24h)
6. **reform_bundle_14d**: Detecta combos típicos de reforma:
   - piso + rodapé
   - tinta + massa + lixa
   - azulejo + rejunte
   - porta + fechadura
   - janela + persiana

## 🎯 Score Ready-to-Reform

Score de 0-100 calculado com pesos ajustáveis:

- **30%** Recência (mais recente = maior score)
- **25%** High Intent (eventos de alta intenção)
- **20%** Frequência (mais engajamento = maior score)
- **15%** Diversidade de categorias
- **10%** Bundles + Abandono de carrinho

### Classificação

- **≥70**: **MOMENTO IDEAL** - Abordar agora
- **40-69**: **NUTRIR** - Continuar engajamento
- **<40**: **NÃO ABORDAR** - Baixo potencial no momento

## 🤖 GitHub Actions

O workflow `daily_score.yml` executa automaticamente às 06:00 UTC todos os dias.

### Configurar Secrets

No GitHub, vá em `Settings > Secrets and variables > Actions` e adicione:

- `BQ_PROJECT_ID`: ID do projeto Google Cloud
- `BQ_DATASET`: Nome do dataset (padrão: "reformas")
- `BQ_CREDENTIALS_JSON`: Conteúdo do arquivo JSON de credenciais

### Executar manualmente

No GitHub: `Actions > Daily Ready-to-Reform Scoring > Run workflow`

## 📖 API Endpoints

### `GET /`
Informações da API

### `GET /health`
Health check

### `POST /score`
Calcula scores

**Request body:**
```json
{
  "use_sample": true  // Usar dados de exemplo
}
```

ou

```json
{
  "anon_ids": ["anon_00001", "anon_00002"]  // Buscar do BigQuery
}
```

ou

```json
{
  "events": [
    {
      "event_time": "2024-01-15T10:30:00",
      "channel": "web",
      "anon_id": "anon_12345",
      "event_name": "submit_quote",
      "event_props": {"category": "piso", "value": 1500.0}
    }
  ]
}
```

**Response:**
```json
{
  "scores": [
    {
      "anon_id": "anon_00001",
      "score": 75.5,
      "class_label": "MOMENTO IDEAL",
      "top_drivers": {
        "recency": 30.0,
        "high_intent": 25.0,
        "frequency": 20.5
      }
    }
  ],
  "count": 1,
  "timestamp": "2024-01-15T10:30:00"
}
```

## 📊 Dashboard

O dashboard Streamlit oferece:

- 📈 **Distribuição por classe**: Gráfico de pizza com % de cada classificação
- 🏆 **Ranking**: Top 50 usuários por score
- 🎯 **Score drivers**: Componentes que mais contribuem para o score
- 🔍 **Filtros**: Por classificação, range de score
- 📊 **Histograma**: Distribuição dos scores

## 🧪 Testes

Para testar o sistema completo em modo local:

```bash
# 1. Gerar dados
python src/generate_sample_data.py

# 2. Rodar scoring
python src/run_daily_score.py --local_sample

# 3. Testar API
uvicorn api.app:app --reload &
curl http://localhost:8000/health

# 4. Testar dashboard
streamlit run dashboard/streamlit_app.py
```

## 🔒 Segurança e LGPD

✅ **Totalmente anônimo**: Nenhum dado pessoal é coletado ou armazenado
- ❌ Sem nome
- ❌ Sem CPF
- ❌ Sem telefone
- ❌ Sem e-mail
- ❌ Sem endereço
- ✅ Apenas `anon_id` (hash/cookie/token)

## 📝 Licença

Este projeto é parte de uma tese de doutorado.

## 👨‍💻 Autor

Henrique F. Moura
