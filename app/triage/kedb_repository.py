import psycopg

from app.triage.kedb_normalization import normalize_text
from app.triage.kedb_schemas import KedbMatch


def search_kedb(
    conn: psycopg.Connection,
    service_candidate: str | None,
    symptoms: list[str],
) -> list[KedbMatch]:
    normalized_service = normalize_text(service_candidate)
    normalized_symptoms = [normalize_text(s) for s in symptoms if normalize_text(s)]

    # 1. Primary matching: Exact equality on normalized service_candidate
    if normalized_service:
        query_service = """
            SELECT error_id, title, summary, workaround
            FROM kedb_entries
            WHERE service_candidate = %s
            ORDER BY error_id ASC
        """
        rows = conn.execute(query_service, (normalized_service,)).fetchall()
        if rows:
            return [
                KedbMatch(
                    error_id=row[0],
                    title=row[1],
                    summary=row[2],
                    match_reasons=[f"service: {normalized_service}"],
                    workaround=row[3],
                )
                for row in rows
            ]

    # 2. Fallback matching: Exact equality on any normalized symptom against symptoms array
    if normalized_symptoms:
        query_symptoms = """
            SELECT error_id, title, summary, symptoms, workaround
            FROM kedb_entries
            WHERE symptoms && %s::text[]
            ORDER BY error_id ASC
        """
        rows = conn.execute(query_symptoms, (normalized_symptoms,)).fetchall()
        matches: list[KedbMatch] = []
        for row in rows:
            row_symptoms = set(row[3])
            matched = [s for s in normalized_symptoms if s in row_symptoms]
            reasons = [f"symptom: {s}" for s in matched] or ["symptom"]
            matches.append(
                KedbMatch(
                    error_id=row[0],
                    title=row[1],
                    summary=row[2],
                    match_reasons=reasons,
                    workaround=row[4],
                )
            )
        return matches

    return []
