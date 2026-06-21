"""Convert a single PDF and run every serializer over the resulting document.

:meth:`DoclingProcessor.process` never raises to the caller — one bad PDF must
not abort a batch — and returns a :class:`ProcessingResult`.
"""

from pathlib import Path

from apdf.detect import is_scanned_pdf
from apdf.job import ProcessingResult
from apdf.serializers.html_serializer import write_html
from apdf.serializers.markdown_serializer import write_markdown
from apdf.serializers.elements import write_elements


class DoclingProcessor:
    def __init__(self, pool, detect=is_scanned_pdf):
        # Pool of converters keyed by OCR setting (#5). Built lazily, reused,
        # not thread-safe. ``detect`` decides per PDF whether OCR is needed.
        self._pool = pool
        self._detect = detect

    def process(self, pdf_path: Path, out_dir: Path) -> ProcessingResult:
        """Convert one PDF into ``out_dir`` and run all serializers.

        Auto-detects scanned PDFs and routes them to the OCR-enabled converter;
        born-digital PDFs use the fast OCR-off converter. Catches **all**
        exceptions and reports them via ``ProcessingResult`` so a single failure
        never propagates.
        """
        name = pdf_path.stem
        do_ocr = self._detect(pdf_path)  # never raises; defaults to False on failure
        converter = self._pool.get(do_ocr=do_ocr)
        try:
            result = converter.convert(pdf_path)
            doc = result.document

            outputs: list[Path] = []
            outputs.append(write_html(doc, out_dir))
            outputs.append(write_markdown(doc, out_dir))
            outputs.extend(write_elements(doc, out_dir))

            return ProcessingResult(ok=True, name=name, outputs=tuple(outputs), ocr=do_ocr)
        except Exception as exc:  # noqa: BLE001 — never raise to the caller
            return ProcessingResult(ok=False, name=name, error=str(exc), ocr=do_ocr)
