# Runbook de despliegue — Asistente de Notas (OneNote ↔ Gemini Enterprise)

Este documento resume cómo queda desplegado el sistema, los pasos exactos
para repetir el despliegue o recuperarlo, los errores que aparecieron durante
la puesta en marcha y cómo se resolvieron, y qué tener en cuenta en próximos
despliegues o mantenimientos.

## 1. Arquitectura final

```
Usuario en Gemini Enterprise ("Asistente OneNote")
        │
        ▼
Agente "Asistente de Notas" (ADK, gemini-2.5-flash)
        │  desplegado en Vertex AI Agent Engine
        ▼
onenote_tools.py
        │  usa SIEMPRE la misma identidad de servicio
        │  (no hay login individual por usuario)
        ▼
Microsoft Graph API — OneNote de svc_servinlabs_01@preservinform.onmicrosoft.com
```

**Decisión de diseño clave:** el agente NO pide login individual a cada
usuario de Gemini Enterprise. Usa una única identidad fija de Microsoft
(`svc_servinlabs_01`), autenticada con un `refresh_token` obtenido una sola
vez y guardado en Secret Manager. Cualquier usuario que hable con el agente
ve el mismo OneNote (el de esa cuenta de servicio).

Se intentaron dos diseños antes de llegar a este, ver [sección 5](#5-decisiones-de-arquitectura-descartadas).

## 2. Recursos y IDs de referencia

| Recurso | Valor |
|---|---|
| Proyecto GCP (activo) | `gcp2-prj-gs-labs-assetintel-01` (project number `37847055767`) |
| Región Agent Engine | `europe-west1` |
| Reasoning Engine | `projects/37847055767/locations/europe-west1/reasoningEngines/5113511921437376512` |
| App Gemini Enterprise | "Asistente OneNote" — engine `asistente-onenote_1784619034124` (región `eu`) |
| Agente registrado en GE | `.../engines/asistente-onenote_1784619034124/assistants/default_assistant/agents/5592294772069062393` |
| Tenant Entra ID | `preservinform.onmicrosoft.com` (`c01595bd-a38f-4ffe-b850-67914a7ef848`) |
| App Entra ID | "Giskard One Note Agent" (`09b748e7-18b3-4009-9333-b6692f4eb369`) — cliente público, sin secret en uso |
| Cuenta de servicio M365 | `svc_servinlabs_01@preservinform.onmicrosoft.com` |
| Secreto (GCP Secret Manager) | `ms-graph-refresh-token` en `gcp2-prj-gs-labs-assetintel-01` |

**Proyecto obsoleto, sin acceso:** hubo un primer despliegue accidental en
`gcp1-prj-sv-dev-agentmind-01` (project number `241752938089`). Nadie del
equipo actual tiene acceso a ese proyecto — se ignora y se abandonó. Todo lo
vigente está en `gcp2-prj-gs-labs-assetintel-01`.

## 3. Cómo desplegar (repetir tras un cambio de código)

```bash
cd asistente-notas

# Reautenticar si hace falta (ver seccion 4.2, caduca a menudo)
gcloud auth login mdeltorom@giskard.es
gcloud auth application-default login

# Regenerar requirements y desplegar
uv export --no-hashes --no-header --no-dev --no-emit-project > app/app_utils/.requirements.txt

PYTHONIOENCODING=utf-8 PYTHONUTF8=1 uv run -m app.app_utils.deploy \
  --project gcp2-prj-gs-labs-assetintel-01 \
  --location europe-west1 \
  --source-packages=./app \
  --entrypoint-module=app.agent_engine_app \
  --entrypoint-object=agent_engine \
  --requirements-file=app/app_utils/.requirements.txt \
  --set-secrets="MS_GRAPH_REFRESH_TOKEN=ms-graph-refresh-token"
```

Esto **actualiza en el sitio** el mismo Reasoning Engine (busca por
`display_name=asistente-notas`), no crea uno nuevo — el registro en Gemini
Enterprise sigue apuntando al mismo recurso sin tocarlo.

### Verificar tras desplegar

```bash
uv run python scripts/smoke_remote_with_graph_token.py \
  --project gcp2-prj-gs-labs-assetintel-01 \
  --location europe-west1 \
  --engine "projects/37847055767/locations/europe-west1/reasoningEngines/5113511921437376512" \
  --token "unused"
```

(El parámetro `--token` ya no se usa — el agente no depende de ningún token
de sesión — pero el script lo sigue pidiendo por compatibilidad).

### Si hay que renovar el refresh_token

El refresh_token puede caducar o ser revocado (política de la organización,
cambio de contraseña de la cuenta de servicio, revocación manual, etc.). Para
generar uno nuevo:

```bash
uv run python scripts/get_service_account_refresh_token.py
```

Sigue las instrucciones en pantalla (login por device code como
`svc_servinlabs_01`), y sube el resultado como nueva versión del secreto:

```bash
echo -n "<refresh_token>" | gcloud secrets versions add ms-graph-refresh-token \
  --project=gcp2-prj-gs-labs-assetintel-01 --data-file=-
```

No hace falta volver a desplegar el agente — Agent Engine lee `:latest` del
secreto en cada arranque de instancia.

## 4. Errores encontrados y solución (por orden de aparición)

### 4.1 `UnicodeEncodeError: 'charmap' codec can't encode` al desplegar
El script de deploy imprime emojis en un banner; la consola de Windows usa
cp1252 por defecto. **Solución:** forzar UTF-8:
```bash
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 uv run -m app.app_utils.deploy ...
```

### 4.2 `Reauthentication is needed` / ADC caducado constantemente
Tanto `gcloud auth login` (CLI) como `gcloud auth application-default login`
(ADC, usado por el SDK de Python) caducan por separado y con frecuencia en
este entorno. Si un comando falla con `RefreshError` o
`Reauthentication is needed`, simplemente relanzar:
```bash
gcloud auth login mdeltorom@giskard.es
gcloud auth application-default login
```
Ambos abren el navegador; hay que completarlos ahí. **Lanzarlos siempre en
background** (o esperando confirmación del usuario) — si se ejecutan en
primer plano bloquean la sesión hasta que el navegador responda.

### 4.3 Error CSRF `MismatchingStateError` al hacer `gcloud auth login`
Ocurrió tras lanzar varios `gcloud auth login` casi seguidos (uno interrumpido
sin cerrar limpiamente). El callback local (`localhost:8085`) recibió la
respuesta de un intento antiguo. **Solución:** comprobar que no quede ningún
proceso colgado escuchando ese puerto y relanzar limpio:
```powershell
Get-NetTCPConnection -LocalPort 8085 -ErrorAction SilentlyContinue
```

### 4.4 Desplegado sin darse cuenta en el proyecto equivocado
El primer `make deploy` fue a `gcp1-prj-sv-dev-agentmind-01`, un proyecto sin
acceso para el equipo actual (mdeltorom@giskard.es no tenía ni permiso para
leer su política IAM). **Lección:** pasar siempre `--project` explícito y
confirmar de antemano en qué proyecto se quiere desplegar — no fiarse del
proyecto por defecto de ADC.

### 4.5 El engine ID de la URL de Gemini Enterprise NO es el ID real
La URL `https://vertexaisearch.cloud.google.com/eu/home/cid/<uuid>` usa un
identificador de interfaz (`cid`) que **no coincide** con el nombre de
recurso real de Discovery Engine. Para encontrar el real:
```bash
curl -H "Authorization: Bearer $(gcloud auth print-access-token)" \
     -H "X-Goog-User-Project: gcp2-prj-gs-labs-assetintel-01" \
     "https://eu-discoveryengine.googleapis.com/v1alpha/projects/37847055767/locations/eu/collections/default_collection/engines"
```
El campo `name` de la respuesta (`.../engines/asistente-onenote_1784619034124`)
es el que hay que usar en `--gemini-enterprise-app-id`.

### 4.6 El agente registrado no aparecía en la galería de Gemini Enterprise
`register-gemini-enterprise` dejó el agente en `state: ENABLED` pero **sin**
`sharingConfig`, por lo que no era visible para los usuarios. Comparando con
un agente nativo (`Deep Research`) se vio que necesitaba
`sharingConfig.scope = ALL_USERS`. Se corrigió con un `PATCH` manual:
```bash
curl -X PATCH ... \
  -d '{"sharingConfig":{"scope":"ALL_USERS"}}' \
  ".../agents/5592294772069062393?updateMask=sharingConfig"
```
También hubo que verificar que se estaba mirando la app correcta — había
**dos** apps de Gemini Enterprise en el mismo proyecto ("Asistente OneNote" y
"gemini-enterprise-asset-intelligent"), cada una con su propia galería de
agentes.

### 4.7 `AADSTS50105` — usuario bloqueado por falta de asignación
Al probar el login OAuth por usuario (diseño descartado, ver sección 5), Entra
bloqueaba a cualquier usuario no asignado explícitamente a la app. Se
resolvió (para ese diseño) desactivando "¿Se requiere asignación de usuario?"
en **Aplicaciones empresariales** (no en "App registrations") → Propiedades.
Ya no aplica en el diseño final porque no hay login por usuario.

### 4.8 `AADSTS7000218` intermitente en el *device code flow*
Al pedir el refresh_token para `svc_servinlabs_01` con device code flow,
aparecía intermitentemente `client_assertion or client_secret required`
incluso enviando el secret, y desaparecía tras confirmar que **"Permitir
flujos de clientes públicos"** (Authentication → Advanced settings) estaba
realmente guardado en "Sí" (se había marcado el check pero no guardado la
primera vez). Con el toggle realmente activo, el flujo funciona **sin** client
secret. **Lección:** si aparece este error con un cliente que se cree
público, verificar el toggle directamente en el registro de la app, no
fiarse de lo que se recuerde haber configurado.

### 4.9 Secret Manager API no habilitada
```
API [secretmanager.googleapis.com] not enabled on project ...
```
Solución:
```bash
gcloud services enable secretmanager.googleapis.com --project=gcp2-prj-gs-labs-assetintel-01
```

### 4.10 El Agent Engine no podía leer el secreto (`--set-secrets`)
```
The Reasoning Engine could not access one or more secrets ...
```
El *service account* de ejecución del Reasoning Engine
(`service-37847055767@gcp-sa-aiplatform-re.iam.gserviceaccount.com`) necesita
el rol `roles/secretmanager.secretAccessor` sobre el secreto (o el proyecto):
```bash
gcloud projects add-iam-policy-binding gcp2-prj-gs-labs-assetintel-01 \
  --member="serviceAccount:service-37847055767@gcp-sa-aiplatform-re.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```
Tras conceder el rol, puede hacer falta esperar ~1 minuto por propagación de
IAM antes de que el deploy funcione.

### 4.11 La `Authorization` de Discovery Engine debe estar en la misma región que el agente
Al crear el recurso `Authorization` (para el diseño OAuth-por-usuario,
descartado) en `locations/global`, el `PATCH` del agente fallaba con
`Authorization location must match agent location. Agent location: 'eu'`.
Hay que crear la Authorization en la misma región (`eu`) que el engine de
Gemini Enterprise.

## 5. Decisiones de arquitectura descartadas

Por si se retoma en el futuro o se necesita entender el porqué del diseño
actual:

1. **Inyección manual de token en estado de sesión** (`ms_graph_token`):
   válido solo para pruebas locales/scripts (`verify_graph_tools.py`,
   `smoke_remote_with_graph_token.py`), nunca funcional para usuarios reales
   de Gemini Enterprise (no hay forma de que la interfaz inyecte ese estado).

2. **OAuth2 delegado por usuario vía Gemini Enterprise Authorization**
   (`tool_context.request_credential`): cada usuario real habría iniciado
   sesión con **su propia** cuenta de Microsoft y visto **sus propias**
   notas. Se implementó completamente (Authorization resource en Discovery
   Engine, client secret en Entra, código ADK con `AuthConfig`) pero se
   descartó porque el requisito real era una identidad única compartida
   (`svc_servinlabs_01`), no notas personales por usuario. Quedó un recurso
   huérfano `projects/37847055767/locations/eu/authorizations/entra-onenote-notes-read`
   que se puede borrar si no se retoma este enfoque.

3. **Diseño final (adoptado):** identidad fija con `refresh_token` en Secret
   Manager (sección 1). Sin login de usuario, sin Authorization en Discovery
   Engine, sin client secret en uso.

## 6. Pendientes / cosas a vigilar en el futuro

- **Caducidad del refresh_token:** no hay alerta automática. Si el agente
  empieza a fallar con "No se pudo obtener acceso a OneNote", lo primero a
  probar es regenerar el refresh_token (sección 3).
- **Limpieza opcional:** el recurso `Authorization` huérfano
  (`entra-onenote-notes-read`, región `eu`) y el client secret de Entra
  generado para el diseño descartado ya no se usan — se pueden revocar/borrar
  si se confirma que no hará falta volver al diseño por-usuario.
- **Coste:** `min_instances=0` en el Agent Engine — cold start de unos
  segundos en la primera consulta tras inactividad, pero sin coste en reposo.
- **Autenticación local:** las sesiones de `gcloud auth login` y
  `gcloud auth application-default login` caducan con frecuencia en este
  entorno — si cualquier comando falla con "Reauthentication is needed",
  repetir ambos comandos antes de investigar nada más.
