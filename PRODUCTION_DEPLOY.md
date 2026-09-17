# 🚀 Despliegue en Producción — Asistente de Notas

**Versión**: 1.0  
**Fecha última actualización**: 2026-09-17  
**Estado**: Listo para producción

---

## 📋 Requisitos Previos

### En Google Cloud
- ✅ Proyecto GCP activo con facturación habilitada
- ✅ `gcloud CLI` instalado y configurado: `gcloud auth login` + `gcloud config set project <PROJECT_ID>`
- ✅ Permisos: `Vertex AI Agent Service Admin`, `Cloud Run Admin`, `Cloud Logging Admin`
- ✅ APIs habilitadas (se habilitan automáticamente):
  - Vertex AI API
  - Cloud Run API
  - Cloud Logging API

### En el entorno local (para validación pre-despliegue)
- ✅ Python 3.10+
- ✅ `uv` package manager (si lo tienes): `pip install uv`, o usa `pip` directamente

---

## 🔧 Estructura del Proyecto

```
asistente-notas/
├── app/
│   ├── agent.py                 # Definición del agente ADK
│   ├── onenote_tools.py         # Herramientas de OneNote (Graph API)
│   └── app_utils/
│       ├── telemetry.py         # Observabilidad
│       ├── deploy.py            # Helpers de despliegue
│       └── typing.py            # Type hints
├── scripts/
│   ├── verify_graph_tools.py    # Test de herramientas Graph
│   ├── get_service_account_refresh_token.py
│   └── smoke_remote_with_graph_token.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── eval/                    # Evaluaciones
├── pyproject.toml               # Dependencias (uv + pip)
├── uv.lock                      # Lock file (check-in a git)
├── Makefile                     # Comandos de desarrollo
├── README.md                    # README técnico
└── deployment_metadata.json     # Metadata del último despliegue
```

---

## 🌍 Configuración Pre-Despliegue

### 1. Entra ID (Azure) — Setup

El agente usa acceso **delegado** a OneNote. El token fluye así:

```
Frontend (MSAL)
    ↓ [obtiene token Graph, scope Notes.Read]
    ↓
Backend/Agente ADK
    ↓ [lee token de sesión, llama a Graph]
    ↓
OneNote (delegado del usuario)
```

**Lo que ya está registrado:**
- Tenant ID: `c01595bd-a38f-4ffe-b850-67914a7ef848`
- Client ID: `09b748e7-18b3-4009-9333-b6692f4eb369`
- Permiso delegado: `Notes.Read`

**Si hay cambios en producción**, actualiza en Entra ID:
- Si hay un nuevo frontend, registra su redirect URI.
- Si cambia el modelo de autenticación (ej: service account), avisa a DevOps.

### 2. Google Cloud — Proyecto

Antes de desplegar, confirma:
```bash
gcloud config set project <YOUR_PROJECT_ID>
gcloud auth application-default login  # Para credenciales locales
```

---

## 🚀 Despliegue (Método Recomendado: Cloud Shell)

### Opción A: Cloud Shell (Sin instalaciones locales)

1. Abre Google Cloud Console: https://console.cloud.google.com

2. Arriba a la derecha, abre **Cloud Shell** (`>_`)

3. Clona o descarga este repo:
   ```bash
   git clone <REPO_URL>
   cd asistente-notas
   ```

4. Ejecuta el despliegue:
   ```bash
   make deploy
   ```
   (o si `make` no está disponible, usa: `bash deploy.sh`)

5. **Espera 3-5 minutos** a que termine. Verás:
   ```
   ✅ DEPLOYMENT SUCCESSFUL
   Agent Engine ID: projects/XXX/locations/europe-west1/reasoningEngines/YYY
   ```

### Opción B: Máquina Local (Con gcloud + Python)

1. Clona el repo:
   ```bash
   git clone <REPO_URL>
   cd asistente-notas
   ```

2. Instala dependencias:
   ```bash
   pip install -r <(python -c "import tomllib; print('\n'.join([d for d in tomllib.load(open('pyproject.toml', 'rb'))['project']['dependencies']]))")
   # O más fácil:
   pip install google-adk requests google-cloud-aiplatform google-cloud-logging
   ```

3. Autentica gcloud:
   ```bash
   gcloud auth application-default login
   gcloud config set project <YOUR_PROJECT_ID>
   ```

