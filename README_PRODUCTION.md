# 🎯 Asistente de Notas — Despliegue en Producción

**Estado**: ✅ Listo para producción  
**Última actualización**: 2026-09-17  
**Versión del Agente**: 1.0 (ADK)

---

## 📖 Descripción Rápida

**Asistente de Notas** es un agente IA en **Vertex AI Agent Engine** que responde preguntas sobre el contenido de OneNote del usuario.

- **Motor**: Google Gemini 2.5 Flash (via ADK — Agent Development Kit)
- **Integración**: Microsoft Graph API (OneNote delegado por usuario)
- **Autenticación**: Token MSAL via frontend → Sesión del agente
- **Despliegue**: Fully managed en Google Cloud (sin infraestructura manual)

---

## 🚀 Para Empezar (DevOps/SRE)

### Opción Rápida: Cloud Shell (Recomendado)

```bash
# 1. Abre Cloud Shell en GCP Console
# 2. Clone/descarga este repo
git clone <REPO_URL> && cd asistente-notas

# 3. Despliegue en una línea
make deploy

# Listo en 3-5 minutos ✅
```

### Opción Local: Tu máquina

```bash
git clone <REPO_URL>
cd asistente-notas
gcloud auth application-default login
gcloud config set project <YOUR_PROJECT_ID>
make deploy
```

**Documentación completa**: Ver [PRODUCTION_DEPLOY.md](./PRODUCTION_DEPLOY.md)

---

## 📂 Estructura del Proyecto

```
.
├── asistente-notas/              # ⭐ CORE (lo que se despliegue)
│   ├── app/
│   │   ├── agent.py              # Agente ADK + instrucciones
│   │   ├── onenote_tools.py      # Tools: list_notebooks, get_page_content, etc.
│   │   └── app_utils/            # Helpers (telemetry, deploy)
│   ├── scripts/                  # Test & verificación
│   ├── tests/                    # Unit + integration + eval
│   ├── pyproject.toml            # Dependencias (uv)
│   ├── uv.lock                   # Lock file
│   ├── Makefile                  # make deploy, make test, etc.
│   └── README.md                 # Documentación técnica
│
├── .gitignore                    # Reglas de versionado
├── PRODUCTION_DEPLOY.md          # Guía de despliegue (LEER ESTO)
├── CLEANUP_INSTRUCTIONS.md       # Qué limpiar antes de git
└── README.md                     # Este archivo

```

---

## ⚙️ Configuración Requerida

### Google Cloud
- ✅ Proyecto GCP activo con facturación
- ✅ `gcloud CLI` configurado
- ✅ Permisos: Vertex AI Admin + Cloud Run Admin
- ✅ APIs activas (se activan automáticamente)

### Entra ID (Azure)
- ✅ App registrada: Client ID `09b748e7-18b3-4009-9333-b6692f4eb369`
- ✅ Permiso delegado: `Notes.Read`
- ✅ Tenant: `c01595bd-a38f-4ffe-b850-67914a7ef848`

**Si algo cambió**, edita `asistente-notas/app/agent.py` y línea 20 de `app/onenote_tools.py`.

---

## 🔑 Características

### ✅ Incluido
- Lectura de cuadernos OneNote (via Graph API delegado)
- Búsqueda de páginas por título/palabra clave
- Extracción de contenido (texto + imágenes codificadas)
- Reconocimiento automático de tablas, listas, etc.
- Observabilidad (Cloud Logging)
- Manejo de errores & reintentos ante throttling

### ❌ NO Incluido (Por Diseño)
- Escritura en OneNote (solo lectura)
- Autenticación OAuth (responsabilidad del frontend)
- UI web (solo API + conversación)

---

## 🧪 Antes de Desplegar: Validación Local

```bash
cd asistente-notas

# 1. Test unitarios
make test-unit

# 2. Verifica herramientas Graph (requiere token válido)
# uv run python scripts/verify_graph_tools.py --token "<TOKEN_AQUI>"

# 3. Smoke test remoto (post-despliegue)
# uv run python scripts/smoke_remote_with_graph_token.py
```

