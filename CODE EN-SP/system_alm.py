"""
PROJECT: Warehouse Core & Real-time ERP Synchronization (Microsip)
AUTHOR: Ares Casale Marentis
AGE: 22 | Computer Engineering Student
-----------------------------------------------------------------------
ESPAÑOL:
Motor transaccional íntegro. Implementa la salida de almacén mediante el 
método de costeo por capas (PEPS/FIFO). Automatiza la creación de documentos 
en Firebird SQL, gestiona la restauración de stock y sincroniza un historial 
local en CSV para redundancia de datos.

ENGLISH:
Full transactional engine. Implements warehouse exit logic using the 
layer costing method (FIFO). Automates document creation in Firebird SQL, 
manages stock restoration, and synchronizes a local CSV history for 
data redundancy.
"""

import tkinter as tk
from tkinter import ttk, Listbox, messagebox
import csv
import os
from datetime import datetime
import conexion_ms

# --- NETWORK ARCHITECTURE / ARQUITECTURA DE RED ---
RUTA_RED = os.getenv("MARETO_NETWORK_PATH", r"\\PROYECTOS\Mareto_sistema")

def obtener_ruta_red(archivo):
    return os.path.join(RUTA_RED, archivo)

ARCHIVO_HISTORIAL = obtener_ruta_red("historial_almacen.csv")
FILE_TRABAJADORES = obtener_ruta_red("lista_trabajadores.csv")



# --- FIFO COSTING LOGIC / LÓGICA DE COSTEO PEPS ---

def obtener_costo_unitario(cursor, articulo_id):
    """Calcula el costo real de la capa activa en el Almacén 19."""
    query = """
        SELECT FIRST 1 VALOR_TOTAL, EXISTENCIA 
        FROM CAPAS_COSTOS 
        WHERE ARTICULO_ID = ? AND ALMACEN_ID = 19 AND EXISTENCIA > 0
        ORDER BY FECHA ASC, CAPA_ID ASC
    """
    cursor.execute(query, (articulo_id,))
    res = cursor.fetchone()
    return (float(res[0]) / float(res[1])) if res else 0.0

