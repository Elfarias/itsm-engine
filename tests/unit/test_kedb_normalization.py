from app.triage.kedb_normalization import normalize_text


def test_normalization_handles_accents_whitespace_and_case() -> None:
    assert normalize_text("  Conexão Lenta  ") == "conexao lenta"
    assert normalize_text("VPN Corporativa") == "vpn corporativa"
    assert normalize_text("AUTENTICAÇÃO FALHOU") == "autenticacao falhou"
    assert normalize_text("Serviço de E-mail") == "servico de e-mail"
    assert normalize_text("Múltiplos    Espaços   Aqui") == "multiplos espacos aqui"


def test_normalization_handles_none_and_empty() -> None:
    assert normalize_text(None) == ""
    assert normalize_text("") == ""
    assert normalize_text("    ") == ""

