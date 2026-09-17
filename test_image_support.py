#!/usr/bin/env python
"""
Test de funcionalidad de imágenes - Valida que get_page_content_with_images
funciona correctamente con HTML que contiene imágenes.

Simula el behavior sin necesidad de Agent Engine.
"""

import base64
import sys
import re

# Copiar las funciones necesarias para prueba local
_TAG_RE = re.compile(r"<[^>]+>")
_BLANKLINES_RE = re.compile(r"\n\s*\n+")
_TABLE_RE = re.compile(r"<table[^>]*>.*?</table>", re.DOTALL | re.IGNORECASE)
_IMG_RE = re.compile(r"<img[^>]*alt=['\"]([^'\"]*)['\"][^>]*>", re.IGNORECASE)
_IMG_NO_ALT_RE = re.compile(r"<img[^>]*>", re.IGNORECASE)
_IMG_SRC_RE = re.compile(r"<img[^>]*src=['\"]([^'\"]*)['\"][^>]*alt=['\"]([^'\"]*)['\"][^>]*>", re.IGNORECASE)
_IMG_SRC_NO_ALT_RE = re.compile(r"<img[^>]*src=['\"]([^'\"]*)['\"][^>]*>", re.IGNORECASE)
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


def _extract_image_urls(html: str) -> list[dict]:
    """Extrae URLs de imágenes del HTML con sus descripciones."""
    images = []
    
    for match in _IMG_SRC_RE.finditer(html):
        src, alt = match.groups()
        if src:
            images.append({"url": src, "alt": alt or "sin descripción"})
    
    for match in _IMG_SRC_NO_ALT_RE.finditer(html):
        src = match.group(1)
        if src and not any(img["url"] == src for img in images):
            images.append({"url": src, "alt": "sin descripción"})
    
    return images


def _create_mock_image_base64(description: str) -> str:
    """Crea una imagen PNG mínima para testing (1x1 pixel)."""
    # PNG válido 1x1 pixel rojo (sin dependencias)
    png_hex = "89504e470d0a1a0a0000000d494844520000000100000001080206000090773db30000000c4944415408d76200f0df0000000049454e44ae426082"
    return base64.b64encode(bytes.fromhex(png_hex)).decode("utf-8")


# ============================================================================
# TESTS
# ============================================================================

def test_1_image_url_extraction():
    """Test: Extracción de URLs de imágenes del HTML"""
    html = """
    <p>Primera imagen:</p>
    <img src="https://example.com/diagram.png" alt="Diagrama de arquitectura">
    <p>Segunda imagen sin alt:</p>
    <img src="https://example.com/photo.jpg">
    """
    
    urls = _extract_image_urls(html)
    assert len(urls) == 2
    assert urls[0]["url"] == "https://example.com/diagram.png"
    assert urls[0]["alt"] == "Diagrama de arquitectura"
    assert urls[1]["url"] == "https://example.com/photo.jpg"
    assert urls[1]["alt"] == "sin descripción"
    print("✓ Test 1 (Extracción URLs): PASS")
    print(f"  Imágenes encontradas: {len(urls)}\n")


def test_2_mock_image_base64():
    """Test: Generación de imagen mock en base64"""
    b64 = _create_mock_image_base64("test image")
    assert isinstance(b64, str), "b64 debe ser string"
    assert len(b64) > 50, f"b64 debe ser > 50 chars, got {len(b64)}"
    
    # Validar que es decodificable
    try:
        decoded = base64.b64decode(b64)
        assert len(decoded) > 0, "decoded image debe tener contenido"
    except Exception as e:
        raise AssertionError(f"No se puede decodificar base64: {e}")
    
    print("✓ Test 2 (Mock Base64): PASS")
    print(f"  Imagen base64: {len(b64)} caracteres\n")


def test_3_page_with_mixed_content_and_images():
    """Test: Página con texto, tabla, lista e imágenes"""
    html = """
    <h2>Reunión Sprint 24</h2>
    <p>Resumen de tareas asignadas:</p>
    
    <table>
        <tr><th>Recurso</th><th>Responsable</th><th>Estado</th></tr>
        <tr><td>Backend API</td><td>Carlos</td><td>En progreso</td></tr>
    </table>
    
    <p>Puntos acordados:</p>
    <ul>
        <li>Validar con cliente antes de viernes</li>
        <li>Preparar demo para Monday</li>
    </ul>
    
    <p>Diagrama del flujo:</p>
    <img src="https://graph.onedrive.com/v1/flows.png" alt="Flujo de procesamiento">
    <img src="https://graph.onedrive.com/v1/arch.jpg">
    """
    
    # Extraer texto
    text = _html_to_text(html)
    
    # Extraer URLs
    urls = _extract_image_urls(html)
    
    # Validaciones
    assert "Reunión Sprint 24" in text
    assert "Carlos" in text
    assert "- Validar con cliente" in text
    assert "[IMAGEN: Flujo de procesamiento]" in text
    assert len(urls) == 2
    
    print("✓ Test 3 (Contenido mixto): PASS")
    print(f"  Texto (primeros 200 chars): {text[:200]}...")
    print(f"  Imágenes encontradas: {len(urls)}\n")


def test_4_gemini_compatible_response():
    """Test: Respuesta compatible con Gemini (texto + imágenes base64)"""
    html = """
    <h1>Diagrama de arquitectura</h1>
    <p>Sistema con tres capas:</p>
    <img src="https://example.com/arch-v2.png" alt="Arquitectura de 3 capas">
    <p>Descripción técnica aquí.</p>
    """
    
    # Simular response que devolvería get_page_content_with_images
    text = _html_to_text(html)
    urls = _extract_image_urls(html)
    
    response = {
        "status": "success",
        "text": text[:20000],
        "images": []
    }
    
    # Mock: descargar y convertir imágenes a base64
    for img in urls:
        b64 = _create_mock_image_base64(img["alt"])
        response["images"].append({
            "data": b64,
            "media_type": "image/png",
            "alt": img["alt"]
        })
    
    # Validar estructura
    assert response["status"] == "success"
    assert "Diagrama de arquitectura" in response["text"]
    assert len(response["images"]) == 1
    assert "data" in response["images"][0]
    assert "media_type" in response["images"][0]
    assert "alt" in response["images"][0]
    
    print("✓ Test 4 (Response Gemini-compatible): PASS")
    print(f"  Status: {response['status']}")
    print(f"  Texto: {len(response['text'])} chars")
    print(f"  Imágenes: {len(response['images'])} items")
    print(f"  Imagen 0 - alt: {response['images'][0]['alt']}")
    print(f"  Imagen 0 - data: {response['images'][0]['data'][:50]}...\n")


def run_all_tests():
    """Ejecuta todos los tests"""
    print("=" * 70)
    print("TEST SUITE: Soporte de imágenes en OneNote Agent")
    print("=" * 70 + "\n")
    
    tests = [
        test_1_image_url_extraction,
        test_2_mock_image_base64,
        test_3_page_with_mixed_content_and_images,
        test_4_gemini_compatible_response,
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
            print(f"  Exception: {type(e).__name__}: {e}\n")
            failed += 1
    
    print("=" * 70)
    print(f"RESULTADOS: {passed} PASS, {failed} FAIL")
    print("=" * 70)
    
    if failed == 0:
        print("\n✅ TODOS LOS TESTS PASARON")
        print("\nProxima acción: prueba local con 'adk web' o despliegue remoto")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
