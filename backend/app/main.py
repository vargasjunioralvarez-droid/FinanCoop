# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base, get_db
from app.models import NivelConfig, TasaDolar, ConfiguracionPago
from app.config import NIVELES_CONFIG_DEFAULT
from app.routers import clientes_router, financiamientos_router, pagos_router, config_router, app_mobile_router
from datetime import datetime

app = FastAPI(title="FinanCash API", version="4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crear tablas
Base.metadata.create_all(bind=engine)

# Inicializar datos
def init_db():
    db = next(get_db())
    
    # Niveles
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
    
    # Tasa inicial
    tasa = db.query(TasaDolar).order_by(TasaDolar.id.desc()).first()
    if not tasa:
        tasa = TasaDolar(tasa=40.0, fuente="manual")
        db.add(tasa)
    
    # Configuración pagos
    config = db.query(ConfiguracionPago).first()
    if not config:
        config = ConfiguracionPago(
            banco_pago_movil="Banco de Venezuela",
            telefono_pago_movil="04121234567",
            cedula_pago_movil="V12345678",
            banco_transferencia="Banco Mercantil",
            cuenta_transferencia="01051234567890123456"
        )
        db.add(config)
    
    db.commit()
    db.close()

# Routers
app.include_router(clientes_router)
app.include_router(financiamientos_router)
app.include_router(pagos_router)
app.include_router(config_router)
app.include_router(app_mobile_router)

@app.on_event("startup")
def startup():
    init_db()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)