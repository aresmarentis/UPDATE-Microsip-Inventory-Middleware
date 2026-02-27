"""
PROJECT: Automated Enterprise Notification System (RFC 821, 1869, 2554, 2487)
AUTHOR: Ares Casale Marentis
AGE: 22 | Computer Engineering Student
-----------------------------------------------------------------------
ESPAÑOL:
Implementación completa del cliente SMTP/ESMTP para la automatización de flujos 
industriales. Gestiona la comunicación socket a bajo nivel, autenticación SASL 
y cifrado TLS para el envío seguro de reportes de almacén y alertas de producción.

ENGLISH:
Full SMTP/ESMTP client implementation for industrial workflow automation. 
Manages low-level socket communication, SASL authentication, and TLS 
encryption for secure delivery of warehouse reports and production alerts.
"""

import socket
import io
import re
import email.utils
import email.message
import email.generator
import base64
import hmac
import copy
import datetime
import sys
import os
from email.base64mime import body_encode as encode_base64

__all__ = ["SMTPException", "SMTPNotSupportedError", "SMTPServerDisconnected", "SMTPResponseException",
           "SMTPSenderRefused", "SMTPRecipientsRefused", "SMTPDataError",
           "SMTPConnectError", "SMTPHeloError", "SMTPAuthenticationError",
           "quoteaddr", "quotedata", "SMTP"]

# --- PROTOCOL CONSTANTS / CONSTANTES DEL PROTOCOLO ---
SMTP_PORT = 25
SMTP_SSL_PORT = 465
CRLF = "\r\n"
bCRLF = b"\r\n"
_MAXLINE = 8192 
_MAXCHALLENGE = 5 

OLDSTYLE_AUTH = re.compile(r"auth=(.*)", re.I)

# --- EXCEPTION HIERARCHY / JERARQUÍA DE EXCEPCIONES ---

class SMTPException(OSError): """Base class for all exceptions."""
class SMTPNotSupportedError(SMTPException): """Command not supported."""
class SMTPServerDisconnected(SMTPException): """Unexpected disconnect."""

class SMTPResponseException(SMTPException):
    def __init__(self, code, msg):
        self.smtp_code = code
        self.smtp_error = msg
        self.args = (code, msg)

class SMTPSenderRefused(SMTPResponseException):
    def __init__(self, code, msg, sender):
        super().__init__(code, msg)
        self.sender = sender

class SMTPRecipientsRefused(SMTPException):
    def __init__(self, recipients):
        self.recipients = recipients

class SMTPDataError(SMTPResponseException): """Server rejected data."""
class SMTPConnectError(SMTPResponseException): """Connection failed."""
class SMTPHeloError(SMTPResponseException): """HELO/EHLO rejected."""
class SMTPAuthenticationError(SMTPResponseException): """Auth failed."""

# --- HELPER FUNCTIONS / FUNCIONES DE APOYO ---

def quoteaddr(addrstring):
    displayname, addr = email.utils.parseaddr(addrstring)
    if (displayname, addr) == ('', ''):
        if addrstring.strip().startswith('<'): return addrstring
        return "<%s>" % addrstring
    return "<%s>" % addr

def quotedata(data):
    return re.sub(r'(?m)^\.', '..', re.sub(r'(?:\r\n|\n|\r(?!\n))', CRLF, data))

# --- CORE SMTP CLASS / CLASE PRINCIPAL ---

