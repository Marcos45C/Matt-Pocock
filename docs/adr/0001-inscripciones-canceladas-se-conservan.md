# Las inscripciones canceladas se conservan

Una inscripción cancelada no se borra: queda la fila con el instante en que el alumno decidió cancelar. La disponibilidad y la validación de capacidad cuentan solo inscripciones vigentes, y el alumno no puede volver a inscribirse en esa actividad. Se descartó borrar la fila porque perdería la decisión del alumno —lo único que el docente puede auditar— a cambio de una simplicidad que el constraint único ya nos da igual.

## Considered Options

- **Borrar la fila.** Disponibilidad y unicidad funcionan sin cambios, pero no queda rastro de la cancelación y una reinscripción futura sería indistinguible de una primera inscripción.
- **Estado + instante (`status` + `cancelled_at`).** Permite más estados a futuro, pero hoy solo hay dos y dos campos pueden contradecirse.
- **Instante nullable (`cancelled_at`).** Elegida: el instante es el estado.

## Consequences

- El `UniqueConstraint(student, activity)` sigue significando "una inscripción por alumno y actividad", ahora vigente o cancelada. Por eso la reinscripción está bloqueada y `register()` necesita un resultado propio (`previously_cancelled`) en lugar de reutilizar "ya estás inscripto".
- Todo cálculo de ocupación debe filtrar canceladas: disponibilidad, validación de capacidad del docente y cualquier conteo futuro.
- `seed_demo` no recrea canceladas porque ya verifica existencia sin filtrar estado; esa propiedad queda cubierta por una prueba.
- La ventana de cancelación es inclusiva en su borde (a las 24:00:00 exactas todavía se puede), al revés que el inicio de la actividad, que rechaza el instante exacto. La asimetría es deliberada: el límite pertenece al lado que rechaza, y en la cancelación el rechazo empieza después de las 24 h.
