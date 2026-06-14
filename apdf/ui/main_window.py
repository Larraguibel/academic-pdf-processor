"""Tkinter main window — file/output pickers, log, progress bar.

Stdlib Tkinter for the UI. The ``Run`` button starts ``BatchRunner.run`` on a
single background daemon thread (the converter is not thread-safe), and the UI
thread polls ``reporter.poll()`` via ``root.after(100, …)`` — so the window
never freezes while a batch runs. The heavy Docling imports are deferred into
the worker thread so the window opens instantly.
"""

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from apdf.config import load_config, save_config
from apdf.job import ProcessingJob
from apdf.progress import EventType, ProgressEvent, ProgressReporter


class MainWindow:
    def __init__(self, root: tk.Tk, reporter: ProgressReporter):
        self.root = root
        self.reporter = reporter
        self.root.title("Academic PDF Processor")

        self._config = load_config()
        self._pdf_paths: list[Path] = []
        self._output_dir: str = self._config.get("last_output_dir", "")

        # Worker state: the single shared converter is built lazily on first Run.
        self._converter = None
        self._batch_done = True
        # Run handler — wired to the worker thread; still overridable for tests.
        self.on_run = self.start_run

        self.overwrite_var = tk.BooleanVar(value=False)
        self._build_widgets()

    # ------------------------------------------------------------------ layout
    def _build_widgets(self) -> None:
        root = self.root
        root.columnconfigure(0, weight=1)
        root.rowconfigure(4, weight=1)

        controls = ttk.Frame(root, padding=8)
        controls.grid(row=0, column=0, sticky="ew")
        ttk.Button(controls, text="Add PDFs…", command=self._add_pdfs).grid(row=0, column=0, padx=4)
        ttk.Button(controls, text="Output folder…", command=self._pick_output).grid(row=0, column=1, padx=4)
        ttk.Checkbutton(controls, text="Overwrite existing", variable=self.overwrite_var).grid(row=0, column=2, padx=4)
        self.run_button = ttk.Button(controls, text="Run", command=self._run_clicked)
        self.run_button.grid(row=0, column=3, padx=4)

        # Selected PDFs
        ttk.Label(root, text="Selected PDFs:").grid(row=1, column=0, sticky="w", padx=8)
        self.listbox = tk.Listbox(root, height=6)
        self.listbox.grid(row=2, column=0, sticky="ew", padx=8)

        # Output folder display
        self.output_label = ttk.Label(root, text=self._output_label_text())
        self.output_label.grid(row=3, column=0, sticky="w", padx=8, pady=(4, 0))

        # Log + progress
        self.log = tk.Text(root, height=10, state="disabled", wrap="word")
        self.log.grid(row=4, column=0, sticky="nsew", padx=8, pady=4)
        self.progress = ttk.Progressbar(root, mode="determinate")
        self.progress.grid(row=5, column=0, sticky="ew", padx=8, pady=(0, 8))

    # ----------------------------------------------------------------- actions
    def _add_pdfs(self) -> None:
        initial = self._config.get("last_input_dir", "") or None
        paths = filedialog.askopenfilenames(
            title="Select PDF files",
            filetypes=[("PDF files", "*.pdf")],
            initialdir=initial,
        )
        if not paths:
            return
        self._pdf_paths = [Path(p) for p in paths]
        self.listbox.delete(0, tk.END)
        for p in self._pdf_paths:
            self.listbox.insert(tk.END, str(p))
        # remember the folder the PDFs came from
        self._config["last_input_dir"] = str(self._pdf_paths[0].parent)
        save_config(self._config)

    def _pick_output(self) -> None:
        initial = self._output_dir or None
        chosen = filedialog.askdirectory(title="Select output folder", initialdir=initial)
        if not chosen:
            return
        self._output_dir = chosen
        self.output_label.config(text=self._output_label_text())
        self._config["last_output_dir"] = chosen
        save_config(self._config)

    def _run_clicked(self) -> None:
        if self.on_run is not None:
            self.on_run()

    # ------------------------------------------------------------- run / worker
    def start_run(self) -> None:
        """Start the batch on a background thread and begin polling for events."""
        job = self.build_job()
        if not job.pdf_paths:
            self.append_log("Add at least one PDF before running.")
            return
        if not self._output_dir:
            self.append_log("Choose an output folder before running.")
            return

        self.run_button.config(state="disabled")
        self._batch_done = False
        self.set_progress(0, len(job.pdf_paths))

        thread = threading.Thread(target=self._run_batch, args=(job,), daemon=True)
        thread.start()
        self.root.after(100, self._drain_events)

    def _run_batch(self, job: ProcessingJob) -> None:
        """Worker-thread body. Builds the shared converter once, runs the batch.

        Runs OFF the UI thread; it must only talk to the UI via ``reporter.emit``.
        Heavy Docling imports happen here so the window opens without waiting.
        """
        try:
            from apdf.batch import BatchRunner
            from apdf.converter import build_converter
            from apdf.processor import DoclingProcessor

            if self._converter is None:
                self._converter = build_converter()
            processor = DoclingProcessor(self._converter)
            BatchRunner(processor, self.reporter).run(job)
        except Exception as exc:  # noqa: BLE001 — surface, then let the batch end
            self.reporter.emit(
                ProgressEvent(EventType.BATCH_COMPLETE, message=f"error: {exc}")
            )

    def _drain_events(self) -> None:
        """UI-thread poll loop: drain events, update widgets, reschedule."""
        for ev in self.reporter.poll():
            if ev.type == EventType.FILE_STARTED:
                self.append_log(f"[{ev.index}/{ev.total}] Processing {ev.name}…")
                self.set_progress(ev.index - 1, ev.total)
            elif ev.type == EventType.FILE_DONE:
                self.append_log(f"  ✓ {ev.name}")
                self.set_progress(ev.index, ev.total)
            elif ev.type == EventType.FILE_FAILED:
                self.append_log(f"  ✗ {ev.name}: {ev.message}")
                self.set_progress(ev.index, ev.total)
            elif ev.type == EventType.FILE_SKIPPED:
                self.append_log(f"  ⊘ {ev.name} (skipped — output exists)")
                self.set_progress(ev.index, ev.total)
            elif ev.type == EventType.BATCH_COMPLETE:
                self.append_log(f"Batch complete: {ev.message}")
                self._batch_done = True
                self.run_button.config(state="normal")

        if not self._batch_done:
            self.root.after(100, self._drain_events)

    # ------------------------------------------------------------------- hooks
    def build_job(self) -> ProcessingJob:
        """Build a ``ProcessingJob`` from the current selections."""
        return ProcessingJob(
            pdf_paths=tuple(self._pdf_paths),
            output_dir=Path(self._output_dir),
            overwrite=self.overwrite_var.get(),
        )

    def append_log(self, text: str) -> None:
        self.log.config(state="normal")
        self.log.insert(tk.END, text + "\n")
        self.log.see(tk.END)
        self.log.config(state="disabled")

    def set_progress(self, current: int, total: int) -> None:
        self.progress.config(maximum=max(total, 1), value=current)

    # ------------------------------------------------------------------ helpers
    def _output_label_text(self) -> str:
        return f"Output: {self._output_dir or '(none selected)'}"
