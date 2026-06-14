#!/bin/bash
# Launch the Academic PDF Processor using the project's venv — no manual
# `source .venv/bin/activate` needed. Run from anywhere: ./run.sh
cd "$(dirname "$0")" || exit 1
exec .venv/bin/python app.py
