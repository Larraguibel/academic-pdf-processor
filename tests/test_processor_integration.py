"""End-to-end integration test: a real Docling conversion of a tiny fixture PDF.

Marked ``slow`` — the first run downloads model weights and formula enrichment is
CPU-heavy. Run with: ``pytest -m slow tests/test_processor_integration.py``.
"""

from pathlib import Path

import pytest

from apdf.converter import build_converter
from apdf.processor import DoclingProcessor

FIXTURE = Path(__file__).parent / "fixtures" / "sample.pdf"


def _count_elements(out_dir: Path) -> tuple[int, int]:
    """Return (n_tables, n_formulas) from the per-element files under ``elements/``."""
    elements = out_dir / "elements"
    n_tables = len(list(elements.glob("table_*.html")))
    n_formula = len(list(elements.glob("equation_*.tex")))
    return n_tables, n_formula


@pytest.mark.slow
def test_real_pdf_produces_structured_outputs(tmp_path):
    converter = build_converter()
    processor = DoclingProcessor(converter)

    result = processor.process(FIXTURE, tmp_path)

    assert result.ok, result.error

    n_tables, n_formula = _count_elements(tmp_path)
    assert n_tables >= 1, f"expected >=1 table element, got {n_tables}"
    assert n_formula >= 1, f"expected >=1 equation element, got {n_formula}"
