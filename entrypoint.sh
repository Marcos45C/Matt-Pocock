#!/bin/sh
set -eu
uv run --locked python manage.py migrate --noinput
uv run --locked python manage.py seed_demo
exec uv run --locked python manage.py runserver 0.0.0.0:8000
