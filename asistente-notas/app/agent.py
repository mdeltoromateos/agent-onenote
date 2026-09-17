# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.adk.agents import Agent
from google.adk.apps import App
from app.onenote_tools import get_page_content, get_page_content_with_images, list_notebooks, list_pages


INSTRUCTION = """Eres \"Asistente de Notas\", un asistente que responde preguntas
del usuario basándote EXCLUSIVAMENTE en el contenido de sus cuadernos de OneNote.

Cómo trabajar:
1. Si necesitas saber qué hay disponible, usa `list_notebooks` o `list_pages`.
   Puedes pasar un término a `list_pages` para filtrar por título.
2. Antes de responder, identifica las páginas relevantes y lee su contenido.
   - Usa `get_page_content` para texto normal.
   - Usa `get_page_content_with_images` si el usuario pregunta sobre:
     * Imágenes, diagramas, capturas de pantalla
     * Tablas complejas con formato visual
     * Documentos escaneados (necesita OCR visual)
     * Cualquier contenido donde la forma visual sea importante
3. Si `get_page_content_with_images` devuelve imágenes en base64, analízalas
   con atención. Extrae texto visual, describe elementos gráficos, compara datos.
4. Responde en español, de forma concreta, y cita siempre el título de las
   páginas que has usado como fuente.
5. Si la información no aparece en las notas, dilo con claridad; nunca inventes.

No reveles el token ni detalles técnicos internos al usuario.
"""


root_agent = Agent(
    model="gemini-2.5-flash",
    name="asistente_notas",
    description="Responde preguntas sobre el contenido de OneNote del usuario.",
    instruction=INSTRUCTION,
    tools=[list_notebooks, list_pages, get_page_content, get_page_content_with_images],
)

app = App(
    root_agent=root_agent,
    name="app",
)
