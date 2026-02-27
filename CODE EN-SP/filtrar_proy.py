"""
PROJECT: Industrial Project Auditor & Analytics UI
AUTHOR: Ares Casale Marentis
AGE: 22 | Computer Engineering Student
------------------------------------------------------------
ESPAÑOL:
Este módulo implementa una herramienta de auditoría para el análisis de 
consumo por proyecto. Utiliza el componente 'GoogleSearchBox' para filtrar 
registros masivos en el historial (CSV), permitiendo a la gerencia visualizar 
en tiempo real todos los materiales asignados a una obra específica.

ENGLISH:
This module implements an auditing tool for project-based consumption analysis. 
It utilizes the 'GoogleSearchBox' component to filter massive history logs (CSV), 
enabling management to visualize in real-time all materials assigned to 
a specific project or work site.
"""

import tkinter as tk
from tkinter import ttk, Listbox, messagebox
import csv
import os

# --- DATA SOURCE CONFIGURATION / CONFIGURACIÓN DE ORIGEN DE DATOS ---
# ES: Referencia al historial centralizado para garantizar la integridad de los datos.
# EN: Reference to centralized history to ensure data integrity.
ARCHIVO_DB = os.getenv("MARETO_HISTORY_PATH", r"\\PROYECTOS\Mareto_sistema\historial_almacen.csv")



class GoogleSearchBox(tk.Frame):
    """
    ES: Widget de búsqueda predictiva reutilizable. Implementa lógica de autocompletado.
    EN: Reusable predictive search widget. Implements autocomplete logic.
    """
    def __init__(self, parent, lista_datos, command=None, width=30, *args, **kwargs):
        super().__init__(parent, bg="black", *args, **kwargs)
        
        # Data sorting and cleaning / Limpieza y ordenamiento de datos
        self.lista_completa = sorted(list(set(lista_datos)))
        self.command = command
        self.var = tk.StringVar()
        
        self.entry = tk.Entry(self, textvariable=self.var, width=width, font=("Arial", 11))
        self.entry.pack(fill=tk.X)
        
        # Event bindings for UX / Enlace de eventos para experiencia de usuario
        self.entry.bind("<KeyRelease>", self.al_escribir)
        self.entry.bind("<Down>", self.mover_a_lista)
        self.entry.bind("<Return>", self.al_dar_enter)
        
        # Floating suggestion list / Lista flotante de sugerencias
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
        # Substring matching algorithm / Algoritmo de coincidencia de subcadenas
        filtrados = [item for item in self.lista_completa if texto in item.lower()]
        if filtrados: self.mostrar_lista(filtrados)
        else: self.cerrar_lista()

    def mostrar_lista(self, items):
        self.lb.delete(0, tk.END)
        for item in items: self.lb.insert(tk.END, item)
        root_v = self.winfo_toplevel()
        # Relative coordinate calculation / Cálculo de coordenadas relativas
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

# --- BUSINESS LOGIC FUNCTIONS / FUNCIONES DE LÓGICA DE NEGOCIO ---

def obtener_proyectos_reales():
    """
    ES: Extrae nombres de proyectos únicos del historial para el motor de búsqueda.
    EN: Extracts unique project names from history for the search engine.
    """
    lista = set()
    if os.path.exists(ARCHIVO_DB):
        try:
            with open(ARCHIVO_DB, mode='r', encoding='utf-8') as f:
                lector = csv.reader(f)
                for fila in lector:
                    if len(fila) > 1 and fila[1].strip():
                        if fila[1].strip().lower() != "proyecto":
                            lista.add(fila[1].strip())
        except: pass
    return sorted(list(lista))

def realizar_filtrado(tabla, buscador, lbl_resultado):
    """
    ES: Procesa el archivo de base de datos para recuperar el historial de un proyecto.
    EN: Processes the database file to retrieve a project's historical log.
    """
    for item in tabla.get_children(): tabla.delete(item)
    buscado = buscador.get().strip().lower()
    if not buscado or not os.path.exists(ARCHIVO_DB): return

    encontrados = 0
    try:
        with open(ARCHIVO_DB, mode='r', encoding='utf-8') as archivo:
            lector = csv.reader(archivo)
            for fila in lector: 
                # Column index 1: Project Name / Índice 1: Nombre del Proyecto
                if len(fila) > 1 and fila[1].strip().lower() == buscado:
                    tabla.insert("", 0, values=fila) # Stack newest on top / Los más nuevos arriba
                    encontrados += 1
        lbl_resultado.config(text=f"Records found: {encontrados}")
    except Exception as e:
        messagebox.showerror("I/O Error", f"Could not access database: {str(e)}")

# --- INTERFACE MOUNTING / MONTAJE DE LA INTERFAZ ---

def montar_interfaz(contenedor, funcion_volver):
    """
    ES: Construye el Dashboard de auditoría con estilo Dark Gold.
    EN: Builds the auditing Dashboard with Dark Gold styling.
    """
    frame = tk.Frame(contenedor, bg="black")
    frame.pack(fill="both", expand=True)

    # UI Header / Cabecera
    tk.Button(frame, text="⬅ Back to History", command=lambda: [frame.destroy(), funcion_volver()],
              bg="black", fg="white", bd=0, font=("Arial", 10, "bold")).pack(anchor="nw", padx=10, pady=10)

    tk.Label(frame, text="PROJECT CONSUMPTION AUDIT", bg="black", fg="#d4af37", font=("Arial", 18, "bold")).pack(pady=20)

    # Search Bar Setup / Configuración de Barra de Búsqueda
    frame_top = tk.Frame(frame, bg="black")
    frame_top.pack(pady=10)
    tk.Label(frame_top, text="Select Project:", bg="black", fg="white", font=("Arial", 12)).pack(side=tk.LEFT, padx=10)

    buscador_proyecto = GoogleSearchBox(frame_top, lista_datos=obtener_proyectos_reales(), width=45)
    buscador_proyecto.pack(side=tk.LEFT, padx=10)

    # Styling Table (Treeview) / Estilo de Tabla
    estilo = ttk.Style()
    estilo.theme_use('clam')
    estilo.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", borderwidth=0, rowheight=25)
    estilo.configure("Treeview.Heading", background="#1a1a1a", foreground="white", font=("Arial", 10, "bold"))
    
    

    # Results Table / Tabla de Resultados
    tabla_container = tk.Frame(frame, bg="black")
    tabla_container.pack(pady=20, anchor="center")

    columnas = ("Date", "Project", "Quantity", "Material", "Requested By")
    tabla = ttk.Treeview(tabla_container, columns=columnas, show="headings", height=15)

    anchos = {"Date": 120, "Project": 250, "Quantity": 80, "Material": 450, "Requested By": 180}
    for c in columnas:
        tabla.heading(c, text=c)
        tabla.column(c, width=anchos.get(c, 150), anchor="center")

    tabla.pack(side=tk.LEFT)
    
    lbl_resultado = tk.Label(frame, text="", bg="black", fg="yellow", font=("Arial", 10))
    lbl_resultado.pack(pady=10)

    # Event Linking / Enlace de eventos
    buscador_proyecto.command = lambda: realizar_filtrado(tabla, buscador_proyecto, lbl_resultado)
    buscador_proyecto.entry.focus_set()
