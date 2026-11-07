import unicodedata


def normalize_text(text: str | None) -> str:
    if not text:
        return ""
    # Normalize unicode to NFKD and drop combining diacritical marks
    decomposed = unicodedata.normalize("NFKD", text)
    without_accents = "".join(
        char for char in decomposed if not unicodedata.combining(char)
    )
    # Lowercase and normalize whitespace sequences to a single space
    cleaned = " ".join(without_accents.lower().split())
    return cleaned.strip()

