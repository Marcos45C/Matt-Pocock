# Catálogo como línea de tiempo

## Pregunta

¿Qué forma debe tener el catálogo de actividades y cómo se propaga ese lenguaje visual al resto de las pantallas?

## Decisión

Se adopta la **variante D — “Línea de tiempo”**: jerarquía “tiempo primero”, riel vertical con puntos, agrupación por día, tarjetas blancas sobre fondo casi blanco, acento índigo y horas en monoespaciada.

El prototipo completo (variantes A/B/C/D, barra de selección y CSS descartable) se conserva como fuente primaria en la rama `prototype/ui-variantes`. La rama principal solo conserva la decisión: D plegada como código de producción.

## Sistema visual

Los tokens viven en un único lugar, `static/styles.css` (`:root`): fondo, superficie, tinta, grises, acento, peligro, radio, tipografías y ancho de columna. Las cuatro pantallas usan los mismos componentes:

- **Catálogo** (`templates/activities/catalog.html`): días agrupados, riel y puntos, hora a la izquierda, cupos como badge pill.
- **Detalle** (`templates/activities/detail.html`): encabezado, datos en `dl` de hechos, panel de estado e inscripción/cancelación.
- **Mis inscripciones** (`templates/activities/mine.html`): misma tarjeta con hora primero y estado.
- **Login** (`templates/registration/login.html`): tarjeta angosta con el mismo encabezado y formulario.

## Hallazgo conservado

`with_availability()` usa `annotate()`, cuyo `GROUP BY` ignora el `Meta.ordering` del modelo. El catálogo mantiene un `.order_by("starts_at", "pk")` explícito porque la agrupación por día depende de ese orden; la prueba `test_catalog_orders_by_start_time` lo fija.

## Textos que la suite verifica

`2 cupos disponibles`, `Cancelar inscripción`, `Inscripción cancelada el DD/MM/AAAA HH:MM` y `hasta 24 horas antes del inicio` siguen presentes en el HTML.