---

## 📊 Coste Estimado

| Concepto | Coste |
|----------|-------|
| Despliegue | 0 € |
| Reposo (min_instances=0) | ~0 €/mes |
| Consulta típica (Gemini 2.5F) | ~0.001 € |
| OneNote API (delegado) | Gratis |
| **Total PoC/Test** | <5€/mes (si min_instances=0) |

Para producción con tráfico constante, estima: **Gemini tokens + runtime Engine**.

---

## 🛠️ Comandos Útiles

```bash
cd asistente-notas

# Deploy
make deploy                    # Full: build, test, deploy

# Desarrollo local
make dev                       # Abre adk web (UI interactiva)
make test                      # Corre todos los tests
make test-unit                 # Solo unitarios
make lint                      # ruff + linting

# Info del despliegue
cat deployment_metadata.json   # Lee ID del agente

# Logs remotos
gcloud logging read "resource.type=cloud_run_revision AND labels.service_name=asistente-notas" --limit 50
```

---

## 🔐 Seguridad

- ✅ **Tokens**: Viajan por sesión, NO hardcodeados
- ✅ **Workload Identity**: IAM automático (sin service accounts)
- ✅ **API Keys**: Ninguna en el código
- ✅ **Permisos**: Delegados (usuario → Graph, no service account → Graph)

---

## 📋 Flujo de Despliegue (Resumido)

```
1. git clone <REPO>
   ↓
2. cd asistente-notas
   ↓
3. make deploy
   ├─ Valida dependencias
   ├─ Corre tests
   ├─ Build contenedor (ADK)
   ├─ Push a Artifact Registry
   └─ Deploy a Vertex AI Agent Engine
   ↓
4. deployment_metadata.json actualizado ✅
   ↓
5. Test en consola GCP (pestaña "Test agent")
```

---

## 🆘 Troubleshooting Rápido

| Problema | Solución |
|----------|----------|
| "Permission denied" | `gcloud auth application-default login` |
| "Model not found" | Cambia a `gemini-2.5-flash` en `pyproject.toml` |
| "Connection timeout" | Cloud Shell > 1h, vuelve a ejecutar en local |
| "403 OneNote" | Token de Graph expirado (responsabilidad frontend) |
| Logs no aparecen | `gcloud logging read ... --limit 100` |

**Guía completa**: [PRODUCTION_DEPLOY.md](./PRODUCTION_DEPLOY.md)

---

## 🔄 Actualizar el Agente

1. Edita `app/agent.py` o `app/onenote_tools.py`
2. Commit & push a git
3. DevOps: `git pull` + `make deploy`
4. Agente reemplazado (sin downtime)

---

## 📞 Referencias

- **Vertex AI Docs**: https://docs.cloud.google.com/vertex-ai
- **ADK (Python SDK)**: https://github.com/googleapis/python-adk
- **OneNote API**: https://learn.microsoft.com/graph/onenote-concept-overview
- **Issue?**: Abre ticket con logs de `gcloud logging`

---

## ✅ Checklist Pre-Despliegue

- [ ] Proyecto GCP creado + facturación ON
- [ ] `gcloud CLI` configurado
- [ ] Repo clonado localmente
- [ ] `.gitignore` respeta `synthetic_data/`, `.venv/`, `*.log`
- [ ] Credenciales NO en `.git` (usar Secret Manager si es necesario)
- [ ] Tests pasan: `make test`
- [ ] Documentación leída: [PRODUCTION_DEPLOY.md](./PRODUCTION_DEPLOY.md)

---

## 📝 Notas

- **Modelo usado**: `gemini-2.5-flash` (rápido + barato)
- **Min instances**: Por defecto `0` (costo 0€ en reposo)
- **Región**: `europe-west1` (cambiar en `Makefile` si necesario)
- **Lenguaje**: Español por defecto (configurable en `app/agent.py` instrucción)

---

**Ready to production!** 🚀  
Preguntas → Abre un issue en el repo o contacta al equipo de backend.
