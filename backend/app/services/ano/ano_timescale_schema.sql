-- SafeNet ANO — TimescaleDB schema
-- Телеметрия скаутов (сырые данные → агрегация → история)
--
-- Установка расширения:
--   CREATE EXTENSION IF NOT EXISTS timescaledb;
--
-- Применение:
--   psql -h localhost -U safenet -d safenet -f ano_timescale_schema.sql

-- ── Сырые пробы скаутов (TTL 24ч) ─────────────────────────────────

CREATE TABLE IF NOT EXISTS scout_log (
    id          BIGSERIAL,
    ts          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    server_id   TEXT NOT NULL,
    rtt_ms      DOUBLE PRECISION,
    jitter_ms   DOUBLE PRECISION,
    loss_pct    DOUBLE PRECISION,
    throughput_kbps DOUBLE PRECISION,
    life_hours  DOUBLE PRECISION,
    source      TEXT NOT NULL DEFAULT 'server'  -- 'server' | 'client'
);

-- Преобразовать в гипертаблицу (партиционирование по времени)
SELECT create_hypertable('scout_log', 'ts',
    chunk_time_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_scout_server_ts
    ON scout_log (server_id, ts DESC);

CREATE INDEX IF NOT EXISTS idx_scout_loss
    ON scout_log (loss_pct DESC, ts DESC)
    WHERE loss_pct > 5;

-- TTL: автоматическая очистка старше 24 часов
SELECT add_retention_policy('scout_log', INTERVAL '24 hours',
    if_not_exists => TRUE
);

-- ── Почасовая агрегация рейтингов (TTL 30 дней) ──────────────────

CREATE TABLE IF NOT EXISTS route_ranking (
    id              BIGSERIAL,
    ts              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    server_id       TEXT NOT NULL,
    hour            TIMESTAMPTZ NOT NULL,
    avg_rtt         DOUBLE PRECISION,
    avg_jitter      DOUBLE PRECISION,
    max_loss        DOUBLE PRECISION,
    avg_throughput  DOUBLE PRECISION,
    rank_score      DOUBLE PRECISION,
    zone            TEXT  -- 'green' | 'yellow' | 'red' | 'black'
);

SELECT create_hypertable('route_ranking', 'ts',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS idx_ranking_server_hour
    ON route_ranking (server_id, hour DESC);

SELECT add_retention_policy('route_ranking', INTERVAL '30 days',
    if_not_exists => TRUE
);

-- ── Посуточные исторические тренды (TTL 90 дней) ─────────────────

CREATE TABLE IF NOT EXISTS route_history (
    id                  BIGSERIAL,
    ts                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    server_id           TEXT NOT NULL,
    date                DATE NOT NULL,
    daily_avg_rtt       DOUBLE PRECISION,
    daily_max_loss      DOUBLE PRECISION,
    daily_avg_jitter    DOUBLE PRECISION,
    daily_uptime_pct    DOUBLE PRECISION,
    total_throughput    DOUBLE PRECISION,
    handover_count      INTEGER DEFAULT 0,
    avg_downtime_sec    DOUBLE PRECISION
);

SELECT create_hypertable('route_history', 'ts',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS idx_history_server_date
    ON route_history (server_id, date DESC);

SELECT add_retention_policy('route_history', INTERVAL '90 days',
    if_not_exists => TRUE
);

-- ── Непрерывные агрегации (материализованные представления) ────────

-- Почасовая агрегация scout_log → route_ranking
CREATE MATERIALIZED VIEW IF NOT EXISTS scout_hourly_agg
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', ts) AS bucket,
    server_id,
    AVG(rtt_ms) AS avg_rtt,
    AVG(jitter_ms) AS avg_jitter,
    MAX(loss_pct) AS max_loss,
    AVG(throughput_kbps) AS avg_throughput
FROM scout_log
GROUP BY bucket, server_id;

-- Посуточная агреска route_ranking → route_history
CREATE MATERIALIZED VIEW IF NOT EXISTS ranking_daily_agg
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', ts) AS bucket,
    server_id,
    AVG(avg_rtt) AS daily_avg_rtt,
    MAX(max_loss) AS daily_max_loss,
    AVG(avg_jitter) AS daily_avg_jitter,
    COUNT(*) AS sample_count
FROM route_ranking
GROUP BY bucket, server_id;

-- ── Комментарии ────────────────────────────────────────────────────

COMMENT ON TABLE scout_log IS 'Сырые пробы скаутов (TTL 24ч)';
COMMENT ON TABLE route_ranking IS 'Почасовая агрегация рейтингов (TTL 30д)';
COMMENT ON TABLE route_history IS 'Посуточные исторические тренды (TTL 90д)';