4. Despliegue:
   ```bash
   make deploy
   ```

---

## ✅ Validación Post-Despliegue

### 1. Verifica que el agente está corriendo
```bash
gcloud ai agents agent-engines list --region=europe-west1
```

### 2. Obtén el ID del agente desplegado
El ID estará en `asistente-notas/deployment_metadata.json`:
```json
{
  "remote_agent_engine_id": "projects/<PROJECT>/locations/europe-west1/reasoningEngines/<ENGINE_ID>",
  "deployment_timestamp": "2026-09-17T..."
}
```

### 3. Abre el agente en consola para probarlo
```
https://console.cloud.google.com/vertex-ai/agents/agent-engines/<ENGINE_ID>?project=<PROJECT>
```

Usa la pestaña **"Test agent"** para chatear.

### 4. Verifica logs
```bash
gcloud logging read "resource.type=cloud_run_revision AND labels.service_name=asistente-notas" --limit 50
```

---

## 🔄 Actualizaciones (Re-Despliegue)

Para actualizar el agente sin cambiar Project/Engine:

1. Haz cambios en `app/agent.py` o `app/onenote_tools.py`

2. Desde la carpeta `asistente-notas`:
   ```bash
   make deploy
   ```

3. El agente se reemplaza en-place. Sin downtime (excepto cold start ~5-15s).

---

## 🛑 Troubleshooting

### ❌ Error: "Permission denied on project"
```
gcloud auth application-default login
gcloud config set project <PROJECT_ID>
```

### ❌ Error: "Model not found: gemini-3-flash-preview"
**Solución**: Abre `pyproject.toml`, busca `gemini-3-flash-preview`, cámbialo por `gemini-2.5-flash`:
```toml
# Antes
# Después
"model": "gemini-2.5-flash"
```

### ❌ Error: "Could not connect to OneNote API (403 Forbidden)"
- El token de Graph puede haber caducado (es por sesión)
- **Solución frontend**: El frontend debe refrescar el token (usando MSAL `offline_access`) y actualizar el estado de sesión.
- **Solución agente**: Nada (el agente solo lee el token que le pasa el frontend).

### ❌ Deployment stuck / timeout
- Cloud Shell cierra tras 1 hora de inactividad
- **Solución**: Usa `gcloud auth application-default login` en tu máquina local y repite

### ❌ "min_instances=1 costs too much"
Para ahorrar costos en desarrollo/pruebas, edita `Makefile`:
```makefile
# Busca: --min_instances
# Cámbialo a: --min_instances 0
```

---

## 📊 Coste Estimado (Producción)

- **Despliegue**: 0 €
- **En reposo** (min_instances=0): ~0 €
- **Por consulta** (gemini-2.5-flash + runtime): ~0.001€/consulta promedio
- **Microsoft Graph** (delegado): Gratis (cubierto por licencia Entra ID)

---

## 🔐 Seguridad

### Credenciales & Secretos
- ✅ El token de acceso a Graph **viaja por sesión**, NO se hardcodea
- ✅ El agente usa **workload identity** (IAM automático)
- ✅ No hay API keys ni secrets en el código

### Si necesitas más controles
- Habilita **VPC Service Controls**: aísla la infraestructura
- Usa **Secret Manager**: para configuración sensible
- Habilita **Access Transparency**: audita accesos

---

## 📞 Contacto & Soporte

- **Issues técnicos**: Abre un issue en el repo con logs de `gcloud logging`
- **Preguntas de ADK**: https://docs.cloud.google.com/gemini-enterprise-agent-platform
- **OneNote API**: https://learn.microsoft.com/graph/api/resources/onenote-api-overview

---

## 🔗 Links Útiles

| Recurso | URL |
|---------|-----|
| **Console GCP** | https://console.cloud.google.com |
| **Vertex AI Docs** | https://docs.cloud.google.com/vertex-ai |
| **Agent Engine Docs** | https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/runtime/use-an-agent |
| **ADK Python SDK** | https://github.com/googleapis/python-adk |
| **Microsoft Graph OneNote** | https://learn.microsoft.com/graph/onenote-concept-overview |

---

**✅ Ready to production!** Si encuentras algo que mejorar, abre un PR. 🚀
