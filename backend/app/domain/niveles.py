# backend/app/domain/niveles.py
"""
⚙️ Lógica de dominio: Configuración y gestión de niveles.
"""

from app.core.config import NIVELES_CONFIG, NIVELES_CONFIG_DEFAULT
from app.modules.config.models import NivelConfig


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