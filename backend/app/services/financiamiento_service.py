# backend/app/services/financiamiento_service.py
"""
Servicio de aplicación para la gestión de financiamientos.
Contiene toda la lógica de negocio: validaciones, cálculos y creación.
"""

import random
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.modules.users.models import Cliente
from app.modules.loans.models import Financiamiento, Cuota
from app.shared.utils import (
    calcular_nivel,
    actualizar_score_cliente,
    calcular_usado_disponible,
    obtener_tasa_actual
)

logger = logging.getLogger(__name__)

MAX_CREDITOS_ACTIVOS = 3


class FinanciamientoService:
    """Servicio para la creación y gestión de financiamientos."""

    @staticmethod
    def crear(
        db: Session,
        cliente_id: int,
        monto_total_bs: float,
        cuotas_solicitadas: int,
        descripcion: str = None,
        numero_factura: str = None,
        tienda_id: int = None,
        usuario_rol: str = None,
        usuario_tienda_id: int = None,
        usuario_id: int = None
    ) -> dict:
        """
        Crea un nuevo financiamiento aplicando todas las reglas de negocio.
        
        Retorna un diccionario con el resultado de la operación.
        """
        # Validar que el cliente existe y está aprobado
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        if not cliente:
            raise ValueError("Cliente no encontrado")

        if cliente.estado != "aprobado":
            raise ValueError("Cliente no está aprobado. Debe ser verificado por el administrador.")

        # Calcular nivel y configuración
        nivel, config = calcular_nivel(cliente.score, db)

        # Validar cantidad de créditos activos
        creditos_activos = db.query(Financiamiento).filter(
            Financiamiento.cliente_id == cliente_id,
            Financiamiento.estado == "activo"
        ).count()

        if creditos_activos >= MAX_CREDITOS_ACTIVOS:
            raise ValueError(f"Límite de {MAX_CREDITOS_ACTIVOS} créditos activos alcanzado")

        # Validar deudas vencidas
        hoy = datetime.now(timezone.utc)
        deudas_vencidas = db.query(Cuota).join(Financiamiento).filter(
            Financiamiento.cliente_id == cliente_id,
            Cuota.estado == "pendiente",
            Cuota.fecha_vencimiento < hoy
        ).count()

        if deudas_vencidas > 0:
            raise ValueError(f"Tiene {deudas_vencidas} cuota(s) vencida(s)")

        # Validar disponibilidad
        disponible = calcular_usado_disponible(cliente_id, db)
        if not disponible["puede_comprar"]:
            raise ValueError("Límite de financiamiento agotado")

        tasa = obtener_tasa_actual(db)
        monto_total_usd = monto_total_bs / tasa if tasa > 0 else 0

        if monto_total_usd > disponible["disponible_usd"]:
            raise ValueError(f"Monto excede disponible: ${disponible['disponible_usd']:.2f}")

        logger.info(f"🔍 DEBUG: cliente={cliente.nombre}, nivel={nivel}, monto_usd={monto_total_usd:.2f}, limite={config['monto_max_usd']:.2f}")

        if monto_total_usd > config["monto_max_usd"]:
            raise ValueError(
                f"❌ Monto excede límite de nivel {nivel}: ${config['monto_max_usd']:.2f} USD (solicitado: ${monto_total_usd:.2f})"
            )

        if cuotas_solicitadas > config["cuotas_max"]:
            raise ValueError(f"Cuotas exceden máximo de {config['cuotas_max']}")
        if cuotas_solicitadas < 1:
            raise ValueError("Debe solicitar al menos 1 cuota")

        # Determinar aprobación
        requiere_aprobacion = cuotas_solicitadas > config["cuotas_base"] and config["aprobacion_extra"]
        cuotas_aprobadas = cuotas_solicitadas if not requiere_aprobacion else config["cuotas_base"]

        # Cálculos financieros
        entrada_pct = config["entrada_pct"] / 100
        financia_pct = config["financia_pct"] / 100

        entrada_bs = monto_total_bs * entrada_pct
        financia_bs = monto_total_bs * financia_pct
        monto_cuota_bs = financia_bs / cuotas_aprobadas if cuotas_aprobadas > 0 else 0

        entrada_usd_ref = entrada_bs / tasa if tasa > 0 else 0
        financia_usd_ref = financia_bs / tasa if tasa > 0 else 0
        monto_cuota_usd_ref = monto_cuota_bs / tasa if tasa > 0 else 0

        # Crear el financiamiento
        codigo = f"F-{random.randint(100000, 999999)}"
        fecha_primera = datetime.now(timezone.utc) + timedelta(days=15)

        fin = Financiamiento(
    cliente_id=cliente_id,
    codigo=codigo,
    descripcion=descripcion,
    monto_total_bs=monto_total_bs,
    monto_entrada_bs=entrada_bs,
    monto_financia_bs=financia_bs,
    monto_cuota_bs=monto_cuota_bs,
    monto_total_usd=monto_total_usd,
    monto_entrada_usd=entrada_usd_ref,
    monto_financia_usd=financia_usd_ref,
    monto_cuota_usd=monto_cuota_usd_ref,
    tasa_aplicada=tasa,
    nivel_aplicado=nivel,
    cuotas_solicitadas=cuotas_solicitadas,
    cuotas_aprobadas=cuotas_aprobadas,
    requiere_aprobacion=requiere_aprobacion,
    entrada_pct=config["entrada_pct"],
    financia_pct=config["financia_pct"],
    fecha_primera_cuota=fecha_primera,
    estado="activo",
    tienda_id=tienda_id,
    numero_factura=numero_factura
)
        db.add(fin)
        db.commit()
        db.refresh(fin)

        # Crear cuotas
        for i in range(1, cuotas_aprobadas + 1):
            cuota = Cuota(
                financiamiento_id=fin.id,
                numero=i,
                monto_base_bs=monto_cuota_bs,
                monto_total_bs=monto_cuota_bs,
                monto_base_usd=monto_cuota_usd_ref,
                monto_total_usd=monto_cuota_usd_ref,
                fecha_vencimiento=fecha_primera + timedelta(days=15 * (i - 1)),
                estado="pendiente"
            )
            db.add(cuota)
        db.commit()

        # Actualizar monto acumulado del cliente
        if hasattr(cliente, 'total_monto_comprado_usd'):
            cliente.total_monto_comprado_usd = (cliente.total_monto_comprado_usd or 0) + monto_total_usd
            db.commit()

        # Actualizar score
        actualizar_score_cliente(cliente, db)

        logger.info(f"✅ Financiamiento creado: {codigo} - Tienda: {tienda_id}")

        return {
            "success": True,
            "financiamiento": {
                "id": fin.id,
                "codigo": fin.codigo,
                "monto_total_bs": round(fin.monto_total_bs, 2),
                "monto_total_usd": round(fin.monto_total_usd, 2),
                "monto_entrada_bs": round(fin.monto_entrada_bs, 2),
                "monto_cuota_bs": round(fin.monto_cuota_bs, 2),
                "tasa_aplicada": fin.tasa_aplicada,
                "cuotas_aprobadas": fin.cuotas_aprobadas,
                "requiere_aprobacion": fin.requiere_aprobacion,
                "tienda_id": tienda_id,
                "estado": fin.estado,
                "numero_factura": fin.numero_factura
            },
            "score_actualizado": cliente.score,
            "nivel_actual": cliente.nivel,
            "mensaje": f"Entrada: Bs {entrada_bs:,.2f}. {cuotas_aprobadas} cuotas de Bs {monto_cuota_bs:,.2f}",
            "advertencia": "Requiere aprobación adicional" if requiere_aprobacion else None
        }