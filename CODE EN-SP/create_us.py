"""
PROJECT: Local User Authentication & Role Management System
AUTHOR: Ares Casale Marentis
AGE: 22 | Computer Engineering Student
------------------------------------------------------------
ESPAÑOL:
Este módulo implementa el sistema de seguridad local para el control de acceso.
Utiliza SQLite para gestionar perfiles de usuario y roles (Administrador/Operador),
garantizando que solo personal autorizado pueda modificar registros críticos de 
inventario o incidentes en el sistema Mareto.

ENGLISH:
This module implements the local security system for access control.
It utilizes SQLite to manage user profiles and roles (Administrator/Operator),
ensuring that only authorized personnel can modify critical inventory or 
incident records within the Mareto system.
"""

import sqlite3
import os

# ES: Nombre de la base de datos de seguridad local.
# EN: Local security database filename.
DB_AUTH = "usuarios.db"



def crear_base_datos_local():
    """
    ES: Inicializa el esquema de seguridad y crea la cuenta de superusuario inicial.
    EN: Initializes the security schema and creates the initial superuser account.
    """
    # ES: Establecimiento de conexión persistente.
    # EN: Establishing persistent connection.
    conexion = sqlite3.connect(DB_AUTH)
    cursor = conexion.cursor()
    
    try:
        # ES: Creación de tabla de usuarios con restricción UNIQUE para el nombre de usuario.
        # EN: User table creation with UNIQUE constraint on the username.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT NOT NULL UNIQUE,
                contrasena TEXT NOT NULL, -- Recommended: Implement PBKDF2 hashing in production
                rol TEXT NOT NULL          -- Role-Based Access Control (RBAC)
            )
        """)
        
        # ES: Inserción de credenciales de administración por defecto.
        # EN: Default administrative credentials insertion.
        cursor.execute("""
            INSERT OR IGNORE INTO usuarios (usuario, contrasena, rol) 
            VALUES ('admin', '1234', 'ADMINISTRADOR')
        """)
        
        conexion.commit()
        print(f"Success: '{DB_AUTH}' security layer deployed.")
        
    except Exception as e:
        # ES: Captura de excepciones durante la inicialización de seguridad.
        # EN: Exception handling during security initialization.
        print(f"CRITICAL ERROR: Security layer failed to initialize: {e}")
        
    finally:
        # ES: Cierre seguro de la conexión para evitar bloqueos de base de datos.
        # EN: Safe connection closure to prevent database locks.
        conexion.close()

if __name__ == "__main__":
    crear_base_datos_local()
