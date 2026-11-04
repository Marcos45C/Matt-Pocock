# 01: Cancelar una inscripción desde el detalle de la actividad

**What to build:** El alumno abre una actividad donde está inscripto y ve un botón para cancelar, con confirmación. Al confirmar, la inscripción queda cancelada con la fecha en que lo decidió, el formulario de inscripción desaparece, el cupo vuelve al catálogo y el docente puede reducir la capacidad de la actividad. Se puede cancelar hasta 24 horas antes del inicio, inclusive, aunque la actividad esté deshabilitada; fuera de esa ventana, o si la actividad ya empezó, la cancelación se rechaza con un mensaje que lo explica.

**Blocked by:** None (can start immediately)

**Spec:** ../spec.md

**Status:** done

- [x] El detalle ofrece el botón solo con inscripción vigente y dentro de la ventana; fuera de la ventana explica el límite.
- [x] `GET` a la ruta de cancelación responde 405; `POST` sin CSRF responde 403; `POST` válido redirige al detalle con mensaje de confirmación.
- [x] La identidad sale de la sesión, nunca del cuerpo del formulario.
- [x] Cancelar conserva la inscripción con el instante recibido y libera el cupo que muestra el catálogo.
- [x] La disponibilidad y la validación de capacidad del docente cuentan solo inscripciones vigentes.
- [x] Exactamente 24 h antes del inicio se acepta; 24 h − 1 s, actividad iniciada o pasada se rechazan.
- [x] Una actividad deshabilitada no impide cancelar dentro de la ventana.
- [x] Cancelar una inscripción ajena o inexistente no modifica nada y devuelve el mismo rechazo.
- [x] Repetir la cancelación informa que ya estaba cancelada y conserva el primer instante.
- [x] La contención de la base se informa como reintentable, sin efectos parciales; otros errores se propagan.
- [x] El detalle de una inscripción cancelada muestra el badge, la fecha en hora de Ushuaia y ningún formulario de inscripción.
- [x] Pruebas de servicio y HTTP cubren todo lo anterior y la suite existente sigue verde.

## Comments

Implementado en la rama actual: campo `cancelled_at`, servicio `cancel_registration`, ruta POST con CSRF, detalle con botón/confirmación, badge y fecha. La suite pasa con 35 pruebas (22 previas + 13 nuevas).
