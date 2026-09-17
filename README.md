# Asistente de Notas — versión ADK / Agent Engine

Versión en **ADK** del asistente que responde preguntas sobre el contenido de
OneNote del usuario. Equivale a la *Opción 5* del documento de investigación
(ADK propio desplegable en Vertex AI Agent Engine).

## Qué hay aquí

- `agent.py` — define `root_agent` (un `Agent` de ADK con `gemini-2.5-flash`) y
  le conecta las tres herramientas de OneNote.
- `onenote_tools.py` — las herramientas que llaman a Microsoft Graph:
  `list_notebooks`, `list_pages`, `get_page_content`. Incluyen reintentos ante
  el throttling de la OneNote API y conversión de HTML a texto.
- `requirements.txt` — dependencias.

## Arquitectura (importante)

Un agente en Agent Engine se ejecuta **server-side y sin navegador**, así que no
puede hacer el redirect de OAuth contra Entra él mismo. El reparto es:

1. **Frontend** (puedes reutilizar la app que ya desplegaste con AI Studio):
   hace el login MSAL contra Entra ID, obtiene el **access token de Graph**
   (scope `Notes.Read`) y al invocar al agente lo pasa en el **estado de la
   sesión**, en la clave `ms_graph_token`.
2. **Agente ADK**: sus herramientas leen ese token de
   `tool_context.state["ms_graph_token"]` y llaman a Graph en nombre del usuario.

El token nunca se hardcodea ni se guarda en el agente; viaja por sesión.

### Cómo inyecta el token el frontend (boceto)

Con el SDK de Agent Engine, al crear la sesión:

```python
session = remote_app.create_session(
    user_id=user_id,
    state={"ms_graph_token": graph_access_token},  # token MSAL del usuario
)
for event in remote_app.stream_query(
    user_id=user_id, session_id=session["id"], message=pregunta_del_usuario
):
    ...
```

Si el token caduca a mitad de conversación, refréscalo en el frontend (MSAL,
`offline_access`) y actualiza el estado de la sesión.

## Configuracion de la app de Entra ID

Datos ya definidos para el registro:

- Tenant ID: `c01595bd-a38f-4ffe-b850-67914a7ef848`
- Client ID: `09b748e7-18b3-4009-9333-b6692f4eb369`
- Permiso delegado de Graph: `Notes.Read`

Lo que sigue faltando para dejarla cerrada:

- La URL exacta del frontend para registrar la redirect URI.
- Saber si el frontend sera SPA/public client o una app web confidencial.

Regla practica:

- Si es una SPA, normalmente no hace falta client secret.
- Si es una app web con backend, el client secret debe ir fuera del codigo, por
  ejemplo en Secret Manager o variables de entorno.

Si se usa localmente, la redirect URI tipica suele ser algo como
`http://localhost:3000` o el puerto real del frontend; hay que registrar la que
use de verdad la app.

## Probar en local

```bash
pip install -r requirements.txt
adk web   # abre la UI de desarrollo de ADK
```

En la UI de `adk web` puedes fijar manualmente el estado de sesión
`ms_graph_token` con un token de prueba (lo puedes sacar del flujo MSAL del
frontend o de Graph Explorer) para validar las herramientas sin desplegar.

## Desplegar en Agent Engine (con agent-starter-pack)

La forma alineada con tu Opción 2: scaffolding con el pack y meter este agente.

```bash
uvx agent-starter-pack create asistente-notas -d agent_engine -a adk@base
# copiar agent.py y onenote_tools.py dentro del paquete del agente generado
# añadir 'requests' a las dependencias del pyproject que genera el pack
cd asistente-notas
make deploy
```

### Dos ajustes que NO debes olvidar

- **Modelo**: usa `gemini-2.5-flash`. Las plantillas suelen traer
  `gemini-3-flash-preview`, al que tu proyecto no tiene acceso y hace fallar al
  agente en la primera consulta. (`grep -r "preview" .` para localizarlo.)
- **`min_instances=0`**: por defecto el pack deja `min_instances=1`, que con la
  config por defecto (4 vCPU, 8 GB) cuesta ~272 €/mes aunque nadie lo use.
  Bájalo a 0 para el PoC (asume un cold start de ~5-15 s).

## Coste

- Despliegue: 0 €.
- En reposo con `min_instances=0`: ~0 €.
- En uso: runtime del Engine + tokens de Gemini + (si los usas) sesiones/Memory
  Bank y Vertex AI Search.
- Microsoft Graph / OneNote (delegado): gratis con la licencia Entra ID Free.

## Alternativa más barata para este caso

Si el objetivo es solo el chat sobre OneNote, este mismo ADK corre dentro de un
**Cloud Run** (con tu propio runner o `adk api_server`) en lugar de Agent
Engine, escalando a cero. Sale más barato y te ahorra el frontend separado.
Agent Engine solo compensa si necesitas sus capacidades (memoria persistente,
observabilidad de agentes) o tráfico constante.
