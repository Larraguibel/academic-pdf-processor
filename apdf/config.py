"""Persist last-used input/output folders between sessions.

Stored in ``~/.academic-pdf-processor/config.json``. All operations degrade to
defaults rather than raising, so a missing or corrupt file never crashes the app.
"""

import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".academic-pdf-processor"
CONFIG_PATH = CONFIG_DIR / "config.json"

_DEFAULTS: dict = {
    "last_input_dir": "",
    "last_output_dir": "",
}


def load_config() -> dict:
    """Return saved config, or sensible defaults if the file is missing/corrupt."""
    config = dict(_DEFAULTS)
    try:
        data = json.loads(CONFIG_PATH.read_text())
        if isinstance(data, dict):
            config.update(data)
    except (OSError, ValueError):
        # missing file or invalid JSON -> fall back to defaults
        pass
    return config


def save_config(data: dict) -> None:
    """Create CONFIG_DIR if needed and atomically write config.json."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(CONFIG_PATH)
