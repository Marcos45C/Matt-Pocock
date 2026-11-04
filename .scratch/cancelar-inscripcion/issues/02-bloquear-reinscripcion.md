# 02: Impedir la reinscripción sobre una inscripción cancelada

**What to build:** Un alumno que canceló no puede volver a inscribirse en esa actividad. Si lo intenta, recibe un mensaje propio —"cancelaste tu inscripción; no podés volver a inscribirte"— en lugar del "ya estás inscripto", y el detalle de la actividad se lo explica sin ofrecer el formulario. Vale aunque la actividad esté llena, deshabilitada o ya haya empezado.

**Blocked by:** 01 (cancelar desde el detalle)

**Spec:** ../spec.md

**Status:** done

- [x] Inscribirse sobre una inscripción cancelada devuelve el resultado propio de cancelación previa y no crea ninguna fila.
- [x] El bloqueo se evalúa antes que habilitación, inicio y cupo, igual que el duplicado actual.
- [x] El mensaje distingue "cancelaste tu inscripción" de "ya estás inscripto".
- [x] El detalle de una cancelada no ofrece el formulario y avisa que no puede reinscribirse.
- [x] Pruebas de servicio y HTTP cubren el bloqueo en actividad llena, deshabilitada e iniciada.

## Comments

Implementado en `09af218`, integrado en `feat/cancelar-inscripcion`. Resultado propio `previously_cancelled` evaluado antes de habilitación, inicio y cupo; mensaje distinto y detalle sin formulario. La cobertura HTTP recorre actividad llena, deshabilitada e iniciada. Suite completa: 49 pruebas OK.
