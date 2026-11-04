# Coding Standards

Reglas que el revisor aplica al diff. Son decisiones de juicio: lo que se pueda verificar con una herramienta va a una herramienta, no acá.

- **Las reglas de negocio se comunican como resultados, no como excepciones.** Las operaciones del servicio devuelven un código de resultado; las excepciones quedan para fallas inesperadas.
- **La disponibilidad se deriva.** Se calcula desde las inscripciones vigentes en el momento de leerla; no se guarda un contador que pueda desincronizarse.
- **Toda mutación es `POST` con CSRF.** La identidad sale de la sesión, nunca del cuerpo del formulario ni de la URL.
- **La contención se traduce, lo demás se propaga.** Solo la contención conocida de la base se convierte en un resultado reintentable; cualquier otro error sube sin disfrazarse.
- **Vocabulario del dominio.** Identificadores en inglés como el resto del modelo; nombres visibles, mensajes y comentarios en español, con los términos de `GLOSSARY.md`.
- **Las pruebas verifican comportamiento externo en los seams existentes.** Servicio y HTTP antes que detalles internos; el ORM se mockea solo para simular contención.
