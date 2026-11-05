# 02: Listados con historial de reinscripciones

**What to build:** "Mis inscripciones" y el detalle docente muestran todas las filas, incluidas varias de la misma actividad. En "Mis inscripciones" las canceladas conservan badge y fecha, no ofrecen cancelar ni reinscribir directamente, y solo enlazan al detalle; la administración sigue mostrando todas las filas de solo consulta.

**Blocked by:** 01 (reinscribirse desde el detalle)

**Spec:** ../spec.md

**Status:** ready-for-agent

- [ ] "Mis inscripciones" lista todas las filas del alumno, vigentes y canceladas, de más nueva a más vieja, incluidas varias de la misma actividad.
- [ ] Las filas canceladas muestran badge y fecha, no ofrecen cancelar ni un POST directo de reinscripción; solo enlazan al detalle.
- [ ] Las filas vigentes conservan el botón de cancelar dentro de la ventana.
- [ ] El detalle docente lista todas las filas, vigentes primero y canceladas después, con varias filas del mismo alumno.
- [ ] La administración muestra todas las filas con `cancelled_at` y sigue sin permitir altas ni bajas.
- [ ] El aislamiento entre alumnos se mantiene: cada uno ve solo sus propias filas.
- [ ] Las pruebas HTTP cubren los listados con una actividad reinscripta y una cancelada.
