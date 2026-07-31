# backend/tests/test_clients.py
"""
Tests para el módulo de clientes.
"""


class TestCrearCliente:
    """Pruebas del endpoint de creación de clientes."""

    def test_crear_cliente_exitoso(self, client, admin_token):
        """Un admin autenticado puede crear un cliente."""
        response = client.post(
            "/api/v1/clientes/json",
            json={
                "nombre": "Juan Pérez",
                "cedula": "V12345678",
                "telefono": "04121234567",
                "email": "juan@example.com",
                "direccion": "Calle 123",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["cliente"]["nombre"] == "Juan Pérez"
        assert data["cliente"]["cedula"] == "V12345678"
        # El PIN debe estar enmascarado en producción, pero en desarrollo se muestra
        assert "pin" in data

    def test_crear_cliente_cedula_duplicada(self, client, admin_token, db_session):
        """No se puede crear dos clientes con la misma cédula."""
        # Crear primer cliente
        from app.modules.users.models import Cliente
        from app.core.crypto import hash_cedula

        cliente = Cliente(
            nombre="Existente",
            cedula="V87654321",
            cedula_hash=hash_cedula("V87654321"),
            telefono="04120000000",
            estado="pendiente",
            nivel="nuevo",
            score=0,
        )
        db_session.add(cliente)
        db_session.commit()

        # Intentar crear otro con la misma cédula
        response = client.post(
            "/api/v1/clientes/json",
            json={
                "nombre": "Duplicado",
                "cedula": "V87654321",
                "telefono": "04121111111",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 409
        assert "ya existe" in response.json()["detail"]