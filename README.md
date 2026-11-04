# Demo de inscripciones · UNTDF

Punto de partida del alumno: Django clásico, sesiones, templates y SQLite. Todas las inscripciones están confirmadas. Uso local docente, datos ficticios; no es una configuración de producción.

## Arranque con uv

Requiere uv 0.12.19 (o compatible); uv prepara Python 3.12.14 si falta. Primera instalación requiere Internet.

```sh
uv sync --locked
uv run --locked python manage.py migrate
uv run --locked python manage.py seed_demo
uv run --locked python manage.py runserver 127.0.0.1:8000
```

Abrir http://localhost:8000/ . Cuentas ficticias: `ana`, `bruno`, `docente`, `docente1`, `docente2`; contraseña inicial `untdf-demo-2026`. Docente entra en `/admin/`; `docente1` y `docente2` pueden consultar sus actividades en `/teacher/activities/`. Las actividades de ejemplo se reparten entre ambos. Las cuentas existentes conservan su contraseña y permisos al repetir seed. Recorrido: ingresar → catálogo → actividad → inscribirme → mis inscripciones → cancelar → salir (POST). Todos los horarios se muestran en America/Argentina/Ushuaia.

```sh
./scripts/check.sh
```

El script ejecuta `manage.py check`, verifica que no falten migraciones y corre la suite completa. Para que se ejecute antes de cada commit con cambios de código, plantillas o dependencias:

```sh
git config core.hooksPath .githooks
```

Los commits de solo documentación no lo disparan. En CI, `.github/workflows/check.yml` corre el mismo script.

Las pruebas usan `data/test.sqlite3`, aislada de `data/db.sqlite3`, y eliminan únicamente la base de pruebas. La suite completa corre 50 pruebas. Las pruebas concurrentes usan conexiones independientes y un archivo real, con barrera de inicio. No ejecutar dos suites sobre la misma carpeta al mismo tiempo.

## Responsables docentes

Cada actividad tiene un responsable staff, asignable desde la administración. El listado **Mis actividades** muestra solo las actividades del docente, incluso pasadas o deshabilitadas, con sus inscripciones vigentes. Antes de eliminar un responsable o quitarle el acceso staff hay que reasignar sus actividades. La migración asigna las actividades existentes al primer usuario staff; si no existe, crea `responsable-migracion` sin contraseña utilizable. Seed conserva los responsables ya asignados; si `docente1` o `docente2` ya existe sin acceso staff, se detiene sin modificar datos hasta resolver el conflicto.

## Cancelar una inscripción

Con una inscripción vigente, el detalle de la actividad y "Mis inscripciones" ofrecen **Cancelar inscripción** con confirmación del navegador. El botón aparece solo dentro de la ventana de cancelación; fuera de ella, el detalle explica el límite. La ventana es inclusiva: se puede cancelar hasta 24 horas antes del inicio, aunque la actividad esté deshabilitada. Si falta menos de 24 horas, si la actividad ya empezó o si ya pasó, la cancelación se rechaza con un mensaje que lo explica.

Cancelar no borra la inscripción: conserva la fila con la fecha y hora de la cancelación en America/Argentina/Ushuaia y libera el cupo de inmediato. El catálogo vuelve a ofrecer la actividad y el docente puede reducir la capacidad, que se valida solo contra inscripciones vigentes. La inscripción cancelada sigue apareciendo en "Mis inscripciones" con su badge y su fecha, sin botón. No hay reinscripción: la misma actividad rechaza un nuevo intento con un mensaje propio —"cancelaste tu inscripción"— y el detalle explica el bloqueo en lugar de mostrar el formulario. El docente ve la fecha de cancelación en el listado y en el detalle de la administración, que sigue siendo de solo consulta.

Cancelar es siempre un `POST` con CSRF e identidad tomada de la sesión; `GET` responde 405. La contención de la base devuelve un resultado reintentable sin efectos parciales, y la operación comparte la transacción `IMMEDIATE` con la inscripción.

## Docker

Requiere Docker y Compose; no requiere Python/uv en el host. Python 3.12.14 y uv 0.12.19 están fijados en Dockerfile, y Django 5.2.17 en uv.lock.

```sh
docker compose up --build
# En otra terminal:
docker compose exec web uv run --locked python manage.py test --noinput
docker compose stop
docker compose start
```

