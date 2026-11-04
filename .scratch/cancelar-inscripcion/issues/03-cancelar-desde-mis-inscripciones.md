# 03: Cancelar desde "Mis inscripciones"

**What to build:** El alumno cancela sin tener que buscar la actividad en el catálogo. En "Mis inscripciones" cada inscripción vigente dentro de la ventana ofrece el botón de cancelar; las canceladas siguen listadas con su badge y su fecha, sin botón.

**Blocked by:** 01 (cancelar desde el detalle)

**Spec:** ../spec.md

**Status:** done

- [x] La lista muestra las inscripciones canceladas con badge y fecha, y sin botón.
- [x] Las inscripciones vigentes dentro de la ventana ofrecen cancelar desde la lista, con confirmación y mensaje de resultado.
- [x] Las inscripciones vigentes fuera de la ventana no ofrecen el botón.
- [x] Cada alumno sigue viendo solo sus propias inscripciones, canceladas incluidas.
- [x] Pruebas HTTP cubren los tres estados de la lista y el aislamiento entre alumnos.

## Comments

Implementado en `48068ba`, integrado en `fa4afb6`. La lista evalúa la ventana con un solo instante por request y el helper `can_cancel`; el formulario de cancelación se comparte con el detalle. Cancelar desde la lista redirige al detalle con el mensaje flash: la revisión de código quitó el destino de retorno `next=mine` por ser alcance no pedido por el spec. Suite completa: 49 pruebas OK.
