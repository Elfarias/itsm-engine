from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_DOCUMENT = PROJECT_ROOT / "PROJECT.md"
VERIFIED_FEATURES = {
    "ticket-api": "API básica de chamados",
    "ticket-triage": "Triagem determinística",
    "ticket-triage-api": "API local de triagem determinística",
}
IN_PROGRESS_FEATURE = (
    "llm-ticket-interpretation",
    "Interpretação de descrições em texto livre por LLM",
)


def _dashboard_rows(project_text: str) -> list[str]:
    return [
        line
        for line in project_text.splitlines()
        if line.startswith("|") and ".specs/features/" in line
    ]


def test_dashboard_lists_verified_deliveries_and_evidence() -> None:
    project_text = PROJECT_DOCUMENT.read_text(encoding="utf-8")
    rows = _dashboard_rows(project_text)

    for feature, name in VERIFIED_FEATURES.items():
        matching_rows = [row for row in rows if f".specs/features/{feature}/spec.md" in row]
        assert len(matching_rows) == 1
        row = matching_rows[0]
        assert name in row
        assert "Concluída e verificada" in row
        assert f".specs/features/{feature}/tasks.md" in row
        assert f".specs/features/{feature}/verification.md" in row

        assert (PROJECT_ROOT / ".specs" / "features" / feature / "spec.md").is_file()
        assert (PROJECT_ROOT / ".specs" / "features" / feature / "tasks.md").is_file()
        assert (
            PROJECT_ROOT / ".specs" / "features" / feature / "verification.md"
        ).is_file()


def test_dashboard_lists_unprioritized_roadmap() -> None:
    project_text = PROJECT_DOCUMENT.read_text(encoding="utf-8")
    planned_rows = [
        row
        for row in project_text.splitlines()
        if row.startswith("|") and "Planejada, sem prioridade" in row
    ]

    assert len(planned_rows) == 7
    assert not any("Interpretação" in row for row in planned_rows)
    assert any("KEDB" in row for row in planned_rows)
    assert any("autenticação e autorização" in row for row in planned_rows)
    assert any("complementação de chamados" in row for row in planned_rows)
    assert any("Integração ITSM externa" in row for row in planned_rows)
    assert any("Interface gráfica" in row for row in planned_rows)
    assert any("Kubernetes" in row for row in planned_rows)
    assert any("procedimentos de correção" in row for row in planned_rows)


def test_dashboard_lists_in_progress_interpretation_delivery() -> None:
    project_text = PROJECT_DOCUMENT.read_text(encoding="utf-8")
    feature, name = IN_PROGRESS_FEATURE
    feature_rows = [
        row
        for row in _dashboard_rows(project_text)
        if f".specs/features/{feature}/spec.md" in row
    ]

    assert len(feature_rows) == 1
    row = feature_rows[0]
    assert name in row
    assert "Em andamento" in row
    assert "aguardando verificação independente" in row
    assert f".specs/features/{feature}/tasks.md" in row
    assert f".specs/features/{feature}/verification.md" in row
    active_status = next(
        line
        for line in project_text.splitlines()
        if line.startswith("**Em andamento:**")
    )
    assert name.casefold() in active_status.casefold()
    assert (PROJECT_ROOT / ".specs" / "features" / feature / "spec.md").is_file()
    assert (PROJECT_ROOT / ".specs" / "features" / feature / "tasks.md").is_file()


def test_dashboard_requires_same_commit_updates() -> None:
    project_text = PROJECT_DOCUMENT.read_text(encoding="utf-8")
    policy = next(
        line
        for line in project_text.splitlines()
        if line.startswith("**Regra de atualização:**")
    )

    assert "cada entrega" in policy
    assert "mesmo commit" in policy
    assert "PROJECT.md" in policy


def test_completed_dashboard_rows_have_passing_verification() -> None:
    project_text = PROJECT_DOCUMENT.read_text(encoding="utf-8")
    completed_rows = [
        row for row in _dashboard_rows(project_text) if "Concluída e verificada" in row
    ]

    assert len(completed_rows) == len(VERIFIED_FEATURES)
    for feature in VERIFIED_FEATURES:
        feature_root = PROJECT_ROOT / ".specs" / "features" / feature
        task_text = (feature_root / "tasks.md").read_text(encoding="utf-8")
        verification_text = (feature_root / "verification.md").read_text(
            encoding="utf-8"
        )

        assert "- [ ]" not in task_text
        assert "**Verdict**: PASS" in verification_text
