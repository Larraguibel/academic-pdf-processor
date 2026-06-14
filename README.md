# Academic PDF Processor

A local desktop app that batch-converts academic PDFs into structured, element-typed
outputs using [Docling](https://github.com/docling-project/docling) — **no cloud, no API
keys, no data leaves your machine**.

Standard PDF-to-text tools flatten multi-column layouts, numbered equations, complex
tables, and captioned figures into unstructured strings, destroying the semantic structure
that makes papers useful for LLMs, search, and RAG. This tool lets a researcher drop a
batch of PDFs into a file picker and receive, per paper: an HTML
render with MathML equations and real `<table>` elements, extracted figure PNGs with
caption files, and per-element flat files (LaTeX equations, HTML tables, plain-text
sections).

> **Status:** scaffolding stage. The repo currently holds the plan
> ([`PLAN.md`](PLAN.md)) and the build is tracked issue-by-issue — see the
> **Issues** tab (start with the pinned *Orchestration guide*).

## Stack

- **Python 3.13** (supported range `>=3.10,<4.0`)
- **Docling 2.102.1** (MIT)
- **Tkinter** (Python stdlib) for the UI — zero extra UI dependencies
- **MIT** licensed

## Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

Then: select PDF files → choose an output folder → click **Run**. Progress and per-file
status (succeeded / failed / skipped) are shown in the in-app log.

> ⚠️ **First-run model download.** On the first conversion, Docling downloads its model
> weights (layout, TableFormer, formula, picture classifier) — **on the order of a few
> hundred MB** — to `~/.cache/docling/models`. This happens once; later runs are offline.
> The app will warn you and can prefetch the models before the first run.

> ℹ️ **Device note (Apple Silicon).** Most stages use MPS, but **formula enrichment runs
> on CPU** (Docling excludes MPS for that stage), so equation extraction is the slowest
> part of a run. The app logs the detected device at startup.

## Output structure

Each input `smith2023.pdf` produces a folder mirroring its name:

```
<output_dir>/
  batch_summary.json
  smith2023/
    document.html         # MathML equations + real <table> elements
    document.md           # human-readable Markdown
    elements/
      text_001.txt        # section/paragraph text blocks
      table_001.html      # each table as a standalone <table> snippet
      equation_001.tex    # each display equation as LaTeX
      figure_001.png      # each extracted figure image
      figure_001_caption.txt
```

## Your own PDFs

This repo does **not** ship any sample PDFs — supply your own. (The `test_pdfs/` folder
used during development is git-ignored.)

## License

[MIT](LICENSE).
