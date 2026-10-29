#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
# Existing task/checkouts are isolated; no worktree or source reset is needed.
python3 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements.lock
.venv/bin/python -m pip check
