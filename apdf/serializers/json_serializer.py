"""Write the lossless DoclingDocument to ``docling.json``.

This is the canonical store from which any other format can be re-serialized
later without re-parsing the PDF.
"""

import json
from pathlib import Path


def write_json(doc, out_dir: Path) -> Path:
    """Write ``doc`` as ``{out_dir}/docling.json`` (lossless) and return the path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "docling.json"
    data = doc.export_to_dict()
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    return path
