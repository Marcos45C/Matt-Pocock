# 04: README y verificación final

**What to build:** El README deja de decir que no hay reinscripción y describe la regla nueva con su recorrido, su historial y el conteo de pruebas actualizado. La verificación final comprueba que no quedan mensajes del bloqueo anterior en el código, las plantillas ni el README.

**Blocked by:** 01, 02, 03

**Spec:** ../spec.md

**Status:** done

- [x] La sección "Cancelar una inscripción" del README dice que la reinscripción está permitida, que crea una fila nueva, que conserva la cancelada y que sigue las reglas de habilitación, inicio y cupo.
- [x] El README describe que el detalle muestra la última cancelación y el formulario normal con "Inscribirme", y que "Mis inscripciones" conserva todo el historial.
- [x] El recorrido del README incluye cancelar y reinscribir, y el conteo de pruebas coincide con la suite final.
- [x] No quedan `previously_cancelled` ni el texto "no vas a poder volver a inscribirte" en código, plantillas o README.
- [x] El README, el glosario y el ADR 0002 no se contradicen.
- [x] `./scripts/check.sh` pasa: system check, verificación de migraciones y suite completa.
## Comments

README actualizado en `6fdd771`: la reinscripción está permitida, el recorrido incluye volver a inscribirse y el conteo de pruebas es 75. Verificación de restos: el grep solo encuentra una aserción negativa en `test_views.py` que comprueba que la confirmación de cancelar ya no promete el bloqueo; es intencional. `./scripts/check.sh` pasa con 75 pruebas OK.