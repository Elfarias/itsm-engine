import psycopg

from app.triage.kedb_repository import search_kedb


def test_search_matches_by_service_candidate(
    migrated_database_roles: tuple[str, str],
) -> None:
    _, runtime_connection = migrated_database_roles
    with psycopg.connect(runtime_connection) as conn:
        matches = search_kedb(conn, "  VPN Corporativa  ", ["qualquer sintoma"])
        assert len(matches) == 1
        assert matches[0].error_id == "ERR-001"
        assert matches[0].title == "Falha de autenticação no gateway VPN corporativo"
        assert any("service" in r for r in matches[0].match_reasons)
        assert "gateway secundário" in matches[0].workaround


def test_search_falls_back_to_symptoms(
    migrated_database_roles: tuple[str, str],
) -> None:
    _, runtime_connection = migrated_database_roles
    with psycopg.connect(runtime_connection) as conn:
        # Service without known error falls back to symptom matching
        matches = search_kedb(
            conn,
            "Servico Inexistente",
            ["Caixa de entrada não atualiza"],
        )
        assert len(matches) == 1
        assert matches[0].error_id == "ERR-002"
        assert matches[0].title == "Sincronização interrompida na caixa postal de e-mail"
        assert any("symptom" in r for r in matches[0].match_reasons)


def test_matches_ordered_by_error_id_asc(
    migrated_database_roles: tuple[str, str],
) -> None:
    _, runtime_connection = migrated_database_roles
    with psycopg.connect(runtime_connection) as conn:
        # Multiple symptoms matching different records
        matches = search_kedb(
            conn,
            None,
            ["timeout vpn", "lentidao", "erro 500"],
        )
        assert len(matches) >= 2
        error_ids = [m.error_id for m in matches]
        assert error_ids == sorted(error_ids)


def test_search_returns_empty_when_no_match(
    migrated_database_roles: tuple[str, str],
) -> None:
    _, runtime_connection = migrated_database_roles
    with psycopg.connect(runtime_connection) as conn:
        matches = search_kedb(conn, "Serviço Qualquer", ["Sintoma desconhecido"])
        assert matches == []

        matches_empty = search_kedb(conn, None, [])
        assert matches_empty == []

