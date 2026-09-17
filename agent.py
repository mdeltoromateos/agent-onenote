"""Asistente de Notas — Agente ADK que responde sobre el contenido de OneNote.

Equivale a la "Opción 5" del documento de investigación: ADK propio desplegable
en Vertex AI Agent Engine (o en Cloud Run con `adk web` / runner propio).

Acceso a OneNote DELEGADO por usuario. El access token de Microsoft Graph se
inyecta por sesión en `tool_context.state["ms_graph_token"]` desde el frontend,
que es quien gestiona el login MSAL contra Entra ID (scope Notes.Read).
"""
from google.adk.agents import Agent

from onenote_tools import list_notebooks, list_pages, get_page_content

INSTRUCTION = """Eres "Asistente de Notas", un asistente que responde preguntas
del usuario basándote EXCLUSIVAMENTE en el contenido de sus cuadernos de OneNote.

Cómo trabajar:
1. Si necesitas saber qué hay disponible, usa `list_notebooks` o `list_pages`.
   Puedes pasar un término a `list_pages` para filtrar por título.
2. Antes de responder, identifica las páginas relevantes y lee su contenido con
   `get_page_content`. No respondas de memoria: lee primero.
3. Responde en español, de forma concreta, y cita siempre el título de las
   páginas que has usado como fuente.
4. Si la información no aparece en las notas, dilo con claridad; nunca inventes.

No reveles el token ni detalles técnicos internos al usuario.
"""

root_agent = Agent(
    model="gemini-2.5-flash",  # NO usar modelos en preview (gemini-3-*-preview falla)
    name="asistente_notas",
    description="Responde preguntas sobre el contenido de los cuadernos de OneNote del usuario.",
    instruction=INSTRUCTION,
    tools=[list_notebooks, list_pages, get_page_content],
)