def registrar_en_microsip(proyecto, material, cantidad):
    """
    Orquestador transaccional. Crea documentos (DOCTOS_IN) y detalles (DET).
    Actualiza saldos mensuales y capas de costos en Firebird SQL.
    """
    db = conexion_ms.conectar()
    if not db: return False, "Error de conexión con el servidor Microsip"
    
    try:
        cursor = db.cursor()
        proyecto_busqueda = proyecto.strip() 
        cant_f = float(cantidad)
        hoy = datetime.now()
        suc_id_real = 384 # Sucursal Mareto específica

        # 1. Recuperación de Artículo y Clave
        cursor.execute("""
            SELECT a.ARTICULO_ID, c.CLAVE_ARTICULO 
            FROM ARTICULOS a 
            JOIN CLAVES_ARTICULOS c ON a.ARTICULO_ID = c.ARTICULO_ID 
            WHERE TRIM(UPPER(a.NOMBRE)) = TRIM(UPPER(?))
        """, (material.strip(),))
        res_art = cursor.fetchone()
        if not res_art: return False, "Material no encontrado en Microsip"
        art_id, clave_art = res_art

        # 2. Identificación de Capa de Costo Activa (FIFO)
        cursor.execute("""
            SELECT FIRST 1 CAPA_ID, (VALOR_TOTAL / EXISTENCIA)
            FROM CAPAS_COSTOS WHERE ARTICULO_ID = ? AND ALMACEN_ID = 19 AND EXISTENCIA > 0
            ORDER BY FECHA ASC, CAPA_ID ASC
        """, (art_id,))
        capa_res = cursor.fetchone()
        
        if not capa_res:
            cursor.execute("""
                SELECT FIRST 1 CAPA_ID, 0.0 FROM CAPAS_COSTOS 
                WHERE ARTICULO_ID = ? AND ALMACEN_ID = 19
                ORDER BY FECHA DESC
            """, (art_id,))
            capa_res = cursor.fetchone()

        if not capa_res: return False, "El artículo no tiene capas en Almacén 19"
        
        capa_id, costo_u = capa_res[0], float(capa_res[1])
        valor_total_nuevo = round(cant_f * costo_u, 2)

        # 3. Gestión de Concepto y Documento Maestro
        cursor.execute("SELECT CONCEPTO_IN_ID, NATURALEZA FROM CONCEPTOS_IN WHERE NOMBRE = 'Consumo de materiales'")
        res_con = cursor.fetchone()
        c_id, natur = res_con[0], res_con[1]

        # Buscar si ya existe un documento del mismo proyecto hoy para agrupar
        cursor.execute("""
            SELECT FIRST 1 DOCTO_IN_ID, FOLIO FROM DOCTOS_IN 
            WHERE DESCRIPCION LIKE ? AND CONCEPTO_IN_ID = ? AND CANCELADO = 'N'
            ORDER BY DOCTO_IN_ID DESC
        """, (f"{proyecto_busqueda}%", c_id))
        res_doc = cursor.fetchone()

        if res_doc:
            docto_id, folio = res_doc 
        else:
            # Crear nuevo documento y asignar folio
            cursor.execute("SELECT SERIE, CONSECUTIVO + 1 FROM FOLIOS_CONCEPTOS WHERE CONCEPTO_ID = ?", (c_id,))
            res_f = cursor.fetchone()
            folio = f"{res_f[0]}{str(res_f[1]).zfill(7)}"
            cursor.execute("SELECT GEN_ID(ID_DOCTOS, 1) FROM RDB$DATABASE")
            docto_id = cursor.fetchone()[0]
            
            cursor.execute("""
                INSERT INTO DOCTOS_IN (DOCTO_IN_ID, ALMACEN_ID, CONCEPTO_IN_ID, FECHA, FOLIO, 
                DESCRIPCION, SUCURSAL_ID, SISTEMA_ORIGEN, NATURALEZA_CONCEPTO, CANCELADO, APLICADO)
                VALUES (?, 19, ?, 'NOW', ?, ?, ?, 'IN', ?, 'N', 'S')
            """, (docto_id, c_id, folio, proyecto.upper(), suc_id_real, natur))
            cursor.execute("UPDATE FOLIOS_CONCEPTOS SET CONSECUTIVO = CONSECUTIVO + 1 WHERE CONCEPTO_ID = ?", (c_id,))

        # 4. Inserción o Actualización de Partida (Detalle)
        cursor.execute("SELECT DOCTO_IN_DET_ID, UNIDADES, COSTO_TOTAL FROM DOCTOS_IN_DET WHERE DOCTO_IN_ID = ? AND ARTICULO_ID = ?", (docto_id, art_id))
        partida_existente = cursor.fetchone()

        if partida_existente:
            det_id, u_viejas, c_viejo = partida_existente
            un_totales = float(u_viejas) + cant_f
            co_totales = float(c_viejo) + valor_total_nuevo
            cursor.execute("UPDATE DOCTOS_IN_DET SET UNIDADES = ?, COSTO_TOTAL = ? WHERE DOCTO_IN_DET_ID = ?", (un_totales, co_totales, det_id))
            cursor.execute("UPDATE USOS_CAPAS_COSTOS SET UNIDADES = ?, VALOR_TOTAL = ? WHERE DOCTO_IN_DET_ID = ? AND CAPA_ID = ?", (un_totales, co_totales, det_id, capa_id))
        else:
            cursor.execute("SELECT GEN_ID(ID_DOCTOS, 1) FROM RDB$DATABASE")
            det_id = cursor.fetchone()[0]
            cursor.execute("""
                INSERT INTO DOCTOS_IN_DET (DOCTO_IN_DET_ID, DOCTO_IN_ID, ALMACEN_ID, CONCEPTO_IN_ID, ARTICULO_ID, 
                CLAVE_ARTICULO, UNIDADES, FECHA, TIPO_MOVTO, METODO_COSTEO, COSTO_UNITARIO, COSTO_TOTAL, APLICADO)
                VALUES (?, ?, 19, ?, ?, ?, ?, 'NOW', 'S', 'P', ?, ?, 'S')
            """, (det_id, docto_id, c_id, art_id, clave_art, cant_f, costo_u, valor_total_nuevo))
            cursor.execute("INSERT INTO USOS_CAPAS_COSTOS (UNIDADES, VALOR_TOTAL, DOCTO_IN_DET_ID, CAPA_ID, TIPO_USO) VALUES (?, ?, ?, ?, 'S')", (cant_f, valor_total_nuevo, det_id, capa_id))

        # 5. Afectación de Inventarios y Capas
        cursor.execute("UPDATE SALDOS_IN SET SALIDAS_UNIDADES = SALIDAS_UNIDADES + ?, SALIDAS_COSTO = SALIDAS_COSTO + ? WHERE ARTICULO_ID = ? AND ALMACEN_ID = 19 AND ANO = ? AND MES = ?", (cant_f, valor_total_nuevo, art_id, hoy.year, hoy.month))
        cursor.execute("UPDATE CAPAS_COSTOS SET EXISTENCIA = EXISTENCIA - ?, VALOR_TOTAL = VALOR_TOTAL - ? WHERE CAPA_ID = ?", (cant_f, valor_total_nuevo, capa_id))

        db.commit()
        return True, f"Registrado en Folio {folio}"
    
    except Exception as e:
        if db: db.rollback()
        return False, str(e)
    finally:
        if db: db.close()

