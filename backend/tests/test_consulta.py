# backend/tests/test_consulta.py
"""
Tests para endpoints de consulta protegidos.
"""

from app.modules.users.models import Cliente
from app.core.crypto import hash_cedula


def crear_cliente(db_session, cedula="V11223344", tienda_id=None):
    """Helper: crea un cliente aprobado."""
    cliente = Cliente(
        nombre="Cliente Consulta",
        cedula=cedula,
        cedula_hash=hash_cedula(cedula),
        telefono="04120003333",
        email="consulta@test.com",
        estado="aprobado",
        nivel="nuevo",
        score=50,
        tienda_id=tienda_id,
    )
    db_session.add(cliente)
    db_session.commit()
    db_session.refresh(cliente)
    return cliente


class TestBuscarCliente:
    """Pruebas para buscar cliente por cédula."""

    def test_buscar_cliente_sin_auth(self, client, db_session):
        """Sin autenticación, debe rechazar."""
        crear_cliente(db_session)

        response = client.get("/api/v1/clientes/buscar/V11223344")

        assert response.status_code == 401

    def test_buscar_cliente_con_auth(self, client, admin_token, db_session):
        """Un admin autenticado puede buscar."""
        crear_cliente(db_session)

        response = client.get(
            "/api/v1/clientes/buscar/V11223344",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["nombre"] == "Cliente Consulta"
        assert data["cedula"] == "V11223344"


class TestDashboard:
    """Pruebas para dashboard admin."""

    def test_dashboard_sin_auth(self, client):
        """Sin token, debe rechazar."""
        response = client.get("/api/v1/admin/dashboard")
        assert response.status_code == 401

    def test_dashboard_con_auth(self, client, admin_token):
        """Con token admin, debe responder con métricas."""
        response = client.get(
            "/api/v1/admin/dashboard",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "clientes" in data
        assert "financiamientos" in data
        assert "pagos_pendientes" in data


class TestPagosPendientes:
    """Pruebas para listar pagos pendientes."""

    def test_pagos_pendientes_sin_auth(self, client):
        """Sin token, debe rechazar."""
        response = client.get("/api/v1/pagos/pendientes")
        assert response.status_code == 401

    def test_pagos_pendientes_con_auth(self, client, admin_token):
        """Con token admin, debe responder."""
        response = client.get(
            "/api/v1/pagos/pendientes",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "pagos" in data
        assert isinstance(data["pagos"], list)