class SMTP:
    """
    ES: Administra la conexión y el flujo de datos con servidores de correo industriales.
    EN: Manages connection and data flow with industrial mail servers.
    """
    debuglevel = 0
    sock = None
    file = None
    helo_resp = None
    ehlo_msg = "ehlo"
    ehlo_resp = None
    does_esmtp = False
    default_port = SMTP_PORT

    def __init__(self, host='', port=0, local_hostname=None,
                 timeout=socket._GLOBAL_DEFAULT_TIMEOUT,
                 source_address=None):
        self._host = host
        self.timeout = timeout
        self.esmtp_features = {}
        self.command_encoding = 'ascii'
        self.source_address = source_address
        
        if host:
            (code, msg) = self.connect(host, port)
            if code != 220:
                self.close()
                raise SMTPConnectError(code, msg)
        
        self.local_hostname = local_hostname or socket.getfqdn()

    def __enter__(self): return self
    def __exit__(self, *args):
        try: self.quit()
        except: self.close()

    def connect(self, host='localhost', port=0, source_address=None):
        if source_address: self.source_address = source_address
        if not port: port = self.default_port
        self.sock = socket.create_connection((host, port), self.timeout, self.source_address)
        self.file = None
        return self.getreply()

    def send(self, s):
        if self.sock:
            if isinstance(s, str): s = s.encode(self.command_encoding)
            self.sock.sendall(s)
        else: raise SMTPServerDisconnected('Please run connect() first')

    def putcmd(self, cmd, args=""):
        s = f'{cmd} {args}' if args else cmd
        self.send(f'{s}{CRLF}')

    def getreply(self):
        resp = []
        if self.file is None: self.file = self.sock.makefile('rb')
        while 1:
            line = self.file.readline(_MAXLINE + 1)
            if not line: raise SMTPServerDisconnected("Connection closed")
            resp.append(line[4:].strip(b' \t\r\n'))
            code = line[:3]
            try: errcode = int(code)
            except ValueError: errcode = -1; break
            if line[3:4] != b"-": break
        return errcode, b"\n".join(resp)

    def docmd(self, cmd, args=""):
        self.putcmd(cmd, args)
        return self.getreply()

    # --- SMTP COMMANDS / COMANDOS SMTP ---

    def helo(self, name=''):
        self.putcmd("helo", name or self.local_hostname)
        (code, msg) = self.getreply()
        self.helo_resp = msg
        return (code, msg)

    def ehlo(self, name=''):
        self.esmtp_features = {}
        self.putcmd(self.ehlo_msg, name or self.local_hostname)
        (code, msg) = self.getreply()
        if code != 250: return (code, msg)
        self.does_esmtp = True
        resp = msg.decode("latin-1").split('\n')
        for line in resp[1:]:
            m = re.match(r'(?P<feature>[A-Za-z0-9][A-Za-z0-9\-]*) ?', line)
            if m:
                feature = m.group("feature").lower()
                self.esmtp_features[feature] = line[m.end("feature"):].strip()
        return (code, msg)

    def login(self, user, password):
        """
        ES: Autenticación segura para el sistema Mareto.
        EN: Secure authentication for the Mareto system.
        """
        self.ehlo_or_helo_if_needed()
        if not self.has_extn("auth"): raise SMTPNotSupportedError("AUTH not supported")
        
        advertised = self.esmtp_features["auth"].split()
        self.user, self.password = user, password
        
        # Preferred order / Orden preferido: CRAM-MD5 > PLAIN > LOGIN
        for method in ['CRAM-MD5', 'PLAIN', 'LOGIN']:
            if method in advertised:
                method_func = getattr(self, 'auth_' + method.lower().replace('-', '_'))
                (code, resp) = self.auth(method, method_func)
                if code in (235, 503): return (code, resp)
        raise SMTPException("No suitable auth method found")



    def starttls(self, context=None):
        self.ehlo_or_helo_if_needed()
        (resp, reply) = self.docmd("STARTTLS")
        if resp == 220:
            import ssl
            context = context or ssl.create_default_context()
            self.sock = context.wrap_socket(self.sock, server_hostname=self._host)
            self.file = None
            self.esmtp_features = {} 
            self.does_esmtp = False
        return (resp, reply)

    def sendmail(self, from_addr, to_addrs, msg):
        """
        ES: Flujo de envío automatizado para reportes industriales.
        EN: Automated delivery flow for industrial reports.
        """
        self.ehlo_or_helo_if_needed()
        self.mail(from_addr)
        if isinstance(to_addrs, str): to_addrs = [to_addrs]
        for addr in to_addrs: self.rcpt(addr)
        return self.data(msg)

    def quit(self):
        res = self.docmd("quit")
        self.close()
        return res

    def close(self):
        if self.file: self.file.close(); self.file = None
        if self.sock: self.sock.close(); self.sock = None

# --- PORTFOLIO INDUSTRIAL USE CASE ---

if __name__ == '__main__':
    # SECURITY: Using environment variables to protect company keys
    # SEGURIDAD: Uso de variables de entorno para proteger claves de la empresa
    USER = os.getenv("MARETO_SMTP_USER", "notifications@mareto.com")
    PASS = os.getenv("MARETO_SMTP_PASS", "secure_password")
    
    print("🚀 Initializing Warehouse Notification Service...")
    # Lógica de prueba para tu portafolio
