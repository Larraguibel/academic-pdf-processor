# Plan — Academic PDF Processor (Docling-based desktop app)

## Context

The repo currently holds only `PRD-academic-pdf-processor.md` and a `test_pdfs/`
folder (four modern ML papers: I-JEPA, ProLIP, GRAFT, Improved Probabilistic
Image-Text Representations — all rich in equations, tables, and figures). The
goal of **this** session is *setup and planning only* — no app code is written.
We will:

1. Initialize git, create a **public** GitHub repo `academic-pdf-processor`, and push.
2. Author a detailed `PLAN.md` committed to the repo (the "full plan document").
3. Open GitHub **milestones + one tracking issue per module** so the build can be
   driven issue-by-issue in a later session.

The build itself (the Tkinter app + Docling pipeline) is deferred to a future session.

Decisions locked with the user: repo `academic-pdf-processor` **public**; UI =
**Tkinter** (stdlib); produce **full PLAN.md + GitHub issues**.

### Docling API — verified 2026-06-14 (drives the build)
The PRD's Docling assumptions all check out against Docling `2.102.1`. Key facts
that shape the design (full report: `buzzing-singing-reef-agent-a8498b82d96bf78fa.md`):
- **Python 3.13 is supported** (`>=3.10,<4.0`). Dev box 3.13.2 is fine.
- Options are **per-format**: `format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=PdfPipelineOptions(...))}` (the PRD's global `PipelineOptions` is legacy v1).
- Formulas → `TextItem` label `FORMULA`, LaTeX in `.text`. **⚠ `do_formula_enrichment=True` forces CPU/CUDA and disables MPS** → on this Mac, equation extraction runs on CPU and is the slowest stage.
- Figures are **opt-in**: must set `generate_picture_images=True` + `images_scale≈2.0`, else images are silently dropped. Save via `picture.get_image(doc).save(fp,"PNG")`; caption via `picture.caption_text(doc)`.
- Tables: TableFormer on by default; `table.export_to_html(doc=...)` (note the `doc=` arg).
- Exports: `export_to_dict()`, `save_as_html()` (**embeds MathML**), `save_as_markdown()`.
- OCR via `do_ocr` (EasyOCR default); keep **off** for born-digital arXiv PDFs (faster), on as fallback.
- **DocumentConverter is not thread-safe** → build it once, run all conversions on a single dedicated worker thread/queue; keep UI thread free.
- First run downloads model weights (~few hundred MB) to `~/.cache/docling/models`; prefetch with `docling.utils.model_downloader.download_models()`.

---

## Execution steps (next session, after approval)

### Phase A — Repo bootstrap
1. `git init` in the project root; create `.gitignore` (Python, `.venv/`, `__pycache__/`, `*.egg-info`, model cache, `outputs/`, OS files).
2. Add `LICENSE` (MIT — matches Docling) and a `README.md` (what/why, install, run, screenshot placeholder).
3. **Keep `test_pdfs/` out of git** (≈14 MB of copyrighted papers) — add to `.gitignore`, note in README that users supply their own. (Confirm with user if they'd rather commit them.)
4. `gh repo create academic-pdf-processor --public --source=. --remote=origin` then push `main`.

### Phase B — Author `PLAN.md` (the full plan document, committed)
A standalone `PLAN.md` at repo root containing: architecture diagram (module
graph), the verified Docling integration notes above, module-by-module build
order mapped to issues, the testing strategy, known caveats (CPU formulas, image
opt-in, model download), and a definition-of-done checklist per milestone.

### Phase C — Project scaffold (files created, not yet implemented)
Proposed layout (package `apdf`):
```
academic-pdf-processor/
  app.py                      # entry point: python app.py
  apdf/
    __init__.py
    config.py                 # load/save ~/.academic-pdf-processor/config.json (last in/out folders)
    job.py                    # ProcessingJob dataclass (frozen): pdf_paths, output_dir, overwrite
    converter.py              # build_converter(): single DocumentConverter w/ PdfPipelineOptions
    processor.py              # DoclingProcessor: 1 PDF -> ProcessingResult; catches all exceptions
    serializers/
      __init__.py
      json_serializer.py      # docling.json via export_to_dict()
      html_serializer.py      # document.html via save_as_html() (MathML)
      markdown_serializer.py  # document.md via save_as_markdown()
      elements.py             # ElementSerializer: text_/table_/equation_/figure_ files
    batch.py                  # BatchRunner: iterate job, emit events, write batch_summary.json
    progress.py               # ProgressReporter: thread-safe queue + event types
    ui/
      __init__.py
      main_window.py          # Tkinter: file multiselect, output picker, run btn, log, progressbar
  tests/
    test_elements.py
    test_batch.py
    test_progress.py
    test_processor_integration.py   # marked slow; real small PDF fixture
    fixtures/                  # one tiny (<=5pp) PDF w/ table+equation+figure
  requirements.txt            # docling, pillow (Pandas pulled by docling); pytest as dev
  pyproject.toml              # metadata + optional console_script
  PLAN.md
  README.md
  LICENSE
  .gitignore
```

### Phase D — Haiku-executable GitHub issues (opus-orchestrated)
Per user direction, the build is decomposed into **18 small, independent, AFK
issues**, each sized for a **haiku** worker dispatched by an **opus** orchestrator,
maximizing parallelism. Granularity is intentionally atomic (≈one module/unit per
issue) rather than thick vertical slices.

**Issue-body template (enriched for weak workers):** What to build (exact module
path + function signature) · a **verified Docling 2.102 snippet** inlined where the
API is involved (prevents haikus hallucinating a stale API) · checkbox acceptance
criteria · explicit *Blocked by* · *Notes for the agent* guardrail.

**Labels:** `afk`, `wave:0|1|2|3`, `area:core|serializer|ui|test|infra`.

**Pinned orchestration issue `#0`** ("Orchestration guide"): the wave plan + how
opus should fan haikus out per wave; single source of truth for the dispatcher.

**The 18 issues + dependency waves:**
- **W0:** #1 Repo scaffold & packaging (blocks all).
- **W1 (10 parallel, ←#1):** #2 `ProcessingJob`+`ProcessingResult` · #3 `config.py` · #4 `build_converter()` · #5 `json_serializer` · #6 `html_serializer` · #7 `markdown_serializer` · #8 `elements/text_writer` (FORMULA→.tex / text→.txt) · #9 `elements/table_writer` · #10 `elements/figure_writer` · #11 `ProgressReporter`+events.
- **W2 (←W1):** #12 `elements/__init__` orchestrator (←#8,9,10) · #13 `DoclingProcessor` (←#2,4,5,6,7,12) · #14 `BatchRunner`+`batch_summary.json` (←#2,13,11) · #17 startup device-log + model prefetch + first-run warning (←#4).
- **W3:** #15 Tkinter `main_window` (←#3,11) · #16 worker-thread wiring + `after(100)` polling (←#14,15) · #18 integration test + tiny fixture PDF (←#13).

Each issue maps to PRD user stories (e.g. #8→US3, #9→US4, #10→US5, #11/#16→US7,
#13→US8, #14→US9,13, #3→US12, #17→US14).

---

## Build-time design notes (captured now, for the issues)

- **`build_converter(opts)`** wires `PdfPipelineOptions`: `do_formula_enrichment` (toggle, default on), `generate_picture_images=True` + `images_scale=2.0`, `do_table_structure=True`, `do_ocr=False` default, `accelerator_options=AcceleratorOptions(device=AUTO)`. Built **once**, reused for the whole batch.
- **`DoclingProcessor.process(pdf, out_dir)`** never raises; returns `ProcessingResult(ok, name, outputs, error)`. Runs all serializers in sequence on `result.document`.
- **`ElementSerializer`** iterates `doc.iterate_items()` handling `TextItem`(FORMULA→`equation_{n}.tex`; section/para→`text_{n}.txt`), `TableItem`(→`table_{n}.html` via `export_to_html(doc=...)`), `PictureItem`(→`figure_{n}.png` via `get_image(doc)` + `figure_{n}_caption.txt` via `caption_text(doc)`).
- **Threading:** `BatchRunner` runs on one worker thread; pushes `FILE_STARTED/FILE_DONE/FILE_FAILED/FILE_SKIPPED/BATCH_COMPLETE` onto `ProgressReporter`'s `queue.Queue`; Tkinter polls via `root.after(100, ...)`.
- **Overwrite:** `overwrite=False` + existing `{name}/` → `FILE_SKIPPED`; `True` → delete & recreate.
- **Startup:** detect/log device; on first run, offer to prefetch Docling models before enabling Run.

---

## Testing strategy
- Unit (fast, mock `DocumentConverter`/`DoclingDocument`): `ElementSerializer` file outputs; `BatchRunner` with 2 valid + 1 missing PDF → 2 ok / 1 failed + correct `batch_summary.json`; `ProgressReporter` event ordering for a 2-file batch.
- Integration (slow, `@pytest.mark.slow`): real small fixture PDF → `docling.json` is valid JSON with ≥1 table and ≥1 FORMULA node.
- Manual end-to-end (deferred build session): `pip install -r requirements.txt && python app.py`, select the four `test_pdfs/`, set output, run; confirm per-paper `docling.json/document.html/document.md/elements/` and `batch_summary.json`.

## Verification of *this* session's deliverable
After Phase A–D: `gh repo view academic-pdf-processor --web` shows the public repo; `PLAN.md`, `README.md`, `LICENSE`, scaffold, and `.gitignore` are on `main`; `gh issue list` shows issues #1–#17 grouped under milestones M1–M3; `git log` shows the bootstrap commit(s).

## Open items / assumptions
- `test_pdfs/` excluded from git by default (copyright + size). Will commit a tiny synthetic/permissive fixture under `tests/fixtures/` instead. Flag if you want the test papers committed anyway.
- Scaffold files are created as stubs/signatures only this session per "don't execute"; full implementation lands in the deferred build session, issue by issue.
