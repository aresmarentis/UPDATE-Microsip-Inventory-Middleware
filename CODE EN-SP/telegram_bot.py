"""
PROJECT: Industrial Project Management & Telegram Automation System
AUTHOR: Ares Casale Marentis
AGE: 22 | Computer Engineering Student
------------------------------------------------------------
ESPAÑOL:
Sistema integral de gestión de entregas para el sector industrial. 
Automatiza el seguimiento de hitos (Despiece, Compras, Taller) y sincroniza 
notificaciones mediante un Bot de Telegram, permitiendo confirmaciones 
interactivas que actualizan la base de datos en tiempo real mediante Multithreading.

ENGLISH:
Integrated delivery management system for the industrial sector. 
It automates milestone tracking (Design, Sourcing, Workshop) and synchronizes 
notifications via a Telegram Bot, enabling interactive confirmations that 
update the database in real-time through Multithreading.
"""

import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
import os
import calendar
from datetime import datetime, timedelta, date
import threading
import urllib.request
import urllib.parse
import json
import time

# --- SEGURIDAD: VARIABLES DE ENTORNO / ENVIRONMENT VARIABLES ---
# ES: Reemplazamos los datos reales por llamadas al sistema para proteger el código.
# EN: Replacing real data with system calls to protect the source code.

TELEGRAM_TOKEN = os.getenv("MARETO_BOT_TOKEN", "TU_TOKEN_AQUI") 

DIRECTORIO_TELEGRAM = {
    "GRUPO": os.getenv("CHAT_ID_GRUPO", "DEFAULT_ID"),
    "JEFE": os.getenv("CHAT_ID_JEFE", "DEFAULT_ID"),
    "COMPRAS": os.getenv("CHAT_ID_COMPRAS", "DEFAULT_ID"),
    "DESPIECE": os.getenv("CHAT_ID_DESPIECE", "DEFAULT_ID"),
    "TALLER": os.getenv("CHAT_ID_TALLER", "DEFAULT_ID")
}

# Abstracción de ruta de red / Network path abstraction
RUTA_RED = os.getenv("DB_NETWORK_PATH", r"\\PROYECTOS\Mareto_sistema")

if not os.path.exists(RUTA_RED):
    DB_PATH = 'entregas_mareto.db'
else:
    DB_PATH = os.path.join(RUTA_RED, 'entregas_mareto.db')

# --- ESTADO GLOBAL / GLOBAL STATE ---
offset_global = 0 
ULTIMAS_CONSULTAS = {}
ID_PROYECTO_EDICION = None 

# --- COMPONENTES DE INTERFAZ / UI COMPONENTS ---

class CalendarioIntegrado(tk.Frame):
    """
    ES: Widget de calendario personalizado para selección de fechas de entrega.
    EN: Custom calendar widget for delivery date selection.
    """
    def __init__(self, parent, entry_cant, combo_tipo, x, y, callback=None, *args, **kwargs):
        super().__init__(parent, bg="white", bd=2, relief="ridge", *args, **kwargs)
        self.entry_cant = entry_cant
        self.combo_tipo = combo_tipo
        self.callback = callback
        self.hoy = date.today()
        self.anio, self.mes = self.hoy.year, self.hoy.month
        self.place(x=x, y=y) 
        
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
        fecha_sel = date(self.anio, self.mes, dia)
        if "alerta" in str(self.entry_cant):
            self.entry_cant.delete(0, tk.END)
            self.entry_cant.insert(0, fecha_sel.strftime('%Y-%m-%d'))
        else:
            diferencia = (fecha_sel - self.hoy).days
            if diferencia < 0: diferencia = 0
            self.entry_cant.delete(0, tk.END)
            self.entry_cant.insert(0, str(diferencia))
            if self.combo_tipo: self.combo_tipo.set("Días")
        if self.callback: self.callback() 
        self.destroy()

# --- FUNCIONES DE TELEGRAM / TELEGRAM FUNCTIONS ---



