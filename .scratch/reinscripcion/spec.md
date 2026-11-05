# Reinscripción después de cancelar

Status: ready-for-agent

## Problem Statement

Un alumno que cancela su inscripción queda bloqueado para siempre en esa actividad: el ADR 0001 y el ticket `02-bloquear-reinscripcion` de la feature de cancelación lo decidieron a propósito. Ahora necesitamos que pueda corregir la decisión. El cupo puede seguir libre, la actividad puede no haber comenzado y el bloqueo obliga a intervenir la base para deshacer un error. Además, la confirmación de cancelación y el detalle le prometen al alumno que no podrá volver a inscribirse, algo que deja de ser cierto.

## Solution

Un alumno con una inscripción cancelada puede volver a inscribirse en la misma actividad, sin límite de veces, si la actividad está habilitada, no comenzó y hay cupo. Cada reinscripción crea una fila nueva: la cancelada se conserva como historial y el constraint único pasa a aplicarse solo sobre inscripciones vigentes. El servicio devuelve `registered`, sin un resultado propio. El detalle muestra la fecha de la última cancelación y el formulario normal con el botón "Inscribirme"; "Mis inscripciones" y la vista docente listan todo el historial; la administración no cambia. El seed no suma escenarios nuevos.

## User Stories

1. Como alumno, quiero volver a inscribirme en una actividad que cancelé, para corregir una cancelación equivocada sin depender de nadie.
2. Como alumno, quiero poder hacerlo sin límite de veces, para no quedar atado a una única oportunidad.
3. Como alumno, quiero que la reinscripción respete las reglas normales —actividad habilitada, antes del inicio y con cupo—, para que no se saltee la capacidad.
4. Como alumno, quiero ver la fecha de mi última cancelación cuando vuelvo al detalle, para entender por qué la fila anterior no cuenta.
5. Como alumno, quiero que si la actividad está llena, deshabilitada o ya empezó se me explique con el rechazo normal, para saber por qué no puedo volver.
6. Como alumno, quiero que la confirmación de cancelación no me prometa un bloqueo que ya no existe, para decidir con información correcta.
7. Como alumno, quiero ver todas mis inscripciones, vigentes y canceladas, para conservar el historial de mis decisiones.
8. Como alumno, quiero que desde una inscripción cancelada solo pueda ir al detalle, para no reinscribirme por accidente desde la lista.
9. Como docente, quiero ver todos los intentos de un alumno en el detalle de la actividad, para auditar la ocupación real.
10. Como docente, quiero que la administración siga siendo de solo consulta, para que las reglas no se eludan.
11. Como mantenedor, quiero que el seed no recree inscripciones canceladas ni reinscripciones, para respetar lo que hizo el alumno.
12. Como mantenedor, quiero pruebas de servicio, HTTP y concurrencia que fijen la nueva regla, para no volver al bloqueo por accidente.

## Implementation Decisions

- **Modelo**: la inscripción conserva su fila al cancelarse y una reinscripción agrega otra fila. Se reemplaza el `UniqueConstraint(student, activity)` por uno parcial sobre `(student, activity)` con condición `cancelled_at IS NULL`: se permiten varias canceladas por par y como máximo una vigente. La migración no transforma datos; las filas existentes ya cumplen la nueva regla. `Meta.ordering`, `Activity.clean()`, `with_availability()` y la validación de capacidad siguen contando solo inscripciones vigentes.
- **Servicio de inscripción**: `register()` busca primero una inscripción vigente y devuelve `already_registered` si existe. Si no existe, evalúa actividad inexistente, habilitación, inicio y cupo, y recién entonces crea una fila. Una inscripción cancelada ya no corta el flujo: la reinscripción recibe los mismos rechazos (`not_available`, `disabled`, `started`, `full`) que una inscripción normal. La reinscripción devuelve `registered`.
- **Resultados**: se elimina `previously_cancelled` de `MESSAGES` y ningún camino del servicio lo devuelve. `already_registered` conserva la precedencia sobre habilitación, inicio y cupo cuando hay una vigente. Un intento de reinscripción nunca reutiliza ni reactiva la fila cancelada.
- **Servicio de cancelación**: sigue cancelando la inscripción vigente dentro de la ventana. Si no hay vigente pero existe alguna cancelada, devuelve `already_cancelled`; si no hay filas, `not_registered`. El instante de cada cancelación queda en su propia fila.
- **Reglas y límites**: no hay ventana propia de reinscripción ni aprobación docente. Se acepta el escenario de cancelar a las 25 h, reinscribirse a las 23 h y quedar sin poder cancelar porque la ventana ya cerró; también se acepta que el cupo liberado lo ocupe otro y que la reinscripción quede bloqueada por `full` hasta que ese otro cancele.
- **Detalle**: si hay una inscripción vigente, se muestra el estado actual y la cancelación como hoy. Si no hay vigente pero sí canceladas, se muestra la fecha de la última cancelación y el formulario normal de inscripción con el botón "Inscribirme" (no "Volver a inscribirme"). Si la actividad está llena, deshabilitada o ya comenzó, se muestra el rechazo normal y se conserva la fecha de la última cancelación, sin formulario. Si no hay ninguna inscripción, no cambia nada.
- **Confirmación de cancelación**: el texto de `_cancel_form.html` deja de decir "no vas a poder volver a inscribirte"; informa que el cupo quedará libre y que se podrá volver a inscribir si todavía hay cupo.
- **"Mis inscripciones"**: lista todas las filas del alumno, vigentes y canceladas, de más nueva a más vieja, incluidas varias filas de la misma actividad. Las canceladas muestran badge y fecha, no ofrecen cancelar ni un POST directo de reinscripción; solo enlazan al detalle. Las vigentes conservan el botón de cancelar dentro de la ventana.
- **Vista docente y administración**: el detalle docente sigue listando todas las filas, vigentes primero y canceladas después, y ahora puede mostrar varias filas del mismo alumno. La administración ya muestra todas las filas con `cancelled_at` y sigue siendo de solo consulta; no se esperan cambios de código, solo verificación.
- **Datos de demo**: el seed no agrega un caso de reinscripción. Sigue verificando existencia sin filtrar estado, así que no recrea una cancelada ni una reinscripción. `reset_demo` no cambia.
- **Documentación**: el ADR 0002 reemplaza al ADR 0001 y el glosario ya distingue Inscripción, Inscripción vigente y Reinscripción. El README debe dejar de decir que no hay reinscripción y actualizar el conteo de pruebas.

