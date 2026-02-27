"""
PROJECT: Workforce Activity Monitor & Historical Auditor
AUTHOR: Ares Casale Marentis
AGE: 22 | Computer Engineering Student
------------------------------------------------------------
ESPAÑOL:
Este módulo permite auditar la actividad de los trabajadores en el almacén.
Utiliza un motor de búsqueda predictiva para filtrar el historial de salidas
por el nombre del solicitante, facilitando el control de insumos y la 
responsabilidad operativa dentro de la red local.

ENGLISH:
This module enables warehouse workforce activity auditing.
It utilizes a predictive search engine to filter checkout history by the 
requestor's name, streamlining supply control and operational 
accountability within the local network.
"""

import tkinter as tk
from tkinter import ttk, Listbox, messagebox
import csv
import os

# --- DATA PERSISTENCE LAYER / CAPA DE PERSISTENCIA ---
# ES: Referencia al historial centralizado para garantizar integridad.
# EN: Reference to centralized history to ensure data integrity.
ARCHIVO_DB = os.getenv("MARETO_HISTORY_PATH", r"\\PROYECTOS\Mareto_sistema\historial_almacen.csv")



class GoogleSearchBox(tk.Frame):
    """
    ES: Componente de búsqueda inteligente con posicionamiento dinámico de lista.
    EN: Intelligent search component with dynamic list positioning.
    """
    def __init__(self, parent, lista_datos, command=None, width=30, *args, **kwargs):
        super().__init__(parent, bg="black", *args, **kwargs)
        
        # Unique sorting logic / Lógica de ordenamiento único
        self.lista_completa = sorted(list(set(lista_datos)))
        self.command = command
        self.var = tk.StringVar()
        
        # Entry Widget / Campo de texto
        self.entry = tk.Entry(self, textvariable=self.var, width=width, font=("Arial", 11))
        self.entry.pack(fill=tk.X)
        
        # Handlers for smooth navigation / Manejadores para navegación fluida
        self.entry.bind("<KeyRelease>", self.al_escribir)
        self.entry.bind("<Down>", self.mover_a_lista)
        self.entry.bind("<Return>", self.al_dar_enter)
        
        # Floating List Container / Contenedor de lista flotante
        self.lista_container = tk.Frame(self.winfo_toplevel(), bg="white", highlightbackground="gray", highlightthickness=1)
        self.lb = Listbox(self.lista_container, font=("Arial", 11), height=5, bg="white", fg="black", borderwidth=0)
        self.lb.pack(fill=tk.BOTH, expand=True)
        
        self.lb.bind("<ButtonRelease-1>", self.seleccionar_item)
        self.lb.bind("<Return>", self.seleccionar_item)
        self.winfo_toplevel().bind("<Button-1>", self.verificar_cierre_externo, add="+")

    def al_escribir(self, event):
        if event.keysym in ('Up', 'Down', 'Return', 'Tab', 'Escape'): return
        texto = self.var.get().lower()
        if not texto: 
            self.cerrar_lista()
            return
        # Real-time substring filter / Filtro de subcadenas en tiempo real
        filtrados = [item for item in self.lista_completa if texto in item.lower()]
        if filtrados: self.mostrar_lista(filtrados)
        else: self.cerrar_lista()

    def mostrar_lista(self, items):
        self.lb.delete(0, tk.END)
        for item in items: self.lb.insert(tk.END, item)
        root_v = self.winfo_toplevel()
        # Relative coordinate mapping / Mapeo de coordenadas relativas
        x = self.entry.winfo_rootx() - root_v.winfo_rootx()
        y = (self.entry.winfo_rooty() - root_v.winfo_rooty()) + self.entry.winfo_height()
        w = self.entry.winfo_width()
        self.lista_container.place(x=x, y=y, width=w, height=120)
        self.lista_container.lift() 

    def seleccionar_item(self, event=None):
        try:
            index = self.lb.curselection()
            if not index: return
            seleccion = self.lb.get(index)
            self.var.set(seleccion)
            self.cerrar_lista()
            if self.command: self.command()
        except: pass

    def cerrar_lista(self):
        self.lista_container.place_forget()

    def verificar_cierre_externo(self, event):
        if event.widget != self.entry and event.widget != self.lb:
            self.after(100, self.cerrar_lista)
        
    def get(self): return self.var.get()