def enviar_telegram(mensaje, chat_id, poner_emoji=False):
    """
    ES: Realiza peticiones HTTP a la API de Telegram. Incluye soporte para reacciones.
    EN: Executes HTTP requests to the Telegram API. Includes reaction support.
    """
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": chat_id,
            "text": mensaje,
            "parse_mode": "Markdown" 
        }).encode()
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req) as response:
            respuesta_json = json.loads(response.read().decode())
            message_id = respuesta_json['result']['message_id']
            if poner_emoji:
                try:
                    url_reaction = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setMessageReaction"
                    payload = json.dumps({
                        "chat_id": chat_id,
                        "message_id": message_id,
                        "reaction": [{"type": "emoji", "emoji": "👍"}] 
                    }).encode('utf-8')
                    req_reaction = urllib.request.Request(url_reaction, data=payload, headers={'Content-Type': 'application/json'})
                    urllib.request.urlopen(req_reaction) 
                except: pass
            return message_id
    except: return None

def responder_con_tabla(comando, chat_id):
    ahora = time.time()
    if chat_id in ULTIMAS_CONSULTAS:
        if ahora - ULTIMAS_CONSULTAS[chat_id] < 4: return
    ULTIMAS_CONSULTAS[chat_id] = ahora
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    
    if comando == "/atrasados":
        titulo = "🔴 *PROYECTOS ATRASADOS*"
        query = "SELECT cliente, producto, fecha_entrega, ok_despiece, ok_compras, ok_taller, estatus FROM entregas WHERE estatus != 'TERMINADO'"
    elif comando == "/faltantes":
        titulo = "📋 *TODOS LOS PENDIENTES*"
        query = "SELECT cliente, producto, fecha_entrega FROM entregas WHERE estatus != 'TERMINADO' ORDER BY id DESC"
    elif comando == "/despiece":
        titulo = "✏️ *PENDIENTES DESPIECE*"
        query = "SELECT cliente, producto, fecha_entrega FROM entregas WHERE ok_despiece = 0 AND estatus != 'TERMINADO' ORDER BY id DESC"
    elif comando == "/compras":
        titulo = "🛒 *PENDIENTES COMPRAS*"
        query = "SELECT cliente, producto, fecha_entrega FROM entregas WHERE ok_despiece = 1 AND ok_compras = 0 AND estatus != 'TERMINADO' ORDER BY id DESC"
    elif comando == "/taller":
        titulo = "🔨 *PENDIENTES TALLER*"
        query = "SELECT cliente, producto, fecha_entrega FROM entregas WHERE ok_compras = 1 AND ok_taller = 0 AND estatus != 'TERMINADO' ORDER BY id DESC"

    cursor.execute(query); filas_raw = cursor.fetchall(); conn.close()
    filas_finales = []
    if comando == "/atrasados":
        for r in filas_raw:
            sit, _ = calcular_situacion(r[2], r[3], r[4], r[5], r[6])
            if "🔴" in sit: filas_finales.append((r[0], r[1], r[2], sit))
    else: filas_finales = filas_raw

    if not filas_finales:
        enviar_telegram(f"{titulo}\n\n✅ *¡Sin pendientes!*", chat_id)
    else:
        mensaje = f"{titulo}\n------------------------------------------\n"
        for r in filas_finales[:20]:
            detalle = f"\n⚠️ {r[3]}" if comando == "/atrasados" else ""
            mensaje += f"👤 *{r[0]}*\n📦 {r[1]}\n📅 {r[2]}{detalle}\n\n"
        enviar_telegram(mensaje, chat_id)

# --- BASE DE DATOS / DATABASE ---

def inicializar_db():
    conn = sqlite3.connect(DB_PATH, timeout=30) 
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA journal_mode=DELETE") 
        cursor.execute('''CREATE TABLE IF NOT EXISTS entregas 
                          (id INTEGER PRIMARY KEY, cliente TEXT, producto TEXT, 
                           fecha_entrega TEXT, estatus TEXT DEFAULT 'PENDIENTE',
                           ok_despiece INTEGER DEFAULT 0, ok_compras INTEGER DEFAULT 0, ok_taller INTEGER DEFAULT 0,
                           f_desp TEXT, f_comp TEXT, f_tall TEXT,
                           m_desp_enviado INTEGER DEFAULT 0, m_comp_enviado INTEGER DEFAULT 0, m_tall_enviado INTEGER DEFAULT 0)''')
        
        try:
            cursor.execute("SELECT reaccion_bot FROM rastreo_mensajes LIMIT 1")
        except:
            cursor.execute("DROP TABLE IF EXISTS rastreo_mensajes")
            cursor.execute('''CREATE TABLE rastreo_mensajes 
                              (message_id INTEGER, chat_id TEXT, nombre_proyecto TEXT, area TEXT, reaccion_bot INTEGER DEFAULT 1)''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS tareas_telegram 
                          (id INTEGER PRIMARY KEY, proyecto TEXT, fecha_envio TEXT, mensaje TEXT, chat_id TEXT, enviado INTEGER DEFAULT 0)''')
        conn.commit()
    except Exception as e:
        print(f"Aviso en DB: {e}")
    finally:
        conn.close()

