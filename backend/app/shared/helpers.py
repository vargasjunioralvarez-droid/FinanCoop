# backend/app/shared/helpers.py
"""
Funciones utilitarias puras (sin dependencias del proyecto).
Separadas para evitar importaciones circulares.
"""

import random
import string
import uuid


def normalizar_telefono(telefono: str) -> str:
    if not telefono:
        return ""
    limpio = ''.join(c for c in telefono if c.isdigit() or c == '+')
    if limpio.startswith('+58') and len(limpio) == 13:
        return limpio
    if limpio.startswith('+580') and len(limpio) == 14:
        return '+58' + limpio[4:]
    if limpio.startswith('0') and len(limpio) == 11:
        return '+58' + limpio[1:]
    if limpio.startswith('4') and len(limpio) == 10:
        return '+58' + limpio
    if limpio.startswith('+'):
        return limpio
    if len(limpio) == 10 and limpio.startswith('4'):
        return '+58' + limpio
    if len(limpio) == 11 and limpio.startswith('4'):
        return '+58' + limpio
    return limpio


def es_numero_valido(telefono: str) -> bool:
    if not telefono:
        return False
    if telefono.startswith('+58') and len(telefono) == 13:
        operadora = telefono[3:5]
        return operadora in ['41', '42', '412', '414', '416', '424', '426']
    return False


def generar_pin():
    """Genera PIN de 6 caracteres (números + letras mayúsculas, sin 0/O/1/I/L)"""
    caracteres = string.digits + string.ascii_uppercase
    caracteres = caracteres.replace('0', '').replace('O', '').replace('1', '').replace('I', '').replace('L', '')
    return ''.join(random.choices(caracteres, k=6))


def generar_token():
    return str(uuid.uuid4())