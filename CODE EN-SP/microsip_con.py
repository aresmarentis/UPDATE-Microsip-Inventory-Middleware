"""
PROJECT: ERP Database Integration (Microsip/Firebird)
AUTHOR: Ares Casale Marentis
------------------------------------------------------------
ESPAÑOL:
Módulo de enlace de bajo nivel para la extracción y sincronización de datos 
con el motor Firebird SQL. Implementa decodificación de credenciales y 
configuración de charset WIN1252 para garantizar la integridad de caracteres.

ENGLISH:
Low-level link module for data extraction and synchronization with the 
Firebird SQL engine. Implements credential decoding and WIN1252 charset 
configuration to ensure data integrity.
"""

import fdb
import base64
import os

# --- SECURITY: ENVIRONMENT VARIABLES / SEGURIDAD: VARIABLES DE ENTORNO ---
# ES: Abstraemos la infraestructura para no exponer IPs o rutas de archivos reales.
# EN: Abstracting infrastructure to avoid exposing real IPs or file paths.

IP_SERVIDOR = os.getenv("MICROSIP_IP", "127.0.0.1")
RUTA_DB = os.getenv("MICROSIP_DB_PATH", r"C:\Database\DATA.FDB")
# ES: Clave ofuscada en Base64 para evitar lectura simple en texto plano.
# EN: Obfuscated key in Base64 to prevent plain text reading.
CLAVE_OCULTA = os.getenv("MICROSIP_B64_KEY", "R2RpZXRlcjE5NzI=")



def conectar():
    """
    ES: Establece la conexión con el servidor Microsip.
        Retorna el objeto de conexión o None si falla.
    EN: Establishes connection with the Microsip server.
        Returns the connection object or None if it fails.
    """
    try:
        # Decodificación de seguridad en tiempo de ejecución
        password_real = base64.b64decode(CLAVE_OCULTA).decode('utf-8')
        
        return fdb.connect(
            host=IP_SERVIDOR,
            database=RUTA_DB,
            user='SYSDBA',
            password=password_real,
            charset='WIN1252' # Crucial para el manejo de acentos en español (WIN1252)
        )
    except Exception as e:
        # ES: Silenciamos el error para no exponer detalles del servidor en logs públicos.
        # EN: Muting error to avoid exposing server details in public logs.
        return None

if __name__ == "__main__":
    test_conn = conectar()
    if test_conn:
        print("✅ Connection successful.")
        test_conn.close()
    else:
        print("❌ Connection failed.")
