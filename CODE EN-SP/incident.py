"""
PROJECT: Industrial Incident Analytics & Automated PDF Reporting
AUTHOR: Ares Casale Marentis
AGE: 22 | Computer Engineering Student
-----------------------------------------------------------------------
ESPAÑOL:
Este archivo contiene la lógica íntegra del sistema de control de calidad. 
Incluye:
1. Cálculo proporcional de costos por daño en materiales (cm2 / metros).
2. Integración con Microsip para obtención de precios reales de stock.
3. Generación de documentos legales PDF con firmas y cláusulas de conformidad.
4. Interfaz dinámica con widgets predictivos y calendarios integrados.

ENGLISH:
Full implementation of the industrial quality control system. Features:
1. Proportional cost calculation for material damage (cm2 / meters).
2. Real-time Microsip integration for accurate stock pricing.
3. Automated legal PDF reporting with signature fields and compliance clauses.
4. Dynamic UI with predictive search widgets and integrated calendars.
"""

import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
import calendar
from datetime import datetime, date
import os
import csv
import sistema_almacen  # Módulo de almacén desarrollado previamente

# Generación de documentos PDF
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# --- CONFIGURACIÓN DE RUTAS ---
RUTA_RED = os.getenv("MARETO_NETWORK_PATH", r"\\PROYECTOS\Mareto_sistema")

class CalendarioIntegrado(tk.Frame):
    """Componente visual para la selección de fechas en reportes."""
    def __init__(self, parent, variable_destino, x, y, *args, **kwargs):
        super().__init__(parent, bg="white", bd=2, relief="ridge", *args, **kwargs)
        self.var = variable_destino
        self.hoy = date.today()
        self.anio, self.mes = self.hoy.year, self.hoy.month
        self.place(x=x, y=y - 200) 
        
        header = tk.Frame(self, bg="#1a1a1a")
        header.pack(fill="x")
        tk.Button(header, text="<", command=self.mes_ant, bg="#1a1a1a", fg="white", bd=0).pack(side="left")
        self.lbl_mes = tk.Label(header, text="", font=("Arial", 9, "bold"), bg="#1a1a1a", fg="white")
        self.lbl_mes.pack(side="left", expand=True)
        tk.Button(header, text=">", command=self.mes_sig, bg="#1a1a1a", fg="white", bd=0).pack(side="right")
        
        self.cuerpo = tk.Frame(self, bg="white")
        self.cuerpo.pack(padx=2, pady=2)
        self.dibujar()

    def dibujar(self):
        for w in self.cuerpo.winfo_children(): w.destroy()
        nombres_m = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        self.lbl_mes.config(text=f"{nombres_m[self.mes-1]} {self.anio}")
        for i, d in enumerate(["L", "M", "M", "J", "V", "S", "D"]):
            tk.Label(self.cuerpo, text=d, font=("Arial", 7, "bold"), bg="white").grid(row=0, column=i)
        
        cal = calendar.monthcalendar(self.anio, self.mes)
        for r, sem in enumerate(cal):
            for c, dia in enumerate(sem):
                if dia != 0:
                    btn = tk.Button(self.cuerpo, text=dia, width=2, font=("Arial", 8),
                                    command=lambda d=dia: self.seleccionar(d))
                    btn.grid(row=r+1, column=c, padx=1, pady=1)
                    if dia == self.hoy.day and self.mes == self.hoy.month and self.anio == self.hoy.year:
                        btn.config(bg="#8B0000", fg="white")

    def mes_ant(self):
        self.mes -= 1
        if self.mes == 0: self.mes = 12; self.anio -= 1
        self.dibujar()

    def mes_sig(self):
        self.mes += 1
        if self.mes == 13: self.mes = 1; self.anio += 1
        self.dibujar()

    def seleccionar(self, dia):
        self.var.set(f"{dia:02d}/{self.mes:02d}/{self.anio}")
        self.destroy()

