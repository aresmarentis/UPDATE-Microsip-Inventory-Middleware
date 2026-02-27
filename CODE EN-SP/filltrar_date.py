"""
PROJECT: Predictive Search & Historical Data Analytics
AUTHOR: Ares Casale Marentis
AGE: 22 | Computer Engineering Student
------------------------------------------------------------
ESPAÑOL:
Implementación de un componente de búsqueda predictiva tipo 'Google Search' 
para la exploración eficiente de registros históricos. Incluye algoritmos de 
filtrado dinámico, gestión de eventos de teclado y renderizado de tablas 
optimizado para grandes volúmenes de datos en archivos CSV.

ENGLISH:
Implementation of a 'Google-style' predictive search component for efficient 
historical record exploration. Features dynamic filtering algorithms, keyboard 
event management, and optimized table rendering for large CSV datasets.
"""

import tkinter as tk
from tkinter import ttk, Listbox
import csv
import os
from datetime import datetime

# ES: Abstracción de la ruta de datos para auditoría industrial.
# EN: Data path abstraction for industrial auditing.
ARCHIVO_DB = os.getenv("MARETO_HISTORY_CSV", r"\\PROYECTOS\Mareto_sistema\historial_almacen.csv")


class GoogleSearchBox(tk.Frame):
    """
    ES: Componente personalizado de búsqueda con autocompletado y lógica de fechas.
    EN: Custom search component with autocomplete and date parsing logic.
    """
    def __init__(self, parent, lista_datos, command=None, width=30, *args, **kwargs):
        super().__init__(parent, bg="black", *args, **kwargs)

        # ES: Limpieza y ordenamiento inteligente de datos (Fechas primero).
        # EN: Smart data cleaning and sorting (Dates priority).
        self.lista_completa = sorted(list(set(lista_datos)), 
                                     key=lambda x: datetime.strptime(x, "%d/%m/%Y") if self.es_fecha(x) else x, 
                                     reverse=True)
        self.command = command
        self.var = tk.StringVar()
        
        # UI Entry Setup
        self.entry = tk.Entry(self, textvariable=self.var, width=width, font=("Arial", 11))
        self.entry.pack(fill=tk.X)
        
        # Keyboard Event Binding / Enlace de eventos de teclado
        self.entry.bind("<KeyRelease>", self.al_escribir)
        self.entry.bind("<Down>", self.mover_a_lista)
        self.entry.bind("<Return>", self.al_dar_enter)

        # Dropdown container logic / Lógica del contenedor desplegable
        self.lista_container = tk.Frame(self.winfo_toplevel(), bg="white", highlightbackground="gray", highlightthickness=1)
        self.lb = Listbox(self.lista_container, font=("Arial", 11), height=5, bg="white", fg="black", borderwidth=0)
        self.lb.pack(fill=tk.BOTH, expand=True)
        
        self.lb.bind("<ButtonRelease-1>", self.seleccionar_item)
        self.lb.bind("<Return>", self.seleccionar_item)
        self.winfo_toplevel().bind("<Button-1>", self.verificar_cierre_externo, add="+")

    def es_fecha(self, texto):
        try:
            datetime.strptime(texto, "%d/%m/%Y")
            return True
        except: return False

    def al_escribir(self, event):
        """
        ES: Algoritmo de filtrado en tiempo real basado en la entrada del usuario.
        EN: Real-time filtering algorithm based on user input.
        """
        if event.keysym in ('Up', 'Down', 'Return', 'Tab', 'Escape'): return
        texto = self.var.get().lower()
        if not texto: 
            self.cerrar_lista()
            return

        # List Comprehension for high performance / Filtrado de alto rendimiento
        filtrados = [item for item in self.lista_completa if texto in item.lower()]
        if filtrados: 
            self.mostrar_lista(filtrados)
        else: 
            self.cerrar_lista()

    def mostrar_lista(self, items):
        """
        ES: Gestiona el posicionamiento absoluto del dropdown sobre otros widgets.
        EN: Manages absolute positioning of the dropdown over other widgets.
        """
        self.lb.delete(0, tk.END)
        for item in items: self.lb.insert(tk.END, item)

        root_v = self.winfo_toplevel()
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

# --- DATA RETRIEVAL FUNCTIONS / FUNCIONES DE OBTENCIÓN DE DATOS ---

