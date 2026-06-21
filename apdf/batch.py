"""Drive a batch: iterate a ProcessingJob, run the processor per file, emit
progress events, handle overwrite/skip, and write ``batch_summary.json``.

Runs on a single worker thread (the converter is not thread-safe). All UI
communication goes through the injected :class:`ProgressReporter`.
"""

import json
import shutil
import time
from datetime import datetime, timezone

from apdf.job import ProcessingJob, ProcessingResult
from apdf.processor import DoclingProcessor
from apdf.progress import ProgressReporter, ProgressEvent, EventType


class BatchRunner:
    def __init__(self, processor: DoclingProcessor, reporter: ProgressReporter):
        self._processor = processor
        self._reporter = reporter

    def run(self, job: ProcessingJob) -> list[ProcessingResult]:
        """Process every PDF in ``job``; emit events; write ``batch_summary.json``."""
        start = time.perf_counter()
        results: list[ProcessingResult] = []
        succeeded = failed = skipped = 0
        total = len(job.pdf_paths)

        for index, pdf in enumerate(job.pdf_paths, start=1):
            name = pdf.stem
            self._reporter.emit(
                ProgressEvent(EventType.FILE_STARTED, name=name, index=index, total=total)
            )

            out_dir = job.output_dir / name
            if out_dir.exists():
                if not job.overwrite:
                    skipped += 1
                    results.append(
                        ProcessingResult(ok=False, name=name, error="skipped (exists)")
                    )
                    self._reporter.emit(
                        ProgressEvent(
                            EventType.FILE_SKIPPED, name=name, index=index, total=total
                        )
                    )
                    continue
                # overwrite=True -> delete & recreate
                shutil.rmtree(out_dir)

            out_dir.mkdir(parents=True, exist_ok=True)
            result = self._processor.process(pdf, out_dir)
            results.append(result)

            if result.ok:
                succeeded += 1
                self._reporter.emit(
                    ProgressEvent(
                        EventType.FILE_DONE,
                        name=name,
                        index=index,
                        total=total,
                        message="ocr" if result.ocr else "",
                    )
                )
            else:
                failed += 1
                self._reporter.emit(
                    ProgressEvent(
                        EventType.FILE_FAILED,
                        name=name,
                        index=index,
                        total=total,
                        message=result.error or "",
                    )
                )

        duration = time.perf_counter() - start
        self._write_summary(job, results, total, succeeded, failed, skipped, duration)

        self._reporter.emit(
            ProgressEvent(
                EventType.BATCH_COMPLETE,
                total=total,
                message=f"{succeeded} ok, {failed} failed, {skipped} skipped",
            )
        )
        return results

    def _write_summary(self, job, results, total, succeeded, failed, skipped, duration):
        job.output_dir.mkdir(parents=True, exist_ok=True)
        summary = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total": total,
            "succeeded": succeeded,
            "failed": failed,
            "skipped": skipped,
            "duration_seconds": round(duration, 3),
            "per_file_results": [
                {
                    "name": r.name,
                    "ok": r.ok,
                    "ocr": r.ocr,
                    "error": r.error,
                    "outputs": [str(p) for p in r.outputs],
                }
                for r in results
            ],
        }
        (job.output_dir / "batch_summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False)
        )
