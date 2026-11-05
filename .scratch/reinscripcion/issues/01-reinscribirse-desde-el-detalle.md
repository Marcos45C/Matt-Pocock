# 01: Reinscribirse desde el detalle

**What to build:** Un alumno con una inscripción cancelada vuelve a inscribirse en la misma actividad desde el detalle: el modelo admite varias filas con una sola vigente, el servicio crea una fila nueva y devuelve `registered`, y el detalle muestra la fecha de la última cancelación con el formulario normal y el botón "Inscribirme". Si la actividad está llena, deshabilitada o ya comenzó, el detalle muestra el rechazo normal junto con la fecha. La confirmación de cancelación deja de prometer que no podrá volver a inscribirse. El corte es vertical: al terminar, el recorrido completo cancelar → reinscribir se puede demostrar desde la UI.

**Blocked by:** None (can start immediately)

**Spec:** ../spec.md

**Status:** ready-for-agent

- [ ] `Registration` permite varias filas canceladas del mismo alumno y actividad y como máximo una vigente; la migración reemplaza el unique total por uno parcial sobre `cancelled_at IS NULL`.
- [ ] `register()` busca primero una inscripción vigente y devuelve `already_registered`; una cancelada ya no corta el flujo.
- [ ] Una reinscripción crea una fila nueva, conserva la cancelada y devuelve `registered`; la disponibilidad baja en uno.
- [ ] Sin límite de reinscripciones: cada una exige una cancelación previa y compite por cupo como cualquier inscripción.
- [ ] `full`, `disabled` y `started` se aplican a la reinscripción igual que a una inscripción normal; una cancelada no los tapa.
- [ ] `cancel_registration()` cancela la vigente; sin vigente devuelve `already_cancelled` si hay alguna cancelada y `not_registered` si no hay filas.
- [ ] `previously_cancelled` se elimina de `MESSAGES` y ningún camino del servicio lo devuelve.
- [ ] El detalle con canceladas y sin vigente muestra la fecha de la última cancelación y el formulario normal con "Inscribirme".
- [ ] El POST desde ese formulario crea una fila nueva, conserva la cancelada y muestra "Inscripción confirmada.".
- [ ] Si la actividad está llena, deshabilitada o iniciada, el detalle muestra el rechazo normal y la fecha de la última cancelación, sin fila nueva.
- [ ] Con una inscripción vigente, el detalle sigue mostrando el estado actual y no ofrece el formulario.
- [ ] `_cancel_form.html` ya no dice "no vas a poder volver a inscribirte"; informa que el cupo quedará libre y que se podrá volver a inscribir si hay cupo.
- [ ] En `activities/tests/test_service.py` se reemplazan `test_previously_cancelled_even_when_now_full_disabled_or_started` y `test_reregistration_over_cancelled_is_its_own_result_and_creates_no_row` por pruebas del comportamiento nuevo; el resto de la suite de servicio sigue verde.
- [ ] En `activities/tests/test_views.py` se reemplazan `test_reregistration_over_cancelled_explains_and_creates_no_row` y `test_http_reregistration_blocked_when_full_disabled_or_started`, y `test_detail_cancel_states` deja de exigir que "Inscribirme" desaparezca después de cancelar.
- [ ] Las pruebas HTTP nuevas cubren la fecha de la última cancelación, el formulario, el POST exitoso y los tres rechazos.
- [ ] Prueba de modelo/migración: varias canceladas del mismo par se permiten y dos vigentes se rechazan.
- [ ] `makemigrations --check` pasa.
