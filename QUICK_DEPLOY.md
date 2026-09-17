# QUICK START: Deploy Opción 2.5 desde Mac/Linux

## TL;DR

El código está listo. Ejecuta esto desde **Mac, Linux o Google Cloud Shell**:

```bash
cd asistente-notas
make deploy
```

**Listo en 5 minutos.** ✨

---

## Opción 1: Google Cloud Shell (⭐ Recomendado)

```bash
# Abrir: https://console.cloud.google.com

# Click "Activate Cloud Shell" (arriba a la derecha)

# Paste:
git clone https://github.com/your-repo/asistente-notas.git
cd asistente-notas
make deploy

# Esperar 3-5 minutos
# Al terminar: ✅ Agent updated successfully
```

---

## Opción 2: Desde Mac

```bash
cd ~/Downloads/agent\ onenote/asistente-notas
make deploy
# Esperar
```

---

## Opción 3: Desde Linux

```bash
cd ~/Downloads/agent_onenote/asistente-notas
make deploy
# Esperar
```

---

## Opción 4: WSL2 (en Windows)

```powershell
wsl
cd /mnt/c/Users/mdeltoro.mateos/Downloads/agent\ onenote/asistente-notas
make deploy
```

---

## ¿Qué Pasa?

1. **Compila el agente** con las nuevas funciones de imagen
2. **Construye un container** Docker
3. **Lo sube a Google Cloud Artifact Registry**
4. **Actualiza el Reasoning Engine** (Agent Engine)
5. ✅ **Nuevo tool `get_page_content_with_images()` disponible**

---

## Después del Deploy

### Verificar que funcionó

```bash
python3 << 'EOF'
from vertexai._genai.agent_engines import AgentEngines
agent = AgentEngines().get("projects/37847055767/locations/europe-west1/reasoningEngines/5113511921437376512")
tools = [tool.__name__ for tool in agent.agent.tools]
print("Herramientas disponibles:")
for t in tools:
    print(f"  - {t}")
if "get_page_content_with_images" in tools:
    print("\n✅ NUEVO TOOL DETECTADO!")
else:
    print("\n❌ Tool no encontrada - revisar logs")
EOF
```

### Probar con OneNote

1. Subir una página con imágenes/diagrama a OneNote
2. Preguntar: "Describe el diagrama de la página"
3. El agente debería:
   - Llamar `get_page_content_with_images()`
   - Descargar la imagen
   - Pasar a Gemini para análisis visual
   - Responder describiendo el diagrama

---

## Troubleshooting

### "Command not found: make"

Instalar Make:
```bash
# Mac
brew install make

# Linux (Ubuntu/Debian)
sudo apt-get install make

# Linux (Fedora/CentOS)
sudo yum install make
```

### "Build failed" error

Revisar logs en Cloud Console:
```
https://console.cloud.google.com/logs/
→ Filter: reasoning_engine_id="5113511921437376512"
```

### Timeout

El deploy puede tardar hasta 10 minutos. **No cancelar.**

---

## Documentación Completa

- **Técnica**: `IMAGEN_SUPPORT_COMPLETE.md`
- **Deployment**: `DEPLOYMENT_STATUS_OPTION2_5.md`
- **Resumen**: `RESUMEN_FINAL_OPTION2_5.md`

---

## ¿Necesitas Ayuda?

1. **Code issues?** → Revisar `test_image_support.py` (local tests)
2. **Deploy issues?** → Ver logs en Cloud Console
3. **Feature questions?** → Ver `IMAGEN_SUPPORT_COMPLETE.md`

---

**Status**: ✅ Code ready, 🚀 Deploy ready

¡Adelante! 🎯
