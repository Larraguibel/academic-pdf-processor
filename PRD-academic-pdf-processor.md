# PRD — Academic PDF Processor (Docling-based)

> **Target agent:** Claude Code  
> **Language / stack:** Python 3.11+, Docling, Tkinter (or PySide6) for UI  
> **Execution model:** local desktop app, no cloud dependency  

---

## Problem Statement

Academic papers arrive as PDFs containing dense mixed content — multi-column text, numbered equations, complex tables with merged cells, and figures with captions spatially separated from their referencing text. Standard PDF-to-text tools flatten all of this into unstructured strings, destroying the semantic structure that makes the content useful for downstream LLM consumption, search, and retrieval-augmented generation (RAG).

There is no convenient tool that lets a researcher drop a batch of academic PDFs into a folder and receive a properly structured, element-typed output (LaTeX equations, HTML tables, extracted figures with captions, clean section text) without writing code or using a cloud API.

---

## Solution

A local desktop application that lets the user:

1. **Select multiple PDF files** from any folder via a graphical file picker.
2. **Set an output folder** where results will be written.
3. **Trigger a batch processing run** that converts each PDF through the Docling pipeline.
4. **Receive structured outputs** per paper: lossless JSON (canonical store), HTML with MathML equations and proper tables, extracted figure images with captions, and per-element flat files (LaTeX equations, HTML tables, plain-text sections).
5. **Monitor progress** via a simple in-app log / progress indicator.

The app runs entirely locally. No API keys required. No data leaves the machine.

---

## User Stories

1. As a researcher, I want to select multiple PDF files at once from a folder dialog, so that I can batch-process an entire paper collection without running a script.
2. As a researcher, I want to set a specific output folder before processing, so that the structured files land exactly where my project expects them.
3. As a researcher, I want equations extracted as LaTeX strings, so that LLMs and search systems can reason about mathematical content instead of seeing garbled OCR.
4. As a researcher, I want tables extracted as standalone HTML files, so that merged cells and hierarchical headers are preserved — not broken into Markdown pipe rows.
5. As a researcher, I want figures saved as PNG images alongside a plain-text caption file, so that I can pass both the image and the caption to a multimodal LLM.
6. As a researcher, I want a lossless JSON export (DoclingDocument format) for each paper, so that I can re-serialize to any other format later without re-parsing the PDF.
7. As a researcher, I want a progress bar and per-file status log visible while batch processing runs, so that I know the app is working and can see which files succeeded or failed.
8. As a researcher, I want failed files to be logged with their error messages and skipped gracefully, so that one corrupt PDF does not abort the entire batch.
9. As a researcher, I want the output folder to mirror the input file names (e.g., `smith2023.pdf` → `smith2023/`), so that outputs are easy to identify and associate with source files.
10. As a researcher, I want an HTML export per paper that embeds MathML-rendered equations and proper `<table>` elements, so that I have a human-readable, browser-viewable version alongside the machine-readable JSON.
11. As a researcher, I want to be able to re-run processing on a single file by selecting it again, with the option to overwrite or skip existing outputs, so that I can refresh a paper's output after changing settings.
12. As a researcher, I want the app to remember the last-used input and output folders between sessions, so that I do not have to re-navigate the same directories every time.
13. As a researcher, I want to see a summary report after a batch run (N succeeded, N failed, total time), so that I can confirm the run was complete.
14. As a researcher, I want scanned or image-only PDF pages to be handled via Docling's OCR fallback automatically, without any manual intervention, so that older scanned papers are processed correctly.
15. As a researcher, I want the app to be launchable as a simple command (`python app.py` or a packaged executable) without a complex installation process beyond `pip install`.

---

## Implementation Decisions

### Modules

