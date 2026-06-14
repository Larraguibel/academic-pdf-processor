"""Write a human-readable ``document.md`` fallback."""

from pathlib import Path


def write_markdown(doc, out_dir: Path) -> Path:
    """Write ``doc`` as ``{out_dir}/document.md`` and return the path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "document.md"
    doc.save_as_markdown(path)
    return path
