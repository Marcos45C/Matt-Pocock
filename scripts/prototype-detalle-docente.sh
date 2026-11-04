#!/bin/sh
# Prototipo descartable: usa una base aislada en /tmp y no toca la demo real.
set -eu
cd "$(dirname "$0")/.."
export DEMO_DATA_DIR=/private/tmp/matt-prototype-detalle-docente-data
mkdir -p "$DEMO_DATA_DIR"
.venv/bin/python manage.py migrate --noinput
.venv/bin/python manage.py seed_demo
.venv/bin/python manage.py shell -c 'from django.contrib.auth import get_user_model; from django.utils import timezone; from activities.models import Activity, Registration; u,_=get_user_model().objects.get_or_create(username="carla-prototipo"); a=Activity.objects.get(seed_key="taller"); Registration.objects.get_or_create(student=u, activity=a, defaults={"cancelled_at": timezone.now()})'
printf '\nAbrí http://127.0.0.1:8017/accounts/login/ con docente1 / utdf-demo-2026; luego http://127.0.0.1:8017/teacher/activities/1/?variant=A\n\n'
.venv/bin/python manage.py runserver 127.0.0.1:8017
