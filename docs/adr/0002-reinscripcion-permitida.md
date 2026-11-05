# La reinscripción después de cancelar está permitida

Status: accepted

Un alumno que canceló su inscripción puede volver a inscribirse en la misma actividad, sin límite de veces, mientras la actividad esté habilitada, no haya comenzado y quede cupo. Cada reinscripción crea una fila nueva: la cancelada se conserva como historial y el constraint único pasa a aplicarse solo sobre inscripciones vigentes. Se mantiene el resultado `registered` para no distinguir la reinscripción en el servicio.

## Considered Options

- **Mantener el bloqueo.** El ADR 0001 lo fijó para conservar la decisión del alumno; se descarta porque impide corregir una cancelación y no protege la capacidad.
- **Reactivar la fila cancelada.** Mantiene un solo registro por par alumno-actividad, pero pierde el instante de cancelación y el `created_at` original deja de describir el vínculo vigente.
- **Fila nueva con único parcial sobre vigentes.** Elegida: conserva el historial completo, da a cada vínculo su propio instante y sigue garantizando a lo sumo una inscripción vigente por alumno y actividad.

## Consequences

- El `UniqueConstraint(student, activity)` se reemplaza por uno parcial sobre `cancelled_at IS NULL`; las canceladas pueden repetirse.
- `register()` deja de devolver `previously_cancelled` y evalúa una inscripción vigente antes que habilitación, inicio y cupo; la reinscripción comparte las reglas y los rechazos de una inscripción normal.
- El resultado es `registered` también para la reinscripción; el mensaje no distingue el caso.
- Un alumno puede acumular varias filas canceladas por actividad; el historial queda visible para él y para el docente.
- La ventana de cancelación no cambia: se puede cancelar hasta 24 h antes del inicio, incluso si la actividad está deshabilitada.
- `seed_demo` sigue comprobando existencia sin filtrar estado, así que no recrea una inscripción cancelada.
