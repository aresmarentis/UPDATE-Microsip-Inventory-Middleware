"""
PROJECT: Industrial Master List Management (ERP Microsip & Local Data)
AUTHOR: Ares Casale Marentis
AGE: 22 | Computer Engineering Student
-----------------------------------------------------------------------
ESPAÑOL:
Este archivo contiene la lógica completa para la administración de catálogos.
Integra de forma híbrida la base de datos SQL de Microsip (para materiales 
y proyectos) con archivos CSV locales (para nómina y trabajadores).
Implementa seguridad de acceso nivel campo y gestión de transacciones SQL.

ENGLISH:
Full implementation for catalog management. Features hybrid integration 
between Microsip SQL database (materials/projects) and local CSV files 
(workers/payroll). Implements field-level access security and SQL 
transaction management.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import csv
import os
import conexion_ms # Módulo de conexión Firebird SQL desarrollado previamente

# --- CONFIGURACIÓN DE RUTAS / PATH CONFIGURATION ---
# Usamos rutas protegidas que pueden ser configuradas vía variables de entorno
FILE_TRABAJADORES = os.getenv("MARETO_WORKERS_CSV", r"\\PROYECTOS\Mareto_sistema\lista_trabajadores.csv")

# Estado global del módulo
modo_edicion_trabajadores = False

# --- COMPONENTES VISUALES / UI WIDGETS ---

def mostrar_mensaje_temporal(root, mensaje):
    """
    ES: Notificación visual tipo 'Toast' para confirmar acciones sin interrumpir el flujo.
    EN: 'Toast' style visual notification to confirm actions without breaking the workflow.
    """
    top = tk.Toplevel(root)
    top.overrideredirect(True)
    x = root.winfo_x() + (root.winfo_width() // 2) - 100
    y = root.winfo_y() + (root.winfo_height() // 2) - 30
    top.geometry(f"250x60+{x}+{y}")
    top.configure(bg="#005500") 
    label = tk.Label(top, text=mensaje, fg="white", bg="#005500", font=("Arial", 12, "bold"))
    label.pack(expand=True, fill="both")
    top.after(1000, top.destroy)

# --- LÓGICA DE PROYECTOS (MICROSIP SQL) ---

def obtener_proyectos_microsip():
    db = conexion_ms.conectar()
    if not db: return []
    try:
        cursor = db.cursor()
        query = "SELECT NOMBRE FROM CENTROS_COSTO WHERE OCULTO IS NULL OR OCULTO = 'N' ORDER BY NOMBRE ASC"
        cursor.execute(query)
        return [row[0].strip() for row in cursor.fetchall()]
    except:
        try:
            cursor.execute("SELECT NOMBRE FROM CENTROS_COSTO ORDER BY NOMBRE ASC")
            return [row[0].strip() for row in cursor.fetchall()]
        except: return []
    finally:
        if db: db.close()

def agregar_proyecto_microsip(nombre, listbox, entry, combo):
    if not nombre.strip():
        messagebox.showwarning("Faltan datos", "El nombre es obligatorio.")
        return
    db = conexion_ms.conectar()
    if not db: return
    try:
        cursor = db.cursor()
        cursor.execute("SELECT MAX(CENTRO_COSTO_ID) FROM CENTROS_COSTO")
        max_id = cursor.fetchone()[0]
        nuevo_id = (max_id + 1) if max_id else 1
        query = "INSERT INTO CENTROS_COSTO (CENTRO_COSTO_ID, NOMBRE, OCULTO) VALUES (?, ?, 'N')"
        cursor.execute(query, (nuevo_id, nombre.upper().strip()))
        db.commit()
        mostrar_mensaje_temporal(listbox.master, "¡Proyecto Guardado!")
        entry.delete(0, tk.END)
        cargar_lista_visual(listbox, combo)
    except Exception as e:
        db.rollback()
        messagebox.showerror("Error SQL", str(e))
    finally: db.close()

def ocultar_proyecto_microsip(listbox, combo):
    seleccion = listbox.curselection()
    if not seleccion:
        messagebox.showwarning("Atención", "Selecciona un proyecto.")
        return
    nombre_proy = listbox.get(seleccion[0])
    if not messagebox.askyesno("Confirmar", f"¿Ocultar '{nombre_proy}'?"): return
    db = conexion_ms.conectar()
    if not db: return
    try:
        cursor = db.cursor()
        cursor.execute("UPDATE CENTROS_COSTO SET OCULTO = 'S' WHERE NOMBRE = ?", (nombre_proy,))
        db.commit()
        mostrar_mensaje_temporal(listbox.master, "¡Proyecto ocultado!")
        cargar_lista_visual(listbox, combo)
    except Exception as e:
        db.rollback(); messagebox.showerror("Error SQL", str(e))
    finally: db.close()

# --- LÓGICA DE MATERIALES (MICROSIP SQL) ---

def obtener_lineas_microsip():
    db = conexion_ms.conectar()
    if not db: return []
    try:
        cursor = db.cursor()
        cursor.execute("SELECT NOMBRE FROM LINEAS_ARTICULOS ORDER BY NOMBRE")
        return [row[0].strip() for row in cursor.fetchall()]
    except: return []
    finally:
        if db: db.close()

def obtener_unidades_microsip():
    return ["Caja", "Centímetro", "Pieza", "Kilogramo", "Litro", "Metro", "Servicio", "Tonelada", "Yarda"]

def cargar_materiales_microsip(listbox):
    listbox.delete(0, tk.END)
    db = conexion_ms.conectar()
    if not db: return
    try:
        cursor = db.cursor()
        cursor.execute("SELECT NOMBRE FROM ARTICULOS WHERE ESTATUS = 'A' ORDER BY NOMBRE")
        for row in cursor.fetchall(): listbox.insert(tk.END, row[0].strip())
    except: pass
    finally: db.close()

def agregar_item_microsip(nombre, linea_nom, unidad_nom, clave, listbox, en, cl, cu, ec):
    if not (nombre and linea_nom and unidad_nom):
        messagebox.showwarning("Faltan datos", "Nombre, Línea y Unidad son obligatorios.")
        return
    db = conexion_ms.conectar()
    if not db: return
    try:
        cursor = db.cursor()
        cursor.execute("SELECT MAX(ARTICULO_ID) FROM ARTICULOS")
        max_art = cursor.fetchone()[0]
        art_id = (max_art + 1) if max_art else 1
        
        cursor.execute("SELECT LINEA_ARTICULO_ID FROM LINEAS_ARTICULOS WHERE NOMBRE = ?", (linea_nom,))
        lin_id = cursor.fetchone()[0]

        cursor.execute("""INSERT INTO ARTICULOS (ARTICULO_ID, NOMBRE, LINEA_ARTICULO_ID, UNIDAD_VENTA, 
                          UNIDAD_COMPRA, CONTENIDO_UNIDAD_COMPRA, ESTATUS, ES_ALMACENABLE) 
                          VALUES (?, ?, ?, ?, ?, 1, 'A', 'S')""", 
                       (art_id, nombre.upper(), lin_id, unidad_nom, unidad_nom))

        if clave.strip():
            cursor.execute("SELECT MAX(CLAVE_ARTICULO_ID) FROM CLAVES_ARTICULOS")
            max_cla = cursor.fetchone()[0]
            cla_id = (max_cla + 1) if max_cla else 1
            cursor.execute("INSERT INTO CLAVES_ARTICULOS (CLAVE_ARTICULO_ID, ARTICULO_ID, CLAVE_ARTICULO, ROL_CLAVE_ART_ID) VALUES (?, ?, ?, 17)", 
                           (cla_id, art_id, clave.upper()))
        
        db.commit()
        mostrar_mensaje_temporal(listbox.master, "¡Material Guardado!")
        en.delete(0, tk.END); ec.delete(0, tk.END); cl.set(''); cu.set('')
        cargar_materiales_microsip(listbox)
        en.focus_set()
    except Exception as e:
        db.rollback(); messagebox.showerror("Error SQL", str(e))
    finally: db.close()

def borrar_item_microsip(listbox):
    seleccion = listbox.curselection()
    if not seleccion:
        messagebox.showwarning("Atención", "Selecciona un artículo.")
        return
    nombre = listbox.get(seleccion[0])
    if not messagebox.askyesno("Confirmar", f"¿Borrar '{nombre}' definitivamente de Microsip?"): return
    db = conexion_ms.conectar()
    if not db: return
    try:
        cursor = db.cursor()
        cursor.execute("SELECT ARTICULO_ID FROM ARTICULOS WHERE NOMBRE = ?", (nombre,))
        res = cursor.fetchone()
        if res:
            art_id = res[0]
            cursor.execute("DELETE FROM CLAVES_ARTICULOS WHERE ARTICULO_ID = ?", (art_id,))
            cursor.execute("DELETE FROM ARTICULOS WHERE ARTICULO_ID = ?", (art_id,))
            db.commit()
            mostrar_mensaje_temporal(listbox.master, "¡Eliminado!")
            cargar_materiales_microsip(listbox)
    except Exception as e:
        db.rollback(); messagebox.showerror("Error SQL", str(e))
    finally: db.close()

# --- LÓGICA DE TRABAJADORES (LOCAL CSV) ---

def cargar_lista_visual(listbox, combo):
    global modo_edicion_trabajadores
    listbox.delete(0, tk.END)
    tipo = combo.get()
    if tipo == "Materiales": 
        cargar_materiales_microsip(listbox)
    elif tipo == "Proyectos":
        for p in obtener_proyectos_microsip(): listbox.insert(tk.END, p)
    else:
        if os.path.exists(FILE_TRABAJADORES):
            filas = []
            with open(FILE_TRABAJADORES, mode='r', encoding='utf-8') as f:
                for fila in csv.reader(f):
                    if fila: filas.append(fila)
            filas.sort(key=lambda x: x[0].lower())
            for f in filas:
                nombre = f[0]
                sueldo = (f[1] if len(f) > 1 else "0") if modo_edicion_trabajadores else "****"
                listbox.insert(tk.END, f"{nombre:<40} ---- Sueldo: {sueldo}")

def agregar_item_csv(entry, listbox, combo):
    nuevo = entry.get().strip()
    if not nuevo: return
    with open(FILE_TRABAJADORES, mode='a', newline='', encoding='utf-8') as f:
        csv.writer(f).writerow([nuevo.upper(), "0"])
    entry.delete(0, tk.END)
    mostrar_mensaje_temporal(listbox.master, f"¡{nuevo} agregado!")
    cargar_lista_visual(listbox, combo)

def borrar_item_csv(listbox, combo):
    seleccion = listbox.curselection()
    if not seleccion: return
    texto_completo = listbox.get(seleccion[0])
    item_a_borrar = texto_completo.split('----')[0].strip()
    if not messagebox.askyesno("Confirmar", f"¿Eliminar a '{item_a_borrar}'?"): return
    filas_restantes = []
    if os.path.exists(FILE_TRABAJADORES):
        with open(FILE_TRABAJADORES, mode='r', encoding='utf-8') as f:
            for fila in csv.reader(f):
                if fila and fila[0].strip() != item_a_borrar:
                    filas_restantes.append(fila)
    with open(FILE_TRABAJADORES, mode='w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerows(filas_restantes)
    cargar_lista_visual(listbox, combo)

# --- CONSTRUCCIÓN DE INTERFAZ DINÁMICA ---

def montar_interfaz(contenedor, funcion_volver, usuario_logueado="USER", indice_inicio=0):
    global modo_edicion_trabajadores
    modo_edicion_trabajadores = False 

    for w in contenedor.winfo_children(): w.destroy()
    frame = tk.Frame(contenedor, bg="#222")
    frame.pack(fill="both", expand=True)

    # Header
    tk.Button(frame, text="⬅ Menú", command=lambda: [frame.destroy(), funcion_volver()], 
              bg="#222", fg="white", font=("Arial", 10, "bold"), bd=0).pack(anchor="nw", padx=15, pady=10)
    tk.Label(frame, text="EDITAR LISTAS MAESTRAS", bg="#222", fg="#d4af37", font=("Arial", 22, "bold")).pack(pady=(0, 15))
    
    combo_tipo = ttk.Combobox(frame, values=["Proyectos", "Materiales", "Trabajadores"], state="readonly", font=("Arial", 20), width=30)
    combo_tipo.current(indice_inicio); combo_tipo.pack(pady=10)

    # Estilo del Combobox
    style = ttk.Style()
    style.theme_use('clam') 
    contenedor.option_add('*TCombobox*Listbox.font', ("Arial", 14))
    
    frame_dinamico = tk.Frame(frame, bg="#222"); frame_dinamico.pack(pady=15)
    btn_editar_saldos = tk.Button(frame, text="EDITAR SALDOS", bg="#d4af37", fg="black", font=("Arial", 10, "bold"))

    # Lista Principal
    lb_frame = tk.Frame(frame, bg="#222"); lb_frame.pack(pady=10)
    lb = tk.Listbox(lb_frame, width=65, height=10, font=("Arial", 14), bg="#1e1e1e", fg="white", selectbackground="#d4af37") 
    lb.pack(side=tk.LEFT)
    sc = tk.Scrollbar(lb_frame, command=lb.yview); sc.pack(side=tk.RIGHT, fill=tk.Y); lb.config(yscrollcommand=sc.set)

    btn_accion = tk.Button(frame, text="ACCION", bg="#880000", fg="white", font=("Arial", 11, "bold"), width=25)
    btn_accion.pack(pady=15)

    # Panel de Sueldos (Restringido)
    f_sueldo = tk.Frame(frame, bg="#222")
    tk.Label(f_sueldo, text="SUELDO SEMANAL:", bg="#222", fg="#00FF00", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
    e_sueldo = tk.Entry(f_sueldo, font=("Arial", 14), width=15, justify="center")
    e_sueldo.pack(side=tk.LEFT, padx=10)

    def toggler_edicion():
        global modo_edicion_trabajadores
        if str(usuario_logueado).lower() != "gerardo":
            messagebox.showerror("Acceso Denegado", "Solo el usuario 'Gerardo' tiene privilegios de nómina.")
            return
        modo_edicion_trabajadores = not modo_edicion_trabajadores
        if modo_edicion_trabajadores:
            btn_editar_saldos.config(text="OCULTAR SALDOS", bg="#555", fg="white")
            f_sueldo.pack(pady=5)
        else:
            btn_editar_saldos.config(text="EDITAR SALDOS", bg="#d4af37", fg="black")
            f_sueldo.pack_forget()
        cargar_lista_visual(lb, combo_tipo)

    btn_editar_saldos.config(command=toggler_edicion)

    def guardar_sueldo_auto(event=None):
        seleccion = lb.curselection()
        if not seleccion: return
        texto_fila = lb.get(seleccion[0])
        nombre = texto_fila.split('----')[0].strip()
        nuevo_s = e_sueldo.get().strip()
        
        filas = []
        with open(FILE_TRABAJADORES, mode='r', encoding='utf-8') as f:
            for fila in csv.reader(f):
                if fila:
                    if fila[0] == nombre: filas.append([nombre, nuevo_s])
                    else: filas.append(fila)
        with open(FILE_TRABAJADORES, mode='w', newline='', encoding='utf-8') as f:
            csv.writer(f).writerows(filas)
        mostrar_mensaje_temporal(frame, "Sueldo Actualizado")
        cargar_lista_visual(lb, combo_tipo)

    e_sueldo.bind("<Return>", guardar_sueldo_auto)

    def cargar_sueldo_seleccion(event=None):
        if not modo_edicion_trabajadores: return
        seleccion = lb.curselection()
        if not seleccion: return
        texto_fila = lb.get(seleccion[0])
        nombre = texto_fila.split('----')[0].strip()
        try:
            with open(FILE_TRABAJADORES, mode='r', encoding='utf-8') as f:
                for fila in csv.reader(f):
                    if fila and fila[0] == nombre:
                        e_sueldo.delete(0, tk.END)
                        e_sueldo.insert(0, fila[1] if len(fila) > 1 else "0")
                        break
        except: pass

    lb.bind("<<ListboxSelect>>", cargar_sueldo_seleccion)

    def switch_vista(event=None):
        for w in frame_dinamico.winfo_children(): w.destroy()
        f_sueldo.pack_forget(); btn_editar_saldos.pack_forget()
        tipo = combo_tipo.get()
        
        if tipo == "Proyectos":
            btn_accion.config(text="OCULTAR SELECCIONADO", bg="#550000", command=lambda: ocultar_proyecto_microsip(lb, combo_tipo))
            f = tk.Frame(frame_dinamico, bg="#333", padx=20, pady=20); f.pack()
            tk.Label(f, text="NUEVO PROYECTO", bg="#333", fg="#d4af37", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=(0,15))
            e_p = tk.Entry(f, width=35, font=("Arial",15)); e_p.grid(row=1, column=0, padx=10)
            tk.Button(f, text="GUARDAR", bg="#005500", fg="white", font=("Arial", 10, "bold"), command=lambda: agregar_proyecto_microsip(e_p.get(), lb, e_p, combo_tipo)).grid(row=1, column=1, padx=10)        

        elif tipo == "Materiales":
            btn_accion.config(text="BORRAR SELECCIONADO", bg="#880000", command=lambda: borrar_item_microsip(lb))
            f_m = tk.Frame(frame_dinamico, bg="#333", padx=10, pady=10); f_m.pack()
            fuente_chica = ("Arial", 11)
            tk.Label(f_m, text="Nombre:", bg="#333", fg="white", font=fuente_chica).grid(row=0, column=0, sticky="e")
            en = tk.Entry(f_m, width=30, font=fuente_chica); en.grid(row=0, column=1, padx=5, pady=2)
            tk.Label(f_m, text="Línea:", bg="#333", fg="white", font=fuente_chica).grid(row=1, column=0, sticky="e")
            cl = ttk.Combobox(f_m, values=obtener_lineas_microsip(), state="readonly", width=28, font=fuente_chica); cl.grid(row=1, column=1, pady=2)
            tk.Label(f_m, text="Unidad:", bg="#333", fg="white", font=fuente_chica).grid(row=2, column=0, sticky="e")
            cu = ttk.Combobox(f_m, values=obtener_unidades_microsip(), state="readonly", width=28, font=fuente_chica); cu.grid(row=2, column=1, pady=2)
            tk.Label(f_m, text="Clave:", bg="#333", fg="white", font=fuente_chica).grid(row=3, column=0, sticky="e")
            ec = tk.Entry(f_m, width=30, font=fuente_chica); ec.grid(row=3, column=1, padx=5, pady=2)
            tk.Button(f_m, text="GUARDAR EN MICROSIP", bg="#005500", fg="white", font=("Arial", 10, "bold"), 
                      command=lambda: agregar_item_microsip(en.get(), cl.get(), cu.get(), ec.get(), lb, en, cl, cu, ec)).grid(row=4, column=0, columnspan=2, pady=10)
        
        else: # Vista Trabajadores
            btn_accion.config(text="BORRAR TRABAJADOR", bg="#880000", command=lambda: borrar_item_csv(lb, combo_tipo))
            btn_editar_saldos.pack(pady=5)
            f_t = tk.Frame(frame_dinamico, bg="#333", padx=15, pady=15); f_t.pack()
            e_t = tk.Entry(f_t, width=35, font=("Arial", 15)); e_t.pack(side=tk.LEFT, padx=10)
            tk.Button(f_t, text="AÑADIR", bg="#005500", fg="white", font=("Arial", 10, "bold"), command=lambda: agregar_item_csv(e_t, lb, combo_tipo)).pack(side=tk.LEFT)

        cargar_lista_visual(lb, combo_tipo)

    combo_tipo.bind("<<ComboboxSelected>>", switch_vista)
    switch_vista()

# --- FIN DEL MÓDULO COMPLETO ---
