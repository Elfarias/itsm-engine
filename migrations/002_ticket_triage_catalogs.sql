CREATE TABLE catalog_versions (
    version_id VARCHAR(32) PRIMARY KEY,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT catalog_versions_id_not_blank CHECK (
        version_id ~ '[^[:space:]]'
    )
);

CREATE UNIQUE INDEX catalog_versions_one_active
    ON catalog_versions (is_active)
    WHERE is_active;

CREATE TABLE cmdb_services (
    version_id VARCHAR(32) NOT NULL
        REFERENCES catalog_versions (version_id) ON DELETE RESTRICT,
    service_id VARCHAR(64) NOT NULL,
    name VARCHAR(160) NOT NULL,
    PRIMARY KEY (version_id, service_id),
    CONSTRAINT cmdb_services_id_not_blank CHECK (
        service_id ~ '[^[:space:]]'
    ),
    CONSTRAINT cmdb_services_name_not_blank CHECK (
        name ~ '[^[:space:]]'
    )
);

CREATE TABLE support_teams (
    version_id VARCHAR(32) NOT NULL
        REFERENCES catalog_versions (version_id) ON DELETE RESTRICT,
    team_id VARCHAR(64) NOT NULL,
    name VARCHAR(160) NOT NULL,
    PRIMARY KEY (version_id, team_id),
    CONSTRAINT support_teams_id_not_blank CHECK (
        team_id ~ '[^[:space:]]'
    ),
    CONSTRAINT support_teams_name_not_blank CHECK (
        name ~ '[^[:space:]]'
    )
);

CREATE TABLE service_team_mappings (
    version_id VARCHAR(32) NOT NULL,
    service_id VARCHAR(64) NOT NULL,
    team_id VARCHAR(64) NOT NULL,
    PRIMARY KEY (version_id, service_id, team_id),
    UNIQUE (version_id, service_id),
    FOREIGN KEY (version_id, service_id)
        REFERENCES cmdb_services (version_id, service_id) ON DELETE RESTRICT,
    FOREIGN KEY (version_id, team_id)
        REFERENCES support_teams (version_id, team_id) ON DELETE RESTRICT
);

CREATE TABLE cmdb_assets (
    version_id VARCHAR(32) NOT NULL,
    asset_id VARCHAR(64) NOT NULL,
    service_id VARCHAR(64) NOT NULL,
    name VARCHAR(160) NOT NULL,
    PRIMARY KEY (version_id, asset_id),
    UNIQUE (version_id, asset_id, service_id),
    FOREIGN KEY (version_id, service_id)
        REFERENCES cmdb_services (version_id, service_id) ON DELETE RESTRICT,
    CONSTRAINT cmdb_assets_id_not_blank CHECK (
        asset_id ~ '[^[:space:]]'
    ),
    CONSTRAINT cmdb_assets_name_not_blank CHECK (
        name ~ '[^[:space:]]'
    )
);

INSERT INTO catalog_versions (version_id, is_active)
VALUES ('catalog-v1', TRUE);

INSERT INTO cmdb_services (version_id, service_id, name)
VALUES
    ('catalog-v1', 'service-connectivity', 'Synthetic Network Connectivity'),
    ('catalog-v1', 'service-endpoint', 'Synthetic Endpoint Management');

INSERT INTO support_teams (version_id, team_id, name)
VALUES
    ('catalog-v1', 'team-network', 'Synthetic Network Operations'),
    ('catalog-v1', 'team-workplace', 'Synthetic Workplace Support');

INSERT INTO service_team_mappings (version_id, service_id, team_id)
VALUES
    ('catalog-v1', 'service-connectivity', 'team-network'),
    ('catalog-v1', 'service-endpoint', 'team-workplace');

INSERT INTO cmdb_assets (version_id, asset_id, service_id, name)
VALUES
    ('catalog-v1', 'asset-router-001', 'service-connectivity', 'Synthetic Router 001'),
    ('catalog-v1', 'asset-laptop-001', 'service-endpoint', 'Synthetic Laptop 001');

ALTER TABLE tickets
    ADD COLUMN service_id VARCHAR(64),
    ADD COLUMN asset_id VARCHAR(64),
    ADD COLUMN impact VARCHAR(8),
    ADD COLUMN urgency VARCHAR(8),
    ADD COLUMN priority VARCHAR(2),
    ADD COLUMN target_team VARCHAR(64),
    ADD COLUMN catalog_version VARCHAR(32),
    ADD COLUMN facts_revision INTEGER NOT NULL DEFAULT 0,
    ADD CONSTRAINT tickets_impact_check CHECK (
        impact IS NULL OR impact IN ('ALTO', 'MEDIO', 'BAIXO')
    ),
    ADD CONSTRAINT tickets_urgency_check CHECK (
        urgency IS NULL OR urgency IN ('ALTA', 'MEDIA', 'BAIXA')
    ),
    ADD CONSTRAINT tickets_priority_check CHECK (
        priority IS NULL OR priority IN ('P1', 'P2', 'P3', 'P4')
    ),
    ADD CONSTRAINT tickets_facts_revision_check CHECK (facts_revision >= 0),
    ADD CONSTRAINT tickets_catalog_version_fk
        FOREIGN KEY (catalog_version)
        REFERENCES catalog_versions (version_id) ON DELETE RESTRICT,
    ADD CONSTRAINT tickets_service_fk
        FOREIGN KEY (catalog_version, service_id)
        REFERENCES cmdb_services (version_id, service_id) ON DELETE RESTRICT,
    ADD CONSTRAINT tickets_asset_fk
        FOREIGN KEY (catalog_version, asset_id)
        REFERENCES cmdb_assets (version_id, asset_id) ON DELETE RESTRICT,
    ADD CONSTRAINT tickets_target_team_fk
        FOREIGN KEY (catalog_version, service_id, target_team)
        REFERENCES service_team_mappings (version_id, service_id, team_id)
        ON DELETE RESTRICT;

ALTER TABLE audit_events
    DROP CONSTRAINT audit_events_ticket_type_unique,
    ADD COLUMN details JSONB NOT NULL DEFAULT '{}'::JSONB;

REVOKE ALL ON catalog_versions, cmdb_services, cmdb_assets,
    support_teams, service_team_mappings FROM PUBLIC, itsm_runtime;
GRANT SELECT ON catalog_versions, cmdb_services, cmdb_assets,
    support_teams, service_team_mappings TO itsm_runtime;

GRANT UPDATE (
    status,
    service_id,
    asset_id,
    impact,
    urgency,
    priority,
    target_team,
    catalog_version,
    facts_revision
) ON tickets TO itsm_runtime;
REVOKE UPDATE, DELETE ON audit_events FROM itsm_runtime;
