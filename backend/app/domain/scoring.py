# backend/app/domain/scoring.py
"""
🎯 Lógica de dominio: Scoring crediticio y límites del cliente.
"""

from datetime import datetime, timezone

from app.core.config import NIVELES_CONFIG, NIVELES_CONFIG_DEFAULT
from app.modules.users.models import Cliente
from app.modules.loans.models import Financiamiento, Cuota
from app.modules.config.models import NivelConfig


def calcular_nivel(score: int, db=None):
    if db:
        niveles_db = db.query(NivelConfig).order_by(NivelConfig.min_score).all()
        if niveles_db:
            for n in niveles_db:
                if n.min_score <= score <= n.max_score:
                    return n.nivel, {
                        "min_score": n.min_score,
                        "max_score": n.max_score,
                        "monto_max_usd": n.monto_max_usd,
                        "entrada_pct": n.entrada_pct,
                        "financia_pct": n.financia_pct,
                        "cuotas_base": n.cuotas_base,
                        "cuotas_max": n.cuotas_max,
                        "mora_diaria": n.mora_diaria,
                        "aprobacion_extra": n.aprobacion_extra
                    }
    
    niveles_ordenados = sorted(NIVELES_CONFIG.items(), key=lambda x: x[1]["min_score"])
    for nivel, config in niveles_ordenados:
        if config["min_score"] <= score <= config["max_score"]:
            return nivel, config
    return "nuevo", NIVELES_CONFIG.get("nuevo", NIVELES_CONFIG_DEFAULT["nuevo"])


def actualizar_score_cliente(cliente: Cliente, db):
    puntos = 0
    
    financiamientos_completados = db.query(Financiamiento).filter(
        Financiamiento.cliente_id == cliente.id,
        Financiamiento.estado == "completado"
    ).all()
    
    puntos += len(financiamientos_completados) * 33
    
    cuotas_pagadas = db.query(Cuota).join(Financiamiento).filter(
        Financiamiento.cliente_id == cliente.id,
        Cuota.estado == "pagada",
        Cuota.fecha_pago != None
    ).all()
    
    for cuota in cuotas_pagadas:
        if cuota.fecha_pago and cuota.fecha_vencimiento:
            dias_diferencia = (cuota.fecha_vencimiento.date() - cuota.fecha_pago.date()).days
            
            if dias_diferencia >= 3:
                puntos += 15
            elif dias_diferencia >= 0:
                puntos += 10
            else:
                puntos -= 5
    
    hoy = datetime.now(timezone.utc)
    cuotas_vencidas = db.query(Cuota).join(Financiamiento).filter(
        Financiamiento.cliente_id == cliente.id,
        Cuota.estado == "pendiente",
        Cuota.fecha_vencimiento < hoy
    ).count()
    
    if cuotas_vencidas == 0 and len(financiamientos_completados) > 0:
        puntos += 5
    
    puntos = max(0, int(puntos))
    
    cliente.score = puntos
    cliente.total_compras = len(financiamientos_completados)
    
    nuevo_nivel, config = calcular_nivel(cliente.score, db)
    cliente.nivel = nuevo_nivel
    
    db.commit()
    
    print(f"🎯 Score: {cliente.nombre} | {cliente.score} pts | Nivel: {cliente.nivel} | Compras: {cliente.total_compras}")
    return puntos


def calcular_usado_disponible(cliente_id: int, db):
    from app.shared.utils import obtener_tasa_actual  # Evita dependencia circular

    tasa = obtener_tasa_actual(db)
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        return {}
    nivel, config = calcular_nivel(cliente.score, db)
    limite_usd = config["monto_max_usd"]
    limite_bs = limite_usd * tasa
    activos = db.query(Financiamiento).filter(
        Financiamiento.cliente_id == cliente_id,
        Financiamiento.estado == "activo"
    ).all()
    usado_usd = sum(f.monto_total_usd for f in activos)
    usado_bs = sum(f.monto_total_bs for f in activos)
    disponible_usd = max(0, limite_usd - usado_usd)
    disponible_bs = max(0, limite_bs - usado_bs)
    return {
        "nivel": nivel,
        "limite_usd": round(limite_usd, 2),
        "limite_bs": round(limite_bs, 2),
        "usado_usd": round(usado_usd, 2),
        "usado_bs": round(usado_bs, 2),
        "disponible_usd": round(disponible_usd, 2),
        "disponible_bs": round(disponible_bs, 2),
        "cantidad_activos": len(activos),
        "puede_comprar": disponible_usd > 0
    }