"""Herramientas de Microsoft Graph (OneNote) para el agente ADK.

Acceso con identidad fija (svc_servinlabs_01@preservinform.onmicrosoft.com):
todos los usuarios del agente ven el mismo OneNote, sin login individual por
usuario. Se usa un refresh_token obtenido una unica vez (ver
scripts/get_service_account_refresh_token.py) y guardado en Secret Manager
como MS_GRAPH_REFRESH_TOKEN, inyectado como variable de entorno en el Agent
Engine. La app de Entra ID es cliente publico (sin client secret), asi que
la renovacion del access token solo necesita client_id + refresh_token.
"""

import base64
import os
import re
import threading
import time
from typing import Optional

import requests

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
_TIMEOUT = 30
_MAX_RETRIES = 4

_TENANT_ID = "c01595bd-a38f-4ffe-b850-67914a7ef848"
_CLIENT_ID = "09b748e7-18b3-4009-9333-b6692f4eb369"
_TOKEN_URL = f"https://login.microsoftonline.com/{_TENANT_ID}/oauth2/v2.0/token"
_REFRESH_TOKEN_ENV = "MS_GRAPH_REFRESH_TOKEN"

_token_lock = threading.Lock()
_cached_access_token: str | None = None
_cached_expires_at: float = 0.0


def _get_token(_tool_context=None) -> str | None:
    """Devuelve un access token de Graph valido, renovandolo si hace falta."""
    global _cached_access_token, _cached_expires_at

    with _token_lock:
        if _cached_access_token and time.time() < _cached_expires_at:
            return _cached_access_token

        refresh_token = os.environ.get(_REFRESH_TOKEN_ENV)
        if not refresh_token:
            return None

        resp = requests.post(
            _TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "client_id": _CLIENT_ID,
                "refresh_token": refresh_token,
                "scope": "https://graph.microsoft.com/Notes.Read offline_access",
            },
            timeout=_TIMEOUT,
        )
        if resp.status_code != 200:
            return None

        payload = resp.json()
        _cached_access_token = payload["access_token"]
        _cached_expires_at = time.time() + payload.get("expires_in", 3600) - 60
        return _cached_access_token


_NEEDS_AUTH_RESPONSE = {
    "status": "error",
    "error_message": "No se pudo obtener acceso a OneNote (revisar MS_GRAPH_REFRESH_TOKEN).",
}


def _graph_get(path: str, token: str, params: dict | None = None) -> requests.Response:
    """GET contra Microsoft Graph con reintentos en throttling (429/503)."""
    url = path if path.startswith("http") else f"{GRAPH_BASE}{path}"
    headers = {"Authorization": f"Bearer {token}"}
    resp = None
    for attempt in range(_MAX_RETRIES):
        resp = requests.get(url, headers=headers, params=params, timeout=_TIMEOUT)
        if resp.status_code in (429, 503):
            wait = int(resp.headers.get("Retry-After", 2**attempt))
            time.sleep(min(wait, 30))
            continue
        break
    resp.raise_for_status()
    return resp


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
                _TAG_RE.sub("", cell).strip()[:50]  # Max 50 chars por celda
                for cell in cells
            ]
            if cell_texts:
                table_lines.append(" | ".join(cell_texts))
                # Agregar separador después de la primera fila (header)
                if row_idx == 0:
                    table_lines.append("|" + "|".join(["---"] * len(cell_texts)) + "|")
        
        if table_lines:
            result.append("\n" + "\n".join(table_lines) + "\n")
    
    return "".join(result)


def _extract_lists_with_structure(html: str) -> str:
    """Preserva listas (ul/ol) con indentación."""
    # Reemplazar items de lista con bullets/números
    result = html
    # Convertir <li> a "- " (bullets) para simplificar
    result = re.sub(r"<li[^>]*>(.*?)</li>", r"- \1\n", result, flags=re.DOTALL | re.IGNORECASE)
    return result


def _extract_images(html: str) -> str:
    """Extrae referencias a imágenes del HTML."""
    images = []
    
    # Buscar imágenes con atributo alt
    for alt_text in _IMG_RE.findall(html):
        if alt_text.strip():
            images.append(f"[IMAGEN: {alt_text}]")
    
    # Buscar imágenes sin alt (pero que existen)
    remaining_imgs = _IMG_NO_ALT_RE.findall(html)
    # Restar las que ya procesamos (rough estimate)
    if len(remaining_imgs) > len(_IMG_RE.findall(html)):
        images.append("[IMAGEN: sin descripción]")
    
    return " ".join(images) if images else ""


def _html_to_text(html: str) -> str:
    """Convierte HTML de OneNote a texto preservando estructura (tablas, listas, imágenes)."""
    # Eliminar scripts y styles
    text = re.sub(r"(?is)<(script|style).*?</\1>", "", html)
    
    # Extraer imágenes antes de eliminar tags
    images_text = _extract_images(text)
    
    # Extraer tablas como Markdown
    tables_text = _extract_table_as_markdown(text)
    
    # Procesar listas
    text = _extract_lists_with_structure(text)
    
    # Eliminar tags HTML restantes
    text = _TAG_RE.sub(" ", text)
    
    # Decodificar entidades HTML
    for ent, ch in (
        ("&nbsp;", " "),
        ("&amp;", "&"),
        ("&lt;", "<"),
        ("&gt;", ">"),
        ("&#39;", "'"),
        ("&quot;", '"'),
    ):
        text = text.replace(ent, ch)
    
    # Normalizar espacios
    text = re.sub(r"[ \t]+", " ", text)
    
    # Construir resultado final
    final = text
    if tables_text:
        final = tables_text + "\n" + final
    if images_text:
        final = final + "\n\n" + images_text
    
    # Limpiar líneas en blanco excesivas
    final = _BLANKLINES_RE.sub("\n\n", final).strip()
    
    return final


