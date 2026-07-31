# backend/app/core/crypto.py
"""
Utilidades de cifrado para datos sensibles (PII).
- EncryptedString: tipo SQLAlchemy que cifra/descifra automáticamente con Fernet.
- hash_cedula: hash SHA-256 para búsquedas exactas de cédula.
"""

import os
import hashlib
from cryptography.fernet import Fernet
from sqlalchemy.types import TypeDecorator, String

DATA_ENCRYPTION_KEY = os.getenv("DATA_ENCRYPTION_KEY", "")

_cipher = None
if DATA_ENCRYPTION_KEY:
    _cipher = Fernet(DATA_ENCRYPTION_KEY.encode())


class EncryptedString(TypeDecorator):
    """Tipo de columna SQLAlchemy que cifra/descifra automáticamente con Fernet."""
    impl = String(500)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return _cipher.encrypt(value.encode()).decode() if _cipher else value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return _cipher.decrypt(value.encode()).decode() if _cipher else value


def hash_cedula(cedula: str) -> str:
    """Hash SHA-256 de la cédula para búsquedas exactas."""
    return hashlib.sha256(cedula.strip().upper().encode()).hexdigest()