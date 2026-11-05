# 02: Listados con historial de reinscripciones

**What to build:** "Mis inscripciones" y el detalle docente muestran todas las filas, incluidas varias de la misma actividad. En "Mis inscripciones" las canceladas conservan badge y fecha, no ofrecen cancelar ni reinscribir directamente, y solo enlazan al detalle; la administración sigue mostrando todas las filas de solo consulta.

**Blocked by:** 01 (reinscribirse desde el detalle)

**Spec:** ../spec.md

**Status:** done

- [x] "Mis inscripciones" lista todas las filas del alumno, vigentes y canceladas, de más nueva a más vieja, incluidas varias de la misma actividad.
- [x] Las filas canceladas muestran badge y fecha, no ofrecen cancelar ni un POST directo de reinscripción; solo enlazan al detalle.
- [x] Las filas vigentes conservan el botón de cancelar dentro de la ventana.
- [x] El detalle docente lista todas las filas, vigentes primero y canceladas después, con varias filas del mismo alumno.
- [x] La administración muestra todas las filas con `cancelled_at` y sigue sin permitir altas ni bajas.
- [x] El aislamiento entre alumnos se mantiene: cada uno ve solo sus propias filas.
- [x] Las pruebas HTTP cubren los listados con una actividad reinscripta y una cancelada.

## Comments

Implementado en la rama `ticket/listados-con-historial`. El comportamiento de los listados ya estaba cubierto por la implementación previa; se agregaron pruebas HTTP que lo fijan: `mis inscripciones` lista las filas vigente y cancelada de una actividad reinscripta de más nueva a más vieja, sin POST de reinscripción ni cancelación en la fila cancelada y aislada de otros alumnos; el detalle docente muestra ambas filas con la vigente primero; la administración muestra todas las filas con `cancelled_at` y sigue bloqueando altas. `./scripts/check.sh` pasa con 73 pruebas OK.
