#!/bin/bash
###############################################################################
# DEPLOYMENT SCRIPT: OneNote Agent with Image Support (Option 2.5)
# 
# Cómo usar:
# 1. Abre Google Cloud Shell: https://console.cloud.google.com
# 2. Abre editor de archivos en Cloud Shell (arriba a la izquierda)
# 3. Crea un nuevo archivo: deploy.sh
# 4. Copia-pega TODO este contenido
# 5. En la terminal: bash deploy.sh
# 6. Espera 5-10 minutos
#
# Eso es. El script hace el resto automáticamente.
###############################################################################

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  DEPLOYING ONENOTE AGENT WITH IMAGE SUPPORT (Option 2.5)      ║"
echo "║  Deployment Timestamp: $(date)                     ║"
echo "╚════════════════════════════════════════════════════════════════╝"

# Configuration
PROJECT="gcp2-prj-gs-labs-assetintel-01"
LOCATION="europe-west1"
AGENT_DISPLAY_NAME="asistente-notas"
SOURCE_DIR="./app"
ENTRYPOINT_MODULE="app.agent_engine_app"
ENTRYPOINT_OBJECT="agent_engine"

echo ""
echo "📋 Configuration:"
echo "   Project: $PROJECT"
echo "   Location: $LOCATION"
echo "   Agent Name: $AGENT_DISPLAY_NAME"
echo ""

# Step 1: Verify gcloud
echo "🔍 Checking gcloud..."
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud not found. Please install Google Cloud SDK."
    exit 1
fi
echo "✓ gcloud found"

# Step 2: Set project
echo ""
echo "🔧 Setting project..."
gcloud config set project $PROJECT
echo "✓ Project set"

# Step 3: Authenticate if needed
echo ""
echo "🔐 Checking authentication..."
if ! gcloud auth application-default print-access-token &> /dev/null; then
    echo "⚠️  Authenticating..."
    gcloud auth application-default login
fi
echo "✓ Authenticated"

# Step 4: Install dependencies (if needed)
echo ""
echo "📦 Checking dependencies..."
if ! command -v uv &> /dev/null; then
    echo "⚠️  Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi
if ! command -v python &> /dev/null; then
    echo "❌ Python not found"
    exit 1
fi
echo "✓ Dependencies OK"

# Step 5: Download code if needed
echo ""
echo "📥 Checking code directory..."
if [ ! -d "asistente-notas" ]; then
    echo "⚠️  Code directory not found. You need to upload/clone it first."
    echo ""
    echo "Options:"
    echo "  A) Upload: Click 'Upload files' in Cloud Shell, select asistente-notas folder"
    echo "  B) Clone: git clone <your-repo-url>"
    echo ""
    echo "Then run this script again."
    exit 1
fi
echo "✓ Code directory found"

# Step 6: Navigate to deployment directory
cd asistente-notas
echo ""
echo "📍 Working directory: $(pwd)"

# Step 7: Verify Python environment
echo ""
echo "🐍 Setting up Python environment..."
uv sync --quiet
echo "✓ Dependencies installed"

# Step 8: Verify code
echo ""
echo "✓ Verifying agent code..."
python3 << 'VERIFY_EOF'
try:
    from app.agent import root_agent
    tools = [t.__name__ for t in root_agent.tools]
    print(f"  Tools: {tools}")
    if "get_page_content_with_images" in tools:
        print("  ✓ NEW TOOL DETECTED: get_page_content_with_images")
    else:
        print("  ⚠️  Warning: get_page_content_with_images not found")
except Exception as e:
    print(f"  ❌ Error: {e}")
    exit(1)
VERIFY_EOF

# Step 9: Export requirements
echo ""
echo "📋 Exporting requirements..."
uv export --no-hashes --no-header --no-dev --no-emit-project > app/app_utils/.requirements.txt
echo "✓ Requirements exported"

# Step 10: Deploy
echo ""
echo "🚀 Deploying to Agent Engine (this takes 3-5 minutes)..."
echo ""
echo "Running: make deploy"
echo ""

make deploy

# Step 11: Success
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  ✅ DEPLOYMENT SUCCESSFUL!                                     ║"
echo "║                                                                ║"
echo "║  New tool available: get_page_content_with_images()           ║"
echo "║                                                                ║"
echo "║  Next steps:                                                   ║"
echo "║  1. Wait 2 minutes for agent to stabilize                     ║"
echo "║  2. Test with: python scripts/smoke_remote_with_graph_token.py║"
echo "║  3. Upload OneNote content with images                        ║"
echo "║  4. Ask agent about diagrams/images                           ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
