# backend/app/services/cliente_service.py
"""
Servicio de aplicación para la gestión de clientes.
"""

import logging
from app.modules.users.models import Cliente
from app.core.crypto import hash_cedula
from app.core.security import hash_pin
from app.shared.utils import generar_pin, generar_token

logger = logging.getLogger(__name__)


class ClienteService:
    """Servicio para el registro y gestión de clientes."""

    @staticmethod
    def crear(
        db,
        nombre: str,
        cedula: str,
        telefono: str,
        email: str = "",
        direccion: str = "",
        referencia_nombre: str = "",
        referencia_telefono: str = "",
        referencia_parentesco: str = "",
        url_cedula: str = None,
        tienda_id: int = None
    ) -> Cliente:
        """
        Crea un nuevo cliente con PIN hasheado y hash de cédula.
        Retorna el objeto Cliente creado.
        """
        pin_generado = generar_pin()
        pin_hasheado = hash_pin(pin_generado)

        db_cliente = Cliente(
            nombre=nombre,
            cedula=cedula,
            cedula_hash=hash_cedula(cedula),
            telefono=telefono,
            email=email or "",
            direccion=direccion or "",
            referencia_nombre=referencia_nombre or "",
            referencia_telefono=referencia_telefono or "",
            referencia_parentesco=referencia_parentesco or "",
            url_cedula=url_cedula,
            pin_hash=pin_hasheado,
            pin=None,
            token_app=generar_token(),
            estado="pendiente",
            nivel="nuevo",
            score=0,
            tienda_id=tienda_id
        )

        db.add(db_cliente)
        db.commit()
        db.refresh(db_cliente)

        logger.info(f"✅ Cliente registrado: ID {db_cliente.id} - Tienda: {tienda_id}")

        return db_cliente, pin_generado