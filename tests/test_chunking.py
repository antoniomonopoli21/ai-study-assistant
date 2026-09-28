import pytest

from app.services.chunking import chunk_text


def test_chunk_text_with_overlap():
    text = "uno due tre quattro cinque sei sette otto nove dieci"

    chunks = chunk_text(
        text,
        chunk_size=4,
        overlap=1
    )

    assert chunks == [
        "uno due tre quattro",
        "quattro cinque sei sette",
        "sette otto nove dieci"
    ]


def test_chunk_text_empty():
    chunks = chunk_text(
        "",
        chunk_size=4,
        overlap=1
    )

    assert chunks == []

import pytest


def test_chunk_text_rejects_invalid_overlap():
    with pytest.raises(ValueError):
        chunk_text(
            "uno due tre quattro",
            chunk_size=4,
            overlap=4
        )