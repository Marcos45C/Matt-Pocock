# Cancelar una inscripción

Status: ready-for-agent

## Problem Statement

Un alumno que se inscribe en una actividad queda atado a ella hasta que la actividad comienza: no hay forma de deshacerse de la inscripción. Si no puede asistir, el cupo queda ocupado por alguien que no va a ir, el catálogo sigue mostrando la actividad completa y el docente no tiene manera de saber que ese lugar está libre en la práctica. La única salida hoy es pedirle a alguien con acceso a la base que borre la fila, algo que la administración ni siquiera permite.

## Solution

El alumno puede cancelar su propia inscripción, desde el detalle de la actividad o desde "Mis inscripciones", hasta 24 horas antes del inicio. La cancelación libera el cupo de inmediato, conserva la inscripción con el instante en que se decidió, y no habilita una nueva inscripción en esa actividad. El docente ve la cancelación y la fecha en la administración, y la validación de capacidad deja de contar esos lugares.

## User Stories

1. Como alumno, quiero cancelar mi inscripción desde el detalle de la actividad, para liberar mi cupo sin depender de nadie.
2. Como alumno, quiero cancelar desde "Mis inscripciones", para hacerlo sin tener que buscar la actividad en el catálogo.
3. Como alumno, quiero ver el botón de cancelar solo cuando todavía puedo usarlo, para no intentar algo que va a ser rechazado.
4. Como alumno, quiero que se me pida confirmación antes de cancelar, para no cancelar por un clic accidental.
5. Como alumno, quiero saber hasta cuándo puedo cancelar, para decidir si todavía estoy a tiempo.
6. Como alumno, quiero que cancelar libere el cupo de inmediato, para que otra persona pueda aprovecharlo.
7. Como alumno, quiero ver el cupo liberado reflejado en la actividad, para confirmar que la cancelación tuvo efecto.
8. Como alumno, quiero ver mi inscripción cancelada con la fecha en que la cancelé, para tener registro de mi decisión.
9. Como alumno, quiero que la inscripción cancelada siga apareciendo en "Mis inscripciones", para conservar el historial de lo que hice.
10. Como alumno, quiero que se me avise que no puedo volver a inscribirme, para no intentarlo en vano.
11. Como alumno, quiero poder cancelar aunque la actividad esté deshabilitada, para no quedar atado a algo que se suspendió.
12. Como alumno, quiero que un segundo intento de cancelar me diga que ya estaba cancelada y no cambie la fecha, para no perder el registro original.
13. Como alumno, quiero que la cancelación se rechace si falta menos de 24 horas para el inicio, para que el cupo no se libere cuando ya nadie puede usarlo.
14. Como alumno, quiero que la cancelación se acepte a las 24 horas exactas, para no perder el último instante útil por un segundo.
15. Como alumno, quiero que la cancelación se rechace si la actividad ya empezó o ya pasó, para no alterar el pasado.
16. Como alumno, quiero que cancelar la inscripción de otra persona no tenga ningún efecto, para que nadie pueda hacerlo por mí.
17. Como alumno, quiero que un error de la base no me deje la cancelación a medias, para poder reintentar con confianza.
18. Como alumno, quiero que cancelar sea una acción explícita y no un enlace que se dispare al abrir una página, para no cancelar por accidente al navegar.
19. Como alumno, quiero un mensaje que confirme que la cancelación se guardó, para no quedarme con la duda.
20. Como alumno, quiero que el detalle explique por qué ya no hay formulario de inscripción cuando cancelé, para no pensar que la página está rota.
21. Como alumno, quiero que la fecha de cancelación se muestre en hora de Ushuaia, para leerla igual que el resto de los horarios del sistema.
22. Como docente, quiero ver en la administración qué inscripciones fueron canceladas y cuándo, para entender la ocupación real de cada actividad.
23. Como docente, quiero que la capacidad se valide solo contra inscripciones vigentes, para poder reducirla después de que alguien cancele.
24. Como docente, quiero que el catálogo vuelva a ofrecer la actividad con el cupo liberado, para que el lugar no se pierda.
25. Como docente, quiero que los datos de demo no recreen una inscripción cancelada, para que el seed respete lo que hizo el alumno.
26. Como docente, quiero que el reinicio de la demo siga borrando todo, para poder restaurar el escenario de clase.
27. Como docente, quiero que la administración siga sin permitir altas ni bajas de inscripciones, para que las reglas del servicio no se eludan.
28. Como docente, quiero una prueba de concurrencia que garantice que nunca quedan dos inscriptos en un cupo de uno, para poder confiar en la demo frente a la clase.

## Implementation Decisions

