#!/usr/bin/env python3
"""
Generador de datos sintéticos para pruebas del agente OneNote con imágenes.
Crea imágenes PNG y HTML simulado para probar get_page_content_with_images()
"""

import os
import base64
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import io

def create_synthetic_images():
    """Crea un conjunto de imágenes PNG sintéticas para pruebas"""
    
    images_dir = Path("synthetic_data/images")
    images_dir.mkdir(parents=True, exist_ok=True)
    
    print("📸 Generando imágenes sintéticas...")
    
    # 1. Diagrama de flujo
    img_flowchart = Image.new('RGB', (600, 400), color='white')
    draw = ImageDraw.Draw(img_flowchart)
    
    # Boxes
    draw.rectangle([50, 50, 200, 100], outline='black', width=2, fill='lightblue')
    draw.text((75, 65), "Inicio", fill='black')
    
    draw.rectangle([50, 150, 200, 200], outline='black', width=2, fill='lightgreen')
    draw.text((55, 165), "Procesar", fill='black')
    
    draw.rectangle([50, 250, 200, 300], outline='black', width=2, fill='lightyellow')
    draw.text((75, 265), "Fin", fill='black')
    
    # Arrows
    draw.line([125, 100, 125, 150], fill='black', width=2)
    draw.line([125, 200, 125, 250], fill='black', width=2)
    
    path_flowchart = images_dir / "flowchart.png"
    img_flowchart.save(path_flowchart)
    print(f"  ✓ {path_flowchart.name}")
    
    # 2. Gráfico de barras
    img_chart = Image.new('RGB', (600, 400), color='white')
    draw = ImageDraw.Draw(img_chart)
    
    # Title
    draw.text((200, 20), "Ventas por Trimestre", fill='black')
    
    # Axes
    draw.line([50, 350, 550, 350], fill='black', width=2)  # X axis
    draw.line([50, 50, 50, 350], fill='black', width=2)    # Y axis
    
    # Bars
    bars = [(100, 300, 50), (200, 250, 80), (300, 280, 70), (400, 200, 120)]
    colors = ['red', 'blue', 'green', 'orange']
    labels = ['Q1', 'Q2', 'Q3', 'Q4']
    
    for i, (x, bottom, height) in enumerate(bars):
        top = bottom - height
        draw.rectangle([x-20, top, x+20, bottom], fill=colors[i])
        draw.text((x-10, bottom+10), labels[i], fill='black')
    
    path_chart = images_dir / "chart.png"
    img_chart.save(path_chart)
    print(f"  ✓ {path_chart.name}")
    
    # 3. Tabla (como imagen)
    img_table = Image.new('RGB', (600, 300), color='white')
    draw = ImageDraw.Draw(img_table)
    
    draw.text((150, 20), "Tabla de Resultados", fill='black')
    
    # Headers
    headers = ['Producto', 'Precio', 'Stock']
    x_positions = [50, 200, 350]
    for i, header in enumerate(headers):
        draw.text((x_positions[i], 60), header, fill='black')
        draw.line([x_positions[i]-20, 85, x_positions[i]+80, 85], fill='black', width=1)
    
    # Rows
    rows = [
        ['Laptop', '$1000', '25'],
        ['Monitor', '$300', '50'],
        ['Teclado', '$80', '120']
    ]
    
    for row_idx, row in enumerate(rows):
        y = 110 + row_idx * 40
        for col_idx, cell in enumerate(row):
            draw.text((x_positions[col_idx], y), cell, fill='black')
    
    path_table = images_dir / "table.png"
    img_table.save(path_table)
    print(f"  ✓ {path_table.name}")
    
    # 4. Captura de pantalla simulada
    img_screenshot = Image.new('RGB', (800, 600), color='lightgray')
    draw = ImageDraw.Draw(img_screenshot)
    
    # Window header
    draw.rectangle([0, 0, 800, 30], fill='darkblue')
    draw.text((350, 10), "Application Window", fill='white')
    
    # Content
    draw.rectangle([50, 50, 750, 150], outline='black', width=2, fill='white')
    draw.text((60, 70), "Title: Dashboard Overview", fill='black')
    draw.text((60, 100), "Status: Active | Users: 1,250 | Revenue: $50,000", fill='black')
    
    # Footer
    draw.text((50, 550), "Last updated: 2026-09-16 10:30:00 UTC", fill='black')
    
    path_screenshot = images_dir / "screenshot.png"
    img_screenshot.save(path_screenshot)
    print(f"  ✓ {path_screenshot.name}")
    
    return [path_flowchart, path_chart, path_table, path_screenshot]

