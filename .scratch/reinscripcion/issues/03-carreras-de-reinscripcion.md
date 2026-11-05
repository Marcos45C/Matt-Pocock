# 03: Carreras de la reinscripción

**What to build:** Pruebas con conexiones reales y barrera de inicio que demuestran que la reinscripción es segura: dos reinscripciones simultáneas del mismo alumno no dejan dos vigentes, y una reinscripción contra el último cupo nunca sobrevende la capacidad.

**Blocked by:** 01 (reinscribirse desde el detalle)

**Spec:** ../spec.md

**Status:** ready-for-agent

- [ ] Dos reinscripciones simultáneas del mismo alumno después de una cancelación devuelven `registered` y `already_registered`, dejan una sola vigente y dos filas en total (una cancelada y una vigente), con la disponibilidad consistente.
- [ ] Reinscripción contra el último cupo: con capacidad 1 y una cancelada de Ana, la carrera entre la reinscripción de Ana y la inscripción de Bruno devuelve `registered` y `full` en cualquier orden, deja una sola vigente y disponibilidad 0.
- [ ] Se reutiliza el patrón existente: `TransactionTestCase`, archivo real, conexiones independientes, barrera, reloj inyectado y `close_old_connections`.
- [ ] Las pruebas fallan de forma reproducible si se quita la protección correspondiente (transacción `IMMEDIATE` o unique parcial), o se documenta por qué la carrera queda cubierta por otra protección.
- [ ] La suite completa sigue verde y no quedan conexiones ni archivos abiertos.
