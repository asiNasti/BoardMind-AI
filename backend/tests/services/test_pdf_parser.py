from types import SimpleNamespace

import pytest

from backend.app.services import pdf_parser


def test_extract_text_uses_fitz(monkeypatch) -> None:
    pages = [
        SimpleNamespace(get_text=lambda: " First "),
        SimpleNamespace(get_text=lambda: ""),
    ]

    class FakeDocument:
        def __iter__(self):
            return iter(pages)

    monkeypatch.setattr(
        pdf_parser,
        "fitz",
        SimpleNamespace(open=lambda **_: FakeDocument()),
    )

    assert pdf_parser.extract_text_from_pdf(b"pdf") == "First"


def test_extract_text_falls_back_to_pypdf(monkeypatch) -> None:
    page = SimpleNamespace(extract_text=lambda: "Rules")
    reader = SimpleNamespace(pages=[page])
    monkeypatch.setattr(pdf_parser, "fitz", None)
    monkeypatch.setattr(pdf_parser, "PdfReader", lambda _: reader)

    assert pdf_parser.extract_text_from_pdf(b"pdf") == "Rules"


def test_extract_text_falls_back_to_pdfplumber(monkeypatch) -> None:
    page = SimpleNamespace(extract_text=lambda: "Rules")

    class FakeDocument:
        def __init__(self):
            self.pages = [page]

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

    monkeypatch.setattr(pdf_parser, "fitz", None)
    monkeypatch.setattr(pdf_parser, "PdfReader", None)
    monkeypatch.setattr(
        pdf_parser, "pdfplumber", SimpleNamespace(open=lambda _: FakeDocument())
    )

    assert pdf_parser.extract_text_from_pdf(b"pdf") == "Rules"


def test_extract_text_rejects_empty_content() -> None:
    with pytest.raises(ValueError, match="PDF content is empty"):
        pdf_parser.extract_text_from_pdf(b"")


def test_extract_text_requires_extraction_library(monkeypatch) -> None:
    monkeypatch.setattr(pdf_parser, "fitz", None)
    monkeypatch.setattr(pdf_parser, "PdfReader", None)
    monkeypatch.setattr(pdf_parser, "pdfplumber", None)

    with pytest.raises(ValueError, match="No PDF extraction library"):
        pdf_parser.extract_text_from_pdf(b"pdf")


@pytest.mark.parametrize(
    ("chunk_size", "overlap", "message"),
    [
        (0, 0, "chunk_size"),
        (10, -1, "overlap"),
        (10, 10, "overlap"),
    ],
)
def test_chunk_text_validates_parameters(chunk_size, overlap, message) -> None:
    with pytest.raises(ValueError, match=message):
        pdf_parser.chunk_text("text", chunk_size=chunk_size, overlap=overlap)


def test_chunk_text_returns_empty_for_whitespace() -> None:
    assert pdf_parser.chunk_text(" \n\t ") == []
