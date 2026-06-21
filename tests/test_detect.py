"""Fast tests for scanned-PDF detection and converter-pool laziness.

No model weights required — detection reads only the text layer (pypdfium2), and
the pool is exercised with a fake builder.
"""

from pathlib import Path

from apdf.converter import ConverterPool
from apdf.detect import is_scanned_pdf
from apdf.processor import DoclingProcessor

FIXTURE = Path(__file__).parent / "fixtures" / "sample.pdf"


def test_born_digital_fixture_is_not_scanned():
    # The bundled fixture has a real text layer -> OCR should stay off.
    assert is_scanned_pdf(FIXTURE) is False


def test_detection_failure_defaults_to_not_scanned(tmp_path):
    # An unreadable/garbage file must not raise and must not force OCR on.
    bogus = tmp_path / "not_a.pdf"
    bogus.write_bytes(b"%PDF-1.4 not really a pdf")
    assert is_scanned_pdf(bogus) is False


class _FakeConverter:
    def __init__(self, do_ocr):
        self.do_ocr = do_ocr


def test_pool_builds_lazily_and_caches():
    built = []

    def fake_build(do_ocr=False):
        built.append(do_ocr)
        return _FakeConverter(do_ocr)

    pool = ConverterPool(build=fake_build)
    assert built == []                       # nothing built until requested

    a = pool.get(do_ocr=False)
    b = pool.get(do_ocr=False)
    assert a is b                            # cached, built once
    assert built == [False]                  # OCR-on never built

    c = pool.get(do_ocr=True)
    assert c is not a
    assert built == [False, True]


def test_processor_routes_scanned_pdf_to_ocr_converter():
    requested = []

    class StubConverter:
        def convert(self, pdf_path):
            raise RuntimeError("stop before real conversion")

    class FakePool:
        def get(self, do_ocr=False):
            requested.append(do_ocr)
            return StubConverter()

    # Force the "scanned" verdict without needing a scanned fixture.
    processor = DoclingProcessor(FakePool(), detect=lambda _p: True)
    result = processor.process(FIXTURE, Path("/tmp/unused"))

    assert requested == [True]               # OCR converter was selected
    assert result.ok is False                # conversion stub raised -> caught
    assert result.ocr is True                # decision recorded on the result
