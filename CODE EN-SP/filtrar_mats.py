"""
PROJECT: Industrial Material Search & Inventory Analytics
AUTHOR: Ares Casale Marentis
AGE: 22 | Computer Engineering Student
------------------------------------------------------------
ESPAÑOL:
Componente avanzado de búsqueda predictiva para catálogos de materiales. 
Implementa una interfaz de búsqueda tipo 'Google' sobre una base de datos 
plana (CSV), optimizando la recuperación de registros históricos de consumo 
mediante algoritmos de filtrado asíncronos y componentes visuales dinámicos.

ENGLISH:
Advanced predictive search component for material catalogs. 
Implements a 'Google-style' search interface over a flat database (CSV), 
optimizing record retrieval through asynchronous filtering algorithms 
and dynamic visual components.
"""

import tkinter as tk
from tkinter import ttk, Listbox
import csv
import os

# --- PATH ABSTRACTION / ABSTRACCIÓN DE RUTA ---
# ES: Referencia al historial centralizado en el servidor local.
# EN: Reference to the centralized history log on the local server.
ARCHIVO_DB = os.getenv("MARETO_INVENTORY_CSV", r"\\PROYECTOS\Mareto_sistema\historial_almacen.csv")



class GoogleSearchBox(tk.Frame):
    """
    ES: Widget reutilizable que encapsula la lógica de búsqueda predictiva.
    EN: Reusable widget encapsulating predictive search logic.
    """
    def __init__(self, parent, lista_datos, command=None, width=30, *args, **kwargs):
        super().__init__(parent, bg="black", *args, **kwargs)
        
        # Data Cleaning / Limpieza de duplicados
        self.lista_completa = sorted(list(set(lista_datos)))
        self.command = command
        self.var = tk.StringVar()
        
        # Main Entry Field
        self.entry = tk.Entry(self, textvariable=self.var, width=width, font=("Arial", 11))
        self.entry.pack(fill=tk.X)
        
        # UI Event Bindings / Enlace de eventos de interfaz
        self.entry.bind("<KeyRelease>", self.al_escribir)
        self.entry.bind("<Down>", self.mover_a_lista)
        self.entry.bind("<Return>", self.al_dar_enter)
        
        # Dropdown UI Setup / Configuración del menú desplegable
        self.lista_container = tk.Frame(self.winfo_toplevel(), bg="white", highlightbackground="gray", highlightthickness=1)
        self.lb = Listbox(self.lista_container, font=("Arial", 11), height=5, bg="white", fg="black", borderwidth=0)
        self.lb.pack(fill=tk.BOTH, expand=True)
        
        self.lb.bind("<ButtonRelease-1>", self.seleccionar_item)
        self.lb.bind("<Return>", self.seleccionar_item)
        self.winfo_toplevel().bind("<Button-1>", self.verificar_cierre_externo, add="+")

    def al_escribir(self, event):
        """
        ES: Filtra la lista de materiales en tiempo real basándose en la coincidencia de subcadenas.
        EN: Filters the material list in real-time based on substring matching.
        """
        if event.keysym in ('Up', 'Down', 'Return', 'Tab', 'Escape'): return
        texto = self.var.get().lower()
        if not texto: 
            self.cerrar_lista()
            return

        filtrados = [item for item in self.lista_completa if texto in item.lower()]
        if filtrados: self.mostrar_lista(filtrados)
        else: self.cerrar_lista()

    def mostrar_lista(self, items):
        """
        ES: Gestiona el posicionamiento de la lista flotante relativo al widget de entrada.
        EN: Manages floating list positioning relative to the entry widget.
        """
        self.lb.delete(0, tk.END)
        for item in items: self.lb.insert(tk.END, item)

        root_v = self.winfo_toplevel()
        # Coordinate calculation / Cálculo de coordenadas en pantalla
        x = self.entry.winfo_rootx() - root_v.winfo_rootx()
        y = (self.entry.winfo_rooty() - root_v.winfo_rooty()) + self.entry.winfo_height()
        w = self.entry.winfo_width()
        
        self.lista_container.place(x=x, y=y, width=w, height=120)
        self.lista_container.lift() 

    def cerrar_lista(self):
        self.lista_container.place_forget()

    def seleccionar_item(self, event=None):
        try:
            index = self.lb.curselection()
            if not index: return
            seleccion = self.lb.get(index)
            self.var.set(seleccion)
            self.cerrar_lista()
            if self.command: self.command()
        except: pass

    def get(self): return self.var.get()

# --- BUSINESS LOGIC / LÓGICA DE NEGOCIO ---

def obtener_materiales():
    """
    ES: Escanea la base de datos industrial para extraer el catálogo único de materiales registrados.
    EN: Scans the industrial database to extract the unique catalog of registered materials.
    """
    lista = set()
    if os.path.exists(ARCHIVO_DB):
        try:
            with open(ARCHIVO_DB, mode='r', encoding='utf-8') as f:
                lector = csv.reader(f)
                for fila in lector:
                    # Robust field validation / Validación robusta de campos
                    if len(fila) > 3 and fila[3].strip():
                        if fila[3].strip().lower() != "material":
                            lista.add(fila[3].strip())
        except: pass
    return sorted(list(lista))

def filtrar(tabla, buscador, lbl_resultado): 
    """
    ES: Actualiza el reporte visual con los consumos históricos del material seleccionado.
    EN: Updates the visual report with historical consumption of the selected material.
    """
    for item in tabla.get_children(): tabla.delete(item)
    buscado = buscador.get().strip().lower()
    
    if not buscado or not os.path.exists(ARCHIVO_DB): return

    encontrados = 0 
    try:
        with open(ARCHIVO_DB, mode='r', encoding='utf-8') as f:
            lector = csv.reader(f)
            for fila in lector:
                if len(fila) > 3 and fila[3].strip().lower() == buscado:
                    # ES: Inserción en orden descendente (más reciente arriba)
                    # EN: Insertion in descending order (most recent first)
                    tabla.insert("", 0, values=fila)
                    encontrados += 1 
        
        lbl_resultado.config(text=f"Total entries found: {encontrados}")
    except: 
        lbl_resultado.config(text="Database access error")

# --- UI ASSEMBLY / MONTAJE DE UI ---

def montar_interfaz(contenedor, funcion_volver):
    """
    ES: Genera el Dashboard de búsqueda en modo oscuro.
    EN: Generates the search Dashboard in Dark Mode.
    """
    frame = tk.Frame(contenedor, bg="black")
    frame.pack(fill="both", expand=True)

    # Styling and Layout / Estilo y Diseño
    # ... (Botones y Labels)

    lista_materiales = obtener_materiales()
    buscador_material = GoogleSearchBox(frame_busq, lista_datos=lista_materiales, width=45)
    buscador_material.pack(side=tk.LEFT, padx=10)

    

    # Data Table (Treeview) configuration
    columnas = ("Fecha", "Proyecto", "Cantidad", "Material", "Solicito")
    tabla = ttk.Treeview(frame, columns=columnas, show="headings", height=15)
    # ... (Configuración de columnas)

    # ES: Enlace de la lógica de filtrado al comando del buscador.
    # EN: Linking filtering logic to the search box command.
    buscador_material.command = lambda: filtrar(tabla, buscador_material, lbl_resultado)
    buscador_material.entry.focus_set()
