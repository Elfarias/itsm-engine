import logging
import psycopg

from app.triage.kedb_repository import search_kedb
from app.triage.kedb_schemas import KedbLookupResult, KedbLookupStatus

logger = logging.getLogger(__name__)


def lookup_kedb(
    database_url: str,
    service_candidate: str | None,
    symptoms: list[str],
) -> KedbLookupResult:
    try:
        with psycopg.connect(database_url) as conn:
            matches = search_kedb(conn, service_candidate, symptoms)
            return KedbLookupResult(
                status=KedbLookupStatus.AVAILABLE,
                matches=matches,
            )
    except psycopg.Error as error:
        logger.warning("KEDB database query failed, falling back to UNAVAILABLE: %s", error)
        return KedbLookupResult(
            status=KedbLookupStatus.UNAVAILABLE,
            matches=[],
        )
