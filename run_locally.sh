#!env bash

uv sync
source .venv/bin/activate
uv run src/main.py