## Testing Decisions

- **Seam de servicio** (principal): reemplazar en `activities/tests/test_service.py` las pruebas que exigen el bloqueo —`test_previously_cancelled_even_when_now_full_disabled_or_started` y `test_reregistration_over_cancelled_is_its_own_result_and_creates_no_row`— por pruebas de la nueva regla: la reinscripción crea una segunda fila, conserva la cancelada, devuelve `registered` y baja la disponibilidad; se puede repetir sin límite; una vigente sigue devolviendo `already_registered`; una cancelada no evita los rechazos `full`, `disabled` ni `started`; y la validación de capacidad sigue contando solo vigentes. Agregar una prueba de modelo/migración: varias canceladas del mismo par se permiten y dos vigentes se rechazan.
- **Seam HTTP**: reemplazar en `activities/tests/test_views.py` `test_reregistration_over_cancelled_explains_and_creates_no_row`, `test_http_reregistration_blocked_when_full_disabled_or_started` y la aserción de `test_detail_cancel_states` que exige que "Inscribirme" desaparezca después de cancelar. Cubrir: el detalle muestra la última cancelación y el formulario con "Inscribirme"; el POST crea una fila nueva y muestra "Inscripción confirmada."; en actividad llena, deshabilitada o iniciada se ve el rechazo normal y la fecha, sin fila nueva; "Mis inscripciones" muestra las dos filas, la cancelada sin botón de cancelar y solo con enlace al detalle; el detalle docente muestra las dos filas con la vigente primero; la confirmación de cancelación ya no promete un bloqueo.
- **Seam de concurrencia**: agregar en `activities/tests/test_concurrency.py` dos pruebas con el patrón existente (`TransactionTestCase`, archivo real, conexiones independientes, barrera y reloj inyectado): (1) dos reinscripciones simultáneas del mismo alumno después de una cancelación devuelven `registered` y `already_registered`, dejan una sola vigente y dos filas en total; (2) reinscripción contra el último cupo con capacidad 1 y una cancelada de Ana: la carrera entre la reinscripción de Ana y la inscripción de Bruno devuelve `registered` y `full` en cualquier orden, deja una sola vigente y disponibilidad 0.
- **Seams confirmados**: servicio, HTTP y concurrencia. No se agregan seams nuevos: no se prueban detalles internos del `UPDATE`, del constraint ni de la plantilla por separado. Las pruebas fijan comportamiento observable del servicio, de las páginas y de la base.

## Out of Scope

- Botón o POST directo de reinscripción desde "Mis inscripciones"; solo enlace al detalle.
- Historial completo de cancelaciones en el detalle; solo se muestra la última.
- Resultado o mensaje propio de reinscripción (`reregistered`); se reutiliza `registered` y el mensaje "Inscripción confirmada.".
- Escenario de reinscripción en el seed de demo.
- Cancelación por parte del docente o del administrador, lista de espera, notificaciones, reportes o cambios a la ventana de cancelación.
- Migración o limpieza de datos existentes: no hay datos que transformar.

## Tickets

- **01 — Reinscribirse desde el detalle** (vertical: modelo, servicio, detalle y texto de la confirmación). Sin bloqueo.
- **02 — Listados con historial de reinscripciones**. Bloqueado por 01.
- **03 — Carreras de la reinscripción**. Bloqueado por 01.
- **04 — README y verificación final**. Bloqueado por 01, 02 y 03.

## Further Notes

- La decisión, sus alternativas y consecuencias están en `docs/adr/0002-reinscripcion-permitida.md`, que deja al ADR 0001 como superseded.
- Términos en `GLOSSARY.md`: Inscripción, Inscripción vigente, Reinscripción, Cancelación, Ventana de cancelación y Cupo disponible.
- Esta spec reemplaza el ítem "Reinscripción después de cancelar" que la spec de cancelación había dejado fuera de alcance y el ticket `02-bloquear-reinscripcion` de esa feature.
- El spec y los tickets históricos pueden seguir mencionando `previously_cancelled`; el código, las plantillas y el README no.
- Después de implementar, correr `./scripts/check.sh` para verificar system check, migraciones y suite completa.
