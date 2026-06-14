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


def write_table_item(item, doc, out_dir, index) -> Path:
    """Write a ``TableItem`` as a standalone ``table_{index:03d}.html`` snippet.

    The ``doc=`` argument is mandatory in Docling v2. Returns the written ``Path``.
    """
    html: str = item.export_to_html(doc=doc, add_caption=True)
    path = out_dir / f"table_{index:03d}.html"
    path.write_text(html)
    return path


def write_figure_item(item, doc, out_dir, index) -> list[Path]:
    """Write a ``PictureItem``'s cropped image and caption.

    Saves ``figure_{index:03d}.png`` (when a retained image exists) and, if a
    caption is present, ``figure_{index:03d}_caption.txt``. Returns the list of
    written ``Path``s. ``get_image(doc)`` may be ``None`` (figures are only
    retained when the converter was built with ``generate_picture_images=True``
    + ``images_scale``); that case is skipped gracefully.
    """
    written: list[Path] = []

    img = item.get_image(doc)                 # -> Optional[PIL.Image]
    if img is not None:
        png_path = out_dir / f"figure_{index:03d}.png"
        with open(png_path, "wb") as fp:
            img.save(fp, "PNG")
        written.append(png_path)

    caption = item.caption_text(doc)          # -> str (concatenated captions)
    if caption:
        cap_path = out_dir / f"figure_{index:03d}_caption.txt"
        cap_path.write_text(caption)
        written.append(cap_path)

    return written
