"""
PROJECT: Warehouse Valuation & Inventory Financial Reporting
AUTHOR: Ares Casale Marentis
AGE: 22 | Computer Engineering Student
-----------------------------------------------------------------------
ESPAÑOL:
Este módulo genera reportes ejecutivos en PDF sobre el valor total del 
inventario. Realiza consultas SQL complejas (JOINs) al ERP Microsip, 
calculando el costo total basado en saldos de entradas y salidas, 
categorizando la información por líneas de productos y excluyendo activos 
no inventariables.

ENGLISH:
This module generates executive PDF reports regarding total inventory value. 
It performs complex SQL queries (JOINs) on the Microsip ERP, calculating 
total costs based on inflow and outflow balances, categorizing data by 
product lines, and excluding non-inventory assets.
"""

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import conexion_ms # ES: Módulo de enlace SQL / EN: SQL link module
from datetime import datetime
from tkinter import messagebox
import os
import tempfile



def generar_reporte_existencias():
    """
    ES: Orquestador de generación de reporte. Maneja la conexión DB, 
        el cálculo de sumatorias y el dibujo del lienzo PDF.
    EN: Report generation orchestrator. Manages DB connection, 
        summation calculations, and PDF canvas drawing.
    """
    db = microsip_con.conectar()
    if not db: 
        return

    # ES: Uso de archivos temporales para evitar conflictos de escritura.
    # EN: Using temporary files to prevent write conflicts.
    fd, path = tempfile.mkstemp(suffix='.pdf')
    
    try:
        c = canvas.Canvas(path, pagesize=letter)
        width, height = letter
        cursor = db.cursor()

        # --- SQL ANALYTICS LOGIC / LÓGICA DE ANALÍTICA SQL ---
        # ES: Consulta para obtener el valor neto (Entradas - Salidas) por categoría.
        # EN: Query to retrieve net value (Inflow - Outflow) per category.
        query_lineas = """
            SELECT 
                L.NOMBRE, 
                SUM(S.ENTRADAS_COSTO - S.SALIDAS_COSTO) as VALOR_TOTAL
            FROM SALDOS_IN S
            JOIN ARTICULOS A ON S.ARTICULO_ID = A.ARTICULO_ID
            JOIN LINEAS_ARTICULOS L ON A.LINEA_ARTICULO_ID = L.LINEA_ARTICULO_ID
            WHERE S.ALMACEN_ID = 19
            AND L.NOMBRE NOT IN ('HERRAMIENTA', 'MISCELANEOS', 'EQUIPO DE TRABAJO', 'ELECTRICIDAD')
            GROUP BY L.NOMBRE
            ORDER BY VALOR_TOTAL DESC
        """
        cursor.execute(query_lineas)
        res_lineas = cursor.fetchall()

        # ES: Cálculo del valor total de activos circulantes.
        # EN: Calculation of total current asset value.
        total_inventario = sum(float(fila[1] or 0) for fila in res_lineas)

        # --- PDF DRAWING LOGIC / LÓGICA DE DIBUJO PDF ---
        
        # Header / Encabezado
        c.setFont("Helvetica", 12)
        c.drawCentredString(width/2, height - 60, "MARETO MUEBLES CON ESTILO")
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(width/2, height - 90, "Costo Total de Almacén")
        
        y = height - 130
        c.setFont("Helvetica", 10)
        c.drawCentredString(width/2, y, f"Almacén General")
        c.drawCentredString(width/2, y - 15, f"Fecha de consulta: {datetime.now().strftime('%d/%m/%Y')}")

        # Summary Box / Cuadro de Resumen
        y -= 60
        c.setFillColorRGB(0.9, 0.9, 0.9)
        c.rect(100, y - 10, 400, 40, fill=1)
        c.setStrokeColorRGB(0, 0, 0)
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(120, y, "VALOR TOTAL DEL ALMACÉN:")
        c.drawRightString(480, y, f"${total_inventario:,.2f}")

        # Categories Breakdown / Desglose por Categorías
        y -= 50
        c.setFont("Helvetica-Bold", 11)
        c.drawString(100, y, "RESUMEN POR CATEGORÍAS:")
        y -= 5
        c.line(100, y, 500, y)
        
        y -= 20
        c.setFont("Helvetica", 10)
        for nombre, valor in res_lineas:
            valor_f = float(valor or 0)
            # ES: Filtro para omitir categorías sin saldo significativo.
            # EN: Filter to skip categories without significant balance.
            if abs(valor_f) > 0.01:
                c.drawString(110, y, f"{nombre}")
                c.drawRightString(490, y, f"${valor_f:,.2f}")
                y -= 18
            
            # Pagination Logic / Lógica de Paginación
            if y < 60:
                c.showPage()
                y = height - 60
                c.setFont("Helvetica", 10)

        c.save()
        
        # ES: Apertura automática del archivo generado en el visor predeterminado.
        # EN: Automatic opening of the generated file in the default viewer.
        os.startfile(path)
            
    except Exception as e:
        messagebox.showerror("Report Error", f"Failed to generate financial document: {e}")
    finally:
        # ES: Cierre de conexiones y recursos del sistema.
        # EN: Closing connections and system resources.
        db.close()
        os.close(fd)
