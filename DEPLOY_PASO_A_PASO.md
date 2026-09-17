# 🚀 DEPLOYMENT FINAL: Paso a Paso

**Tiempo total**: ~10 minutos  
**Dificultad**: ⭐ Muy fácil (solo copiar-pegar)

---

## 📝 Instrucciones Exactas (3 pasos simples)

### PASO 1️⃣: Abre Google Cloud Shell

1. Abre esto en el navegador:
   ```
   https://console.cloud.google.com
   ```

2. Arriba a la derecha, haz clic en **`>_`** (Cloud Shell)

3. Espera a que se abra la terminal (abajo)

### PASO 2️⃣: Sube el código

En Cloud Shell, tienes un botón con **tres puntos verticales** (`⋮`) arriba a la derecha.

Haz clic → **Selecciona "Upload files"**

Luego:
- Navega a: `c:\Users\mdeltoro.mateos\Downloads\agent onenote`
- Selecciona la carpeta **`asistente-notas`** (la carpeta entera)
- Haz clic **Upload**

Espera a que termine (1-2 minutos).

### PASO 3️⃣: Ejecuta el deployment

En la terminal de Cloud Shell, copia-pega exactamente esto:

```bash
cd asistente-notas && bash ../deploy.sh
```

Luego presiona **Enter** y espera.

La terminal mostrará:
- ✓ Project set
- ✓ Dependencies installed  
- ✓ Verifying agent code
- 🚀 Deploying...
- ✅ DEPLOYMENT SUCCESSFUL

**Tiempo**: ~5-10 minutos

---

## 🎯 Qué Pasará

```
Terminal mostrará:
├─ Verificando gcloud ........................ ✓
├─ Configurando proyecto .................... ✓
├─ Autenticando ............................. ✓
├─ Instalando dependencias .................. ✓
├─ Verificando código
│  └─ Tools: list_notebooks, list_pages, get_page_content, 
│     get_page_content_with_images ......... ✓ (NEW!)
├─ Exportando requirements .................. ✓
├─ 🚀 Deploying (3-5 min) ................... ✓
└─ ✅ SUCCESS!
```

---

## ✅ Después del Deployment

Cuando veas **✅ DEPLOYMENT SUCCESSFUL**, el agente ya está actualizado.

### Para Verificar (opcional)

Espera 2 minutos y luego en la terminal Cloud Shell:

```bash
cd asistente-notas
uv run python scripts/smoke_remote_with_graph_token.py
```

Deberías ver que aparece:
```
✓ get_page_content_with_images PRESENTE
```

---

## 🆘 Si Algo Falla

### "Upload failed"
- Intenta con carpetas más pequeñas
- O usa: `git clone https://github.com/your-repo.git` (si tienes GitHub)

### "gcloud not found"
- Cloud Shell lo tiene pre-instalado
- Asegúrate de estar EN Cloud Shell (terminal azul arriba)

### Timeout (más de 15 min)
- Es normal, el deployment puede tardar
- NO cierres la ventana
- Déjalo continuar

### "Deploy failed"
- El error apareceátter en la terminal
- Copia el error y búscalo en la documentación DEPLOYMENT_STATUS_OPTION2_5.md

---

## 📊 Línea de Tiempo

| Momento | Acción | Tiempo |
|---------|--------|--------|
| 0:00 | Upload asistente-notas | 1-2 min |
| 1:30 | Ejecutas bash deploy.sh | Inmediato |
| 1:30-3:00 | Verificación y setup | 1-2 min |
| 3:00-8:00 | 🚀 Deployment real | 5 min |
| 8:00 | ✅ Success! | Inmediato |

**Total**: ~10 minutos

---

## 🎁 Resultado Final

Después de esto:
- ✅ Agente actualizado en Vertex AI
- ✅ Nueva herramienta: `get_page_content_with_images()`
- ✅ Soporte automático para análisis de imágenes/diagramas
- ✅ Imagen support en producción

---

## 💡 Nota Importante

El `deploy.sh` que creé:
- Automatiza TODO lo que necesitas
- Solo necesitas copiar-pegar UNA línea en Cloud Shell
- Hace todas las verificaciones automáticamente
- Te muestra el progreso en tiempo real

**Eso es. Sin complicaciones.** ✨

---

## 🚀 ¡Empecemos!

Cuando estés listo:

1. Abre https://console.cloud.google.com
2. Cloud Shell (arriba a la derecha)
3. Upload Files → asistente-notas
4. Terminal: `cd asistente-notas && bash ../deploy.sh`
5. Espera ✅

¿Necesitas ayuda en algún paso?