# --- CATALOG LOADERS ---

def cargar_proyectos_microsip():
    db = conexion_ms.conectar()
    if not db: return []
    try:
        cursor = db.cursor()
        cursor.execute("SELECT NOMBRE FROM CENTROS_COSTO ORDER BY NOMBRE ASC")
        return [row[0].strip() for row in cursor.fetchall()]
    except: return []
    finally: db.close()

def cargar_materiales_microsip():
    db = conexion_ms.conectar()
    if not db: return {}
    try:
        cursor = db.cursor()
        cursor.execute("SELECT NOMBRE, UNIDAD_VENTA FROM ARTICULOS WHERE ESTATUS = 'A' ORDER BY NOMBRE ASC")
        return {row[0].strip(): (row[1].strip() if row[1] else "PZA") for row in cursor.fetchall()}
    except: return {}
    finally: db.close()

# --- UI CLASS: SEARCH BOX ---

class GoogleSearchBox(tk.Frame):
    def __init__(self, parent, lista_datos, width=30, callback_seleccion=None, *args, **kwargs):
        super().__init__(parent, bg="black", *args, **kwargs)
        self.lista_completa = sorted([str(i).strip() for i in lista_datos if i])
        self.var = tk.StringVar()
        self.callback_seleccion = callback_seleccion
        self.siguiente_widget = None 
        
        self.entry = tk.Entry(self, textvariable=self.var, width=width, font=("Arial", 11))
        self.entry.pack(fill=tk.X)
        self.entry.bind("<KeyRelease>", self.al_escribir)
        self.entry.bind("<Down>", self.mover_a_lista)
        self.entry.bind("<Return>", self.al_dar_enter)
        
        self.lista_container = tk.Frame(self.winfo_toplevel(), bg="white", highlightthickness=1)
        self.lb = Listbox(self.lista_container, font=("Arial", 11), height=5)
        self.lb.pack(fill=tk.BOTH, expand=True)
        self.lb.bind("<ButtonRelease-1>", self.seleccionar_item)
        self.winfo_toplevel().bind("<Button-1>", self.verificar_cierre_externo, add="+")

    def al_escribir(self, event):
        if event.keysym in ('Up', 'Down', 'Return'): return
        texto = self.var.get().lower()
        if not texto: self.cerrar_lista(); return
        filtrados = [item for item in self.lista_completa if texto in item.lower()]
        if filtrados: self.mostrar_lista(filtrados)
        else: self.cerrar_lista()

    def mostrar_lista(self, items):
        self.lb.delete(0, tk.END)
        for item in items: self.lb.insert(tk.END, item)
        root_v = self.winfo_toplevel()
        x = self.entry.winfo_rootx() - root_v.winfo_rootx()
        y = (self.entry.winfo_rooty() - root_v.winfo_rooty()) + self.entry.winfo_height()
        self.lista_container.place(x=x, y=y, width=self.entry.winfo_width(), height=120)
        self.lista_container.lift() 

    def seleccionar_item(self, event=None):
        try:
            seleccion = self.lb.get(self.lb.curselection())
            self.var.set(seleccion); self.cerrar_lista()
            if self.callback_seleccion: self.callback_seleccion()
            if self.siguiente_widget: self.siguiente_widget.focus_set()
        except: pass

    def mover_a_lista(self, event):
        if self.lista_container.winfo_viewable(): self.lb.focus_set(); self.lb.select_set(0)

    def al_dar_enter(self, event):
        if self.lista_container.winfo_viewable(): self.seleccionar_item()
        elif self.siguiente_widget: self.siguiente_widget.focus_set()

    def cerrar_lista(self): self.lista_container.place_forget()
    def verificar_cierre_externo(self, event):
        if event.widget != self.entry and event.widget != self.lb: self.cerrar_lista()
    def get(self): return self.var.get()
    def set(self, v): self.var.set(v)

