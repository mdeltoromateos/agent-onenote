#!/usr/bin/env python3
"""
Autonomous deployment script for OneNote Agent with Image Support.
Ejecuta: python3 autonomous_deploy.py
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description=""):
    """Ejecuta un comando y retorna resultado"""
    print(f"\n▶️  {description}")
    print(f"   Ejecutando: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(Path.cwd()),
            capture_output=False,
            text=True,
            shell=isinstance(cmd, str)
        )
        return result.returncode == 0
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("=" * 70)
    print("🚀 AUTONOMOUS DEPLOYMENT: OneNote Agent with Image Support")
    print("=" * 70)
    
    # 1. Navigate to deployment directory
    deploy_dir = Path.cwd() / "asistente-notas"
    if not deploy_dir.exists():
        print(f"\n❌ Error: {deploy_dir} not found")
        sys.exit(1)
    
    os.chdir(deploy_dir)
    print(f"\n✓ Working directory: {deploy_dir}")
    
    # 2. Export requirements
    print("\n📦 Exporting dependencies...")
    result = subprocess.run(
        ["uv", "export", "--no-hashes", "--no-header", "--no-dev", "--no-emit-project"],
        cwd=".",
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        with open("app/app_utils/.requirements.txt", "w") as f:
            f.write(result.stdout)
        print("✓ Requirements exported successfully")
    else:
        print(f"⚠️  Warning during export: {result.stderr}")
    
    # 3. Run make deploy
    print("\n" + "=" * 70)
    print("🚀 STARTING DEPLOYMENT (3-5 minutes)")
    print("=" * 70)
    
    success = run_command(
        "make deploy",
        "Executing: make deploy"
    )
    
    # 4. Results
    print("\n" + "=" * 70)
    if success:
        print("✅ DEPLOYMENT COMPLETED SUCCESSFULLY")
        print("\n✨ New tool available: get_page_content_with_images()")
    else:
        print("⚠️  Deployment completed (check output above for details)")
    
    print("\nNext steps:")
    print("1. Wait 2-3 minutes for agent to stabilize")
    print("2. Test: uv run python scripts/smoke_remote_with_graph_token.py")
    print("3. Upload OneNote content with images")
    print("4. Query agent about diagrams")
    print("=" * 70)

if __name__ == "__main__":
    main()
