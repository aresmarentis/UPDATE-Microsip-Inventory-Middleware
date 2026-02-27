"""
PROJECT: Industrial System Bootloader & Error Tracking
AUTHOR: Ares Casale Marentis
AGE: 22 | Computer Engineering Student
-----------------------------------------------------------------------
ESPAÑOL:
Punto de entrada principal del sistema Mareto. Gestiona la inicialización 
del entorno, la vinculación dinámica de librerías en red y un sistema robusto 
de captura de excepciones (Error Logging). Asegura que cualquier fallo crítico 
sea registrado automáticamente en el servidor para auditoría técnica.

ENGLISH:
Main entry point for the Mareto system. Manages environment initialization, 
dynamic linking of network libraries, and a robust exception handling system 
(Error Logging). Ensures that any critical failure is automatically logged 
on the server for technical auditing.
"""

import ctypes
import sys
import traceback
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import os

# ES: Configuración de ID de proceso para que Windows reconozca la App correctamente.
# EN: Process ID configuration for Windows to correctly identify the application.
myappid = 'mareto.sistema.vFinal'
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except:
    pass # Fallback for non-windows environments



def lanzar():
    """
    ES: Orquestador de arranque. Configura el sys.path e invoca el módulo principal.
    EN: Boot orchestrator. Configures sys.path and invokes the main module.
    """
    # ES: Ruta de red donde residen los módulos centrales.
    # EN: Network path where central modules reside.
    ruta_red = os.getenv("MARETO_NETWORK_PATH", r"\\PROYECTOS\Mareto_sistema")

    try:
        # ES: Inyección dinámica de dependencias en el path del sistema.
        # EN: Dynamic dependency injection into the system path.
        if ruta_red not in sys.path:
            sys.path.insert(0, ruta_red)

        # ES: Importación diferida para permitir la configuración previa del entorno.
        # EN: Deferred import to allow previous environment configuration.
        import menu_principal
        menu_principal.main()

    except Exception:
        # --- ROBUST ERROR LOGGING SYSTEM ---
        # ES: Captura el traceback completo para facilitar la depuración remota.
        # EN: Captures full traceback to facilitate remote debugging.
        error_detalle = traceback.format_exc()
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            ruta_logs = os.path.join(ruta_red, "logs")
            os.makedirs(ruta_logs, exist_ok=True)

            with open(
                os.path.join(ruta_logs, "errores.log"),
                "a",
                encoding="utf-8"
            ) as f:
                f.write(f"\n[{fecha}] CRITICAL SYSTEM ERROR:\n{error_detalle}\n")
        except:
            # ES: Evita que el fallo del log detenga el reporte al usuario.
            # EN: Prevents logging failure from stopping user reporting.
            pass  

        # --- USER NOTIFICATION / NOTIFICACIÓN AL USUARIO ---
        root = tk.Tk()
        root.withdraw() # ES: Oculta la ventana raíz de Tkinter / EN: Hides the root window
        
        messagebox.showerror(
            "Error del sistema",
            "No se pudo iniciar el sistema Mareto.\n\n"
            "El error ha sido registrado en el servidor.\n"
            "Por favor, contacta al Ingeniero Ares para soporte técnico."
        )
        root.destroy()

if __name__ == "__main__":
    lanzar()
