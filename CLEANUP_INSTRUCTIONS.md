# 🧹 Instrucciones de Limpieza Pre-Subida a Git

Este documento describe qué archivos se pueden eliminar y cuál es la estructura final que se debe subir a Git.

---

## 📂 Archivos a ELIMINAR (Desarrollo Local)

```
❌ .venv/                          # Ambiente virtual (reconstruible)
❌ __pycache__/                    # Compilados Python
❌ asistente-notas/.venv/          # Otro ambiente virtual
❌ synthetic_data/                 # Datos de prueba sintéticos
❌ test_html_parsing.py            # Scripts de prueba local
❌ test_image_support.py           # Scripts de prueba local
❌ generate_synthetic_data.py      # Generador local
❌ autonomous_deploy.py            # Despliegue local (no usado)
❌ deploy.sh                        # Script local (no necesario en git)
❌ asistente-notas/deploy_log.txt  # Logs de despliegue
❌ asistente-notas/deploy_windows.py  # Script Windows local
❌ asistente-notas/deploy_api.py   # Deprecated
❌ asistente-notas/update_agent.py # Helper local
```

**Por qué**: Estos archivos son para desarrollo local. Git los reconstruye o el CI/CD los genera.

---

## 📋 Archivos a MANTENER (Estructura Final)

```
✅ asistente-notas/
   ├── app/
   │   ├── __init__.py
   │   ├── agent.py                # ⭐ CORE: definición del agente
   │   ├── onenote_tools.py        # ⭐ CORE: herramientas Graph
   │   └── app_utils/
   │       ├── __init__.py
   │       ├── deploy.py           # Helpers
   │       ├── telemetry.py        # Observabilidad
   │       └── typing.py           # Type hints
   │
   ├── scripts/
   │   ├── verify_graph_tools.py   # Test helper (mantener)
   │   ├── smoke_remote_with_graph_token.py
   │   └── get_service_account_refresh_token.py
   │
   ├── tests/
   │   ├── unit/
   │   ├── integration/
   │   └── eval/
   │
   ├── pyproject.toml              # ⭐ Dependencias
   ├── uv.lock                     # ⭐ Lock file
   ├── Makefile                    # ⭐ Comandos build/deploy
   ├── README.md                   # Documentación
   ├── DEPLOYMENT_RUNBOOK.md       # Runbook
   ├── GEMINI.md                   # Notas de configuración
   └── deployment_metadata.json    # ⭐ Metadata (actualizado por CI/CD)

✅ .gitignore                      # (raíz) Reglas globales
✅ PRODUCTION_DEPLOY.md            # Guía de despliegue
✅ README.md                       # (raíz) Overview
✅ requirements.txt                # (raíz) Opcional, pero mantener
```

---

## 🔑 Archivos Críticos (NUNCA Eliminar)

| Archivo | Razón |
|---------|-------|
| `app/agent.py` | Definición del agente ADK |
| `app/onenote_tools.py` | Herramientas de integración |
| `pyproject.toml` | Dependencias officielles |
| `uv.lock` | Reproducibilidad de builds |
| `Makefile` | Automatización de despliegue |
| `.gitignore` | Reglas de versionado |

---

## 🗑️ Cómo Limpiar (Commands)

### En Windows PowerShell:
```powershell
# Desde la raíz del repo
Remove-Item -Recurse -Force .venv
Remove-Item -Recurse -Force __pycache__
Remove-Item -Recurse -Force synthetic_data
Remove-Item -Force test_html_parsing.py
Remove-Item -Force test_image_support.py
Remove-Item -Force generate_synthetic_data.py
Remove-Item -Force autonomous_deploy.py
Remove-Item -Force deploy.sh

# En asistente-notas/
cd asistente-notas
Remove-Item -Recurse -Force .venv
Remove-Item -Force deploy_log.txt
Remove-Item -Force deploy_windows.py
Remove-Item -Force deploy_api.py
Remove-Item -Force update_agent.py
cd ..
```

### En Linux/Mac:
```bash
# Desde la raíz del repo
rm -rf .venv __pycache__ synthetic_data
rm -f test_html_parsing.py test_image_support.py
rm -f generate_synthetic_data.py autonomous_deploy.py deploy.sh

# En asistente-notas/
cd asistente-notas
rm -rf .venv
rm -f deploy_log.txt deploy_windows.py deploy_api.py update_agent.py
cd ..
```

---

## ✅ Validación Pre-Git

Después de limpiar, verifica:

1. **Estructura limpia**:
   ```bash
   ls -la asistente-notas/
   ```
   Debe mostrar: `app/`, `scripts/`, `tests/`, archivos `.py`, `.toml`, `.lock`, `.md`

2. **Sin archivos temporales**:
   ```bash
   find . -name "*.pyc" -o -name "__pycache__" -o -name "*.log"
   ```
   No debe mostrar nada.

3. **Git listo**:
   ```bash
   git status
   ```
   Debe mostrar solo los archivos que quieres subir.

4. **Ignora bien el .gitignore**:
   ```bash
   git check-ignore -v .venv/ synthetic_data/ *.log
   ```
   Debe confirmar que `.gitignore` ignora los archivos.

---

## 🚀 Después de Limpiar

1. **Añade todo a Git**:
   ```bash
   git add .
   git commit -m "Clean: remove dev artifacts for production"
   ```

2. **Push a repo**:
   ```bash
   git push origin main
   ```

3. **Los responsables hacen**:
   ```bash
   git clone <REPO>
   cd asistente-notas
   make deploy
   ```

---

## 📝 Notas Importantes

- ⚠️ **`deployment_metadata.json`**: Déjalo (el CI/CD lo actualiza)
- ⚠️ **`uv.lock`**: SIEMPRE a Git (reproducibilidad)
- ⚠️ **`.gitignore`**: Actualizado a nivel raíz, no necesitas duplicados
- ⚠️ **Credenciales**: Si accidentalmente añadiste algo, usa `git rm --cached <FILE>` + actualiza `.gitignore`

---

✅ **LISTO PARA GIT!** Una vez limpio, sigue `PRODUCTION_DEPLOY.md` para instruir a DevOps.
