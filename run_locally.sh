#!env bash

uv sync
source .venv/bin/activate
uv run app/main.py
