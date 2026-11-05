# 04: README y verificación final

**What to build:** El README deja de decir que no hay reinscripción y describe la regla nueva con su recorrido, su historial y el conteo de pruebas actualizado. La verificación final comprueba que no quedan mensajes del bloqueo anterior en el código, las plantillas ni el README.

**Blocked by:** 01, 02, 03

**Spec:** ../spec.md

**Status:** ready-for-agent

- [ ] La sección "Cancelar una inscripción" del README dice que la reinscripción está permitida, que crea una fila nueva, que conserva la cancelada y que sigue las reglas de habilitación, inicio y cupo.
- [ ] El README describe que el detalle muestra la última cancelación y el formulario normal con "Inscribirme", y que "Mis inscripciones" conserva todo el historial.
- [ ] El recorrido del README incluye cancelar y reinscribir, y el conteo de pruebas coincide con la suite final.
- [ ] No quedan `previously_cancelled` ni el texto "no vas a poder volver a inscribirte" en código, plantillas o README.
- [ ] El README, el glosario y el ADR 0002 no se contradicen.
- [ ] `./scripts/check.sh` pasa: system check, verificación de migraciones y suite completa.
