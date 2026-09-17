#!/usr/bin/env python
"""
Validación de funciones mejoradas de HTML parsing en onenote_tools.py
Demuestra conversión de:
- Tablas HTML → Markdown
- Listas → Viñetas
- Imágenes → Referencias
"""

import re
import sys

# Copiar las funciones del archivo onenote_tools para validación local
_TAG_RE = re.compile(r"<[^>]+>")
_BLANKLINES_RE = re.compile(r"\n\s*\n+")
_TABLE_RE = re.compile(r"<table[^>]*>.*?</table>", re.DOTALL | re.IGNORECASE)
_IMG_RE = re.compile(r"<img[^>]*alt=['\"]([^'\"]*)['\"][^>]*>", re.IGNORECASE)
_IMG_NO_ALT_RE = re.compile(r"<img[^>]*>", re.IGNORECASE)
_LI_RE = re.compile(r"<li[^>]*>(.*?)</li>", re.DOTALL | re.IGNORECASE)
_UL_OL_RE = re.compile(r"<(?:ul|ol)[^>]*>(.*?)</(?:ul|ol)>", re.DOTALL | re.IGNORECASE)


def _extract_table_as_markdown(html: str) -> str:
    """Extrae tablas HTML y las convierte a Markdown."""
    tables = _TABLE_RE.findall(html)
    if not tables:
        return ""
    
    result = []
    for table_html in tables:
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table_html, re.DOTALL | re.IGNORECASE)
        if not rows:
            continue
        
        table_lines = []
        for row_idx, row_html in enumerate(rows):
            cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row_html, re.DOTALL | re.IGNORECASE)
            cell_texts = [
                _TAG_RE.sub("", cell).strip()[:50]
                for cell in cells
            ]
            if cell_texts:
                table_lines.append(" | ".join(cell_texts))
                if row_idx == 0:
                    table_lines.append("|" + "|".join(["---"] * len(cell_texts)) + "|")
        
        if table_lines:
            result.append("\n" + "\n".join(table_lines) + "\n")
    
    return "".join(result)


def _extract_lists_with_structure(html: str) -> str:
    """Preserva listas (ul/ol) con viñetas."""
    result = html
    result = re.sub(r"<li[^>]*>(.*?)</li>", r"- \1\n", result, flags=re.DOTALL | re.IGNORECASE)
    return result


def _extract_images(html: str) -> str:
    """Extrae referencias a imágenes del HTML."""
    images = []
    for alt_text in _IMG_RE.findall(html):
        if alt_text.strip():
            images.append(f"[IMAGEN: {alt_text}]")
    
    remaining_imgs = _IMG_NO_ALT_RE.findall(html)
    if len(remaining_imgs) > len(_IMG_RE.findall(html)):
        images.append("[IMAGEN: sin descripción]")
    
    return " ".join(images) if images else ""


def _html_to_text(html: str) -> str:
    """Convierte HTML de OneNote a texto preservando estructura."""
    text = re.sub(r"(?is)<(script|style).*?</\1>", "", html)
    images_text = _extract_images(text)
    tables_text = _extract_table_as_markdown(text)
    text = _extract_lists_with_structure(text)
    text = _TAG_RE.sub(" ", text)
    
    for ent, ch in (("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"),
                    ("&gt;", ">"), ("&#39;", "'"), ("&quot;", '"')):
        text = text.replace(ent, ch)
    
    text = re.sub(r"[ \t]+", " ", text)
    final = text
    if tables_text:
        final = tables_text + "\n" + final
    if images_text:
        final = final + "\n\n" + images_text
    
    final = _BLANKLINES_RE.sub("\n\n", final).strip()
    return final


# ============================================================================
# PRUEBAS
# ============================================================================

def test_1_table_extraction():
    """Test: Conversión de tabla HTML a Markdown"""
    html = """
    <table>
        <tr><th>Recurso</th><th>Responsable</th><th>Fecha</th></tr>
        <tr><td>Diseño UI</td><td>María García</td><td>2026-09-20</td></tr>
        <tr><td>Backend API</td><td>Juan López</td><td>2026-09-22</td></tr>
    </table>
    """
    result = _extract_table_as_markdown(html)
    assert "Recurso | Responsable | Fecha" in result
    assert "---|---|---" in result
    assert "Diseño UI | María García | 2026-09-20" in result
    print("✓ Test 1 (Tablas): PASS")
    print(f"  Resultado:\n{result}\n")


def test_2_list_extraction():
    """Test: Conversión de listas HTML a viñetas"""
    html = """
    <ul>
        <li>Revisar requisitos</li>
        <li>Configurar entorno de desarrollo</li>
        <li>Ejecutar test suite</li>
    </ul>
    """
    result = _extract_lists_with_structure(html)
    assert "- Revisar requisitos" in result
    assert "- Configurar entorno de desarrollo" in result
    print("✓ Test 2 (Listas): PASS")
    print(f"  Resultado:\n{result}\n")


def test_3_image_extraction():
    """Test: Extracción de imágenes con descripción"""
    html = """
    <p>Aquí está la captura:</p>
    <img src="cap1.png" alt="Flujo de autenticación OAuth">
    <img src="cap2.png">
    <p>Fin de contenido.</p>
    """
    result = _extract_images(html)
    assert "[IMAGEN: Flujo de autenticación OAuth]" in result
    print("✓ Test 3 (Imágenes): PASS")
    print(f"  Resultado: {result}\n")


def test_4_mixed_content():
    """Test: Contenido mixto (tabla + lista + imagen + texto)"""
    html = """
    <h2>Reunión de Sprint</h2>
    <p>Estos son los items de esta semana:</p>
    
    <table>
        <tr><th>Tarea</th><th>Responsable</th></tr>
        <tr><td>Implementar login</td><td>Carlos</td></tr>
    </table>
    
    <p>Acuerdos tomados:</p>
    <ul>
        <li>Daily a las 9:30 AM</li>
        <li>Review cada jueves</li>
    </ul>
    
    <p>Aquí el diagrama:</p>
    <img src="arch.png" alt="Arquitectura del sistema">
    """
    
    result = _html_to_text(html)
    assert "Tarea | Responsable" in result
    assert "- Daily a las 9:30 AM" in result
    assert "[IMAGEN: Arquitectura del sistema]" in result
    assert "Reunión de Sprint" in result
    print("✓ Test 4 (Contenido mixto): PASS")
    print(f"  Resultado (primeras 500 chars):\n{result[:500]}...\n")


def test_5_entity_decoding():
    """Test: Decodificación de entidades HTML"""
    html = "<p>Código: &lt;script&gt; &amp; &quot;test&quot; &nbsp; acceso</p>"
    result = _html_to_text(html)
    assert "Código: <script> & \"test\"" in result
    print("✓ Test 5 (Entidades HTML): PASS")
    print(f"  Resultado: {result}\n")


def run_all_tests():
    """Ejecuta todos los tests de validación"""
    print("=" * 60)
    print("VALIDACIÓN DE MEJORAS HTML PARSING EN onenote_tools.py")
    print("=" * 60 + "\n")
    
    tests = [
        test_1_table_extraction,
        test_2_list_extraction,
        test_3_image_extraction,
        test_4_mixed_content,
        test_5_entity_decoding,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test_func.__name__}: FAIL")
            print(f"  Error: {e}\n")
            failed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__}: ERROR")
            print(f"  Exception: {e}\n")
            failed += 1
    
    print("=" * 60)
    print(f"RESULTADOS: {passed} PASS, {failed} FAIL")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