def list_notebooks(tool_context=None) -> dict:
    """Lista los cuadernos de OneNote."""
    token = _get_token(tool_context)
    if not token:
        return _NEEDS_AUTH_RESPONSE
    try:
        resp = _graph_get("/me/onenote/notebooks", token, {"$select": "id,displayName"})
        notebooks = [
            {"id": n["id"], "name": n.get("displayName", "")}
            for n in resp.json().get("value", [])
        ]
        return {"status": "success", "notebooks": notebooks}
    except requests.HTTPError as exc:
        return {"status": "error", "error_message": f"Error al leer cuadernos: {exc}"}


def list_pages(search: str = "", tool_context=None) -> dict:
    """Lista paginas de OneNote, opcionalmente filtradas por titulo."""
    token = _get_token(tool_context)
    if not token:
        return _NEEDS_AUTH_RESPONSE
    params = {
        "$select": "id,title",
        "$top": "50",
        "$orderby": "lastModifiedDateTime desc",
    }
    try:
        resp = _graph_get("/me/onenote/pages", token, params)
        pages = [
            {"id": p["id"], "title": p.get("title") or "(sin titulo)"}
            for p in resp.json().get("value", [])
        ]
        if search:
            s = search.lower()
            pages = [p for p in pages if s in p["title"].lower()]
        return {"status": "success", "pages": pages}
    except requests.HTTPError as exc:
        return {"status": "error", "error_message": f"Error al listar paginas: {exc}"}


def get_page_content(page_id: str, tool_context=None) -> dict:
    """Devuelve texto plano del contenido de una pagina de OneNote."""
    token = _get_token(tool_context)
    if not token:
        return _NEEDS_AUTH_RESPONSE
    try:
        resp = _graph_get(f"/me/onenote/pages/{page_id}/content", token)
        text = _html_to_text(resp.text)
        return {"status": "success", "text": text[:20000]}
    except requests.HTTPError as exc:
        return {"status": "error", "error_message": f"Error al leer la pagina: {exc}"}


def _extract_image_urls(html: str) -> list:
    """Extrae URLs de imágenes del HTML con sus descripciones."""
    images = []
    
    # Imágenes con src y alt
    for match in _IMG_SRC_RE.finditer(html):
        src, alt = match.groups()
        if src:
            images.append({"url": src, "alt": alt or "sin descripción"})
    
    # Imágenes solo con src (no alt)
    for match in _IMG_SRC_NO_ALT_RE.finditer(html):
        src = match.group(1)
        if src and not any(img["url"] == src for img in images):
            images.append({"url": src, "alt": "sin descripción"})
    
    return images


def _download_image_as_base64(url: str, token: str) -> Optional[str]:
    """Descarga una imagen de Graph y la convierte a base64.
    
    Returns:
        string base64 de la imagen, o None si hay error.
    """
    try:
        resp = _graph_get(url, token)
        if resp.status_code == 200:
            return base64.b64encode(resp.content).decode("utf-8")
    except Exception:
        pass
    return None


def get_page_content_with_images(page_id: str, tool_context=None) -> dict:
    """Devuelve contenido de página con imágenes en base64 para análisis por Gemini.
    
    Útil cuando el usuario pregunta sobre imágenes, diagramas, etc.
    Las imágenes se descargan solo si existen.
    
    Returns:
        dict con "status", "text" (contenido textual) e "images" (array de dicts
        con "data" en base64, "media_type", "alt"). Si hay error, "error_message".
    """
    token = _get_token(tool_context)
    if not token:
        return _NEEDS_AUTH_RESPONSE
    
    try:
        # Obtener HTML de la página
        resp = _graph_get(f"/me/onenote/pages/{page_id}/content", token)
        html = resp.text
        
        # Extraer texto
        text = _html_to_text(html)
        
        # Extraer URLs de imágenes
        image_urls = _extract_image_urls(html)
        images_data = []
        
        # Descargar imágenes en base64
        for img_info in image_urls:
            url = img_info["url"]
            alt = img_info["alt"]
            
            # Intentar descargar
            b64 = _download_image_as_base64(url, token)
            if b64:
                # Detectar tipo MIME (heurística simple)
                media_type = "image/png"
                if ".jpg" in url.lower() or ".jpeg" in url.lower():
                    media_type = "image/jpeg"
                elif ".gif" in url.lower():
                    media_type = "image/gif"
                elif ".webp" in url.lower():
                    media_type = "image/webp"
                
                images_data.append({
                    "data": b64,
                    "media_type": media_type,
                    "alt": alt
                })
        
        result = {
            "status": "success",
            "text": text[:20000],
            "images": images_data
        }
        
        return result
    except requests.HTTPError as exc:
        return {"status": "error", "error_message": f"Error al leer la pagina: {exc}"}

