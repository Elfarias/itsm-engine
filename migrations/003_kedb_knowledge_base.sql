CREATE TABLE kedb_entries (
    error_id VARCHAR(32) PRIMARY KEY,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    service_candidate TEXT,
    symptoms TEXT[] NOT NULL DEFAULT '{}',
    workaround TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT kedb_error_id_not_blank_check CHECK (error_id ~ '[^[:space:]]'),
    CONSTRAINT kedb_title_not_blank_check CHECK (title ~ '[^[:space:]]'),
    CONSTRAINT kedb_summary_not_blank_check CHECK (summary ~ '[^[:space:]]'),
    CONSTRAINT kedb_workaround_not_blank_check CHECK (workaround ~ '[^[:space:]]')
);

CREATE INDEX idx_kedb_service ON kedb_entries (service_candidate);

INSERT INTO kedb_entries (error_id, title, summary, service_candidate, symptoms, workaround) VALUES
(
    'ERR-001',
    'Falha de autenticação no gateway VPN corporativo',
    'Usuários enfrentam timeout ou erro de credenciais no cliente VPN devido a instabilidade no serviço de diretório.',
    'vpn corporativa',
    ARRAY['falha de conexao', 'timeout vpn', 'erro de autenticacao'],
    'Reiniciar o cliente VPN, alternar para o gateway secundário (vpn2.empresa.com) e sincronizar credenciais no portal de autoatendimento.'
),
(
    'ERR-002',
    'Sincronização interrompida na caixa postal de e-mail',
    'Clientes de e-mail não recebem novas mensagens quando o armazenamento da caixa atinge o limite de alerta.',
    'servico de e-mail',
    ARRAY['caixa de entrada nao atualiza', 'falha de sincronizacao', 'caixa cheia'],
    'Acessar o webmail corporativo, esvaziar a pasta de lixeira e itens excluídos e solicitar expurgo de mensagens antigas ao suporte.'
),
(
    'ERR-003',
    'Pool de conexões esgotado no cluster de banco de dados',
    'Aplicações relatam lentidão e recusa de conexão com o PostgreSQL durante picos de processamento em lote.',
    'banco de dados',
    ARRAY['lentidao', 'conexao recusada', 'pool esgotado', 'timeout no banco'],
    'Reiniciar o pooler PgBouncer e executar kill de sessões ociosas em transação (idle in transaction).'
),
(
    'ERR-004',
    'Erro 500 no módulo de emissão do ERP financeiro',
    'Falha de comunicação entre o ERP e a SEFAZ bloqueia a geração e validação de notas fiscais.',
    'erp financeiro',
    ARRAY['erro 500', 'modulo fiscal travado', 'falha na emissao'],
    'Reiniciar o serviço do integrador fiscal local e reenviar o lote em modo de contingência offline.'
);

REVOKE ALL ON kedb_entries FROM PUBLIC, itsm_runtime;
GRANT SELECT ON kedb_entries TO itsm_runtime;
