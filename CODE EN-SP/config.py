"""
PROJECT: File System & Path Management Module
AUTHOR: Ares Casale Marentis
AGE: 22 | Computer Engineering Student
------------------------------------------------------------
ESPAÑOL:
Este módulo centraliza la gestión de rutas del sistema. Utiliza la librería 'os' 
para garantizar la compatibilidad entre diferentes sistemas operativos, 
administrando los archivos CSV que funcionan como bases de datos locales 
para el historial, trabajadores, usuarios y materiales.

ENGLISH:
This module centralizes the system's path management. It uses the 'os' library 
to ensure cross-platform compatibility, managing the CSV files that serve 
as local flat-file databases for history, workers, users, and materials.
"""

import os

# ES: Definición de la raíz del proyecto. 
# Usar "." permite portabilidad total al mover la carpeta del sistema.
# EN: Project root definition. 
# Using "." allows full portability when moving the system folder.
RUTA_BASE = "." 

# --- DATA PERSISTENCE LAYER / CAPA DE PERSISTENCIA DE DATOS ---



# ES: Historial de movimientos de almacén (Entradas/Salidas).
# EN: Warehouse movement history (Check-in/Check-out).
ARCHIVO_DB = os.path.join(RUTA_BASE, "historial_almacen.csv")

# ES: Gestión de Capital Humano y Control de Acceso.
# EN: Human Capital Management and Access Control.
FILE_TRABAJADORES = os.path.join(RUTA_BASE, "lista_trabajadores.csv")
FILE_USUARIOS = os.path.join(RUTA_BASE, "usuarios_sistema.csv")

# ES: Listas Maestras para validación de datos en el ERP.
# EN: Master Lists for data validation within the ERP system.
FILE_PROYECTOS = os.path.join(RUTA_BASE, "lista_proyectos.csv")
FILE_MATERIALES = os.path.join(RUTA_BASE, "lista_materiales.csv")

# --- OBSERVATION FOR PORTFOLIO ---
# ES: El uso de os.path.join previene errores de sintaxis en las rutas (vía '/' o '\').
# EN: Using os.path.join prevents path syntax errors (across '/' or '\').
