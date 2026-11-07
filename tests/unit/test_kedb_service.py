from unittest.mock import MagicMock, patch
import psycopg

from app.triage.kedb_schemas import KedbLookupStatus, KedbMatch
from app.triage.kedb_service import lookup_kedb


def test_service_returns_available_status_with_matches() -> None:
    dummy_match = KedbMatch(
        error_id="ERR-001",
        title="VPN Timeout",
        summary="Erro de gateway",
        match_reasons=["service: vpn corporativa"],
        workaround="Reiniciar conexao",
    )
    with patch("psycopg.connect") as mock_connect, patch(
        "app.triage.kedb_service.search_kedb"
    ) as mock_search:
        mock_search.return_value = [dummy_match]
        result = lookup_kedb(
            "postgresql://fake/db",
            "vpn corporativa",
            ["timeout"],
        )

        assert result.status == KedbLookupStatus.AVAILABLE
        assert len(result.matches) == 1
        assert result.matches[0].error_id == "ERR-001"


def test_service_returns_available_status_when_matches_empty() -> None:
    with patch("psycopg.connect") as mock_connect, patch(
        "app.triage.kedb_service.search_kedb"
    ) as mock_search:
        mock_search.return_value = []
        result = lookup_kedb(
            "postgresql://fake/db",
            "servico_desconhecido",
            [],
        )

        assert result.status == KedbLookupStatus.AVAILABLE
        assert result.matches == []


def test_service_handles_database_error_as_unavailable() -> None:
    with patch(
        "psycopg.connect",
        side_effect=psycopg.OperationalError("Database down"),
    ):
        result = lookup_kedb(
            "postgresql://fake/db",
            "vpn corporativa",
            ["timeout"],
        )

        assert result.status == KedbLookupStatus.UNAVAILABLE
        assert result.matches == []