def mostrar_notificacion_temporal(titulo, mensaje, tiempo=1000):
    aviso = tk.Toplevel()
    aviso.configure(bg="#004400")
    aviso.overrideredirect(True) 
    ancho, alto = 300, 80
    x = (aviso.winfo_screenwidth() // 2) - (ancho // 2)
    y = (aviso.winfo_screenheight() // 2) - (alto // 2)
    aviso.geometry(f"{ancho}x{alto}+{x}+{y}")
    tk.Label(aviso, text=mensaje, fg="white", bg="#004400", font=("Arial", 11, "bold"), pady=25).pack()
    aviso.after(tiempo, aviso.destroy)

def obtener_precio_real_microsip(m_nombre):
    """Consulta al ERP Microsip para obtener el costo promedio ponderado del artículo."""
    db = sistema_almacen.conexion_ms.conectar()
    if not db: return 0.0
    try:
        cursor = db.cursor()
        cursor.execute("SELECT ARTICULO_ID FROM ARTICULOS WHERE NOMBRE = ?", (m_nombre.upper(),))
        res_id = cursor.fetchone()
        if not res_id: return 0.0
        # Obtener costo de la última entrada válida
        cursor.execute("""SELECT FIRST 1 (ENTRADAS_COSTO / ENTRADAS_UNIDADES) 
                          FROM SALDOS_IN WHERE ARTICULO_ID = ? AND ENTRADAS_UNIDADES > 0 
                          ORDER BY ANO DESC, MES DESC""", (res_id[0],))
        res_p = cursor.fetchone()
        return float(res_p[0]) if res_p and res_p[0] else 0.0
    except: return 0.0
    finally: db.close()



def generar_pdf_incidente(trabajador, f_inicio, f_fin):
    """Genera el reporte PDF consolidado para un periodo y trabajador específico."""
    if not trabajador: return
    try:
        d_ini = datetime.strptime(f_inicio, "%d/%m/%Y")
        d_fin = datetime.strptime(f_fin, "%d/%m/%Y")
    except:
        messagebox.showerror("Error", "Formato de fecha inválido. Use dd/mm/aaaa")
        return
        
    nombre_archivo = f"Reporte_Incidentes_{trabajador.replace(' ', '_')}.pdf"
    doc = SimpleDocTemplate(nombre_archivo, pagesize=letter, 
                            leftMargin=50, rightMargin=50, topMargin=50, bottomMargin=150)
    elementos = []
    estilos = getSampleStyleSheet()
    
    # Estilos personalizados para el reporte
    estilo_n = ParagraphStyle('estilo_n', parent=estilos['Normal'], fontSize=9, alignment=1, leading=10)
    estilo_b = ParagraphStyle('estilo_b', parent=estilos['Normal'], fontSize=9, alignment=1, fontName='Helvetica-Bold')
    estilo_leyenda = ParagraphStyle('estilo_leyenda', parent=estilos['Normal'], fontSize=9, 
                                    alignment=1, leading=12, fontName='Helvetica-Oblique')
    
    elementos.append(Paragraph(f"HISTORIAL DE INCIDENTES - {trabajador.upper()}", estilos['Title']))
    elementos.append(Paragraph(f"Periodo: {f_inicio} al {f_fin}", estilos['Normal']))
    elementos.append(Spacer(1, 20))
    
    data = [["FECHA", "MATERIAL", "DESCRIPCIÓN", "COSTO"]]
    total_p = 0.0
    try:
        conn = sqlite3.connect(os.path.join(RUTA_RED, "incidentes.db"))
        cursor = conn.cursor()
        sql_ini, sql_fin = d_ini.strftime("%Y-%m-%d"), d_fin.strftime("%Y-%m-%d")
        
        # Query de filtrado por rango de fechas ISO
        cursor.execute("""
            SELECT SUBSTR(fecha, 1, 10), material, descripcion, costo FROM registro_incidentes 
            WHERE trabajador = ? 
            AND SUBSTR(fecha, 7, 4) || '-' || SUBSTR(fecha, 4, 2) || '-' || SUBSTR(fecha, 1, 2) BETWEEN ? AND ?
            ORDER BY id DESC
        """, (trabajador, sql_ini, sql_fin))
        
        filas = cursor.fetchall()
        conn.close()
        
        if not filas:
            messagebox.showinfo("Reporte", "No se encontraron registros para este trabajador en el periodo seleccionado.")
            return
            
        for f in filas:
            val = float(f[3]) if f[3] else 0.0
            total_p += val
            data.append([f[0], Paragraph(str(f[1]), estilo_n), Paragraph(str(f[2]), estilo_n), f"${val:,.2f}"])
        
        data.append(["", "", Paragraph("TOTAL PÉRDIDA:", estilo_b), f"${total_p:,.2f}"])
    except Exception as e:
        messagebox.showerror("Error DB", f"No se pudo generar el reporte: {e}"); return

    # Estilo de la tabla PDF
    t = Table(data, colWidths=[80, 170, 170, 90])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.red), 
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'), 
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, -1), (-1, -1), colors.yellow),
    ]))
    elementos.append(t)

    def footer(canvas, doc):
        """Dibuja el pie de página con firmas y cláusula de responsabilidad."""
        canvas.saveState()
        leyenda = (
            "Reconozco y acepto mi mal desempeño laboral en la calidad, productividad "
            "y cumplimiento de los procesos establecidos, en la fabricación y manejo de los "
            "muebles, incluyendo errores recurrentes, cortes, armado, acabados, uso de "
            "materiales inadecuadamente y falta de seguimiento a las instrucciones de trabajo."
        )
        p = Paragraph(f"<i>{leyenda}</i>", estilo_leyenda)
        w, h = p.wrap(doc.width, doc.bottomMargin)
        p.drawOn(canvas, doc.leftMargin, 100) 
        
        # Líneas de firma
        canvas.line(doc.leftMargin, 70, doc.leftMargin + 200, 70)
        canvas.line(doc.width + doc.leftMargin - 200, 70, doc.width + doc.leftMargin, 70)
        
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawCentredString(doc.leftMargin + 100, 55, "FIRMA DE TRABAJADOR")
        canvas.drawCentredString(doc.width + doc.leftMargin - 100, 55, "FIRMA DE ENCARGADO")
        canvas.restoreState()

    try:
        doc.build(elementos, onFirstPage=footer, onLaterPages=footer)
        os.startfile(nombre_archivo)
    except: 
        messagebox.showerror("Error", "Cierre el archivo PDF antes de generar uno nuevo con el mismo nombre.")

