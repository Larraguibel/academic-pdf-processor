"""Immutable value objects describing a batch job and a per-PDF result."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProcessingJob:
    """A batch of PDFs to convert into a single output directory."""

    pdf_paths: tuple[Path, ...]   # tuple keeps the frozen dataclass hashable
    output_dir: Path
    overwrite: bool = False


@dataclass(frozen=True)
class ProcessingResult:
    """The outcome of processing a single PDF."""

    ok: bool
    name: str                       # input stem, e.g. "smith2023"
    outputs: tuple[Path, ...] = ()  # files/dirs written for this PDF
    error: str | None = None        # error message when ok is False
    ocr: bool = False               # True if OCR was auto-enabled (scanned PDF)
