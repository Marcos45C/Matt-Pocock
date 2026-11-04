# 04: El docente ve las cancelaciones y los datos de demo las respetan

**What to build:** El docente entiende la ocupación real de una actividad: la administración muestra qué inscripciones se cancelaron y cuándo, sin habilitar altas ni bajas. Los datos de demo respetan la decisión del alumno: correr el seed después de una cancelación no la recrea, y el reinicio de la demo sigue borrando todo. El README describe el recorrido con la cancelación, la ventana de 24 h, la conservación del registro y la ausencia de reinscripción.

**Blocked by:** 01 (cancelar desde el detalle)

**Spec:** ../spec.md

**Status:** done

- [x] La administración muestra el instante de cancelación en el listado y en el detalle de la inscripción.
- [x] La administración sigue sin permitir altas ni bajas de inscripciones.
- [x] Correr el seed después de una cancelación no recrea la inscripción ni emite advertencia de faltante.
- [x] El reinicio de la demo sigue eliminando las actividades de la demo y sus inscripciones, canceladas incluidas.
- [x] El README describe el recorrido, la ventana, la conservación de la cancelada y la ausencia de reinscripción, con el conteo de pruebas actualizado.
- [x] Pruebas de seed cubren la preservación de la cancelación.

## Comments

Implementado en `ed7c0f7`, integrado en `af2e1d6`. `cancelled_at` visible en listado y detalle del admin, que sigue siendo de solo consulta; el seed preserva la cancelación sin advertencia; el reset borra las actividades de la demo y sus canceladas; el README documenta recorrido, ventana inclusiva, conservación y bloqueo de reinscripción, con 49 pruebas. Suite completa: 49 pruebas OK.
