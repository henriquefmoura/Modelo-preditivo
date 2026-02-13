-- BigQuery DDL para a tabela de eventos omnichannel
-- Esta tabela armazena eventos anônimos de múltiplos canais (web, app, loja, whatsapp)
-- sem dados pessoais (LGPD-safe)

CREATE TABLE IF NOT EXISTS `{project_id}.{dataset}.events` (
  event_time TIMESTAMP NOT NULL,
  channel STRING NOT NULL,  -- web|app|store|whatsapp
  anon_id STRING NOT NULL,  -- identificador anônimo (hash/cookie/token)
  event_name STRING NOT NULL,
  event_props STRING,  -- JSON serializado com propriedades do evento
  ingestion_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(event_time)
CLUSTER BY anon_id, event_name
OPTIONS(
  description="Eventos omnichannel anônimos para detecção de momento ideal de reforma",
  require_partition_filter=true
);

-- Tabela para armazenar os scores calculados
CREATE TABLE IF NOT EXISTS `{project_id}.{dataset}.scores_ready` (
  anon_id STRING NOT NULL,
  score FLOAT64 NOT NULL,
  class_label STRING NOT NULL,  -- MOMENTO IDEAL | NUTRIR | NÃO ABORDAR
  score_date DATE NOT NULL,
  top_drivers STRING,  -- JSON com os 3 principais componentes do score
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY score_date
CLUSTER BY anon_id, class_label
OPTIONS(
  description="Scores de prontidão para reforma calculados diariamente"
);

-- Índices recomendados (não necessário criar explicitamente no BigQuery devido ao clustering)
-- O clustering por anon_id e event_name já otimiza queries por esses campos

-- Exemplo de query para validar a tabela após criação:
-- SELECT 
--   DATE(event_time) as event_date,
--   channel,
--   COUNT(*) as event_count,
--   COUNT(DISTINCT anon_id) as unique_users
-- FROM `{project_id}.{dataset}.events`
-- WHERE DATE(event_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
-- GROUP BY 1, 2
-- ORDER BY 1 DESC, 3 DESC;