- **Modelo**: la inscripción conserva su fila al cancelarse. Se agrega un instante de cancelación nullable; ausencia del valor significa inscripción vigente. No se agrega un estado separado ni un booleano: el instante es el estado y no puede contradecirse. Una migración nueva, sin datos que transformar.
- **Servicio**: se agrega una operación de cancelación con la misma forma que la de inscripción — identidad del alumno, actividad, reloj inyectable para pruebas — que devuelve un código de resultado en vez de lanzar excepciones de negocio. Corre dentro de la misma transacción `IMMEDIATE` que la inscripción y traduce la contención de SQLite a un resultado reintentable; cualquier otro error se propaga.
- **Resultados**: cancelación exitosa, sin inscripción (incluye la de otra persona, sin distinguir), ya cancelada, fuera de ventana, actividad inexistente y base ocupada. La inscripción sobre una cancelada necesita un resultado propio —"cancelaste tu inscripción"— en lugar de reutilizar el de duplicado.
- **Ventana**: se acepta mientras el inicio esté a 24 horas o más. El borde es inclusivo, al revés que el inicio de la actividad, que rechaza el instante exacto; la asimetría es deliberada y está registrada en el ADR. El reloj se lee dentro de la transacción, no al renderizar.
- **Habilitación**: deshabilitar una actividad frena inscripciones, no cancelaciones. La ventana es la única condición temporal o administrativa para cancelar.
- **Cupo**: la disponibilidad y la validación de capacidad del docente cuentan solo inscripciones vigentes. El mensaje de validación habla de inscripciones vigentes, no de confirmadas.
- **Unicidad**: se mantiene una inscripción por alumno y actividad, vigente o cancelada. Por eso no hay reinscripción: el bloqueo es explícito y tiene su propio mensaje.
- **Precedencia en la inscripción**: una inscripción cancelada se reconoce antes de evaluar habilitación, inicio y cupo, igual que hoy ocurre con el duplicado.
- **HTTP**: ruta de cancelación por actividad, solo `POST` con CSRF, identidad tomada de la sesión y nunca del cuerpo. El resultado se comunica como mensaje flash con una etiqueta que permita estilarlo. `GET` responde 405.
- **Plantillas**: el detalle ofrece el botón con confirmación del navegador solo cuando la inscripción está vigente y dentro de la ventana; fuera de la ventana explica el límite; cancelada muestra el badge, la fecha y el aviso de no reinscripción. "Mis inscripciones" lista las canceladas con su badge y sin botón.
- **Administración**: el instante de cancelación es visible en listado y detalle, y sigue siendo de solo consulta.
- **Datos de demo**: el seed verifica existencia sin filtrar estado, así que ya no recrea canceladas; se agrega cobertura para que esa propiedad no se rompa.
- **Documentación**: el README describe el recorrido con la cancelación, la ventana, la conservación del registro y la ausencia de reinscripción.

## Testing Decisions

- Se prueba comportamiento externo: resultados observables del servicio, respuestas HTTP y estado visible en las páginas. Nada de aserciones sobre detalles internos como el nombre del campo o la forma del `UPDATE`.
- **Seam de servicio** (el principal): todas las reglas de dominio — ventana y sus bordes, actividad deshabilitada, liberación de cupo, repetición de la cancelación, inscripción ajena, bloqueo de reinscripción, contención — con reloj inyectado. Prior art: las pruebas de inscripción existentes en la suite.
- **Seam HTTP**: `GET` 405, `POST` sin CSRF 403, `POST` válido redirige con mensaje y persiste, botón presente o ausente según ventana y estado, y qué muestran el detalle y "Mis inscripciones". Prior art: las pruebas de CSRF, catálogo y "Mis inscripciones" existentes.
- **Seam de concurrencia**: `TransactionTestCase` con archivo real y barrera, como las pruebas actuales de último cupo y duplicado simultáneo. Dos carreras: cancelar mientras otro ocupa el último cupo, y dos cancelaciones simultáneas del mismo alumno.
- No se agregan seams nuevos: no hay pruebas aisladas del campo ni pruebas de plantilla por separado.

## Out of Scope

- Reinscripción después de cancelar; se evalúa más adelante y hoy está bloqueada a propósito.
- Cancelación por parte del docente o del administrador.
- Lista de espera, notificaciones, correo, o asignación del cupo liberado a una persona en particular.
- Auditoría más allá del instante de la cancelación (quién canceló ya está implícito: el dueño).
- Historial de cancelaciones en el catálogo, reportes o exportaciones.
- Cambios en la política de inscripción (ventana de inscripción, cupos, horarios).
- Pruebas de concurrencia a nivel HTTP.

## Further Notes

- Términos del dominio en `GLOSSARY.md`: alumno, actividad, inscripción, cancelación, ventana de cancelación, cupo disponible, docente.
- La decisión de conservar la inscripción cancelada, sus alternativas descartadas y la asimetría del borde están en `docs/adr/0001-inscripciones-canceladas-se-conservan.md`.
- El conteo de pruebas del README queda desactualizado con esta feature; conviene corregirlo en la misma tanda.
- El servicio de inscripción y el de cancelación deben compartir el patrón de contención; si uno cambia, el otro también.
