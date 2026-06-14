"""End-to-end integration test: a real Docling conversion of a tiny fixture PDF.

Marked ``slow`` — the first run downloads model weights and formula enrichment is
CPU-heavy. Run with: ``pytest -m slow tests/test_processor_integration.py``.
"""

import json
from pathlib import Path

import pytest

from apdf.converter import build_converter
from apdf.processor import DoclingProcessor

FIXTURE = Path(__file__).parent / "fixtures" / "sample.pdf"


def _count_nodes(docling_json: dict) -> tuple[int, int]:
    """Return (n_tables, n_formula_nodes) from an exported docling.json dict."""
    n_tables = len(docling_json.get("tables", []))
    n_formula = sum(
        1
        for text in docling_json.get("texts", [])
        if str(text.get("label", "")).lower() == "formula"
    )
    return n_tables, n_formula


@pytest.mark.slow
def test_real_pdf_produces_structured_outputs(tmp_path):
    converter = build_converter()
    processor = DoclingProcessor(converter)

    result = processor.process(FIXTURE, tmp_path)

    assert result.ok, result.error

    docling_json_path = tmp_path / "docling.json"
    assert docling_json_path.exists()
    data = json.loads(docling_json_path.read_text())  # valid JSON

    n_tables, n_formula = _count_nodes(data)
    assert n_tables >= 1, f"expected >=1 table node, got {n_tables}"
    assert n_formula >= 1, f"expected >=1 FORMULA node, got {n_formula}"
