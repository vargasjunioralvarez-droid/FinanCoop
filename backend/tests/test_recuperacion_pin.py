# backend/tests/test_recuperacion_pin.py
"""
Tests para el flujo de recuperación de PIN.
"""

from datetime import datetime, timezone, timedelta
from app.modules.users.models import Cliente
from app.core.crypto import hash_cedula


def crear_cliente_con_email(db_session, email="cliente@test.com", cedula="V12345678"):
    """Helper: crea un cliente aprobado con email configurado."""
    cliente = Cliente(
        nombre="Cliente Recuperación",
        cedula=cedula,
        cedula_hash=hash_cedula(cedula),
        telefono="04120001111",
        email=email,
        estado="aprobado",
        nivel="nuevo",
        score=50,
    )
    db_session.add(cliente)
    db_session.commit()
    db_session.refresh(cliente)
    return cliente


class TestRecuperacionPIN:
    """Pruebas del flujo completo de recuperación de PIN."""

    def test_solicitar_codigo_cliente_existente(self, client, db_session):
        """Un cliente con email registrado puede solicitar un código."""
        crear_cliente_con_email(db_session)

        response = client.post("/api/v1/auth/recuperar-pin/solicitar-codigo", json={
            "cedula": "V12345678"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Código enviado" in data["mensaje"]

    def test_solicitar_codigo_cliente_sin_email(self, client, db_session):
        """Un cliente sin email no puede solicitar código."""
        cliente = Cliente(
            nombre="Cliente Sin Email",
            cedula="V87654321",
            cedula_hash=hash_cedula("V87654321"),
            telefono="04120002222",
            email="",
            estado="aprobado",
        )
        db_session.add(cliente)
        db_session.commit()

        response = client.post("/api/v1/auth/recuperar-pin/solicitar-codigo", json={
            "cedula": "V87654321"
        })

        assert response.status_code == 400
        assert "correo" in response.json()["detail"].lower()

    def test_solicitar_codigo_cliente_no_existente(self, client):
        """Un cliente inexistente recibe mensaje genérico (sin revelar información)."""
        response = client.post("/api/v1/auth/recuperar-pin/solicitar-codigo", json={
            "cedula": "V00000000"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Si la cédula está registrada" in data["mensaje"]