# --- UI MOUNTING ---

def montar_interfaz(contenedor, funcion_volver, usuario_logeado="USER"):
    frame = tk.Frame(contenedor, bg="black")
    frame.pack(fill="both", expand=True)

    dict_ms = cargar_materiales_microsip()
    mats = list(dict_ms.keys())
    proyectos_ms = cargar_proyectos_microsip()

    # Header
    tk.Button(frame, text="⬅ Menú", command=lambda: [frame.destroy(), funcion_volver()], bg="black", fg="white", bd=0).pack(anchor="nw", padx=10, pady=10)
    tk.Label(frame, text=datetime.now().strftime("%d/%m/%Y"), bg="black", fg="yellow", font=("Arial", 22, "bold")).pack(pady=5)

    f = tk.Frame(frame, bg="black"); f.pack(pady=10)

    # Form Fields
    tk.Label(f, text="Proyecto:", bg="black", fg="white").grid(row=0, column=0, sticky="e")
    b_proy = GoogleSearchBox(f, lista_datos=proyectos_ms, width=60)
    b_proy.grid(row=0, column=1, pady=5, padx=5)

    tk.Label(f, text="Material:", bg="black", fg="white").grid(row=1, column=0, sticky="e")
    def act_u(): ent_u.config(state='normal'); ent_u.delete(0, tk.END); ent_u.insert(0, dict_ms.get(b_mat.get(), "")); ent_u.config(state='readonly')
    b_mat = GoogleSearchBox(f, lista_datos=mats, callback_seleccion=act_u, width=60)
    b_mat.grid(row=1, column=1, pady=5, padx=5)

    tk.Label(f, text="Unidad:", bg="black", fg="white").grid(row=2, column=0, sticky="e")
    ent_u = tk.Entry(f, width=30, state='readonly'); ent_u.grid(row=2, column=1, sticky="w", padx=5)

    tk.Label(f, text="Cantidad:", bg="black", fg="white").grid(row=3, column=0, sticky="e")
    e_cant = tk.Entry(f, width=30); e_cant.grid(row=3, column=1, sticky="w", padx=5)

    tk.Label(f, text="Solicitó:", bg="black", fg="white").grid(row=4, column=0, sticky="e")
    b_sol = GoogleSearchBox(f, lista_datos=cargar_lista_local(FILE_TRABAJADORES), width=30)
    b_sol.grid(row=4, column=1, sticky="w", padx=5)

    # Treeview Results
    cols = ("Fecha", "Proyecto", "Cantidad", "Material", "Solicito")
    tabla = ttk.Treeview(frame, columns=cols, show="headings", height=8)
    for c in cols: tabla.heading(c, text=c.upper()); tabla.column(c, width=150, anchor="center")
    tabla.pack(pady=10, padx=20, fill="both", expand=True)

    def guardar_handler():
        proy, cant, mat, sol = b_proy.get(), e_cant.get(), b_mat.get(), b_sol.get()
        if not (proy and cant and mat and sol):
            messagebox.showwarning("Faltan datos", "Complete todos los campos."); return
        
        exito, msj = registrar_en_microsip(proy, mat, cant)
        if exito:
            datos = [datetime.now().strftime("%d/%m/%Y"), proy, f"{cant} {ent_u.get()}", mat, sol]
            with open(ARCHIVO_HISTORIAL, mode='a', newline='', encoding='utf-8') as f: csv.writer(f).writerow(datos)
            tabla.insert("", 0, values=datos)
            # Reset form
            for b in [b_proy, b_mat, b_sol]: b.set('')
            e_cant.delete(0, tk.END); b_proy.entry.focus()
            messagebox.showinfo("Éxito", msj)
        else: messagebox.showerror("Error ERP", msj)

    tk.Button(frame, text="GUARDAR REGISTRO", bg="#005500", fg="white", font=("Arial", 12, "bold"), command=guardar_handler).pack(pady=15)

    # Initial Load
    if os.path.exists(ARCHIVO_HISTORIAL):
        with open(ARCHIVO_HISTORIAL, mode='r', encoding='utf-8') as h:
            for r in reversed(list(csv.reader(h))): 
                if r: tabla.insert("", "end", values=r)

    b_proy.siguiente_widget = b_mat.entry
    b_mat.siguiente_widget = e_cant
    e_cant.bind("<Return>", lambda e: b_sol.entry.focus())
    b_sol.siguiente_widget = None # Guardar vía botón o Enter
