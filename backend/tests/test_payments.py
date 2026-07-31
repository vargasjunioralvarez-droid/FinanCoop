# backend/tests/test_payments.py
"""
Tests para el módulo de pagos.
"""

import json
from datetime import datetime, timezone, timedelta
from app.modules.users.models import Cliente
from app.modules.loans.models import Financiamiento, Cuota
from app.modules.payments.models import Pago
from app.core.crypto import hash_cedula


def crear_cliente_aprobado(db_session):
    """Helper: crea un cliente aprobado en la BD de prueba."""
    cliente = Cliente(
        nombre="Cliente Pagos",
        cedula="V55667788",
        cedula_hash=hash_cedula("V55667788"),
        telefono="04120009999",
        estado="aprobado",
        nivel="nuevo",
        score=50,
    )
    db_session.add(cliente)
    db_session.commit()
    db_session.refresh(cliente)
    return cliente


def crear_financiamiento_con_cuotas(db_session, cliente_id):
    """Helper: crea un financiamiento activo con 3 cuotas pendientes."""
    fin = Financiamiento(
        cliente_id=cliente_id,
        codigo="F-TEST-001",
        descripcion="Test financiamiento",
        monto_total_bs=3000,
        monto_entrada_bs=900,
        monto_financia_bs=2100,
        monto_cuota_bs=700,
        monto_total_usd=100,
        monto_entrada_usd=30,
        monto_financia_usd=70,
        monto_cuota_usd=23.33,
        tasa_aplicada=30,
        nivel_aplicado="nuevo",
        cuotas_solicitadas=3,
        cuotas_aprobadas=3,
        requiere_aprobacion=False,
        entrada_pct=30,
        financia_pct=70,
        fecha_primera_cuota=datetime.now(timezone.utc) + timedelta(days=15),
        estado="activo",
    )
    db_session.add(fin)
    db_session.commit()
    db_session.refresh(fin)

    cuotas = []
    for i in range(1, 4):
        cuota = Cuota(
            financiamiento_id=fin.id,
            numero=i,
            monto_base_bs=700,
            monto_base_usd=23.33,
            monto_total_bs=700,
            monto_total_usd=23.33,
            fecha_vencimiento=datetime.now(timezone.utc) + timedelta(days=15 * i),
            estado="pendiente",
        )
        db_session.add(cuota)
        cuotas.append(cuota)
    db_session.commit()
    for c in cuotas:
        db_session.refresh(c)
        # Forzar timezone para compatibilidad con SQLite
        if c.fecha_vencimiento.tzinfo is None:
            c.fecha_vencimiento = c.fecha_vencimiento.replace(tzinfo=timezone.utc)
    return fin, cuotas


class TestReportarPago:
    """Pruebas del endpoint para reportar pagos."""

    def test_reportar_pago_exitoso(self, client, admin_token, db_session):
        """Un admin autenticado puede reportar un pago para una cuota existente."""
        cliente = crear_cliente_aprobado(db_session)
        fin, cuotas = crear_financiamiento_con_cuotas(db_session, cliente.id)
        cuota = cuotas[0]

        response = client.post(
            "/api/v1/pagos/reportar",
            json={
                "cuota_id": cuota.id,
                "monto_bs": 700,
                "metodo": "pago_movil",
                "referencia": "REF-001",
                "banco_origen": "BancoTest",
                "telefono_pago": "04120001111",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "pago_id" in data
        assert data["estado"] == "pendiente"

    def test_reportar_pago_sin_autenticacion(self, client):
        """Sin token de autenticación, el endpoint debe rechazar la petición."""
        response = client.post(
            "/api/v1/pagos/reportar",
            json={
                "cuota_id": 1,
                "monto_bs": 500,
                "metodo": "transferencia",
                "referencia": "REF-SIN-AUTH",
            },
        )
        assert response.status_code == 401

    def test_reportar_pago_cuota_ya_pagada(self, client, admin_token, db_session):
        """No se puede reportar un pago para una cuota que ya fue pagada."""
        cliente = crear_cliente_aprobado(db_session)
        fin, cuotas = crear_financiamiento_con_cuotas(db_session, cliente.id)
        cuota = cuotas[0]

        # Marcar la cuota como pagada manualmente
        cuota.estado = "pagada"
        db_session.commit()

        response = client.post(
            "/api/v1/pagos/reportar",
            json={
                "cuota_id": cuota.id,
                "monto_bs": 700,
                "metodo": "pago_movil",
                "referencia": "REF-002",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 400
        assert "ya fue pagada" in response.json()["detail"].lower()


class TestConciliarPago:
    """Pruebas del endpoint para conciliar pagos."""

    def test_conciliar_pago_exitoso(self, client, admin_token, db_session):
        """Un admin puede conciliar un pago pendiente."""
        cliente = crear_cliente_aprobado(db_session)
        fin, cuotas = crear_financiamiento_con_cuotas(db_session, cliente.id)
        cuota = cuotas[0]

        # Crear un pago pendiente
        pago = Pago(
            cuota_id=cuota.id,
            financiamiento_id=fin.id,
            referencia="REF-CONCILIAR",
            metodo="pago_movil",
            monto_reportado_bs=700,
            estado="pendiente",
            fecha_reporte=datetime.now(timezone.utc),
        )
        db_session.add(pago)
        db_session.commit()
        db_session.refresh(pago)

        response = client.post(
            "/api/v1/pagos/conciliar",
            json={
                "pago_id": pago.id,
                "monto_confirmado_bs": 700,
                "estado": "conciliado",
                "conciliado_por": "admin_test",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["estado"] == "conciliado"


class TestPagarEfectivo:
    """Pruebas del endpoint para pagar en efectivo."""

    def test_pagar_efectivo_exitoso(self, client, admin_token, db_session):
        """Un admin puede registrar un pago en efectivo."""
        cliente = crear_cliente_aprobado(db_session)
        fin, cuotas = crear_financiamiento_con_cuotas(db_session, cliente.id)
        cuota = cuotas[0]

        response = client.post(
            f"/api/v1/pagos/cuotas/{cuota.id}/pagar-efectivo",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["cuota_pagada"] == cuota.numero

    def test_pagar_efectivo_sin_auth(self, client):
        """Sin autenticación, el endpoint rechaza la petición."""
        response = client.post("/api/v1/pagos/cuotas/1/pagar-efectivo")
        assert response.status_code == 401