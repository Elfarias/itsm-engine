from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
README = PROJECT_ROOT / "README.md"


def test_readme_documents_local_proposal_flow_and_configuration() -> None:
    readme = README.read_text(encoding="utf-8")
    heading = "## Interpretação local por LLM"
    section_start = readme.index(heading)
    next_section = readme.find("\n## ", section_start + len(heading))
    section = readme[section_start:next_section]
    request_example = section.split("```powershell", maxsplit=1)[1].split(
        "```",
        maxsplit=1,
    )[0]

    assert "/tickets/$($ticket.id)/interpretation" in request_example
    assert "-Body" not in request_example
    assert "OPENROUTER_API_KEY" not in request_example
    assert "OPENROUTER_API_KEY" in section
    assert "OPENROUTER_MODEL" in section
    assert "descrição já persistida" in section
    assert "não é persistida" in section
    assert "POST /tickets/{ticket_id}/triage" in section
    assert "`404`" in section
    assert "`503`" in section
    assert "`502`" in section
    assert "`127.0.0.1`" in section
