# 05: Verificar las carreras de la cancelación

**What to build:** Pruebas con conexiones reales y barrera de inicio que demuestran que la cancelación es segura frente a la inscripción: cancelar el último cupo mientras otro alumno se inscribe nunca deja dos inscripciones vigentes, y dos cancelaciones simultáneas del mismo alumno producen una cancelación y un aviso de que ya estaba cancelada, con un único instante persistido.

**Blocked by:** 01 (cancelar desde el detalle)

**Spec:** ../spec.md

**Status:** done

- [x] Cancelar el último cupo mientras otro alumno se inscribe nunca deja dos vigentes y el cupo final es consistente en cualquier orden.
- [x] Dos cancelaciones simultáneas del mismo alumno devuelven cancelación y "ya estaba cancelada", con un solo instante persistido.
- [x] La doble cancelación falla de forma reproducible si se quita la transacción `IMMEDIATE` de la cancelación (11 de 15 corridas); la carrera de último cupo queda protegida por la transacción de la inscripción, porque cancelar no crea filas.
- [x] Se reutiliza el patrón existente de concurrencia: conexiones independientes, archivo real, barrera y reloj inyectado.
- [x] La suite completa sigue verde y no quedan conexiones ni archivos abiertos.

## Comments

Implementado en `357e2e4`, integrado en `b252b91`. Ambas carreras usan `TransactionTestCase`, archivo real, barrera y reloj inyectado. Verificación de sabotaje: al reemplazar la transacción de `cancel_registration` por un no-op, la carrera de doble cancelación falla en 11 de 15 corridas, porque ambas leen la inscripción vigente y devuelven "cancelled". La carrera de último cupo no puede detectar esa remoción: cancelar no crea filas, y la unicidad más la validación de capacidad se sostienen con la transacción de la inscripción; se conserva como prueba de consistencia de cupo. Suite completa: 49 pruebas OK.
