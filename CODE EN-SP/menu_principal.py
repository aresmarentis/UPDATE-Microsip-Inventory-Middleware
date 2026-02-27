"""
PROJECT: Integrated Industrial Management System (Mareto ERP)
AUTHOR: Ares Casale Marentis
AGE: 22 | Computer Engineering Student
-----------------------------------------------------------------------
ESPAÑOL:
Orquestador central del ecosistema Mareto. Gestiona el ciclo de vida de la App,
autenticación de usuarios con roles diferenciados, navegación entre módulos 
(Almacén, Incidentes, Historial) y la vinculación dinámica de servicios de 
red y notificaciones en tiempo real.

ENGLISH:
Central orchestrator of the Mareto ecosystem. Manages the App lifecycle, 
user authentication with role-based access control (RBAC), module navigation 
(Warehouse, Incidents, History), and dynamic linking of network services 
and real-time notifications.
"""

import tkinter as tk
from tkinter import messagebox, ttk
import os
import sys  
import sqlite3 
from datetime import datetime

# --- IMPORTACIÓN DE MÓDULOS DEL ECOSISTEMA ---
import sistema_almacen
import editor_listas
import filtrar_proyecto
import filtrar_trabajador
import filtrar_material
import filtrar_fecha
import reportes_pdf
import gestion_usuarios
import incidentes
import calendario_entregas

# ES: Abstracción de infraestructura para despliegue en red corporativa.
# EN: Infrastructure abstraction for corporate network deployment.
RUTA_RED = os.getenv("MARETO_SERVER_PATH", r"\\PROYECTOS\Mareto_sistema")

def obtener_ruta(archivo):
    return os.path.join(RUTA_RED, archivo)
    
# --- GLOBAL SYSTEM STATE / ESTADO GLOBAL DEL SISTEMA ---
ES_ADMIN = False
USUARIO_ACTUAL = ""



# --- UI ENHANCEMENTS / MEJORAS DE INTERFAZ ---

def aplicar_hover(boton, color_encima, color_original):
    """ES: Implementa retroalimentación visual (Hover) para mejorar la UX."""
    boton.config(cursor="hand2")
    boton.bind("<Enter>", lambda e: boton.config(bg=color_encima))
    boton.bind("<Leave>", lambda e: boton.config(bg=color_original))

# --- SECURITY LAYER / CAPA DE SEGURIDAD ---

def verificar_credenciales(usuario, password):
    """
    ES: Valida acceso contra la base de datos SQL de seguridad.
    EN: Validates access against the SQL security database.
    """
    usuario = usuario.strip().lower() 
    password = password.strip()
    
    try:
        ruta_db = obtener_ruta('usuarios.db')
        conn = sqlite3.connect(ruta_db)
        cursor = conn.cursor()
        
        # SQL Injection protected query / Consulta protegida contra Inyección SQL
        cursor.execute("SELECT rol, usuario FROM usuarios WHERE usuario = ? AND contrasena = ?", (usuario, password))
        resultado = cursor.fetchone()
        conn.close()
        
        if resultado:
            # ES: Retorna estado de autenticación, nivel de privilegio y nombre real.
            return True, (resultado[0].upper() in ["ADMINISTRADOR", "ADMIN"]), resultado[1]
    except Exception as e:
        messagebox.showerror("Network Error", f"Database unreachable: {e}")
    return False, False, ""

# --- NAVIGATION LOGIC / LÓGICA DE NAVEGACIÓN ---

def limpiar():
    """ES: Purga el contenedor principal para renderizar un nuevo módulo."""
    for widget in contenedor_principal.winfo_children(): widget.destroy()

def ir_a_menu():
    limpiar()
    dibujar_menu()

def ir_a_almacen():
    limpiar()
    sistema_almacen.montar_interfaz(contenedor_principal, ir_a_menu, "ADMIN" if ES_ADMIN else "OPERADOR")

def ir_a_historial():
    limpiar()
    # Construcción de la sub-interfaz de consultas históricas
    tk.Button(contenedor_principal, text="⬅ Menú", command=ir_a_menu, 
              bg="#1a1a1a", fg="white", bd=0, font=("Arial", 11, "bold")).pack(anchor="nw", padx=20, pady=20)
    
    tk.Label(contenedor_principal, text="HISTORIAL Y CONSULTAS", 
             bg="#1a1a1a", fg="#d4af37", font=("Arial", 20, "bold")).pack(pady=20)
    
    filtros = [
        ("Filtrar por Proyecto", lambda: filtrar_proyecto.montar_interfaz(contenedor_principal, ir_a_historial)),
        ("Filtrar por Trabajador", lambda: filtrar_trabajador.montar_interfaz(contenedor_principal, ir_a_historial)),
        ("Filtrar por Material", lambda: filtrar_material.montar_interfaz(contenedor_principal, ir_a_historial)),
        ("Filtrar por Fecha", lambda: filtrar_fecha.montar_interfaz(contenedor_principal, ir_a_historial))
    ]

    for texto, comando in filtros:
        btn_f = tk.Button(contenedor_principal, text=texto, command=comando, 
                          bg="#444444", fg="white", font=("Arial", 12, "bold"), width=40, bd=0, pady=10)
        btn_f.pack(pady=5)
        aplicar_hover(btn_f, "#555555", "#444444")

# --- MAIN INTERFACE RENDERERS / RENDERIZADO DE INTERFACES ---

