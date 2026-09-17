# asistente-notas

Asistente ADK que responde preguntas sobre OneNote del usuario llamando a Microsoft Graph.

## Arquitectura de auth (Microsoft Graph)

- El login de Entra/MSAL ocurre en frontend.
- El frontend pasa el access token de Graph en el estado de sesion: `ms_graph_token`.
- Las tools del agente leen ese token desde `tool_context.state["ms_graph_token"]`.
- El agente no guarda ni hardcodea tokens.

## Estructura relevante

```
asistente-notas/
├── app/
│   ├── agent.py                 # Root agent (gemini-2.5-flash)
│   ├── onenote_tools.py         # list_notebooks/list_pages/get_page_content
│   ├── agent_engine_app.py      # Wrapper para Agent Engine
│   └── app_utils/deploy.py      # Script de despliegue (min_instances=0)
├── scripts/
│   └── verify_graph_tools.py    # Prueba local tools con token de Graph
├── deployment_metadata.json     # Guarda el resource name del Engine desplegado
├── Makefile
└── pyproject.toml
```

## Scaffold (referencia)

Comando pedido originalmente:

```bash
uvx agent-starter-pack create asistente-notas -d agent_engine -a adk@base
```

En agent-starter-pack `0.41.3`, `adk@base` no existe. Equivalente funcional usado:

```bash
uvx agent-starter-pack create asistente-notas -d agent_engine -a adk -y
```

## Requisitos

- Google Cloud SDK autenticado y con proyecto por defecto.
- ADC configurado para librerias Python:

```bash
gcloud auth application-default login
gcloud config set project <GCP_PROJECT_ID>
```

- `uv` y `make` disponibles.

## Despliegue exacto (Agent Engine)

```bash
cd asistente-notas
make install
make deploy
```

Notas importantes del despliegue:

- Modelo configurado: `gemini-2.5-flash` (sin preview).
- Region por defecto: `europe-west1` (cumple restriccion de ejecutar en Europa).
- `min_instances` por defecto: `0` para evitar coste idle.

Al terminar `make deploy`, el resource name del Engine queda en `deployment_metadata.json` en `remote_agent_engine_id`.

## Borrado exacto del Engine (evitar coste acumulado)

Opcion 1, por Python SDK leyendo `deployment_metadata.json`:

```bash
cd asistente-notas
uv run python -c "import json,vertexai; from vertexai import agent_engines; d=json.load(open('deployment_metadata.json','r',encoding='utf-8')); rn=d.get('remote_agent_engine_id'); assert rn and rn!='None', 'No hay engine desplegado en deployment_metadata.json'; vertexai.init(); ae=agent_engines.get(rn); ae.delete(); print('Deleted:', rn)"
```

Opcion 2, si ya tienes el resource name:

```bash
uv run python -c "import vertexai; from vertexai import agent_engines; rn='projects/PROJECT_NUMBER/locations/europe-west1/reasoningEngines/ENGINE_ID'; vertexai.init(); agent_engines.get(rn).delete(); print('Deleted:', rn)"
```

## Prueba de auth Graph por estado de sesion

Prueba local de tools (sin Agent Engine):

```bash
cd asistente-notas
uv run python scripts/verify_graph_tools.py --token "<GRAPH_ACCESS_TOKEN>" --search "reunion"
```

Si `list_pages` devuelve paginas, el script lee la primera con `get_page_content` y muestra una preview.

Prueba remota en el Engine desplegado (inyectando `ms_graph_token` en sesion):

```bash
cd asistente-notas
uv run python scripts/smoke_remote_with_graph_token.py \
  --project gcp1-prj-sv-dev-agentmind-01 \
  --location europe-west1 \
  --engine "projects/241752938089/locations/europe-west1/reasoningEngines/6158276666243153920" \
  --token "<GRAPH_ACCESS_TOKEN>"
```

Este script crea una sesion con `state={"ms_graph_token": "..."}` y ejecuta una consulta que fuerza el uso de `list_pages` + `get_page_content`.
