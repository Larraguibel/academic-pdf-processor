"""Convert a single PDF and run every serializer over the resulting document.

:meth:`DoclingProcessor.process` never raises to the caller — one bad PDF must
not abort a batch — and returns a :class:`ProcessingResult`.
"""

from pathlib import Path

from apdf.job import ProcessingResult
from apdf.serializers.json_serializer import write_json
from apdf.serializers.html_serializer import write_html
from apdf.serializers.markdown_serializer import write_markdown
from apdf.serializers.elements import write_elements


class DoclingProcessor:
    def __init__(self, converter):
        # The single shared DocumentConverter (#5). Built once, reused, not thread-safe.
        self._converter = converter

    def process(self, pdf_path: Path, out_dir: Path) -> ProcessingResult:
        """Convert one PDF into ``out_dir`` and run all serializers.

        Catches **all** exceptions and reports them via ``ProcessingResult`` so a
        single failure never propagates.
        """
        name = pdf_path.stem
        try:
            result = self._converter.convert(pdf_path)
            doc = result.document

            outputs: list[Path] = []
            outputs.append(write_json(doc, out_dir))
            outputs.append(write_html(doc, out_dir))
            outputs.append(write_markdown(doc, out_dir))
            outputs.extend(write_elements(doc, out_dir))

            return ProcessingResult(ok=True, name=name, outputs=tuple(outputs))
        except Exception as exc:  # noqa: BLE001 — never raise to the caller
            return ProcessingResult(ok=False, name=name, error=str(exc))
