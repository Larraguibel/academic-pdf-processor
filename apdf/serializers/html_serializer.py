"""Write a human-readable ``document.html`` with MathML equations + figures.

``save_as_html()`` embeds formulas as MathML and renders real ``<table>``
elements; figures are inlined via ``image_mode=ImageRefMode.EMBEDDED``.
"""

from pathlib import Path

from docling_core.types.doc import ImageRefMode


def write_html(doc, out_dir: Path) -> Path:
    """Write ``doc`` as ``{out_dir}/document.html`` and return the path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "document.html"
    doc.save_as_html(path, image_mode=ImageRefMode.EMBEDDED)
    return path
