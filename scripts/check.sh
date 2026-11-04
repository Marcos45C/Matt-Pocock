#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
uv run --locked python manage.py check
uv run --locked python manage.py makemigrations --check --dry-run
uv run --locked python manage.py test --noinput