El servicio `web` sirve http://localhost:8000/ solo en loopback. Las migraciones y seed iniciales son automáticos; reconstruir o reiniciar conserva las inscripciones. El volumen `sdd-base_sqlite-data` está separado de la base local. `.venv` del host se excluye; las dependencias del contenedor viven en `/opt/venv`. El código se monta para recarga; cambiar uv.lock requiere reconstruir.

Para una práctica independiente, usar una **copia de código nueva**, puerto y nombre diferentes:

```sh
DEMO_PORT=8016 COMPOSE_PROJECT_NAME=sdd-practica docker compose up --build
```

El puerto8016 es un ejemplo para la copia restaurada: comprobar que esté libre y elegir otro puerto y nombre de proyecto si existe otra práctica simultánea.

No usar `down -v` para reinicios cotidianos. Stop/start conserva datos.

## Datos repetibles y reinicio explícito

Seed crea cinco actividades: taller a +48h, clínica a +12h, laboratorio completo a +72h, deshabilitada a +96h e iniciada a −2h. Ana está en taller/clínica; Bruno en taller/laboratorio. La primera carga persiste su ancla; cargas siguientes no desplazan fechas, duplican registros ni reescriben usuarios o ediciones. Si falta una inscripción inicial y ya no se cumplen condiciones, seed informa el resultado y preserva lo existente.

Para reproducir una referencia exacta en una base nueva:

```sh
uv run --locked python manage.py seed_demo --reference-time '2030-10-01T09:00:00-03:00'
```

**Reset elimina las cinco actividades identificadas de la demo y todas sus inscripciones, incluso las creadas manualmente sobre ellas. Conserva usuarios, sus contraseñas, actividades ajenas y registros asociados a las actividades ajenas.** Recalcula el ancla para una nueva clase; el comando muestra primero la base destino y sus efectos. Sin `--confirm` no modifica nada.

```sh
uv run --locked python manage.py reset_demo --confirm
# O dentro del volumen Docker:
docker compose exec web uv run --locked python manage.py reset_demo --confirm
# Para reloj reproducible:
uv run --locked python manage.py reset_demo --confirm --reference-time '2030-10-01T09:00:00-03:00'
```

## Configuración y límites

Django lee variables de entorno; **no carga `.env` automáticamente**. `.env.example` es una referencia; Compose sí utiliza `.env` para sus propias variables. `DEMO_DATA_DIR` cambia la ubicación de SQLite, `DJANGO_DEBUG`/`DJANGO_SECRET_KEY` configuran Django. Hay defaults docentes para arrancar sin pasos ocultos.

La disponibilidad se calcula desde registros. Las transacciones de inscripción y edición administrativa empiezan en SQLite `IMMEDIATE`; timeout 10s. Así se adquiere la reserva de escritura antes de leer el cupo. SQLite serializa escritores: es adecuado para esta demo local, no para alta carga. Un timeout devuelve `busy`, sin efecto parcial, y permite reintentar. Otros errores no se ocultan. `select_for_update()` no protege este caso en SQLite. La administración de inscripciones es de consulta, sin altas/bajas que eludan las reglas.

## Recuperar punto de partida

La exportación `../material-docente/checkpoints/base.tar.gz` contiene solo código, migraciones y lockfile, con raíz `demo-inscripciones/`. Su manifiesto registra checksum. Restaurar a **una carpeta nueva**, nunca encima del original:

```sh
mkdir -p /tmp/sdd-clase
 tar -xzf ../material-docente/checkpoints/base.tar.gz -C /tmp/sdd-clase
cd /tmp/sdd-clase/demo-inscripciones
uv sync --locked
uv run --locked python manage.py migrate
uv run --locked python manage.py seed_demo
uv run --locked python manage.py runserver 127.0.0.1:8016
```

La exportación excluye bases SQLite, entornos, caches y secretos. Las soluciones docentes se entregan fuera de esta carpeta.

## Revisión técnica del checkpoint actual

La base actual (v2) evalúa el reloj real de inscripción dentro de IMMEDIATE inmediatamente antes de verificar el inicio. Así, una solicitud que espera un escritor y llega a una actividad ya iniciada devuelve `started` sin ocupar cupo. El parámetro `now` conserva el reloj fijo de pruebas; los duplicados se reconocen primero. La versión anterior se preserva como `base-v1.tar.gz` para reproducir los recorridos históricos; no se reescribe su procedencia.
