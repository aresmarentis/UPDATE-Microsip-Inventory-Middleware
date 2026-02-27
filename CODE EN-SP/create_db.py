"""
PROJECT: Industrial Incident Logging & Quality Assurance System
AUTHOR: Ares Casale Marentis
AGE: 22 | Computer Engineering Student
------------------------------------------------------------
ESPAÑOL:
Este módulo gestiona la persistencia de incidentes operativos en almacén. 
Implementa una arquitectura SQL para el registro de fallas en materiales 
o mano de obra, permitiendo el análisis de causa-raíz y la mejora de procesos 
industriales mediante el monitoreo de la red local.

ENGLISH:
This module manages the persistence of operational warehouse incidents. 
It implements a SQL architecture for logging material or labor failures, 
enabling root-cause analysis and industrial process improvement through 
local network monitoring.
"""

import sqlite3
import os

# --- SECURITY: NETWORK ABSTRACTION / SEGURIDAD: ABSTRACCIÓN DE RED ---
# ES: Usamos variables de entorno para no exponer la estructura del servidor real.
# EN: Environment variables are used to avoid exposing real server structures.
RUTA_RED = os.getenv("MARETO_INCIDENTS_PATH", r"\\SERVER\Quality_Control")



def crear_base_datos_incidentes():
    """
    ES: Inicializa la base de datos relacional y define la estructura de tablas 
        para el control de calidad. Maneja excepciones de red.
    EN: Initializes the relational database and defines table structures 
        for quality control. Handles network exceptions.
    """
    # ES: Generamos la ruta absoluta del archivo de base de datos.
    # EN: Generating the absolute path for the database file.
    ruta_archivo = os.path.join(RUTA_RED, "incidentes.db")
    
    print(f"Status: Attempting to initialize DB at {ruta_archivo}...")
    
    try:
        # ES: Establecimiento de conexión con motor SQLite3.
        # EN: Establishing connection with SQLite3 engine.
        conexion = sqlite3.connect(ruta_archivo)
        cursor = conexion.cursor()
        
        # ES: Definición de esquema para auditoría industrial.
        # EN: Schema definition for industrial auditing.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registro_incidentes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT,           -- ISO-8601 Format Recommended
                trabajador TEXT,      -- Operator Name
                material TEXT,        -- Part Number or Material ID
                descripcion TEXT      -- Incident details for Kaizen analysis
            )
        """)
        
        conexion.commit()
        conexion.close()
        
        print("Success: 'incidentes.db' is ready for operations.")
        
    except Exception as e:
        # ES: Log de errores detallado para depuración en entornos de red.
        # EN: Detailed error logging for debugging in network environments.
        print(f"CRITICAL ERROR: Could not create database. Check network connectivity.")
        print(f"Debug Info: {e}")

if __name__ == "__main__":
    # ES: Validación de integridad de la ruta de red antes de la ejecución.
    # EN: Network path integrity validation before execution.
    if os.path.exists(RUTA_RED):
        crear_base_datos_incidentes()
    else:
        print(f"CONNECTION ERROR: Remote path {RUTA_RED} is unreachable.")
