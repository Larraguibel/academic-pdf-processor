# Build prompt — next session

Paste the block below as the opening message of the next (build) session. It drives the
fully-autonomous, wave-by-wave build from the GitHub issues.

---

```
Build the Academic PDF Processor app, wave by wave, from the GitHub issues. This is an
execution session — the planning, repo, and 19 issues are already done and approved. Do
the work; don't re-plan. Work AUTONOMOUSLY through all four waves without stopping for
confirmation; only stop if a blocker genuinely can't be resolved.

Repo (already created, PUBLIC, gh authenticated as "Larraguibel"):
  https://github.com/Larraguibel/academic-pdf-processor
Working dir: /Users/diegolarraguibel/Desktop/Proyectos/pdf-handling-tool  (already a git repo, on main)

START HERE — read these first for full context:
  1. Issue #1 (pinned "Orchestration guide") — the wave plan + dependency edges + the
     issue-body contract. Read it with: gh issue view 1
  2. PLAN.md in the repo root — architecture, module layout, Docling caveats.
  3. The issues themselves: gh issue list --limit 50   (each has exact module path +
     function signature, verified Docling 2.102 snippets to use VERBATIM, checkbox
     acceptance criteria, "Blocked by", and a "Notes for the agent" guardrail.)

Locked decisions (do not re-ask):
  - Stack: Python 3.13, Docling 2.102.1, Tkinter (stdlib), MIT. Package name: apdf.
  - Build strictly in DEPENDENCY-WAVE ORDER. A wave cannot start until the issues it
    depends on are merged to main.
       W0: #2 (scaffold — blocks everything)
       W1: #3 #4 #5 #6 #7 #8 #9 #10 #11 #12 (10 independent modules — fan these out in parallel)
       W2: #13 #14 #15 #16
       W3: #17 #18 #19
  - You are the opus orchestrator: within a wave, dispatch one worker per open issue in
    PARALLEL (sub-agents), each scoped to exactly the module its issue names. Honor each
    issue's "Notes for the agent" guardrails — workers stay inside their one module and use
    the inlined Docling snippets verbatim (the v2 API is format-keyed; stale calls fail).
  - NOTE: issues #9, #10, #11, #13 all edit apdf/serializers/elements.py. Sequence or
    coordinate those so parallel workers don't clobber each other's edits to that one file.

Per-issue workflow:
  - Create a feature branch, implement exactly what the issue specifies, satisfy every
    acceptance checkbox, run any tests, commit (Co-Authored-By trailer), open a PR that
    says "Closes #N", and merge to main before starting any issue that depends on it.
  - End each issue: tick its acceptance-criteria checkboxes on the GitHub issue.

Environment notes:
  - First Docling conversion downloads ~few-hundred MB of model weights to
    ~/.cache/docling/models. Create a .venv and `pip install -r requirements.txt` once #2
    exists. On Apple Silicon, formula enrichment runs on CPU (MPS excluded) — expect it slow.
  - Issue #19's fixture must be a tiny SYNTHETIC pdf (table + equation). NEVER use or commit
    test_pdfs/ — it's git-ignored copyrighted papers.

Constraints:
  - Don't merge an issue whose blockers aren't merged.
  - Don't commit test_pdfs/ or .claude/.
  - When the app is buildable (after W3), verify end-to-end: create a .venv, install deps,
    run `python app.py`, process a couple of PDFs, confirm per-paper
    docling.json/document.html/document.md/elements/ + batch_summary.json, and run
    `pytest -m slow`.

When all 19 issues are merged and the end-to-end verification passes, report a final
summary: what was built, test results, and anything that needed a judgment call.
```