# --- LÓGICA DE NEGOCIO / BUSINESS LOGIC ---

def notificar_nuevo_proyecto(cliente, producto, fecha):
    texto = (f"📦 *NUEVO PROYECTO REGISTRADO*\n\n👤 *Cliente:* {cliente}\n📌 *Producto:* {producto}\n📅 *Entrega:* {fecha}\n\n👇 _Reacciona de enterado_")
    enviar_telegram(texto, DIRECTORIO_TELEGRAM["GRUPO"], poner_emoji=True)

def revisar_y_mandar_pendientes():
    while True:
        time.sleep(5) 
        hoy = datetime.now().strftime('%Y-%m-%d')
        try:
            conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
            cursor.execute("SELECT id, proyecto, mensaje, chat_id FROM tareas_telegram WHERE fecha_envio <= ? AND enviado = 0 LIMIT 1", (hoy,))
            t = cursor.fetchone()
            if t:
                id_t, proy, msj, destino_id = t
                cursor.execute("UPDATE tareas_telegram SET enviado = 1 WHERE id = ?", (id_t,))
                conn.commit() 
                mid = enviar_telegram(f"📂 *Proyecto:* {proy}\n\n👉 {msj}", destino_id, poner_emoji=True)
                if mid:
                    cli, prod = proy.split(" - ", 1)
                    m_u = msj.upper()
                    area = "DESPIECE" if "DESPIECE" in m_u else "COMPRAS" if "COMPRAS" in m_u else "TALLER" if ("PRODUCCIÓN" in m_u or "TALLER" in m_u) else None
                    col = "m_desp_enviado" if area == "DESPIECE" else "m_comp_enviado" if area == "COMPRAS" else "m_tall_enviado" if area == "TALLER" else None
                    if col: cursor.execute(f"UPDATE entregas SET {col} = 1 WHERE cliente = ? AND producto = ?", (cli, prod))
                    if area: cursor.execute("INSERT INTO rastreo_mensajes VALUES (?,?,?,?)", (mid, str(destino_id), proy, area))
                    if str(destino_id) != str(DIRECTORIO_TELEGRAM["JEFE"]):
                        mid_j = enviar_telegram(f"👁\n\n{msj}", DIRECTORIO_TELEGRAM["JEFE"], poner_emoji=True)
                        if mid_j and area: cursor.execute("INSERT INTO rastreo_mensajes VALUES (?,?,?,?)", (mid_j, str(DIRECTORIO_TELEGRAM["JEFE"]), proy, area))
                    conn.commit()
            conn.close()
        except: pass

def listener_telegram_unico(callback_actualizar):
    global offset_global
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={offset_global}&timeout=20"
            with urllib.request.urlopen(urllib.request.Request(url), timeout=25) as response:
                datos = json.loads(response.read().decode())
                for update in datos.get("result", []):
                    offset_global = update["update_id"] + 1
                    if "message" in update and "text" in update["message"]:
                        msg = update["message"]
                        texto = msg["text"].lower().strip()
                        chat_id = str(msg["chat"]["id"])
                        if texto in ["/faltantes", "/compras", "/despiece", "/taller", "/atrasados"]:
                            threading.Thread(target=responder_con_tabla, args=(texto, chat_id), daemon=True).start()
                    if "message_reaction" in update:
                        reac = update["message_reaction"]
                        procesar_confirmacion(reac["message_id"], str(reac["chat"]["id"]), callback_actualizar)
        except Exception as e:
            print(f"Error en Listener: {e}")
            time.sleep(2)