#### 1. `UI Layer` — File selection and run control
- **Input:** User interactions (folder picker, file multi-select, output folder picker, run button).
- **Output:** A `ProcessingJob` value object containing: list of PDF paths, output base folder path, overwrite flag.
- **Framework:** Tkinter (stdlib, zero extra deps) preferred for simplicity; PySide6 acceptable if richer progress reporting is needed.
- **Persistence:** Store last-used paths in a local `config.json` (in the app's directory or `~/.academic-pdf-processor/`).
- The UI must remain responsive during processing. Processing must run in a background thread; progress updates are pushed to the UI via a thread-safe queue.

#### 2. `ProcessingJob` — Value object
- Fields: `pdf_paths: list[Path]`, `output_dir: Path`, `overwrite: bool`.
- Immutable once created. Passed from UI to the Processor.

#### 3. `DoclingProcessor` — Core conversion engine
- **Input:** A single `Path` pointing to a PDF file + an output subfolder `Path`.
- **Output:** A `ProcessingResult` (success/failure, output paths, error message if failed).
- Internally calls `docling.document_converter.DocumentConverter`.
- After conversion, calls all serializers (see below) in sequence.
- Catches all exceptions per file; never raises to the caller.

#### 4. `Serializers` — Output writers (one per format)

Each serializer receives the `DoclingDocument` object and the output subfolder:

| Serializer | Output | Notes |
|---|---|---|
| `JsonSerializer` | `{name}/docling.json` | Lossless. Uses `doc.export_to_dict()`. |
| `HtmlSerializer` | `{name}/document.html` | Full doc with MathML + `<table>`. Uses `doc.export_to_html()`. |
| `MarkdownSerializer` | `{name}/document.md` | Human-readable fallback. |
| `ElementSerializer` | `{name}/elements/` | Per-element flat files (see below). |

`ElementSerializer` sub-outputs:
- `text_{n}.txt` — paragraph text blocks, prefixed with section heading.
- `table_{n}.html` — each table as a standalone `<table>` HTML snippet.
- `equation_{n}.tex` — each display equation as a LaTeX string.
- `figure_{n}.png` — each extracted figure image.
- `figure_{n}_caption.txt` — VLM-generated or extracted caption text.

#### 5. `BatchRunner` — Orchestrator
- Accepts a `ProcessingJob`.
- Iterates over PDF paths, calls `DoclingProcessor` for each.
- Emits progress events (current file index, total count, status, elapsed time) via a callback or queue.
- Collects `ProcessingResult` objects.
- After completion, writes a `batch_summary.json` to the output root: `{timestamp, total, succeeded, failed, duration_seconds, per_file_results}`.

#### 6. `ProgressReporter` — UI ↔ BatchRunner bridge
- Thread-safe queue between background `BatchRunner` thread and UI thread.
- UI polls the queue on a timer (e.g., every 100 ms via `after()` in Tkinter).
- Events: `FILE_STARTED`, `FILE_DONE`, `FILE_FAILED`, `BATCH_COMPLETE`.

### Docling Configuration Decisions

- Enable **formula enrichment** (`PipelineOptions` with `do_formula_enrichment=True`) to get LaTeX output.
- Enable **table structure** (TableFormer is on by default in Docling).
- Enable **OCR fallback** for scanned pages (`do_ocr=True`, using EasyOCR or RapidOCR).
- Enable **figure extraction** with VLM captioning if GPU is available; fall back to caption-from-text if not.
- Multi-threading: Docling's converter is not thread-safe per instance. Instantiate one `DocumentConverter` per worker thread, or serialize calls through a single instance with a lock.

### Output Directory Structure

```
<output_dir>/
  batch_summary.json
  smith2023/
    docling.json
    document.html
    document.md
    elements/
      text_001.txt
      text_002.txt
      table_001.html
      table_002.html
      equation_001.tex
      figure_001.png
      figure_001_caption.txt
  jones2024/
    ...
```

### Overwrite Behavior

- If `overwrite=False` and `{name}/` already exists: skip the file, emit a `FILE_SKIPPED` event, log in summary.
- If `overwrite=True`: delete and recreate the subfolder before processing.

---

## Testing Decisions

### What makes a good test here

Tests should verify **observable outputs**, not internal Docling calls. The unit under test is the serialization and orchestration logic; Docling itself is treated as a trusted dependency.

### Modules to test

| Module | What to test |
|---|---|
| `ElementSerializer` | Given a mock `DoclingDocument` with known tables/equations/figures, assert the correct files are created with correct content. |
| `BatchRunner` | Given a list of 3 PDFs (2 valid, 1 corrupt/missing), assert 2 succeed, 1 fails gracefully, summary JSON is correct. |
| `ProgressReporter` | Assert all expected events are emitted in correct order for a 2-file batch. |
| `DoclingProcessor` | Integration test with a real small academic PDF (include a fixture). Assert `docling.json` is valid JSON and contains at least one table and one equation node. |

### Test fixtures

- Include at least one small (≤ 5 page) real academic PDF as a test fixture, ideally one with a table, an equation, and a figure.
- Mock `DocumentConverter` for unit tests that don't need real Docling output.

---

## Out of Scope

- Cloud storage integration (S3, Google Drive, etc.).
- Automatic downstream ingestion into a vector database or RAG pipeline.
- Gemini Flash / any cloud VLM fallback for hard pages (can be added later as an enrichment pass).
- Mathpix integration for specialist equation extraction.
- Citation / bibliography parsing and linking.
- Cross-reference resolution at chunk time (e.g., injecting Equation 3 into the paragraph that references it).
- GUI-based settings for Docling pipeline options (OCR model, VLM model, etc.) — these are set in code defaults.
- Packaging as a standalone executable (`.app`, `.exe`) — `python app.py` is sufficient.
- Multi-user or networked operation.

---

## Further Notes

- **Docling install:** `pip install docling` pulls in all required models. First run downloads model weights (~1–2 GB). Warn the user on first launch.
- **GPU:** Docling runs on CPU but is significantly faster on GPU (MPS on Apple Silicon, CUDA on Linux/Windows). The app should log which device is detected at startup.
- **Formula enrichment:** As of Docling's current release, formula enrichment requires explicitly enabling `PipelineOptions(do_formula_enrichment=True)`. Without it, equations are extracted as text blocks, not LaTeX.
- **Academic paper formats:** Many journals provide papers in multiple formats. If a JATS XML version is available alongside the PDF, Docling can parse it directly for higher fidelity — worth a future enhancement to accept `.xml` inputs too.
- **Reference benchmark:** The OmniDocBench benchmark is the current standard for evaluating PDF parser quality. Docling scores competitively on it for academic content.
- **License:** Docling is MIT licensed. The app can be distributed freely.
