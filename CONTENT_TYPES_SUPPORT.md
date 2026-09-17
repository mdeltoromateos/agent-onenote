# Soporte de tipos de contenido en OneNote (Opción 2)

Versión: 2026-09-16  
Estado: Implementado en `onenote_tools.py` (ambos ubicaciones)

## Resumen de cambios

La función `_html_to_text()` ha sido mejorada para **preservar estructura** de:
1. **Tablas HTML** → Convertidas a Markdown
2. **Listas** (ul/ol) → Preservadas con viñetas "-"
3. **Imágenes** → Extracción de descripción (alt text)

Sin cambios en la interfaz pública: `get_page_content()` sigue devolviendo texto plano (no JSON), pero ahora **estructura preservada**.

## Qué se procesa ahora

### 1. Tablas HTML → Markdown

**Entrada:**
```html
<table>
  <tr><th>Nombre</th><th>Fecha</th></tr>
  <tr><td>Proyecto A</td><td>2026-09-15</td></tr>
  <tr><td>Proyecto B</td><td>2026-09-16</td></tr>
</table>
```

**Salida:**
```
Nombre | Fecha
---|---
Proyecto A | 2026-09-15
Proyecto B | 2026-09-16
```

**Máximo de caracteres por celda:** 50 (evita datos gigantes)

### 2. Listas HTML → Viñetas

**Entrada:**
```html
<ul>
  <li>Tarea 1: Completar diseño</li>
  <li>Tarea 2: Validar con cliente</li>
</ul>
```

**Salida:**
```
- Tarea 1: Completar diseño
- Tarea 2: Validar con cliente
```

**Nota:** No diferencia entre `<ul>` y `<ol>` (ambas se convierten a viñetas "-").

### 3. Imágenes → Referencias de texto

**Entrada:**
```html
<img src="..." alt="Captura de pantalla del flujo">
<img src="...">
```

**Salida:**
```
[IMAGEN: Captura de pantalla del flujo]
[IMAGEN: sin descripción]
```

**Ubicación en texto:** Al final de la página.

## Funciones nuevas en `onenote_tools.py`

| Función | Propósito |
|---------|-----------|
| `_extract_table_as_markdown()` | Busca `<table>` y convierte filas/celdas a Markdown |
| `_extract_lists_with_structure()` | Convierte `<li>` a "- " preservando orden |
| `_extract_images()` | Extrae `<img>` con `alt` y crea referencias |

Todas usan **regex sin dependencias nuevas** (solo `re`, `time`, `requests` como antes).

## Limitaciones conocidas

| Limitación | Razón | Posible workaround |
|------------|-------|-------------------|
| Listas anidadas pierden nivel | Regex simple no captura jerarquía | Usar BeautifulSoup (new dependency) |
| Imágenes no son descargables | Solo se extrae descripción | Nueva tool `get_image` con URL |
| Tablas complejas (rowspan/colspan) | Parsing manual no es trivial | BeautifulSoup |
| Hipervínculos se pierden | Se convierten a texto | Nueva function `_extract_links()` |

## Cómo probar

### 1. Localmente con datos ficticios

Crear página en OneNote con:

```
Página: "Prueba Contenido Avanzado"

# Tabla de ejemplo
| Recurso | Responsable | Fecha límite |
| --- | --- | --- |
| Diseño UI | María | 2026-09-20 |
| Backend | Juan | 2026-09-22 |

# Checklist
- Revisar requisitos
- Configurar entorno
- Ejecutar tests

[Una imagen con descripción aquí]
```

Luego: `python scripts/verify_graph_tools.py --token "<TOKEN>" --search "Prueba Contenido"`

Resultado esperado: Verás tabla en formato Markdown, lista con "-", imagen como "[IMAGEN: ...]"

### 2. Preguntas para validar en el agente remoto

1. **Tabla:** "¿Qué recursos aparecen en la tabla y quién es responsable?"
   - Esperado: Agente lee tabla Markdown y responde estructura

2. **Lista:** "Resume los pasos del checklist."
   - Esperado: Agente lista los items sin perder viñetas

3. **Imagen:** "¿Cuántas imágenes hay en la página?"
   - Esperado: Agente cuenta referencias `[IMAGEN: ...]`

4. **Mixto:** "Resume esta página en formato JSON: recursos, responsables, pasos."
   - Esperado: Agente extrae del texto estructurado correctamente

## Próximos pasos (si se necesita más)

### Opción 3 completa (rich content):
- Nueva tool `get_page_content_rich()` que devuelva JSON con campos:
  ```json
  {
    "text": "contenido textual",
    "tables": [{"headers": [...], "rows": [...]}],
    "images": [{"alt": "...", "url": "..."}],
    "lists": [{"items": [...]}],
    "links": [{"text": "...", "url": "..."}]
  }
  ```

### Mejoras inmediatas (bajo esfuerzo):
- [ ] Detectar `<a href>` y preservar links
- [ ] Diferenciar entre `<ul>` (bullets) y `<ol>` (números)
- [ ] Manejar listas anidadas con indentación

### Mejoras medianas (alto esfuerzo):
- [ ] Agregar BeautifulSoup como dependencia (más robusto)
- [ ] Soportar `<blockquote>`, `<code>`, `<pre>`
- [ ] Descargar imágenes y almacenarlas (reqs memoria/tiempo)

## Validación de sintaxis

Ambos archivos han sido validados:
- `onenote_tools.py` (root)
- `asistente-notas/app/onenote_tools.py`

Regex compiladas al módulo load, sin errores de sintaxis.
