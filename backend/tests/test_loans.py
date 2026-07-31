# backend/tests/test_loans.py
"""
Tests para el módulo de financiamientos.
"""


class TestCrearFinanciamiento:
    """Pruebas del endpoint de creación de financiamientos."""

    def test_crear_financiamiento_exitoso(self, client, admin_token, db_session):
        """Un admin puede crear un financiamiento para un cliente aprobado."""
        from app.modules.users.models import Cliente
        from app.core.crypto import hash_cedula

        # Crear cliente aprobado
        cliente = Cliente(
            nombre="María López",
            cedula="V11223344",
            cedula_hash=hash_cedula("V11223344"),
            telefono="04123334444",
            estado="aprobado",
            nivel="nuevo",
            score=50,
        )
        db_session.add(cliente)
        db_session.commit()
        db_session.refresh(cliente)

        # Crear financiamiento
        response = client.post(
            "/api/v1/financiamientos",
            json={
                "cliente_id": cliente.id,
                "descripcion": "Lavadora",
                "monto_total_bs": 2000,
                "cuotas_solicitadas": 3,
                "numero_factura": "FAC-001",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "financiamiento" in data
        assert data["financiamiento"]["estado"] == "activo"
        assert data["financiamiento"]["cuotas_aprobadas"] > 0

    def test_crear_financiamiento_sin_autenticacion(self, client):
        """Sin token de autenticación, el endpoint debe rechazar la petición."""
        response = client.post(
            "/api/v1/financiamientos",
            json={
                "cliente_id": 1,
                "descripcion": "Test sin auth",
                "monto_total_bs": 1000,
                "cuotas_solicitadas": 2,
            },
        )

        assert response.status_code == 401

    def test_crear_financiamiento_cliente_no_aprobado(self, client, admin_token, db_session):
        """No se puede crear un financiamiento para un cliente no aprobado."""
        from app.modules.users.models import Cliente
        from app.core.crypto import hash_cedula

        cliente = Cliente(
            nombre="Pedro Pendiente",
            cedula="V99887766",
            cedula_hash=hash_cedula("V99887766"),
            telefono="04125556666",
            estado="pendiente",
            nivel="nuevo",
            score=0,
        )
        db_session.add(cliente)
        db_session.commit()
        db_session.refresh(cliente)

        response = client.post(
            "/api/v1/financiamientos",
            json={
                "cliente_id": cliente.id,
                "descripcion": "No debería funcionar",
                "monto_total_bs": 500,
                "cuotas_solicitadas": 1,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 400
        assert "no está aprobado" in response.json()["detail"].lower()