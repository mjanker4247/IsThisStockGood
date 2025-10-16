#!/usr/bin/env bash
set -euo pipefail

uv pip compile pyproject.toml -o requirements.txt
gcloud app deploy app.yaml