def procesar_confirmacion(msg_id, chat_id, callback_actualizar):
    try:
        conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
        query = "SELECT nombre_proyecto, area FROM rastreo_mensajes WHERE message_id=? AND chat_id=?"
        res = None
        for _ in range(8):
            cursor.execute(query, (msg_id, chat_id))
            res = cursor.fetchone()
            if res: break
            time.sleep(0.4)
        if res:
            proy, area = res
            cli, prod = proy.split(" - ", 1)
            col_ok = "ok_despiece" if area == "DESPIECE" else "ok_compras" if area == "COMPRAS" else "ok_taller"
            col_env = "m_desp_enviado" if area == "DESPIECE" else "m_comp_enviado" if area == "COMPRAS" else "m_tall_enviado"
            cursor.execute(f"UPDATE entregas SET {col_ok} = 1, {col_env} = 1 WHERE cliente = ? AND producto = ?", (cli, prod))
            conn.commit()
            if callback_actualizar: 
                try: callback_actualizar()
                except: pass
        conn.close()
    except Exception as e:
        print(f"Error procesando reacción: {e}")

def programar_fechas_atras_manual(cliente, producto, f_ent_dt, f_desp, f_comp, f_tall):
    nombre_p = f"{cliente} - {producto}"
    hoy_str = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("""SELECT m_desp_enviado, m_comp_enviado, m_tall_enviado, 
                             ok_despiece, ok_compras, ok_taller 
                      FROM entregas WHERE cliente=? AND producto=?""", (cliente, producto))
    res = cursor.fetchone() or (0, 0, 0, 0, 0, 0)
    tareas_operativas = [
        (f_desp, res[0] or res[3], f"✏️ *URGENTE DESPIECE:* Iniciar hoy para: *{nombre_p}*\n\n👇 _Reacciona 👍 si ya está listo_", DIRECTORIO_TELEGRAM["DESPIECE"]),
        (f_comp, res[1] or res[4], f"🛒 *COMPRAS:* Solicitar hoy materiales para: *{nombre_p}*\n\n👇 _Reacciona 👍 si ya está listo_", DIRECTORIO_TELEGRAM["COMPRAS"]),
        (f_tall, res[2] or res[5], f"🔨 *PRODUCCIÓN:* Hoy entra a taller: *{nombre_p}*\n\n👇 _Reacciona 👍 si ya está listo_", DIRECTORIO_TELEGRAM["TALLER"]),
        (f_ent_dt.strftime('%Y-%m-%d'), 0, f"🚀 Hoy se entrega al cliente: *{nombre_p}*", DIRECTORIO_TELEGRAM["GRUPO"])
    ]
    cursor.execute("DELETE FROM tareas_telegram WHERE proyecto = ? AND enviado = 0", (nombre_p,))
    for fecha, ya_procesado, msj, chat in tareas_operativas:
        if fecha and fecha >= hoy_str and ya_procesado == 0:
            cursor.execute("INSERT INTO tareas_telegram (proyecto, fecha_envio, mensaje, chat_id) VALUES (?,?,?,?)", 
                           (nombre_p, fecha, msj, chat))
    msj_jefe = f"🔔 *SISTEMA:* Proyecto *{nombre_p}* actualizado.\n📅 Entrega: {f_ent_dt.strftime('%d/%m/%Y')}"
    cursor.execute("INSERT INTO tareas_telegram (proyecto, fecha_envio, mensaje, chat_id) VALUES (?,?,?,?)", 
                   (nombre_p, hoy_str, msj_jefe, DIRECTORIO_TELEGRAM["JEFE"]))
    conn.commit(); conn.close()

def calcular_situacion(f_entrega_txt, ok_d, ok_c, ok_t, est_actual):
    if est_actual == "TERMINADO": return "✅ FINALIZADO", 0
    try:
        meses = {"enero":1,"febrero":2,"marzo":3,"abril":4,"mayo":5,"junio":6,"julio":7,"agosto":8,"septiembre":9,"octubre":10,"noviembre":11,"diciembre":12}
        p = f_entrega_txt.lower().split(" de ")
        dt_ent = datetime(int(p[2]), meses[p[1]], int(p[0]))
    except: return "---", 0
    hoy = datetime.now(); alertas = []; max_r = 0
    tiempos = [(ok_d, 21, "DESPIECE"), (ok_c, 14, "COMPRAS"), (ok_t, 7, "TALLER")]
    for ok, dias, label in tiempos:
        if ok == 0:
            lim = dt_ent - timedelta(days=dias)
            if hoy > lim:
                d = (hoy-lim).days; alertas.append(f"{label} -{d}d"); max_r = max(max_r, d)
    return ("🔴 " + " | ".join(alertas), max_r) if alertas else ("EN TIEMPO", 0)

