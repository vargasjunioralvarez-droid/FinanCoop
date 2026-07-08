# app/utils.py
import random
import uuid
from datetime import datetime
from app.config import NIVELES_CONFIG, NIVELES_CONFIG_DEFAULT
from app.models import Cliente, Financiamiento, Cuota, NivelConfig, TasaDolar

def calcular_nivel(score: int):
    for nivel, config in NIVELES_CONFIG.items():
        if config["min_score"] <= score <= config["max_score"]:
            return nivel, config
    return "nuevo", NIVELES_CONFIG["nuevo"]

def actualizar_score_cliente(cliente: Cliente, db):
    financiamientos_completados = db.query(Financiamiento).filter(
        Financiamiento.cliente_id == cliente.id,
        Financiamiento.estado == "completado"
    ).count()
    
    cliente.score = financiamientos_completados
    cliente.total_compras = db.query(Financiamiento).filter(
        Financiamiento.cliente_id == cliente.id
    ).count()
    
    nuevo_nivel, config = calcular_nivel(cliente.score)
    cliente.nivel = nuevo_nivel
    
    db.commit()

def generar_pin():
    return str(random.randint(1000, 9999))

def generar_token():
    return str(uuid.uuid4())

def obtener_tasa_actual(db):
    tasa = db.query(TasaDolar).order_by(TasaDolar.id.desc()).first()
    if not tasa:
        tasa = TasaDolar(tasa=40.0)
        db.add(tasa)
        db.commit()
    return tasa.tasa

def recalcular_cuotas_pendientes(db, nueva_tasa: float):
    financiamientos = db.query(Financiamiento).filter(
        Financiamiento.estado == "activo"
    ).all()
    
    recalculados = 0
    for fin in financiamientos:
        fin.monto_total_usd = fin.monto_total_bs / nueva_tasa
        fin.monto_entrada_usd = fin.monto_entrada_bs / nueva_tasa
        fin.monto_financia_usd = fin.monto_financia_bs / nueva_tasa
        fin.monto_cuota_usd = fin.monto_cuota_bs / nueva_tasa
        
        cuotas = db.query(Cuota).filter(
            Cuota.financiamiento_id == fin.id,
            Cuota.estado.in_(["pendiente", "conciliando"])
        ).all()
        
        for c in cuotas:
            c.monto_base_usd = c.monto_base_bs / nueva_tasa
            c.monto_interes_mora_usd = c.monto_interes_mora_bs / nueva_tasa
            c.monto_total_usd = c.monto_total_bs / nueva_tasa
        
        recalculados += len(cuotas)
    
    db.commit()
    return recalculados

def calcular_usado_disponible(cliente_id: int, db):
    tasa = obtener_tasa_actual(db)
    
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    nivel, config = calcular_nivel(cliente.score)
    
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

def init_niveles_db(db):
    for nivel_key, config in NIVELES_CONFIG_DEFAULT.items():
        existe = db.query(NivelConfig).filter(NivelConfig.nivel == nivel_key).first()
        if not existe:
            nc = NivelConfig(
                nivel=nivel_key,
                min_score=config["min_score"],
                max_score=config["max_score"],
                monto_max_usd=config["monto_max_usd"],
                entrada_pct=config["entrada_pct"],
                financia_pct=config["financia_pct"],
                cuotas_base=config["cuotas_base"],
                cuotas_max=config["cuotas_max"],
                mora_diaria=config["mora_diaria"],
                aprobacion_extra=config["aprobacion_extra"]
            )
            db.add(nc)
    db.commit()

def get_niveles_config(db):
    global NIVELES_CONFIG
    niveles = db.query(NivelConfig).all()
    if niveles:
        NIVELES_CONFIG = {}
        for n in niveles:
            NIVELES_CONFIG[n.nivel] = {
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
    return NIVELES_CONFIG