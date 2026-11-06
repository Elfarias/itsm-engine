REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO itsm_runtime;

CREATE TABLE tickets (
    id UUID PRIMARY KEY,
    description TEXT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'NOVO',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT tickets_status_check CHECK (
        status IN (
            'NOVO',
            'EM_TRIAGEM',
            'PENDENTE_INFORMACAO',
            'CLASSIFICADO',
            'ERRO_INTEGRACAO'
        )
    ),
    CONSTRAINT tickets_description_length_check CHECK (
        char_length(description) BETWEEN 1 AND 4000
    ),
    CONSTRAINT tickets_description_not_blank_check CHECK (
        description ~ '[^[:space:]]'
    )
);

CREATE TABLE audit_events (
    id UUID PRIMARY KEY,
    ticket_id UUID NOT NULL REFERENCES tickets (id) ON DELETE RESTRICT,
    event_type VARCHAR(64) NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT audit_events_type_not_blank_check CHECK (
        event_type ~ '[^[:space:]]'
    ),
    CONSTRAINT audit_events_ticket_type_unique UNIQUE (ticket_id, event_type)
);

REVOKE ALL ON tickets, audit_events FROM PUBLIC;
GRANT SELECT, INSERT ON tickets TO itsm_runtime;
GRANT SELECT, INSERT ON audit_events TO itsm_runtime;
REVOKE UPDATE, DELETE ON audit_events FROM itsm_runtime;
