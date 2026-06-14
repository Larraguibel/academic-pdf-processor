"""Per-element serializers for a DoclingDocument.

Each helper writes one file for one item; the orchestrator (#13) owns the
``elements/`` directory and the per-type running indices.
"""

from pathlib import Path

from docling_core.types.doc import TextItem
from docling_core.types.doc.labels import DocItemLabel


def write_text_item(item, doc, out_dir, index) -> Path | None:
    """Write a single ``TextItem``.

    A FORMULA item is written to ``equation_{index:03d}.tex`` (LaTeX from
    ``item.text``); any other text item is written to ``text_{index:03d}.txt``.
    Returns the written ``Path``, or ``None`` if the item has no usable text.
    """
    text = getattr(item, "text", None)
    if not text:
        return None

    if item.label == DocItemLabel.FORMULA:
        path = out_dir / f"equation_{index:03d}.tex"
    else:
        path = out_dir / f"text_{index:03d}.txt"
    path.write_text(text)
    return path