# --- INTERFAZ GRÁFICA / GUI ---

def mostrar_notificacion_temporal(titulo, mensaje, tiempo=2000):
    aviso = tk.Toplevel()
    aviso.overrideredirect(True)
    aviso.config(bg="#004400") 
    aviso.geometry(f"300x80+{(aviso.winfo_screenwidth()//2)-150}+{(aviso.winfo_screenheight()//2)-40}")
    tk.Label(aviso, text=mensaje, fg="white", bg="#004400", font=("Arial", 11, "bold")).pack(fill="both", expand=True)
    aviso.after(tiempo, aviso.destroy)

def mostrar_calendario(contenedor, usuario_actual, funcion_volver):
    for widget in contenedor.winfo_children(): widget.destroy()
    ver_terminados = tk.BooleanVar(value=False); ver_solo_atrasados = tk.BooleanVar(value=False)
    frame = tk.Frame(contenedor, bg="black"); frame.pack(fill="both", expand=True)
    
    frame_top = tk.Frame(frame, bg="black"); frame_top.pack(fill="x", padx=20, pady=10)
    tk.Button(frame_top, text="⬅ Menú", command=lambda: [frame.destroy(), funcion_volver()], bg="black", fg="white", font=("Arial", 10, "bold"), bd=0).pack(side="left")
    tk.Label(frame_top, text="CALENDARIO DE ENTREGAS", bg="black", fg="white", font=("Arial", 18, "bold")).pack(side="left", padx=50)

    f_formulario = tk.Frame(frame, bg="#1a1a1a", pady=15); f_formulario.pack(fill="x", padx=100, pady=(0, 20)) 
    f_grid = tk.Frame(f_formulario, bg="#1a1a1a"); f_grid.pack(anchor="center")

    tk.Label(f_grid, text="Cliente:", bg="#1a1a1a", fg="white", font=("Arial", 11, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="e")
    e_cli = tk.Entry(f_grid, width=30, font=("Arial", 11), bg="white", fg="black"); e_cli.grid(row=0, column=1, padx=5, pady=5, sticky="w")
    tk.Label(f_grid, text="Producto:", bg="#1a1a1a", fg="white", font=("Arial", 11, "bold")).grid(row=0, column=2, padx=5, pady=5, sticky="e")
    e_pro = tk.Entry(f_grid, width=30, font=("Arial", 11), bg="white", fg="black"); e_pro.grid(row=0, column=3, padx=5, pady=5, sticky="w")
    
    tk.Label(f_grid, text="Entrega:", bg="#1a1a1a", fg="white", font=("Arial", 11, "bold")).grid(row=1, column=0, padx=5, pady=5, sticky="e")
    f_tiempo = tk.Frame(f_grid, bg="#1a1a1a"); f_tiempo.grid(row=1, column=1, padx=5, pady=5, sticky="w")
    e_cant = tk.Entry(f_tiempo, width=5, font=("Arial", 11), justify="center"); e_cant.pack(side="left")
    c_tipo = ttk.Combobox(f_tiempo, values=["Días", "Semanas"], width=10, state="readonly", font=("Arial", 10)); c_tipo.current(1); c_tipo.pack(side="left", padx=5)

    def sugerir_fechas():
        try:
            cant = int(e_cant.get() or 0)
            tipo = c_tipo.get()
            f_ent = datetime.now() + timedelta(days=cant*7 if tipo=="Semanas" else cant)
            e_fdesp.delete(0, tk.END); e_fdesp.insert(0, (f_ent - timedelta(days=21)).strftime('%Y-%m-%d'))
            e_fcomp.delete(0, tk.END); e_fcomp.insert(0, (f_ent - timedelta(days=14)).strftime('%Y-%m-%d'))
            e_ftall.delete(0, tk.END); e_ftall.insert(0, (f_ent - timedelta(days=7)).strftime('%Y-%m-%d'))
        except: pass

    tk.Button(f_tiempo, text="📅", bg="#1a1a1a", fg="white", bd=0, cursor="hand2", font=("Arial", 20),
              command=lambda: CalendarioIntegrado(frame, e_cant, c_tipo, 450, 150, callback=sugerir_fechas)).pack(side="left", padx=2)
     
    f_hitos = tk.Frame(f_grid, bg="#1a1a1a")
    f_hitos.grid(row=1, column=2, columnspan=2, padx=5, pady=5, sticky="w")
    tk.Label(f_hitos, text="Alertas:", bg="#1a1a1a", fg="#d4af37", font=("Arial", 8, "bold")).pack(side="left", padx=(0, 5))

    def crear_columna_alerta(texto, nombre_id):
        col = tk.Frame(f_hitos, bg="#1a1a1a"); col.pack(side="left", padx=8)
        tk.Label(col, text=texto, bg="#1a1a1a", fg="#aaaaaa", font=("Arial", 7, "bold")).pack()
        fila = tk.Frame(col, bg="#1a1a1a"); fila.pack()
        ent = tk.Entry(fila, width=10, font=("Arial", 9), justify="center", name=f"alerta_{nombre_id}"); ent.pack(side="left")
        tk.Button(fila, text="📅", bg="#1a1a1a", fg="white", bd=0, font=("Arial", 8),
                  command=lambda: CalendarioIntegrado(frame, ent, None, 600, 250)).pack(side="left", padx=2)
        return ent

    e_fdesp = crear_columna_alerta("DESPIECE", "desp")
    e_fcomp = crear_columna_alerta("COMPRAS", "comp")
    e_ftall = crear_columna_alerta("TALLER", "tall")

    def guardar():
        global ID_PROYECTO_EDICION
        try:
            if not e_cli.get() or not e_pro.get(): return
            cli, prod = e_cli.get().upper(), e_pro.get().upper()
            nombre_proyecto_completo = f"{cli} - {prod}"
            if e_cant.get().strip(): 
                cant, tipo = int(e_cant.get()), c_tipo.get()
                f_entrega_dt = datetime.now() + timedelta(days=cant*7 if tipo=="Semanas" else cant)
                meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
                f_str = f"{f_entrega_dt.day} de {meses[f_entrega_dt.month - 1]} de {f_entrega_dt.year}"
            else:
                sel = tabla.selection(); f_str = tabla.item(sel)['values'][3]
                p = f_str.lower().split(" de ")
                meses_n = {"enero":1,"febrero":2,"marzo":3,"abril":4,"mayo":5,"junio":6,"julio":7,"agosto":8,"septiembre":9,"octubre":10,"noviembre":11,"diciembre":12}
                f_entrega_dt = datetime(int(p[2]), meses_n[p[1]], int(p[0]))

            conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
            if ID_PROYECTO_EDICION:
                if messagebox.askyesno("Confirmar", f"¿Actualizar proyecto {prod}?"):
                    cur.execute("DELETE FROM tareas_telegram WHERE proyecto = ? AND enviado = 0", (nombre_proyecto_completo,))
                    cur.execute("UPDATE entregas SET cliente=?, producto=?, fecha_entrega=?, f_desp=?, f_comp=?, f_tall=? WHERE id=?", 
                                (cli, prod, f_str, e_fdesp.get(), e_fcomp.get(), e_ftall.get(), ID_PROYECTO_EDICION))
                    conn.commit() 
                    programar_fechas_atras_manual(cli, prod, f_entrega_dt, e_fdesp.get(), e_fcomp.get(), e_ftall.get())
                    ID_PROYECTO_EDICION = None
                    btn_g.config(text="GUARDAR PROYECTO", bg="#d4af37", fg="black")
                    actualizar_tabla(); [e.delete(0, 'end') for e in [e_cli, e_pro, e_cant, e_fdesp, e_fcomp, e_ftall]]
                    mostrar_notificacion_temporal("Éxito", "PROYECTO ACTUALIZADO")
            else:
                if messagebox.askyesno("Confirmar", f"¿Guardar {prod}?\nEntrega: {f_str}"):
                    cur.execute("INSERT INTO entregas (cliente, producto, fecha_entrega, f_desp, f_comp, f_tall) VALUES (?,?,?,?,?,?)", 
                                (cli, prod, f_str, e_fdesp.get(), e_fcomp.get(), e_ftall.get()))
                    conn.commit()
                    notificar_nuevo_proyecto(cli, prod, f_str)
                    programar_fechas_atras_manual(cli, prod, f_entrega_dt, e_fdesp.get(), e_fcomp.get(), e_ftall.get())
                    actualizar_tabla(); [e.delete(0, 'end') for e in [e_cli, e_pro, e_cant, e_fdesp, e_fcomp, e_ftall]]
                    e_cli.focus_set(); mostrar_notificacion_temporal("Éxito", "PROYECTO REGISTRADO")
            conn.close()
        except Exception as ex: messagebox.showerror("Error", f"Error: {ex}")

    btn_g = tk.Button(f_grid, text="GUARDAR PROYECTO", command=guardar, bg="#d4af37", fg="black", font=("Arial", 10, "bold"), width=20, cursor="hand2")
    btn_g.grid(row=1, column=6, padx=5, pady=5, sticky="e")

    f_toolbar = tk.Frame(frame, bg="black"); f_toolbar.pack(fill="x", padx=100, pady=(10, 5))
    tk.Label(f_toolbar, text="Búsqueda:", bg="black", fg="white", font=("Arial", 11, "bold")).pack(side="left")
    var_busqueda = tk.StringVar(); var_busqueda.trace("w", lambda *args: actualizar_tabla())
    tk.Entry(f_toolbar, textvariable=var_busqueda, font=("Arial", 11), width=25).pack(side="left", padx=10)
    tk.Checkbutton(f_toolbar, text="VER ATRASADOS", variable=ver_solo_atrasados, command=lambda: actualizar_tabla(), bg="black", fg="#ff6666", selectcolor="black", font=("Arial", 10, "bold")).pack(side="right", padx=20)
    tk.Checkbutton(f_toolbar, text="VER TERMINADOS", variable=ver_terminados, command=lambda: actualizar_tabla(), bg="black", fg="gray", font=("Arial", 10, "bold")).pack(side="right")

    estilo = ttk.Style(); estilo.theme_use("clam")
    estilo.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", rowheight=30, font=("Arial", 10))
    estilo.configure("Treeview.Heading", background="#1a1a1a", foreground="white", font=("Arial", 11, "bold"))

    tabla_container = tk.Frame(frame, bg="black"); tabla_container.pack(pady=(0, 50), padx=100, expand=True, fill="both") 
    columnas = ("ID", "CLIENTE", "PRODUCTO", "ENTREGA", "SITUACIÓN", "ESTATUS")
    tabla = ttk.Treeview(tabla_container, columns=columnas, show="headings", height=20) 
    anchos = {"ID": 50, "CLIENTE": 180, "PRODUCTO": 220, "ENTREGA": 180, "SITUACIÓN": 280, "ESTATUS": 120}
    for col in columnas:
        tabla.heading(col, text=col); tabla.column(col, width=anchos.get(col, 150), anchor="center")
    tabla.pack(side=tk.LEFT, fill="both", expand=True)

    def actualizar_tabla():
        for i in tabla.get_children(): tabla.delete(i)
        texto_busqueda = var_busqueda.get().upper().strip()
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor() 
        filtro = "WHERE estatus = 'TERMINADO'" if ver_terminados.get() else "WHERE estatus != 'TERMINADO'"
        cur.execute(f"SELECT id, cliente, producto, fecha_entrega, estatus, ok_despiece, ok_compras, ok_taller FROM entregas {filtro} ORDER BY id DESC")
        for r in cur.fetchall():
            if not texto_busqueda or texto_busqueda in f"{r[1]} {r[2]}".upper():
                sit, _ = calcular_situacion(r[3], r[5], r[6], r[7], r[4])
                if ver_solo_atrasados.get() and "🔴" not in sit: continue
                item = tabla.insert("", "end", values=(r[0], r[1], r[2], r[3], sit, r[4]))
                if "🔴" in sit: tabla.tag_configure("rojo", foreground="#ff6666"); tabla.item(item, tags=("rojo",))
        conn.close()

    actualizar_tabla()

# --- INICIO DE SERVICIOS / START SERVICES ---

def iniciar_servicios_telegram():
    inicializar_db()
    threading.Thread(target=revisar_y_mandar_pendientes, daemon=True).start()
    threading.Thread(target=listener_telegram_unico, args=(None,), daemon=True).start()
    print("🤖 Bot de Mareto optimizado y encendido.")

if __name__ == '__main__':
    # Este bloque solo se ejecuta si se corre este script directamente
    # Para integrarlo a tu App principal, llama a iniciar_servicios_telegram() al iniciar.
    iniciar_servicios_telegram()
