"""Heuristically decide whether a PDF is scanned (image-only) and so needs OCR.

Academic batches are overwhelmingly born-digital (arXiv, LaTeX/Word exports),
where the text is embedded as a real text layer and OCR only adds a slow,
error-prone pass. The rare scanned paper has no text layer at all and is
useless without OCR. This module tells the two apart cheaply — by counting the
embedded text layer, not by rendering — so the processor can switch OCR on only
when it is actually needed.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# A born-digital page exposes its text layer as hundreds-to-thousands of
# characters; a scanned page is an image with ~0 extractable characters. A page
# below this floor is treated as "no usable text layer".
MIN_CHARS_PER_PAGE = 40

# Cap the probe: counting chars is cheap, but a 400-page scan needn't be read in
# full to be classified. The first pages are representative enough.
MAX_PAGES_SAMPLED = 10

# Fraction of sampled pages that must lack a text layer for the whole document to
# count as scanned. Using a fraction (rather than a mean) keeps one text-heavy
# cover page from masking a scan behind it.
SCANNED_PAGE_FRACTION = 0.5


def is_scanned_pdf(
    pdf_path: Path,
    min_chars_per_page: int = MIN_CHARS_PER_PAGE,
    max_pages: int = MAX_PAGES_SAMPLED,
    scanned_fraction: float = SCANNED_PAGE_FRACTION,
) -> bool:
    """Return True if ``pdf_path`` looks scanned (image-only) and needs OCR.

    Counts the embedded text layer on a sample of pages via ``pypdfium2`` (a
    Docling dependency, so no extra install and no page rendering). The document
    is "scanned" when at least ``scanned_fraction`` of the sampled pages hold
    fewer than ``min_chars_per_page`` characters.

    Detection never raises: any failure (unreadable/encrypted PDF, missing
    backend) is logged and treated as *not* scanned, so we fall back to the fast
    OCR-off path rather than forcing a slow OCR pass on a file we couldn't probe.
    """
    try:
        import pypdfium2 as pdfium
    except Exception:  # pragma: no cover - pypdfium2 ships with Docling
        logger.warning("pypdfium2 unavailable; assuming %s is born-digital", pdf_path)
        return False

    pdf = None
    try:
        pdf = pdfium.PdfDocument(str(pdf_path))
        n_pages = len(pdf)
        if n_pages == 0:
            return False

        sample = min(n_pages, max_pages)
        low_text_pages = 0
        total_chars = 0
        for i in range(sample):
            page = pdf[i]
            textpage = page.get_textpage()
            chars = max(textpage.count_chars(), 0)  # count_chars can return -1 on error
            textpage.close()
            page.close()
            total_chars += chars
            if chars < min_chars_per_page:
                low_text_pages += 1

        scanned = (low_text_pages / sample) >= scanned_fraction
        logger.info(
            "%s: %d/%d sampled pages lack a text layer (%.0f chars/page avg) -> %s",
            getattr(pdf_path, "name", pdf_path),
            low_text_pages,
            sample,
            total_chars / sample,
            "scanned (OCR on)" if scanned else "born-digital (OCR off)",
        )
        return scanned
    except Exception as exc:  # noqa: BLE001 - never block a batch on detection
        logger.warning(
            "scanned-PDF detection failed for %s (%s); assuming born-digital",
            pdf_path,
            exc,
        )
        return False
    finally:
        if pdf is not None:
            try:
                pdf.close()
            except Exception:  # pragma: no cover - best-effort cleanup
                pass
