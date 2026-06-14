"""Build the single, shared Docling ``DocumentConverter`` for the batch.

The converter loads models and is **not** thread-safe: build it once via
:func:`build_converter` and reuse it for every PDF on one worker thread.
"""

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import (
    AcceleratorDevice,
    AcceleratorOptions,
    PdfPipelineOptions,
)
from docling.datamodel.base_models import InputFormat

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
