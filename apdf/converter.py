"""Build the single, shared Docling ``DocumentConverter`` for the batch.

The converter loads models and is **not** thread-safe: build it once via
:func:`build_converter` and reuse it for every PDF on one worker thread.

Also provides startup helpers: :func:`detect_device` logs the accelerator,
:func:`models_present` checks the local model cache, and :func:`prefetch_models`
performs the first-run download.
"""

import logging
from pathlib import Path

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import (
    AcceleratorDevice,
    AcceleratorOptions,
    PdfPipelineOptions,
)
from docling.datamodel.base_models import InputFormat

logger = logging.getLogger(__name__)

# Docling caches downloaded model weights here (layout, TableFormer, formula, ...).
MODELS_CACHE_DIR = Path.home() / ".cache" / "docling" / "models"

# 1.0 == 72 DPI; 2.0 ~= 144 DPI. Required (with generate_picture_images) to
# retain figure crops — without it Docling silently drops images.
IMAGE_RESOLUTION_SCALE = 2.0


def build_converter(
    do_formula_enrichment: bool = True,
    do_ocr: bool = False,
    images_scale: float = IMAGE_RESOLUTION_SCALE,
) -> DocumentConverter:
    """Construct a configured ``DocumentConverter`` for academic PDFs.

    Built once and reused for the whole batch (the converter is not thread-safe).
    Formula enrichment restricts the accelerator to CPU/CUDA (MPS excluded), so
    on Apple Silicon equation extraction runs on CPU while layout/TableFormer can
    still use MPS.
    """
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_formula_enrichment = do_formula_enrichment

    # Figure retention — both required, or images are silently dropped.
    pipeline_options.images_scale = images_scale
    pipeline_options.generate_picture_images = True

    # OCR off by default (born-digital arXiv PDFs); TableFormer is on by default.
    pipeline_options.do_ocr = do_ocr

    pipeline_options.accelerator_options = AcceleratorOptions(
        device=AcceleratorDevice.AUTO,   # AUTO | CPU | CUDA | MPS | XPU
        num_threads=8,
    )

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )
    return converter


def detect_device() -> str:
    """Return a short label for the accelerator AUTO will select, and log it.

    Mirrors ``AcceleratorDevice.AUTO``: MPS on Apple Silicon, CUDA on NVIDIA,
    else CPU. Notes that formula enrichment always runs on CPU (Docling excludes
    MPS for that stage), which is why equation extraction is slow on Mac.
    """
    device = "cpu"
    try:
        import torch

        if torch.cuda.is_available():
            device = "cuda"
        elif torch.backends.mps.is_available():
            device = "mps"
    except Exception:  # torch missing or backend probe failed -> assume CPU
        device = "cpu"

    note = ""
    if device == "mps":
        note = " (note: formula enrichment still runs on CPU — MPS is excluded for that stage)"
    logger.info("Compute device: %s%s", device, note)
    return device


def models_present() -> bool:
    """True if Docling model weights already exist in the local cache."""
    return MODELS_CACHE_DIR.exists() and any(MODELS_CACHE_DIR.iterdir())


def prefetch_models() -> str | None:
    """Download Docling model weights up front (the first-run pull).

    Returns a user-facing warning string when a download is needed (so the UI can
    display it), or ``None`` if the models are already cached.
    """
    if models_present():
        logger.info("Docling models already present at %s", MODELS_CACHE_DIR)
        return None

    warning = (
        "First run: downloading Docling model weights (~few hundred MB) to "
        f"{MODELS_CACHE_DIR}. This happens once and may take several minutes."
    )
    logger.warning(warning)

    from docling.utils.model_downloader import download_models

    download_models()  # pulls layout, TableFormer, picture classifier, formula model, ...
    return warning