def obtener_fechas():
    """
    ES: Extrae y valida fechas únicas del historial para alimentar el buscador.
    EN: Extracts and validates unique dates from history to feed the search box.
    """
    lista = set()
    if os.path.exists(ARCHIVO_DB):
        try:
            with open(ARCHIVO_DB, mode='r', encoding='utf-8') as f:
                lector = csv.reader(f)
                for fila in lector:
                    if fila and len(fila) > 0:
                        dato = fila[0].strip()
                        try:
                            datetime.strptime(dato, "%d/%m/%Y")
                            lista.add(dato)
                        except: continue
        except: pass
    return list(lista)

def filtrar(tabla, buscador, lbl_resultado):
    """
    ES: Motor de búsqueda que actualiza el Treeview basándose en el componente GoogleSearchBox.
    EN: Search engine that updates the Treeview based on the GoogleSearchBox component.
    """
    for item in tabla.get_children(): tabla.delete(item)
    buscado = buscador.get().strip()
    
    if not buscado or not os.path.exists(ARCHIVO_DB): 
        lbl_resultado.config(text="Registros encontrados: 0")
        return

    encontrados = 0
    try:
        with open(ARCHIVO_DB, mode='r', encoding='utf-8') as f:
            lector = csv.reader(f)
            for fila in lector:
                if fila and len(fila) > 0:
                    if fila[0].strip() == buscado:
                        tabla.insert("", 0, values=fila)
                        encontrados += 1
        lbl_resultado.config(text=f"Registros encontrados: {encontrados}")
    except Exception as e:
        lbl_resultado.config(text=f"Error: {e}")

# --- INTERFACE MOUNTING / MONTAJE DE LA INTERFAZ ---

def montar_interfaz(contenedor, funcion_volver):
    """
    ES: Crea la vista de historial con estilo 'Dark Mode' y tablas de alta visibilidad.
    EN: Creates the history view with 'Dark Mode' styling and high-visibility tables.
    """
    frame = tk.Frame(contenedor, bg="black")
    frame.pack(fill="both", expand=True)

    # Header & Back Button
    btn_volver = tk.Button(frame, text="⬅ Historial", 
                        command=lambda: [frame.destroy(), funcion_volver()],
                        bg="#000000", fg="white", font=("Arial", 10, "bold"), bd=0)    
    btn_volver.pack(anchor="nw", padx=10, pady=10)
    
    tk.Label(frame, text="BÚSQUEDA AVANZADA POR FECHA", bg="black", fg="white", font=("Arial", 16, "bold")).pack(pady=10)

    # Search Area
    frame_busq = tk.Frame(frame, bg="black")
    frame_busq.pack(pady=10)
    tk.Label(frame_busq, text="Escribe la Fecha:", bg="black", fg="white", font=("Arial", 12)).pack(side=tk.LEFT, padx=10)

    lista_fechas = obtener_fechas()
    buscador_fecha = GoogleSearchBox(frame_busq, lista_datos=lista_fechas, width=20)
    buscador_fecha.pack(side=tk.LEFT, padx=10)

    # Table Styling / Estilo de la Tabla
    estilo = ttk.Style()
    estilo.theme_use("clam")
    estilo.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", rowheight=25)
    estilo.configure("Treeview.Heading", background="#1a1a1a", foreground="white", font=("Arial", 10, "bold"))

    

    # Data Table / Tabla de Datos
    tabla_container = tk.Frame(frame, bg="black")
    tabla_container.pack(pady=20, anchor="center")

    columnas = ("Fecha", "Proyecto", "Cantidad", "Material", "Solicito")
    tabla = ttk.Treeview(tabla_container, columns=columnas, show="headings", height=15)
    
    anchos = {"Fecha": 120, "Proyecto": 250, "Cantidad": 80, "Material": 400, "Solicito": 180}
    for col in columnas:
        tabla.heading(col, text=col)
        tabla.column(col, width=anchos.get(col, 150), anchor="center")

    tabla.pack(side=tk.LEFT)
    
    lbl_resultado = tk.Label(frame, text="", bg="black", fg="yellow", font=("Arial", 10, "bold"))
    lbl_resultado.pack(pady=10)

    # Callback Integration / Integración de retorno
    buscador_fecha.command = lambda: filtrar(tabla, buscador_fecha, lbl_resultado)
    buscador_fecha.entry.focus_set()
