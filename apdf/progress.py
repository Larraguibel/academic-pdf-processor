"""Thread-safe bridge between the background BatchRunner and the Tkinter UI.

The worker thread calls :meth:`ProgressReporter.emit`; the UI thread drains
pending events with the non-blocking :meth:`ProgressReporter.poll`.
"""

import queue
from dataclasses import dataclass
from enum import Enum


class EventType(Enum):
    FILE_STARTED = "file_started"
    FILE_DONE = "file_done"
    FILE_FAILED = "file_failed"
    FILE_SKIPPED = "file_skipped"
    BATCH_COMPLETE = "batch_complete"


@dataclass
class ProgressEvent:
    type: EventType
    name: str = ""          # the PDF being processed (empty for BATCH_COMPLETE)
    index: int = 0          # 1-based file index
    total: int = 0
    message: str = ""       # error text for FILE_FAILED, summary for BATCH_COMPLETE


class ProgressReporter:
    def __init__(self) -> None:
        self._q: "queue.Queue[ProgressEvent]" = queue.Queue()

    def emit(self, event: ProgressEvent) -> None:
        """Enqueue an event (called from the worker thread)."""
        self._q.put(event)

    def poll(self) -> list[ProgressEvent]:
        """Drain and return all currently-queued events without blocking.

        Called from the UI thread. Returns ``[]`` when nothing is queued.
        """
        events: list[ProgressEvent] = []
        while True:
            try:
                events.append(self._q.get_nowait())
            except queue.Empty:
                break
        return events
