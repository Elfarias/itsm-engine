\getenv runtime_password POSTGRES_RUNTIME_PASSWORD

CREATE ROLE itsm_runtime LOGIN PASSWORD :'runtime_password';
GRANT CONNECT ON DATABASE itsm TO itsm_runtime;
