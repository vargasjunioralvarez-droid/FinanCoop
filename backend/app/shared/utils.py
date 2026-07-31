# backend/app/shared/utils.py
"""
Utilidades del dominio y acceso a datos.
La lógica de negocio (scoring, niveles) se movió a app.domain.scoring y app.domain.niveles.
La infraestructura de mensajería (Twilio) se movió a app.infrastructure.twilio.
Las utilidades puras se movieron a app.shared.helpers.
Se re-exportan aquí para mantener compatibilidad.
"""

from datetime import datetime, timezone

from app.modules.loans.models import Financiamiento, Cuota
from app.modules.config.models import TasaDolar

# Re-exportar funciones de dominio (compatibilidad)
from app.domain.scoring import (
    calcular_nivel,
    actualizar_score_cliente,
    calcular_usado_disponible
)

# Re-exportar funciones de niveles (compatibilidad)
from app.domain.niveles import (
    init_niveles_db,
    get_niveles_config
)

# Re-exportar funciones de mensajería (compatibilidad)
from app.infrastructure.twilio import (
    enviar_whatsapp,
    enviar_pin_sms,
    enviar_pin_cliente,
    enviar_pin_cliente_completo,
    enviar_notificacion_generica
)

# Re-exportar funciones auxiliares puras (compatibilidad)
from app.shared.helpers import (
    normalizar_telefono,
    es_numero_valido,
    generar_pin,
    generar_token
)

# ============ FUNCIONES DE ACCESO A DATOS ============

def obtener_tasa_actual(db):
    tasa = db.query(TasaDolar).order_by(TasaDolar.id.desc()).first()
    if not tasa:
        tasa = TasaDolar(tasa=40.0)
        db.add(tasa)
        db.commit()
    return tasa.tasa

def recalcular_cuotas_pendientes(db, nueva_tasa: float):
    financiamientos = db.query(Financiamiento).filter(Financiamiento.estado == "activo").all()
    recalculados = 0
    for fin in financiamientos:
        fin.monto_total_bs = fin.monto_total_usd * nueva_tasa
        fin.monto_entrada_bs = fin.monto_entrada_usd * nueva_tasa
        fin.monto_financia_bs = fin.monto_financia_usd * nueva_tasa
        fin.monto_cuota_bs = fin.monto_cuota_usd * nueva_tasa
        cuotas = db.query(Cuota).filter(Cuota.financiamiento_id == fin.id, Cuota.estado.in_(["pendiente", "conciliando"])).all()
        for c in cuotas:
            c.monto_base_bs = c.monto_base_usd * nueva_tasa
            c.monto_interes_mora_bs = c.monto_interes_mora_usd * nueva_tasa
            c.monto_total_bs = c.monto_total_usd * nueva_tasa
        recalculados += len(cuotas)
    db.commit()
    return recalculados