def montar_incidentes(contenedor, funcion_volver, es_admin, usuario_logeado="USER"):
    """Construye la interfaz completa de gestión de incidentes."""
    for widget in contenedor.winfo_children(): widget.destroy()
    
    try:
        dict_ms = sistema_almacen.cargar_materiales_microsip()
        mats = list(dict_ms.keys())
        trabs = sistema_almacen.cargar_lista_local(sistema_almacen.FILE_TRABAJADORES)
        lista_cantos = [m for m in mats if "CANTO" in m.upper()]
    except: mats, trabs, lista_cantos = [], [], []

    frame = tk.Frame(contenedor, bg="black")
    frame.pack(fill="both", expand=True)

    def actualizar_lista_reportes():
        try:
            conn = sqlite3.connect(os.path.join(RUTA_RED, "incidentes.db"))
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT trabajador FROM registro_incidentes")
            nombres = [r[0] for r in cursor.fetchall()]
            conn.close()
            combo_rep['values'] = nombres
        except: pass

    def actualizar_incidentes():
        try:
            nuevos_trabs = sistema_almacen.cargar_lista_local(sistema_almacen.FILE_TRABAJADORES)
            b_trab.lista_completa = sorted([str(i).strip() for i in nuevos_trabs if i])
            b_acom.lista_completa = sorted([str(i).strip() for i in nuevos_trabs if i])
            b_mat.lista_completa = sorted([str(i).strip() for i in mats if i])
        except: pass
        
        for item in tabla.get_children(): tabla.delete(item)
        try:
            conn = sqlite3.connect(os.path.join(RUTA_RED, "incidentes.db"))
            cursor = conn.cursor()
            cursor.execute("SELECT fecha, trabajador, material, descripcion, costo FROM registro_incidentes ORDER BY id DESC")
            for r in cursor.fetchall():
                p_fmt = f"${r[4]:,.2f}" if r[4] is not None else "$0.00"
                tabla.insert("", "end", values=(r[0], r[1], r[2], r[3], p_fmt))
            conn.close()
        except: pass
        actualizar_lista_reportes()

    frame.actualizar = actualizar_incidentes
    
    # Navegación
    tk.Button(frame, text="⬅ Menú", command=lambda: [frame.destroy(), funcion_volver()], 
              bg="black", fg="white", bd=0, font=("Arial", 10, "bold")).pack(anchor="nw", padx=10, pady=10)
    
    tk.Label(frame, text="REGISTRO DE INCIDENTES", bg="black", fg="#FF0000", font=("Arial", 22, "bold")).pack(pady=5)
    
    # Grid Principal
    f_split = tk.Frame(frame, bg="black"); f_split.pack(pady=10)
    f_form = tk.Frame(f_split, bg="black"); f_form.pack(side="left", padx=20, anchor="n")
    estilo_label = {"bg": "black", "fg": "white", "font": ("Arial", 12)}

    # Entradas de Datos
    tk.Label(f_form, text="Trabajador:", **estilo_label).grid(row=0, column=0, sticky="e", pady=5)
    b_trab = sistema_almacen.GoogleSearchBox(f_form, lista_datos=trabs, width=50)
    b_trab.grid(row=0, column=1, pady=5, padx=5, sticky="w")

    tk.Label(f_form, text="Material:", **estilo_label).grid(row=1, column=0, sticky="e", pady=5)
    f_mat_line = tk.Frame(f_form, bg="black")
    f_mat_line.grid(row=1, column=1, pady=5, padx=5, sticky="w")
    b_mat = sistema_almacen.GoogleSearchBox(f_mat_line, lista_datos=mats, width=38)
    b_mat.pack(side="left")
    
    tk.Label(f_mat_line, text="CANT:", **estilo_label).pack(side="left", padx=(10, 2))
    e_cantidad = tk.Entry(f_mat_line, width=5, font=("Arial", 11), justify="center")
    e_cantidad.insert(0, "1")
    e_cantidad.pack(side="left")

    tk.Label(f_form, text="Incidente:", **estilo_label).grid(row=2, column=0, sticky="e", pady=5)
    opciones = ["Material rayado / tallado", "Material golpeado / despostillado", "Error de corte / Medida incorrecta", "Material manchado", "Material quebrado", "Material Perdido", "Falta de piezas en el paquete", "Veta invertida", "OTRO"]
    combo_inc = ttk.Combobox(f_form, values=opciones, width=48, font=("Arial", 11), state="readonly")
    combo_inc.grid(row=2, column=1, pady=5, padx=5, sticky="w")

    # Campos Dinámicos
    frame_det = tk.Frame(f_form, bg="black")
    tk.Label(frame_det, text="¿Cuál?:", bg="black", fg="#d4af37", font=("Arial", 12)).pack(side="left")
    e_det = tk.Entry(frame_det, width=41, font=("Arial", 11)); e_det.pack(side="left", padx=5)

    var_cliente = tk.BooleanVar(); f_cliente_extra = tk.Frame(f_form, bg="black")
    def toggle_cliente():
        if var_cliente.get(): f_cliente_extra.grid(row=5, column=1, pady=5, sticky="w", padx=5)
        else: f_cliente_extra.grid_forget(); e_km.delete(0, tk.END); e_hrs.delete(0, tk.END)

    tk.Checkbutton(f_form, text="¿FUE CON UN CLIENTE?", variable=var_cliente, command=toggle_cliente,
                   bg="black", fg="#00FF00", font=("Arial", 10, "bold"), selectcolor="black").grid(row=4, column=1, sticky="w", padx=5)

    tk.Label(f_cliente_extra, text="KM:", fg="white", bg="black").pack(side="left")
    e_km = tk.Entry(f_cliente_extra, width=8, font=("Arial", 11)); e_km.pack(side="left", padx=5)
    tk.Label(f_cliente_extra, text="HRS PERDIDAS:", fg="white", bg="black").pack(side="left", padx=(10,0))
    e_hrs = tk.Entry(f_cliente_extra, width=8, font=("Arial", 11)); e_hrs.pack(side="left", padx=5)

    var_acom = tk.BooleanVar(); f_acom_box = tk.Frame(f_form, bg="black")
    def toggle_acom():
        if var_acom.get(): f_acom_box.grid(row=7, column=1, pady=5, sticky="w", padx=5)
        else: f_acom_box.grid_forget(); b_acom.set('')

    tk.Checkbutton(f_form, text="¿LLEVABA ACOMPAÑANTE?", variable=var_acom, command=toggle_acom,
                   bg="black", fg="#00FF00", font=("Arial", 10, "bold"), selectcolor="black").grid(row=6, column=1, sticky="w", padx=5)
    
    b_acom = sistema_almacen.GoogleSearchBox(f_acom_box, lista_datos=trabs, width=50); b_acom.pack()

    # Lógica de Medidas Especiales
    f_medidas_extra = tk.Frame(f_split, bg="black")
    f_med_box = tk.Frame(f_medidas_extra, bg="#1a1a1a", bd=2, relief="groove", padx=15, pady=10)
    # ... (Widgets de ancho/alto/daño omitidos aquí por brevedad pero incluidos en lógica de guardado)

    def obtener_sueldo_trabajador(nombre_trabajador):
        try:
            with open(sistema_almacen.FILE_TRABAJADORES, mode='r', encoding='utf-8') as f:
                lector = csv.reader(f)
                for fila in lector:
                    if fila and fila[0].strip() == nombre_trabajador:
                        return float(fila[1].replace('$', '').replace(',', '').strip())
        except: pass
        return 0.0

    def guardar():
        t, ac, m, i, d = b_trab.get(), b_acom.get(), b_mat.get(), combo_inc.get(), e_det.get()
        try: cant = float(e_cantidad.get() if e_cantidad.get() else 1)
        except: cant = 1

        if not (t and m and i and (i != "OTRO" or d)):
            messagebox.showwarning("Atención", "Complete todos los campos obligatorios.")
            return
            
        try:
            f_a = datetime.now().strftime("%d/%m/%Y %H:%M")
            p_mat = obtener_precio_real_microsip(m)
            conn = sqlite3.connect(os.path.join(RUTA_RED, "incidentes.db"))
            cursor = conn.cursor()

            # LÓGICA DE COSTEO POR ÁREA (Hojas Industriales)
            if f_med_box.winfo_viewable():
                v_ah, v_alh, v_bd, v_ad = float(e_ah.get()), float(e_alh.get()), float(e_bd.get()), float(e_ad.get())
                # Costo Proporcional: (Precio Hoja * (Área Daño / Área Hoja)) * Cantidad
                costo_m = round((p_mat * ((v_bd * v_ad) / (v_ah * v_alh))) * cant, 2)
                desc_m = f"{int(cant)}pzs {v_bd}x{v_ad}cm ({d if i == 'OTRO' else i})"
                cursor.execute("INSERT INTO registro_incidentes (fecha, trabajador, material, descripcion, costo) VALUES (?,?,?,?,?)", 
                               (f_a, t, m, desc_m, costo_m))
            
            # LÓGICA LOGÍSTICA (Gasolina y Tiempo)
            if var_cliente.get():
                km, hrs = float(e_km.get() or 0), float(e_hrs.get() or 0)
                if km > 0:
                    cursor.execute("INSERT INTO registro_incidentes ...", (f_a, t, "GASOLINA", f"Viaje {km}km", round(km * 6, 2)))
                if hrs > 0:
                    s_sem = obtener_sueldo_trabajador(t)
                    costo_h = round(hrs * (s_sem/50.5), 2)
                    cursor.execute("INSERT INTO registro_incidentes ...", (f_a, t, "TIEMPO PERDIDO", f"{hrs} hrs", costo_h))

            conn.commit(); conn.close()
            actualizar_incidentes()
            mostrar_notificacion_temporal("Éxito", "Registro Guardado")
        except Exception as e: messagebox.showerror("Error", f"Fallo al guardar incidente: {e}")

    # UI Botón Guardar y Tabla Final
    tk.Button(frame, text="GUARDAR INCIDENTE", bg="#8B0000", fg="white", font=("Arial", 12, "bold"), 
              width=35, command=guardar, bd=0).pack(pady=10)

    # ... (Resto de la tabla Treeview y botones de eliminación)
    actualizar_incidentes()
