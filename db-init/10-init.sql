CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR NOT NULL UNIQUE,
    password_hash VARCHAR NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_default_password BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT now(),
    role VARCHAR NOT NULL DEFAULT 'viewer',
    email VARCHAR UNIQUE,
    tags JSON NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS wazuh_connections (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL UNIQUE,
    indexer_url VARCHAR NOT NULL,
    wazuh_user VARCHAR NOT NULL,
    wazuh_password VARCHAR NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT now(),
    tested BOOLEAN DEFAULT FALSE,
    last_tested_at TIMESTAMPTZ,
    last_test_ok BOOLEAN
);

CREATE TABLE IF NOT EXISTS user_interactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    endpoint VARCHAR,
    method VARCHAR,
    details TEXT,
    "timestamp" TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS wazuh_vulnerabilities (
    id SERIAL PRIMARY KEY,
    connection_id INTEGER NOT NULL REFERENCES wazuh_connections(id),
    status VARCHAR DEFAULT 'ACTIVE',
    agent_id VARCHAR NOT NULL,
    agent_name VARCHAR,
    os_full TEXT,
    os_platform TEXT,
    os_version TEXT,
    package_name TEXT,
    package_version TEXT,
    tags JSON NOT NULL DEFAULT '[]',
    package_type TEXT,
    package_arch TEXT,
    cve_id TEXT NOT NULL,
    severity TEXT,
    score_base NUMERIC,
    score_version TEXT,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    published_at TIMESTAMPTZ,
    description TEXT,
    reference TEXT,
    scanner_vendor TEXT,
    first_seen TIMESTAMPTZ DEFAULT now(),
    last_seen TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT uniq_wazuh_vuln UNIQUE (
        connection_id,
        agent_id,
        package_name,
        package_version,
        cve_id
    )
);

CREATE TABLE IF NOT EXISTS vulnerability_history (
    id SERIAL PRIMARY KEY,
    vulnerability_id INTEGER NOT NULL REFERENCES wazuh_vulnerabilities(id),
    action VARCHAR NOT NULL,
    details TEXT,
    "timestamp" TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS vulnerability_events (
    id BIGSERIAL,
    event_time TIMESTAMPTZ NOT NULL DEFAULT now(),
    event_type VARCHAR NOT NULL,
    vulnerability_id INTEGER REFERENCES wazuh_vulnerabilities(id),
    connection_id INTEGER REFERENCES wazuh_connections(id),
    agent_id VARCHAR,
    cve_id TEXT,
    severity TEXT,
    status TEXT,
    details JSONB,
    CONSTRAINT uniq_vulnerability_events_id_time UNIQUE (id, event_time)
);

SELECT create_hypertable(
    'vulnerability_events',
    'event_time',
    if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS ix_user_interactions_endpoint
    ON user_interactions (endpoint);

CREATE INDEX IF NOT EXISTS ix_vulnerability_history_vulnerability_time
    ON vulnerability_history (vulnerability_id, "timestamp" DESC);

CREATE INDEX IF NOT EXISTS ix_wazuh_vulnerabilities_agent_id
    ON wazuh_vulnerabilities (agent_id);

CREATE INDEX IF NOT EXISTS ix_wazuh_vulnerabilities_status
    ON wazuh_vulnerabilities (status);

CREATE INDEX IF NOT EXISTS ix_wazuh_vulnerabilities_severity
    ON wazuh_vulnerabilities (severity);

CREATE INDEX IF NOT EXISTS ix_wazuh_vulnerabilities_last_seen
    ON wazuh_vulnerabilities (last_seen DESC);

CREATE INDEX IF NOT EXISTS ix_wazuh_vulnerabilities_connection_last_seen
    ON wazuh_vulnerabilities (connection_id, last_seen DESC);

CREATE INDEX IF NOT EXISTS ix_wazuh_vulnerabilities_cve_id
    ON wazuh_vulnerabilities (cve_id);

CREATE INDEX IF NOT EXISTS ix_vulnerability_events_vulnerability_time
    ON vulnerability_events (vulnerability_id, event_time DESC);

CREATE INDEX IF NOT EXISTS ix_vulnerability_events_connection_time
    ON vulnerability_events (connection_id, event_time DESC);

CREATE INDEX IF NOT EXISTS ix_vulnerability_events_agent_time
    ON vulnerability_events (agent_id, event_time DESC);

CREATE INDEX IF NOT EXISTS ix_vulnerability_events_cve_time
    ON vulnerability_events (cve_id, event_time DESC);

CREATE INDEX IF NOT EXISTS ix_vulnerability_events_severity_time
    ON vulnerability_events (severity, event_time DESC);

CREATE INDEX IF NOT EXISTS ix_vulnerability_events_type_time
    ON vulnerability_events (event_type, event_time DESC);

CREATE OR REPLACE FUNCTION fn_calculate_dwell_time(
    p_first_seen TIMESTAMPTZ,
    p_last_seen TIMESTAMPTZ
) RETURNS NUMERIC
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
    IF p_first_seen IS NULL OR p_last_seen IS NULL THEN
        RETURN NULL;
    END IF;
    RETURN EXTRACT(EPOCH FROM (p_last_seen - p_first_seen)) / 86400.0;
END;
$$;

CREATE OR REPLACE FUNCTION fn_calculate_total_age(
    p_first_seen TIMESTAMPTZ
) RETURNS NUMERIC
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
    IF p_first_seen IS NULL THEN
        RETURN NULL;
    END IF;
    RETURN EXTRACT(EPOCH FROM (now() - p_first_seen)) / 86400.0;
END;
$$;

CREATE OR REPLACE FUNCTION fn_vulnerability_events_in_range(
    p_connection_id INTEGER,
    p_from TIMESTAMPTZ,
    p_to TIMESTAMPTZ
) RETURNS SETOF vulnerability_events
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
    RETURN QUERY
    SELECT *
    FROM vulnerability_events
    WHERE (p_connection_id IS NULL OR connection_id = p_connection_id)
      AND (p_from IS NULL OR event_time >= p_from)
      AND (p_to IS NULL OR event_time < p_to)
    ORDER BY event_time DESC;
END;
$$;
