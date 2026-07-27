"""
Inicialización de datos de la base de datos
"""

import logging
from app.core.database import get_db
from app.modules.config.models import NivelConfig, TasaDolar
from app.modules.payments.models import ConfiguracionPago
from app.core.config import NIVELES_CONFIG_DEFAULT

logger = logging.getLogger(__name__)

def init_db():
    """
    Inicializa la base de datos con datos mínimos:
    - Niveles de configuración
    - Tasa de cambio
    - Configuración de pagos
    """
    db = next(get_db())
    try:
        # Crear niveles si no existen
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
                logger.info(f"✅ Nivel creado: {nivel_key}")

        # Crear tasa de cambio si no existe
        tasa = db.query(TasaDolar).order_by(TasaDolar.id.desc()).first()
        if not tasa:
            tasa = TasaDolar(tasa=40.0, fuente="manual")
            db.add(tasa)
            logger.info("✅ Tasa dólar inicial creada: 40.0")

        # Crear configuración de pagos si no existe
        config_pago = db.query(ConfiguracionPago).first()
        if not config_pago:
            config_pago = ConfiguracionPago(
                banco_pago_movil="Banco de Venezuela",
                telefono_pago_movil="04121234567",
                cedula_pago_movil="V12345678",
                banco_transferencia="Banco Mercantil",
                cuenta_transferencia="01051234567890123456"
            )
            db.add(config_pago)
            logger.info("✅ Configuración de pagos inicial creada")

        db.commit()
        logger.info("🚀 Base de datos inicializada correctamente")
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error inicializando BD: {e}")
        raise
    finally:
        db.close()