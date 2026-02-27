"""
PROJECT: Enterprise User Access & Security Management System
AUTHOR: Ares Casale Marentis
AGE: 22 | Computer Engineering Student
-----------------------------------------------------------------------
ESPAÑOL:
Implementación completa del módulo de seguridad. Gestiona el ciclo de vida 
de usuarios (CRUD) mediante persistencia en SQLite. Incluye lógica de 
privilegios jerárquicos: el Super Administrador ('Ares') posee visibilidad 
total, mientras que otros perfiles operan con datos ofuscados.

ENGLISH:
Full implementation of the security module. Manages the user lifecycle (CRUD) 
via SQLite persistence. Includes hierarchical privilege logic: the Super 
Administrator ('Ares') has full visibility, while other profiles operate 
with obfuscated data.
"""

import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
import os

# --- PATH CONFIGURATION / CONFIGURACIÓN DE RUTAS ---
# ES: Definimos la ruta de la base de datos centralizada.
# EN: Defining the centralized database path.
RUTA_DB = os.getenv("MARETO_AUTH_DB", r"\\PROYECTOS\Mareto_sistema\usuarios.db")



def montar_interfaz(contenedor, volver_callback, usuario_logueado):
    """
    ES: Construye dinámicamente la interfaz de gestión de identidades.
    EN: Dynamically builds the identity management interface.
    """
    for widget in contenedor.winfo_children():
        widget.destroy()

    # ES: Normalización de privilegios. Solo 'ares' tiene acceso raíz.
    # EN: Privilege normalization. Only 'ares' has root access.
    usuario_logueado_str = str(usuario_logueado).lower()
    es_super_admin = (usuario_logueado_str == "ares")
    
    id_seleccionado = None # Estado para control de edición/inserción

    frame_main = tk.Frame(contenedor, bg="#1a1a1a")
    frame_main.pack(fill="both", expand=True)

    # --- UI HEADER / ENCABEZADO ---
    tk.Button(frame_main, text="⬅ Menú", command=volver_callback, 
              bg="#1a1a1a", fg="white", font=("Arial", 10, "bold"), bd=0, cursor="hand2"
              ).pack(anchor="nw", padx=15, pady=10)
    
    tk.Label(frame_main, text="GESTIÓN DE USUARIOS", font=("Arial", 18, "bold"), 
             fg="#d4af37", bg="#1a1a1a").pack(pady=20)

    # --- DATA TOAST / NOTIFICACIÓN TEMPORAL ---
    def mostrar_notificacion_temporal(titulo, mensaje, tiempo=2000):
        aviso = tk.Toplevel()
        aviso.geometry("300x80")
        aviso.configure(bg="#004400")
        aviso.overrideredirect(True) 
        x = (aviso.winfo_screenwidth() // 2) - 150
        y = (aviso.winfo_screenheight() // 2) - 40
        aviso.geometry(f"+{x}+{y}")
        tk.Label(aviso, text=mensaje, fg="white", bg="#004400", 
                 font=("Arial", 11, "bold"), pady=25).pack()
        aviso.after(tiempo, aviso.destroy)

    # --- USER FORM / FORMULARIO ---
    frame_form = tk.LabelFrame(frame_main, text=" Datos de Usuario ", bg="#1a1a1a", 
                               fg="white", padx=20, pady=20)
    frame_form.pack(pady=10)

    tk.Label(frame_form, text="Usuario:", bg="#1a1a1a", fg="white", font=("Arial", 11)).grid(row=0, column=0, sticky="e", pady=5)
    ent_user = tk.Entry(frame_form, font=("Arial", 11), width=25)
    ent_user.grid(row=0, column=1, padx=10, pady=5)

    tk.Label(frame_form, text="Contraseña:", bg="#1a1a1a", fg="white", font=("Arial", 11)).grid(row=1, column=0, sticky="e", pady=5)
    ent_pass = tk.Entry(frame_form, font=("Arial", 11), width=25)
    ent_pass.grid(row=1, column=1, padx=10, pady=5)

    cmb_rol = ttk.Combobox(frame_form, values=["ADMINISTRADOR", "OPERADOR"], state="readonly", font=("Arial", 11), width=23)
    cmb_rol.set("OPERADOR")
    cmb_rol.grid(row=2, column=1, pady=10)

    # --- TREEVIEW STYLING / ESTILO DE TABLA ---
    estilo = ttk.Style()
    estilo.theme_use("clam")
    estilo.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", 
                     borderwidth=0, font=("Arial", 10), rowheight=25)
    estilo.configure("Treeview.Heading", background="#1a1a1a", foreground="white", relief="raised", 
                     font=("Arial", 10, "bold"), borderwidth=1)
    estilo.map("Treeview", background=[('selected', '#004400')])

    # --- DATA TABLE / TABLA DE DATOS ---
    tabla_container = tk.Frame(frame_main, bg="#1a1a1a")
    tabla_container.pack(fill="both", expand=True, padx=50, pady=10)

    columnas = ("ID", "User", "Pass", "Rol")
    tree = ttk.Treeview(tabla_container, columns=columnas, show="headings", height=8)
    scrollbar_y = tk.Scrollbar(tabla_container, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar_y.set)

    anchos = {"ID": 50, "User": 200, "Pass": 200, "Rol": 150}
    for col in columnas: 
        tree.heading(col, text=col)
        tree.column(col, width=anchos.get(col, 100), anchor="center")

    tree.pack(side=tk.LEFT, fill="both", expand=True)
    scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

    # --- BUSINESS LOGIC FUNCTIONS / FUNCIONES DE LÓGICA ---

    def refrescar():
        """ES: Sincroniza la UI con la base de datos SQL."""
        for i in tree.get_children(): tree.delete(i)
        try:
            conn = sqlite3.connect(RUTA_DB) 
            cursor = conn.cursor()
            cursor.execute("SELECT id, usuario, contrasena, rol FROM usuarios")
            for r in cursor.fetchall():
                # ES: Ofuscación si no es Super Admin.
                # EN: Masking if not Super Admin.
                mostrar = r if es_super_admin else (r[0], r[1], "********", r[3])
                tree.insert("", "end", values=mostrar)
            conn.close()
        except Exception as e:
            messagebox.showerror("Error de Red", f"Conexión fallida: {e}")

    def limpiar_formulario():
        nonlocal id_seleccionado
        id_seleccionado = None
        ent_user.delete(0, 'end')
        ent_pass.delete(0, 'end')
        cmb_rol.set("OPERADOR")
        ent_user.focus_set()

    def seleccionar_registro(event):
        nonlocal id_seleccionado
        seleccion = tree.selection()
        if not seleccion: return
        valores = tree.item(seleccion)['values']
        id_seleccionado = valores[0]
        ent_user.delete(0, 'end')
        ent_user.insert(0, valores[1])
        ent_pass.delete(0, 'end')
        if valores[2] != "********": ent_pass.insert(0, valores[2])
        cmb_rol.set(valores[3])

    def borrar():
        sel = tree.selection()
        if not sel: return
        id_u = tree.item(sel)['values'][0]
        if messagebox.askyesno("Confirmar", "¿Borrar usuario permanentemente?"):
            try:
                conn = sqlite3.connect(RUTA_DB) 
                conn.cursor().execute("DELETE FROM usuarios WHERE id=?", (id_u,))
                conn.commit()
                conn.close()
                limpiar_formulario(); refrescar()
                mostrar_notificacion_temporal("Éxito", "Usuario eliminado")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def abrir_menu(event):
        item_id = tree.identify_row(event.y)
        if not item_id: return
        tree.selection_set(item_id)
        menu = tk.Menu(frame_main, tearoff=0)
        menu.add_command(label="✏️ Editar Usuario", command=lambda: ent_user.focus_set())
        if es_super_admin:
            menu.add_separator()
            menu.add_command(label="🗑️ Eliminar Usuario", command=borrar, foreground="red")
        menu.post(event.x_root, event.y_root)

    def guardar(event=None):
        u = ent_user.get().strip().lower() 
        p = ent_pass.get().strip()
        r = cmb_rol.get()
        if not u or not p: 
            messagebox.showwarning("Faltan datos", "Escriba credenciales completas")
            return
        try:
            conn = sqlite3.connect(RUTA_DB) 
            cursor = conn.cursor()
            if id_seleccionado is None: # Inserción
                cursor.execute("INSERT INTO usuarios (usuario, contrasena, rol) VALUES (?, ?, ?)", (u, p, r))
            else: # Actualización
                cursor.execute("UPDATE usuarios SET usuario=?, contrasena=?, rol=? WHERE id=?", (u, p, r, id_seleccionado))
            conn.commit()
            conn.close()
            limpiar_formulario(); refrescar()
            mostrar_notificacion_temporal("Éxito", "Cambios guardados correctamente")
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al guardar: {e}")

    # --- EVENT BINDING / VINCULACIÓN DE EVENTOS ---
    tree.bind("<<TreeviewSelect>>", seleccionar_registro)
    tree.bind("<Button-3>", abrir_menu) 
    ent_user.bind("<Return>", lambda e: ent_pass.focus_set())
    ent_pass.bind("<Return>", lambda e: cmb_rol.focus_set())
    cmb_rol.bind("<Return>", guardar)

    # --- BUTTON PANEL / PANEL DE BOTONES ---
    btn_frame = tk.Frame(frame_main, bg="#1a1a1a")
    btn_frame.pack(pady=20)
    tk.Button(btn_frame, text="GUARDAR", command=guardar, bg="#d4af37", 
              font=("Arial", 10, "bold"), width=20, cursor="hand2").pack(side="left", padx=5)
    tk.Button(btn_frame, text="LIMPIAR", command=limpiar_formulario, bg="#0055a5", 
              fg="white", font=("Arial", 10, "bold"), width=15, cursor="hand2").pack(side="left", padx=5)

    refrescar() # Carga inicial de datos