# --- BUSINESS LOGIC / LÓGICA DE NEGOCIO ---

def obtener_trabajadores():
    """
    ES: Escanea el archivo histórico para extraer la lista de personal activo.
    EN: Scans the history file to extract the list of active staff.
    """
    lista = set()
    if os.path.exists(ARCHIVO_DB):
        try:
            with open(ARCHIVO_DB, mode='r', encoding='utf-8') as f:
                lector = csv.reader(f)
                for fila in lector:
                    # Column 4: Employee name / Columna 4: Nombre del empleado
                    if len(fila) > 4 and fila[4].strip():
                        if fila[4].strip().lower() != "solicito":
                            lista.add(fila[4].strip())
        except: pass
    return sorted(list(lista))

def filtrar(tabla, buscador, lbl_resultado):
    """
    ES: Procesa la búsqueda y actualiza la tabla con los registros del trabajador.
    EN: Processes the search and updates the table with the worker's records.
    """
    for item in tabla.get_children(): tabla.delete(item)
    buscado = buscador.get().strip().lower()
    if not buscado or not os.path.exists(ARCHIVO_DB): 
        lbl_resultado.config(text="Entries found: 0")
        return

    encontrados = 0
    try:
        with open(ARCHIVO_DB, mode='r', encoding='utf-8') as f:
            lector = csv.reader(f)
            for fila in lector:
                if len(fila) > 4 and fila[4].strip().lower() == buscado:
                    tabla.insert("", 0, values=fila) # Push newest to top / Los más nuevos arriba
                    encontrados += 1
        lbl_resultado.config(text=f"Total records for employee: {encontrados}")
    except Exception as e:
        lbl_resultado.config(text=f"Database Access Error: {e}")

# --- UI MOUNTING / MONTAJE DE LA INTERFAZ ---

def montar_interfaz(contenedor, funcion_volver):
    """
    ES: Genera el Dashboard de auditoría de personal.
    EN: Generates the staff auditing Dashboard.
    """
    frame = tk.Frame(contenedor, bg="black")
    frame.pack(fill="both", expand=True)

    # Navigation / Navegación
    tk.Button(frame, text="⬅ Historial", 
              command=lambda: [frame.destroy(), funcion_volver()],
              bg="#000000", fg="white", font=("Arial", 10, "bold"), bd=0).pack(anchor="nw", padx=10, pady=10)

    tk.Label(frame, text="STAFF ACTIVITY MONITOR", bg="black", fg="#d4af37", font=("Arial", 16, "bold")).pack(pady=20)

    # Search Bar Area / Área de Búsqueda
    frame_busq = tk.Frame(frame, bg="black")
    frame_busq.pack(pady=10)
    tk.Label(frame_busq, text="Requestor Name:", bg="black", fg="white", font=("Arial", 12)).pack(side=tk.LEFT, padx=10)

    buscador_trabajador = GoogleSearchBox(frame_busq, lista_datos=obtener_trabajadores(), width=42)
    buscador_trabajador.pack(side=tk.LEFT, padx=10)

    

    # Results Table (Treeview)
    tabla_container = tk.Frame(frame, bg="black")
    tabla_container.pack(pady=20, anchor="center")

    columnas = ("Date", "Project", "Quantity", "Material", "Staff")
    tabla = ttk.Treeview(tabla_container, columns=columnas, show="headings", height=15)
    
    # Column styling / Estilo de columnas
    anchos = {"Date": 120, "Project": 250, "Quantity": 80, "Material": 400, "Staff": 180}
    for col in columnas:
        tabla.heading(col, text=col)
        tabla.column(col, width=anchos.get(col, 150), anchor="center")

    tabla.pack(side=tk.LEFT)
    
    lbl_resultado = tk.Label(frame, text="", bg="black", fg="yellow", font=("Arial", 10, "bold"))
    lbl_resultado.pack(pady=10)

    # Connect components / Conectar componentes
    buscador_trabajador.command = lambda: filtrar(tabla, buscador_trabajador, lbl_resultado)
    buscador_trabajador.entry.focus_set()