def dibujar_login():
    limpiar()
    frame_login = tk.Frame(contenedor_principal, bg="#1a1a1a")
    frame_login.place(relx=0.5, rely=0.5, anchor="center")

    # Logo Loader / Cargador de Identidad Visual
    try:
        img = tk.PhotoImage(file=obtener_ruta("logo.png"))
        lbl = tk.Label(frame_login, image=img, bg="#1a1a1a")
        lbl.image = img; lbl.pack(pady=20)
    except: pass

    tk.Label(frame_login, text="SISTEMA MARETO", font=("Arial", 18, "bold"), fg="#d4af37", bg="#1a1a1a").pack(pady=10)
    
    # Entry Fields / Campos de Entrada
    ent_user = tk.Entry(frame_login, font=("Arial", 12), width=25, justify="center")
    ent_user.pack(pady=5); ent_user.insert(0, "Usuario")
    
    ent_pass = tk.Entry(frame_login, font=("Arial", 12), width=25, show="*", justify="center")
    ent_pass.pack(pady=5)

    def intentar_entrar(event=None):
        global ES_ADMIN, USUARIO_ACTUAL
        exito, es_admin_real, nombre = verificar_credenciales(ent_user.get(), ent_pass.get())
        if exito:
            ES_ADMIN = es_admin_real
            USUARIO_ACTUAL = nombre
            ir_a_menu()
        else:
            messagebox.showerror("Error", "Credenciales incorrectas")

    btn = tk.Button(frame_login, text="INGRESAR AL SISTEMA", command=intentar_entrar, bg="#d4af37", 
                    font=("Arial", 12, "bold"), width=25, bd=0, cursor="hand2")
    btn.pack(pady=20)
    aplicar_hover(btn, "#f1c40f", "#d4af37")

def dibujar_menu():
    """ES: Dashboard Principal. Expone funciones basadas en el rol del usuario."""
    limpiar()
    
    # User Profile Header / Barra de Estado de Usuario
    barra = tk.Frame(contenedor_principal, bg="#1a1a1a")
    barra.pack(fill="x", padx=20, pady=10)
    tk.Label(barra, text=f"OPERADOR: {USUARIO_ACTUAL.upper()}", fg="#666666", bg="#1a1a1a").pack(side="left")
    tk.Label(barra, text=datetime.now().strftime('%d/%m/%Y'), fg="#666666", bg="#1a1a1a").pack(side="right")

    

    # --- CORE OPERATIONS / OPERACIONES CENTRALES ---
    btn_salida = tk.Button(contenedor_principal, text="REGISTRAR SALIDA DE ALMACÉN", command=ir_a_almacen, 
                           bg="#0055a5", fg="white", font=("Arial", 14, "bold"), width=40, bd=0)
    btn_salida.pack(pady=10)
    aplicar_hover(btn_salida, "#0078d7", "#0055a5")

    # --- ADMIN EXCLUSIVE MODULES / MÓDULOS EXCLUSIVOS ADMIN ---
    if ES_ADMIN:
        btn_cal = tk.Button(contenedor_principal, text="CALENDARIO DE PROYECTOS", 
                            command=lambda: calendario_entregas.mostrar_calendario(contenedor_principal, USUARIO_ACTUAL, dibujar_menu), 
                            bg="#d4af37", fg="black", font=("Arial", 14, "bold"), width=40, bd=0)
        btn_cal.pack(pady=10)
        
        btn_repo = tk.Button(contenedor_principal, text="GENERAR PDF DE EXISTENCIAS", command=reportes_pdf.generar_reporte_existencias, 
                             bg="#004400", fg="white", font=("Arial", 12, "bold"), width=40, bd=0)
        btn_repo.pack(pady=10)

    # --- SHARED MODULES / MÓDULOS COMPARTIDOS ---
    btn_inc = tk.Button(contenedor_principal, text="REPORTAR INCIDENTE / MERMA", 
                        command=lambda: incidentes.montar_incidentes(contenedor_principal, ir_a_menu, ES_ADMIN, USUARIO_ACTUAL), 
                        bg="#880000", fg="white", font=("Arial", 12, "bold"), width=40, bd=0)
    btn_inc.pack(pady=10)

    btn_hist = tk.Button(contenedor_principal, text="HISTORIAL Y CONSULTAS", command=ir_a_historial, 
                         bg="#444444", fg="white", font=("Arial", 12, "bold"), width=40, bd=0)
    btn_hist.pack(pady=10)

    # Logout / Cierre de Sistema
    tk.Button(contenedor_principal, text="Cerrar Sesión", command=dibujar_login, bg="#d4af37", width=20, bd=0).pack(pady=(30, 5))

# --- MAIN APP ENTRY POINT / PUNTO DE ENTRADA ---

ventana = tk.Tk()
ventana.title("MARETO MUEBLES - CONTROL DE PRODUCCIÓN v2.0")
ventana.minsize(1000, 700)
ventana.configure(bg="#1a1a1a")

try: ventana.state('zoomed')
except: ventana.attributes('-zoomed', True)

contenedor_principal = tk.Frame(ventana, bg="#1a1a1a")
contenedor_principal.pack(fill="both", expand=True)

if __name__ == "__main__":
    # Initialize background network services / Iniciar servicios de red
    calendario_entregas.iniciar_servicios_telegram()
    
    dibujar_login()
    ventana.mainloop()