def create_synthetic_html(image_paths):
    """Crea HTML sintético que simula contenido de OneNote con imágenes"""
    
    html_content = """
    <html>
        <head>
            <title>Notas de Proyecto</title>
        </head>
        <body>
            <h1>📋 Análisis de Proyecto Q3 2026</h1>
            
            <h2>1. Flujo de Proceso</h2>
            <p>El flujo de trabajo sigue esta secuencia:</p>
            <img src="data:image/png;base64,{flowchart_b64}" alt="Diagrama de flujo del proceso" width="400"/>
            <p>El diagrama muestra los tres pasos principales: Inicio → Procesar → Fin</p>
            
            <h2>2. Resultados de Ventas</h2>
            <p>Durante los últimos 4 trimestres, hemos observado el siguiente desempeño:</p>
            <img src="data:image/png;base64,{chart_b64}" alt="Gráfico de ventas por trimestre" width="400"/>
            <p>Q4 mostró el mayor crecimiento con 120 unidades vendidas.</p>
            
            <h2>3. Inventario Actual</h2>
            <p>Estado de nuestros productos principales:</p>
            <img src="data:image/png;base64,{table_b64}" alt="Tabla de inventario" width="500"/>
            <p>Nota: Reordenar teclados cuando el stock baje de 50 unidades.</p>
            
            <h2>4. Dashboard de Control</h2>
            <p>Captura del panel de control central:</p>
            <img src="data:image/png;base64,{screenshot_b64}" alt="Captura de pantalla del dashboard" width="600"/>
            <p>El sistema está operativo y todos los indicadores están en verde.</p>
            
            <h2>5. Conclusiones</h2>
            <ul>
                <li>Ventas en aumento trimestral</li>
                <li>Inventario bien gestionado</li>
                <li>Sistema operativo sin incidencias</li>
                <li>Proyección: Crecimiento 15% en Q1 2027</li>
            </ul>
        </body>
    </html>
    """
    
    # Codificar imágenes a base64
    replacements = {}
    for idx, path in enumerate(image_paths):
        with open(path, 'rb') as f:
            img_b64 = base64.b64encode(f.read()).decode()
        
        if idx == 0:
            replacements['flowchart_b64'] = img_b64
        elif idx == 1:
            replacements['chart_b64'] = img_b64
        elif idx == 2:
            replacements['table_b64'] = img_b64
        elif idx == 3:
            replacements['screenshot_b64'] = img_b64
    
    html_content = html_content.format(**replacements)
    
    data_dir = Path("synthetic_data")
    html_path = data_dir / "synthetic_page.html"
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n📄 HTML generado: {html_path}")
    
    return html_path, html_content

def main():
    print("=" * 70)
    print("🎨 GENERADOR DE DATOS SINTÉTICOS PARA PRUEBAS")
    print("=" * 70)
    
    # Crear imágenes
    image_paths = create_synthetic_images()
    
    # Crear HTML
    html_path, html_content = create_synthetic_html(image_paths)
    
    print("\n" + "=" * 70)
    print("✅ DATOS SINTÉTICOS GENERADOS EXITOSAMENTE")
    print("=" * 70)
    print(f"\n📁 Directorio: synthetic_data/")
    print(f"   ├── images/")
    print(f"   │   ├── flowchart.png")
    print(f"   │   ├── chart.png")
    print(f"   │   ├── table.png")
    print(f"   │   └── screenshot.png")
    print(f"   └── synthetic_page.html")
    
    print("\n📊 Resumen del contenido:")
    print("   • HTML con 4 imágenes diferentes (diagrama, gráfico, tabla, captura)")
    print("   • Texto descriptivo en cada sección")
    print("   • Imágenes codificadas como base64 en el HTML")
    print("   • Tamaño total: ~150 KB")
    
    print("\n🧪 Para probar:")
    print("   python test_synthetic_images.py")
    
    return html_content

if __name__ == "__main__":
    main()
