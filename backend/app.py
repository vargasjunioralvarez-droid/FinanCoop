from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum, Boolean
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta
import random
import uuid
import enum

# ============ CONFIGURACIÓN ============
app = FastAPI(title="FinanCash API", version="4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base = declarative_base()

# ============ ENUMS ============
class EstadoFinanciamiento(str, enum.Enum):
    ACTIVO = "activo"
    COMPLETADO = "completado"
    CANCELADO = "cancelado"
    MORA = "mora"

class EstadoCuota(str, enum.Enum):
    PENDIENTE = "pendiente"
    PAGADA = "pagada"
    ATRASADA = "atrasada"
    CONCILIANDO = "conciliando"

class MetodoPago(str, enum.Enum):
    PAGO_MOVIL = "pago_movil"
    TRANSFERENCIA = "transferencia"
    ZELLE = "zelle"
    BINANCE = "binance"
    EFECTIVO = "efectivo"
    PUNTO_VENTA = "punto_venta"

class Nivel(str, enum.Enum):
    NUEVO = "nuevo"
    BRONCE = "bronce"
    PLATA = "plata"
    ORO = "oro"
    PLATINO = "platino"

# ============ NIVELES CONFIG (default, editable desde admin) ============
NIVELES_CONFIG_DEFAULT = {
    "nuevo": {
        "min_score": 0, "max_score": 2,
        "monto_max_usd": 160,
        "entrada_pct": 60, "financia_pct": 40,
        "cuotas_base": 3, "cuotas_max": 3,
        "mora_diaria": 2.0,
        "aprobacion_extra": False
    },
    "bronce": {
        "min_score": 3, "max_score": 5,
        "monto_max_usd": 200,
        "entrada_pct": 50, "financia_pct": 50,
        "cuotas_base": 3, "cuotas_max": 5,
        "mora_diaria": 1.5,
        "aprobacion_extra": True
    },
    "plata": {
        "min_score": 6, "max_score": 10,
        "monto_max_usd": 250,
        "entrada_pct": 40, "financia_pct": 60,
        "cuotas_base": 6, "cuotas_max": 8,
        "mora_diaria": 1.0,
        "aprobacion_extra": True
    },
    "oro": {
        "min_score": 11, "max_score": 20,
        "monto_max_usd": 350,
        "entrada_pct": 30, "financia_pct": 70,
        "cuotas_base": 8, "cuotas_max": 12,
        "mora_diaria": 0.5,
        "aprobacion_extra": True
    },
    "platino": {
        "min_score": 21, "max_score": 999,
        "monto_max_usd": 500,
        "entrada_pct": 20, "financia_pct": 80,
        "cuotas_base": 12, "cuotas_max": 15,
        "mora_diaria": 0.5,
        "aprobacion_extra": True
    },
}

# Variable global que se puede modificar
NIVELES_CONFIG = dict(NIVELES_CONFIG_DEFAULT)

# ============ MODELOS ============
class NivelConfig(Base):
    __tablename__ = "niveles_config"
    id = Column(Integer, primary_key=True)
    nivel = Column(String(20), unique=True)
    min_score = Column(Integer)
    max_score = Column(Integer)
    monto_max_usd = Column(Float)
    entrada_pct = Column(Float)
    financia_pct = Column(Float)
    cuotas_base = Column(Integer)
    cuotas_max = Column(Integer)
    mora_diaria = Column(Float)
    aprobacion_extra = Column(Boolean, default=False)

class TasaDolar(Base):
    __tablename__ = "tasas_dolar"
    id = Column(Integer, primary_key=True)
    tasa = Column(Float, default=40.0)
    fecha_actualizacion = Column(DateTime, default=datetime.now)
    actualizado_por = Column(String(50), default="sistema")
    fuente = Column(String(20), default="manual")

class Cliente(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100))
    cedula = Column(String(20), unique=True)
    telefono = Column(String(20))
    email = Column(String(100))
    direccion = Column(String(300), default="")
    referencia_nombre = Column(String(100), default="")
    referencia_telefono = Column(String(20), default="")
    referencia_parentesco = Column(String(30), default="")
    
    score = Column(Integer, default=0)
    nivel = Column(String(20), default="nuevo")
    
    total_compras = Column(Integer, default=0)
    total_monto_comprado_usd = Column(Float, default=0.0)
    cuotas_pagadas_tiempo = Column(Integer, default=0)
    cuotas_con_mora = Column(Integer, default=0)
    
    pin = Column(String(4), nullable=True)
    token_app = Column(String(100), nullable=True)
    ultimo_acceso = Column(DateTime, nullable=True)

class Financiamiento(Base):
    __tablename__ = "financiamientos"
    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    
    codigo = Column(String(20), unique=True)
    descripcion = Column(Text)
    
    monto_total_bs = Column(Float)
    monto_entrada_bs = Column(Float)
    monto_financia_bs = Column(Float)
    monto_cuota_bs = Column(Float)
    
    monto_total_usd = Column(Float)
    monto_entrada_usd = Column(Float)
    monto_financia_usd = Column(Float)
    monto_cuota_usd = Column(Float)
    
    tasa_aplicada = Column(Float)
    
    nivel_aplicado = Column(String(20))
    cuotas_solicitadas = Column(Integer)
    cuotas_aprobadas = Column(Integer)
    requiere_aprobacion = Column(Boolean, default=False)
    aprobado_por = Column(String(50), nullable=True)
    
    entrada_pct = Column(Float)
    financia_pct = Column(Float)
    
    estado = Column(String(20), default="activo")
    
    fecha_creacion = Column(DateTime, default=datetime.now)
    fecha_primera_cuota = Column(DateTime)
    fecha_completado = Column(DateTime, nullable=True)
    
    cliente = relationship("Cliente", backref="financiamientos")
    cuotas = relationship("Cuota", backref="financiamiento")
    pagos = relationship("Pago", backref="financiamiento")

class Cuota(Base):
    __tablename__ = "cuotas"
    id = Column(Integer, primary_key=True)
    financiamiento_id = Column(Integer, ForeignKey("financiamientos.id"))
    
    numero = Column(Integer)
    
    monto_base_bs = Column(Float)
    monto_interes_mora_bs = Column(Float, default=0)
    monto_total_bs = Column(Float)
    
    monto_base_usd = Column(Float)
    monto_interes_mora_usd = Column(Float, default=0)
    monto_total_usd = Column(Float)
    
    fecha_vencimiento = Column(DateTime)
    fecha_pago = Column(DateTime, nullable=True)
    
    estado = Column(String(20), default="pendiente")
    
    pagos = relationship("Pago", backref="cuota")

class Pago(Base):
    __tablename__ = "pagos"
    id = Column(Integer, primary_key=True)
    cuota_id = Column(Integer, ForeignKey("cuotas.id"), nullable=True)
    financiamiento_id = Column(Integer, ForeignKey("financiamientos.id"), nullable=True)
    
    referencia = Column(String(100))
    metodo = Column(String(20))
    
    monto_reportado_bs = Column(Float)
    monto_confirmado_bs = Column(Float, nullable=True)
    
    fecha_reporte = Column(DateTime, default=datetime.now)
    fecha_confirmacion = Column(DateTime, nullable=True)
    
    estado = Column(String(20), default="pendiente")
    
    banco_origen = Column(String(50), nullable=True)
    telefono_pago = Column(String(20), nullable=True)
    cedula_pago = Column(String(20), nullable=True)
    comprobante = Column(String(200), nullable=True)
    
    conciliado_por = Column(String(50), nullable=True)

class ConfiguracionPago(Base):
    __tablename__ = "configuracion_pagos"
    id = Column(Integer, primary_key=True)
    
    banco_pago_movil = Column(String(50))
    telefono_pago_movil = Column(String(20))
    cedula_pago_movil = Column(String(20))
    
    banco_transferencia = Column(String(50))
    cuenta_transferencia = Column(String(20))
    
    correo_zelle = Column(String(100), nullable=True)
    correo_binance = Column(String(100), nullable=True)

# ============ DATABASE ============
engine = create_engine("postgresql://postgres:TU_PASSWORD@localhost:5432/financash_db")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_niveles_db(db: Session):
    """Carga niveles en BD si no existen"""
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

def get_niveles_config(db: Session):
    """Obtiene niveles desde BD"""
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

def init_db():
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Inicializar niveles
    init_niveles_db(db)
    get_niveles_config(db)
    
    tasa = db.query(TasaDolar).order_by(TasaDolar.id.desc()).first()
    if not tasa:
        tasa = TasaDolar(tasa=40.0, fuente="manual")
        db.add(tasa)
    
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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============ UTILIDADES TASA ============
def obtener_tasa_actual(db: Session):
    tasa = db.query(TasaDolar).order_by(TasaDolar.id.desc()).first()
    if not tasa:
        tasa = TasaDolar(tasa=40.0)
        db.add(tasa)
        db.commit()
    return tasa.tasa

def recalcular_cuotas_pendientes(db: Session, nueva_tasa: float):
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

# ============ SCHEMAS ============
class ClienteCreate(BaseModel):
    nombre: str
    cedula: str
    telefono: str
    email: str = ""
    direccion: str = ""
    referencia_nombre: str = ""
    referencia_telefono: str = ""
    referencia_parentesco: str = ""

class LoginApp(BaseModel):
    cedula: str
    pin: str

class PagoReporte(BaseModel):
    cuota_id: int
    monto_bs: float
    metodo: str
    referencia: str
    banco_origen: str = ""
    telefono_pago: str = ""
    cedula_pago: str = ""
    comprobante: str = ""

class ConciliacionPago(BaseModel):
    pago_id: int
    monto_confirmado_bs: float
    estado: str
    conciliado_por: str

class TasaUpdate(BaseModel):
    tasa: float
    actualizado_por: str = "admin"

class AprobacionExtra(BaseModel):
    financiamiento_id: int
    cuotas_aprobadas: int
    aprobado_por: str

class FinanciamientoCreate(BaseModel):
    cliente_id: int
    descripcion: str
    monto_total_bs: float
    cuotas_solicitadas: int

class NivelConfigUpdate(BaseModel):
    monto_max_usd: float
    entrada_pct: float
    financia_pct: float
    cuotas_base: int
    cuotas_max: int
    mora_diaria: float
    aprobacion_extra: bool

# ============ UTILIDADES ============
def calcular_nivel(score: int):
    for nivel, config in NIVELES_CONFIG.items():
        if config["min_score"] <= score <= config["max_score"]:
            return nivel, config
    return "nuevo", NIVELES_CONFIG["nuevo"]

def actualizar_score_cliente(cliente: Cliente, db: Session):
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

def calcular_usado_disponible(cliente_id: int, db: Session):
    """Calcula cuánto ha usado y cuánto le queda disponible"""
    tasa = obtener_tasa_actual(db)
    
    # Obtener nivel actual del cliente
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    nivel, config = calcular_nivel(cliente.score)
    
    limite_usd = config["monto_max_usd"]
    limite_bs = limite_usd * tasa
    
    # Sumar financiamientos activos
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

# ============ API TASA ============
@app.get("/config/tasa-dolar")
def obtener_tasa(db: Session = Depends(get_db)):
    tasa = obtener_tasa_actual(db)
    historial = db.query(TasaDolar).order_by(TasaDolar.id.desc()).limit(10).all()
    
    return {
        "tasa": tasa,
        "fecha": datetime.now().isoformat(),
        "historial": [
            {
                "tasa": h.tasa,
                "fecha": h.fecha_actualizacion.isoformat() if h.fecha_actualizacion else None,
                "fuente": h.fuente,
                "actualizado_por": h.actualizado_por
            } for h in historial
        ]
    }

@app.post("/config/tasa-dolar")
def actualizar_tasa_manual(tasa_update: TasaUpdate, db: Session = Depends(get_db)):
    nueva_tasa = tasa_update.tasa
    
    tasa = TasaDolar(
        tasa=nueva_tasa, 
        fuente="manual", 
        actualizado_por=tasa_update.actualizado_por
    )
    db.add(tasa)
    db.commit()
    
    recalculados = recalcular_cuotas_pendientes(db, nueva_tasa)
    
    return {
        "mensaje": f"Tasa actualizada a {nueva_tasa} BS/$",
        "tasa": nueva_tasa,
        "fuente": "manual",
        "financiamientos_afectados": db.query(Financiamiento).filter(
            Financiamiento.estado == "activo"
        ).count(),
        "cuotas_recalculadas": recalculados
    }

@app.get("/config/historial-tasas")
def historial_tasas(db: Session = Depends(get_db)):
    tasas = db.query(TasaDolar).order_by(TasaDolar.id.desc()).limit(50).all()
    return [
        {
            "id": t.id,
            "tasa": t.tasa,
            "fecha_actualizacion": t.fecha_actualizacion.isoformat() if t.fecha_actualizacion else None,
            "fuente": t.fuente,
            "actualizado_por": t.actualizado_por
        } for t in tasas
    ]

# ============ API NIVELES CONFIG ============
@app.get("/config/niveles")
def obtener_niveles(db: Session = Depends(get_db)):
    """Obtiene configuración de niveles"""
    niveles = get_niveles_config(db)
    return {
        "niveles": niveles,
        "tasa_actual": obtener_tasa_actual(db)
    }

@app.put("/config/niveles/{nivel}")
def actualizar_nivel(nivel: str, config: NivelConfigUpdate, db: Session = Depends(get_db)):
    """Actualiza configuración de un nivel"""
    nc = db.query(NivelConfig).filter(NivelConfig.nivel == nivel).first()
    if not nc:
        raise HTTPException(status_code=404, detail="Nivel no encontrado")
    
    nc.monto_max_usd = config.monto_max_usd
    nc.entrada_pct = config.entrada_pct
    nc.financia_pct = config.financia_pct
    nc.cuotas_base = config.cuotas_base
    nc.cuotas_max = config.cuotas_max
    nc.mora_diaria = config.mora_diaria
    nc.aprobacion_extra = config.aprobacion_extra
    
    db.commit()
    
    # Recargar en memoria
    get_niveles_config(db)
    
    return {"mensaje": f"Nivel {nivel} actualizado", "config": NIVELES_CONFIG[nivel]}

@app.post("/config/niveles/reset")
def reset_niveles(db: Session = Depends(get_db)):
    """Restaura niveles a valores por defecto"""
    db.query(NivelConfig).delete()
    db.commit()
    init_niveles_db(db)
    get_niveles_config(db)
    return {"mensaje": "Niveles restaurados a valores por defecto"}

# ============ API CLIENTES ============
@app.post("/clientes")
def crear_cliente(cliente: ClienteCreate, db: Session = Depends(get_db)):
    existe = db.query(Cliente).filter(Cliente.cedula == cliente.cedula).first()
    if existe:
        return {"error": "Cliente ya existe", "cliente": existe}
    
    db_cliente = Cliente(
        nombre=cliente.nombre,
        cedula=cliente.cedula,
        telefono=cliente.telefono,
        email=cliente.email,
        direccion=cliente.direccion,
        referencia_nombre=cliente.referencia_nombre,
        referencia_telefono=cliente.referencia_telefono,
        referencia_parentesco=cliente.referencia_parentesco,
    )
    db_cliente.pin = generar_pin()
    db.add(db_cliente)
    db.commit()
    db.refresh(db_cliente)
    
    return {
        "cliente": db_cliente,
        "pin_generado": db_cliente.pin,
        "mensaje": "Cliente creado. PIN para app: " + db_cliente.pin
    }

@app.get("/clientes")
def listar_clientes(db: Session = Depends(get_db)):
    return db.query(Cliente).all()

@app.get("/clientes/buscar/{cedula}")
def buscar_cliente_por_cedula(cedula: str, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.cedula == cedula).first()
    if not cliente:
        return {"error": "Cliente no encontrado", "encontrado": False}
    
    actualizar_score_cliente(cliente, db)
    db.refresh(cliente)
    
    nivel, config = calcular_nivel(cliente.score)
    tasa = obtener_tasa_actual(db)
    
    # Calcular límite disponible
    disponible = calcular_usado_disponible(cliente.id, db)
    
    return {
        "encontrado": True,
        "id": cliente.id,
        "nombre": cliente.nombre,
        "cedula": cliente.cedula,
        "telefono": cliente.telefono,
        "email": cliente.email,
        "direccion": cliente.direccion,
        "referencia_nombre": cliente.referencia_nombre,
        "referencia_telefono": cliente.referencia_telefono,
        "referencia_parentesco": cliente.referencia_parentesco,
        "score": cliente.score,
        "nivel": cliente.nivel,
        "total_compras": cliente.total_compras,
        "limite_disponible": disponible,  # NUEVO
        "nivel_config": {
            "monto_max_usd": config["monto_max_usd"],
            "monto_max_bs": round(config["monto_max_usd"] * tasa, 2),
            "entrada_pct": config["entrada_pct"],
            "financia_pct": config["financia_pct"],
            "cuotas_base": config["cuotas_base"],
            "cuotas_max": config["cuotas_max"],
            "mora_diaria": config["mora_diaria"],
            "aprobacion_extra": config["aprobacion_extra"]
        }
    }

@app.get("/clientes/{id}")
def obtener_cliente(id: int, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == id).first()
    if not cliente:
        return {"error": "Cliente no encontrado"}
    
    actualizar_score_cliente(cliente, db)
    db.refresh(cliente)
    
    nivel, config = calcular_nivel(cliente.score)
    tasa = obtener_tasa_actual(db)
    disponible = calcular_usado_disponible(cliente.id, db)
    
    return {
        "id": cliente.id,
        "nombre": cliente.nombre,
        "cedula": cliente.cedula,
        "telefono": cliente.telefono,
        "email": cliente.email,
        "direccion": cliente.direccion,
        "referencia_nombre": cliente.referencia_nombre,
        "referencia_telefono": cliente.referencia_telefono,
        "referencia_parentesco": cliente.referencia_parentesco,
        "score": cliente.score,
        "nivel": cliente.nivel,
        "total_compras": cliente.total_compras,
        "limite_disponible": disponible,
        "nivel_config": {
            "monto_max_usd": config["monto_max_usd"],
            "monto_max_bs": round(config["monto_max_usd"] * tasa, 2),
            "entrada_pct": config["entrada_pct"],
            "financia_pct": config["financia_pct"],
            "cuotas_base": config["cuotas_base"],
            "cuotas_max": config["cuotas_max"],
            "mora_diaria": config["mora_diaria"],
            "aprobacion_extra": config["aprobacion_extra"]
        }
    }

@app.get("/clientes/{id}/estado-cuenta")
def estado_cuenta_cliente(id: int, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    hoy = datetime.now()
    
    cuotas_vencidas = db.query(Cuota).join(Financiamiento).filter(
        Financiamiento.cliente_id == id,
        Cuota.estado == "pendiente",
        Cuota.fecha_vencimiento < hoy
    ).all()
    
    deuda_vencida_bs = sum(c.monto_total_bs for c in cuotas_vencidas)
    deuda_vencida_usd = sum(c.monto_total_usd for c in cuotas_vencidas)
    
    bloqueado = len(cuotas_vencidas) > 0
    
    riesgo = "bajo"
    if len(cuotas_vencidas) >= 3:
        riesgo = "alto"
    elif len(cuotas_vencidas) >= 1:
        riesgo = "medio"
    
    # Límite disponible
    disponible = calcular_usado_disponible(id, db)
    
    return {
        "cliente_id": id,
        "nombre": cliente.nombre,
        "bloqueado": bloqueado,
        "riesgo": riesgo,
        "deudas_vencidas": len(cuotas_vencidas),
        "deuda_vencida_bs": round(deuda_vencida_bs, 2),
        "deuda_vencida_usd": round(deuda_vencida_usd, 2),
        "limite_disponible": disponible,
        "cuotas_vencidas": [
            {
                "id": c.id,
                "numero": c.numero,
                "financiamiento_codigo": c.financiamiento.codigo,
                "monto_bs": round(c.monto_total_bs, 2),
                "fecha_vencimiento": c.fecha_vencimiento.isoformat() if c.fecha_vencimiento else None,
                "dias_vencida": (hoy - c.fecha_vencimiento).days if c.fecha_vencimiento else 0
            } for c in cuotas_vencidas
        ],
        "puede_comprar": not bloqueado and disponible["disponible_usd"] > 0,
        "mensaje": "Tiene deudas vencidas" if bloqueado else "Cliente al día"
    }

@app.get("/clientes/{id}/nivel-propuesta")
def propuesta_financiamiento(
    id: int, 
    monto_total_bs: float = Query(..., gt=0, description="Monto total en Bolívares"), 
    db: Session = Depends(get_db)
):
    cliente = db.query(Cliente).filter(Cliente.id == id).first()
    if not cliente:
        return {"error": "Cliente no encontrado"}
    
    tasa = obtener_tasa_actual(db)
    actualizar_score_cliente(cliente, db)
    nivel, config = calcular_nivel(cliente.score)
    
    # Validar límite disponible
    disponible = calcular_usado_disponible(id, db)
    monto_total_usd = monto_total_bs / tasa
    
    if not disponible["puede_comprar"]:
        return {
            "error": "LÍMITE AGOTADO",
            "mensaje": "Ha usado todo su límite disponible. Debe pagar financiamientos activos.",
            "limite_usd": disponible["limite_usd"],
            "usado_usd": disponible["usado_usd"],
            "disponible_usd": disponible["disponible_usd"]
        }
    
    if monto_total_usd > disponible["disponible_usd"]:
        return {
            "error": "Monto excede límite disponible",
            "monto_solicitado_usd": round(monto_total_usd, 2),
            "disponible_usd": disponible["disponible_usd"],
            "disponible_bs": disponible["disponible_bs"],
            "mensaje": f"Solo puede financiar hasta ${disponible['disponible_usd']:.2f} USD más (BS {disponible['disponible_bs']:.2f})"
        }
    
    # Validar monto máximo del nivel
    if monto_total_usd > config["monto_max_usd"]:
        return {
            "error": "Monto excede el límite del nivel",
            "monto_maximo_permitido_usd": config["monto_max_usd"],
            "monto_maximo_permitido_bs": round(config["monto_max_usd"] * tasa, 2),
            "mensaje": f"Su nivel {nivel} permite máximo ${config['monto_max_usd']} USD por operación"
        }
    
    entrada_bs = monto_total_bs * (config["entrada_pct"] / 100)
    financia_bs = monto_total_bs - entrada_bs
    
    monto_total_usd_ref = monto_total_bs / tasa
    entrada_usd_ref = entrada_bs / tasa
    financia_usd_ref = financia_bs / tasa
    
    opciones = []
    for cuotas_num in range(config["cuotas_base"], config["cuotas_max"] + 1):
        monto_cuota_bs = financia_bs / cuotas_num
        monto_cuota_usd_ref = monto_cuota_bs / tasa
        
        opciones.append({
            "cuotas": cuotas_num,
            "monto_cuota_bs": round(monto_cuota_bs, 2),
            "monto_cuota_usd": round(monto_cuota_usd_ref, 2),
            "requiere_aprobacion": cuotas_num > config["cuotas_base"],
            "frecuencia": "quincenal",
            "label": f"{cuotas_num} cuotas - BS {round(monto_cuota_bs, 2)} cada una"
        })
    
    cuotas_sugeridas = config["cuotas_base"]
    requiere_aprobacion = False
    
    return {
        "cliente": {
            "id": cliente.id,
            "nombre": cliente.nombre,
            "nivel": nivel,
            "score": cliente.score
        },
        "limite": {
            "total_usd": disponible["limite_usd"],
            "usado_usd": disponible["usado_usd"],
            "disponible_usd": disponible["disponible_usd"],
            "disponible_bs": disponible["disponible_bs"]
        },
        "tasa_aplicada": tasa,
        "monto_total_bs": round(monto_total_bs, 2),
        "monto_total_usd": round(monto_total_usd_ref, 2),
        "entrada_pct": config["entrada_pct"],
        "monto_entrada_bs": round(entrada_bs, 2),
        "monto_entrada_usd": round(entrada_usd_ref, 2),
        "financia_pct": config["financia_pct"],
        "monto_financia_bs": round(financia_bs, 2),
        "monto_financia_usd": round(financia_usd_ref, 2),
        "cuotas_base": config["cuotas_base"],
        "cuotas_max": config["cuotas_max"],
        "cuotas_sugeridas": cuotas_sugeridas,
        "mora_diaria": config["mora_diaria"],
        "aprobacion_extra": config["aprobacion_extra"],
        "requiere_aprobacion": requiere_aprobacion,
        "opciones_cuotas": opciones
    }

# ============ API FINANCIAMIENTOS ============
@app.post("/financiamientos")
def crear_financiamiento(f: FinanciamientoCreate, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == f.cliente_id).first()
    if not cliente:
        return {"error": "Cliente no encontrado"}
    
    # Verificar deudas vencidas
    hoy = datetime.now()
    deudas_vencidas = db.query(Cuota).join(Financiamiento).filter(
        Financiamiento.cliente_id == f.cliente_id,
        Cuota.estado == "pendiente",
        Cuota.fecha_vencimiento < hoy
    ).count()
    
    if deudas_vencidas > 0:
        return {
            "error": "BLOQUEADO",
            "mensaje": f"Tiene {deudas_vencidas} cuota(s) vencida(s). Debe pagar antes de comprar.",
            "deudas_vencidas": deudas_vencidas
        }
    
    # Verificar límite disponible
    disponible = calcular_usado_disponible(f.cliente_id, db)
    if not disponible["puede_comprar"]:
        return {
            "error": "LÍMITE AGOTADO",
            "mensaje": "Ha usado todo su límite de financiamiento",
            "limite_usd": disponible["limite_usd"],
            "usado_usd": disponible["usado_usd"]
        }
    
    tasa = obtener_tasa_actual(db)
    nivel, config = calcular_nivel(cliente.score)
    
    monto_total_usd = f.monto_total_bs / tasa
    
    if monto_total_usd > disponible["disponible_usd"]:
        return {
            "error": "Monto excede disponible",
            "disponible_usd": disponible["disponible_usd"],
            "disponible_bs": disponible["disponible_bs"]
        }
    
    if monto_total_usd > config["monto_max_usd"]:
        return {
            "error": "Monto excede límite",
            "monto_maximo_usd": config["monto_max_usd"],
            "monto_maximo_bs": round(config["monto_max_usd"] * tasa, 2)
        }
    
    if f.cuotas_solicitadas > config["cuotas_max"]:
        return {
            "error": "Cuotas exceden límite",
            "cuotas_maximas": config["cuotas_max"]
        }
    
    requiere_aprobacion = f.cuotas_solicitadas > config["cuotas_base"] and config["aprobacion_extra"]
    cuotas_aprobadas = f.cuotas_solicitadas
    
    entrada_bs = f.monto_total_bs * (config["entrada_pct"] / 100)
    financia_bs = f.monto_total_bs - entrada_bs
    monto_cuota_bs = financia_bs / cuotas_aprobadas
    
    monto_total_usd_ref = f.monto_total_bs / tasa
    entrada_usd_ref = entrada_bs / tasa
    financia_usd_ref = financia_bs / tasa
    monto_cuota_usd_ref = monto_cuota_bs / tasa
    
    codigo = f"F-{random.randint(100000, 999999)}"
    fecha_primera = datetime.now() + timedelta(days=15)
    
    fin = Financiamiento(
        cliente_id=f.cliente_id,
        codigo=codigo,
        descripcion=f.descripcion,
        monto_total_bs=f.monto_total_bs,
        monto_entrada_bs=entrada_bs,
        monto_financia_bs=financia_bs,
        monto_cuota_bs=monto_cuota_bs,
        monto_total_usd=monto_total_usd_ref,
        monto_entrada_usd=entrada_usd_ref,
        monto_financia_usd=financia_usd_ref,
        monto_cuota_usd=monto_cuota_usd_ref,
        tasa_aplicada=tasa,
        nivel_aplicado=nivel,
        cuotas_solicitadas=f.cuotas_solicitadas,
        cuotas_aprobadas=cuotas_aprobadas,
        requiere_aprobacion=requiere_aprobacion,
        entrada_pct=config["entrada_pct"],
        financia_pct=config["financia_pct"],
        fecha_primera_cuota=fecha_primera
    )
    db.add(fin)
    db.commit()
    db.refresh(fin)
    
    for i in range(1, cuotas_aprobadas + 1):
        cuota = Cuota(
            financiamiento_id=fin.id,
            numero=i,
            monto_base_bs=monto_cuota_bs,
            monto_total_bs=monto_cuota_bs,
            monto_base_usd=monto_cuota_usd_ref,
            monto_total_usd=monto_cuota_usd_ref,
            fecha_vencimiento=fecha_primera + timedelta(days=15 * (i - 1))
        )
        db.add(cuota)
    db.commit()
    
    cliente.total_monto_comprado_usd += monto_total_usd
    db.commit()
    
    return {
        "financiamiento": {
            "id": fin.id,
            "codigo": fin.codigo,
            "monto_total_bs": round(fin.monto_total_bs, 2),
            "monto_total_usd": round(fin.monto_total_usd, 2),
            "monto_entrada_bs": round(fin.monto_entrada_bs, 2),
            "monto_entrada_usd": round(fin.monto_entrada_usd, 2),
            "monto_cuota_bs": round(fin.monto_cuota_bs, 2),
            "monto_cuota_usd": round(fin.monto_cuota_usd, 2),
            "tasa_aplicada": fin.tasa_aplicada,
            "cuotas_aprobadas": fin.cuotas_aprobadas,
            "requiere_aprobacion": fin.requiere_aprobacion
        },
        "mensaje": f"Entrada de BS {entrada_bs:.2f} pagada. {cuotas_aprobadas} cuotas quincenales de BS {monto_cuota_bs:.2f}",
        "advertencia": "Requiere aprobación del establecimiento" if requiere_aprobacion else None
    }

@app.post("/financiamientos/{id}/aprobar")
def aprobar_financiamiento(id: int, aprobacion: AprobacionExtra, db: Session = Depends(get_db)):
    fin = db.query(Financiamiento).filter(Financiamiento.id == id).first()
    if not fin:
        return {"error": "Financiamiento no encontrado"}
    
    if not fin.requiere_aprobacion:
        return {"error": "Este financiamiento no requiere aprobación"}
    
    fin.cuotas_aprobadas = aprobacion.cuotas_aprobadas
    fin.aprobado_por = aprobacion.aprobado_por
    db.commit()
    
    return {
        "mensaje": f"Financiamiento aprobado con {aprobacion.cuotas_aprobadas} cuotas",
        "aprobado_por": aprobacion.aprobado_por
    }

@app.get("/financiamientos")
def listar_financiamientos(db: Session = Depends(get_db)):
    return db.query(Financiamiento).all()

@app.get("/financiamientos/{id}")
def obtener_financiamiento(id: int, db: Session = Depends(get_db)):
    fin = db.query(Financiamiento).filter(Financiamiento.id == id).first()
    if not fin:
        return {"error": "No encontrado"}
    
    cliente = db.query(Cliente).filter(Cliente.id == fin.cliente_id).first()
    
    return {
        "financiamiento": fin,
        "cliente": {
            "nombre": cliente.nombre,
            "telefono": cliente.telefono
        }
    }

@app.get("/financiamientos/{id}/cuotas")
def ver_cuotas(id: int, db: Session = Depends(get_db)):
    cuotas = db.query(Cuota).filter(Cuota.financiamiento_id == id).all()
    
    hoy = datetime.now()
    resultado = []
    
    for c in cuotas:
        data = {
            "id": c.id,
            "numero": c.numero,
            "monto_base_bs": round(c.monto_base_bs, 2),
            "monto_interes_mora_bs": round(c.monto_interes_mora_bs, 2),
            "monto_total_bs": round(c.monto_total_bs, 2),
            "monto_base_usd": round(c.monto_base_usd, 2),
            "monto_interes_mora_usd": round(c.monto_interes_mora_usd, 2),
            "monto_total_usd": round(c.monto_total_usd, 2),
            "fecha_vencimiento": c.fecha_vencimiento.isoformat() if c.fecha_vencimiento else None,
            "estado": c.estado,
            "dias_atraso": 0
        }
        
        if c.estado == "pendiente" and hoy > c.fecha_vencimiento:
            dias_atraso = (hoy - c.fecha_vencimiento).days
            data["dias_atraso"] = dias_atraso
        
        resultado.append(data)
    
    return resultado

# ============ API PAGOS Y CONCILIACIÓN ============
@app.post("/pagos/reportar")
def reportar_pago(pago: PagoReporte, db: Session = Depends(get_db)):
    cuota = db.query(Cuota).filter(Cuota.id == pago.cuota_id).first()
    if not cuota:
        return {"error": "Cuota no encontrada"}
    
    nuevo_pago = Pago(
        cuota_id=pago.cuota_id,
        financiamiento_id=cuota.financiamiento_id,
        referencia=pago.referencia,
        metodo=pago.metodo,
        monto_reportado_bs=pago.monto_bs,
        banco_origen=pago.banco_origen,
        telefono_pago=pago.telefono_pago,
        cedula_pago=pago.cedula_pago,
        comprobante=pago.comprobante,
        estado="pendiente"
    )
    
    db.add(nuevo_pago)
    cuota.estado = "conciliando"
    db.commit()
    
    return {
        "pago_id": nuevo_pago.id,
        "estado": "pendiente",
        "mensaje": "Pago reportado. Esperando conciliación."
    }

@app.get("/pagos/pendientes")
def pagos_pendientes_conciliacion(db: Session = Depends(get_db)):
    pagos = db.query(Pago).filter(Pago.estado == "pendiente").all()
    
    resultado = []
    for p in pagos:
        cuota = db.query(Cuota).filter(Cuota.id == p.cuota_id).first()
        cliente = db.query(Cliente).join(Financiamiento).filter(
            Financiamiento.id == p.financiamiento_id
        ).first()
        
        resultado.append({
            "pago_id": p.id,
            "fecha_reporte": p.fecha_reporte.isoformat(),
            "cliente": cliente.nombre if cliente else "Desconocido",
            "cedula": cliente.cedula if cliente else "",
            "cuota_numero": cuota.numero if cuota else 0,
            "monto_reportado_bs": p.monto_reportado_bs,
            "metodo": p.metodo,
            "referencia": p.referencia,
            "banco_origen": p.banco_origen,
            "telefono_pago": p.telefono_pago,
            "comprobante": p.comprobante
        })
    
    return resultado

@app.post("/pagos/conciliar")
def conciliar_pago(conciliacion: ConciliacionPago, db: Session = Depends(get_db)):
    pago = db.query(Pago).filter(Pago.id == conciliacion.pago_id).first()
    if not pago:
        return {"error": "Pago no encontrado"}
    
    pago.monto_confirmado_bs = conciliacion.monto_confirmado_bs
    pago.estado = conciliacion.estado
    pago.conciliado_por = conciliacion.conciliado_por
    pago.fecha_confirmacion = datetime.now()
    
    cuota = db.query(Cuota).filter(Cuota.id == pago.cuota_id).first()
    
    if conciliacion.estado == "conciliado":
        cuota.estado = "pagada"
        cuota.fecha_pago = datetime.now()
        
        fin = db.query(Financiamiento).filter(Financiamiento.id == pago.financiamiento_id).first()
        cliente = db.query(Cliente).filter(Cliente.id == fin.cliente_id).first()
        
        cuotas_pendientes = db.query(Cuota).filter(
            Cuota.financiamiento_id == fin.id,
            Cuota.estado.in_(["pendiente", "conciliando"])
        ).count()
        
        if cuotas_pendientes == 0:
            fin.estado = "completado"
            fin.fecha_completado = datetime.now()
            db.commit()
            actualizar_score_cliente(cliente, db)
        
        return {
            "estado": "conciliado",
            "cuota_pagada": cuota.numero,
            "monto_bs": conciliacion.monto_confirmado_bs,
            "mensaje": "Pago conciliado correctamente"
        }
    else:
        cuota.estado = "pendiente"
        db.commit()
        return {
            "estado": "rechazado",
            "mensaje": "Pago rechazado. Cuota vuelve a pendiente."
        }

@app.post("/cuotas/{id}/pagar-efectivo")
def pagar_cuota_efectivo(id: int, db: Session = Depends(get_db)):
    cuota = db.query(Cuota).filter(Cuota.id == id).first()
    if not cuota:
        return {"error": "Cuota no encontrada"}
    
    fin = db.query(Financiamiento).filter(Financiamiento.id == cuota.financiamiento_id).first()
    cliente = db.query(Cliente).filter(Cliente.id == fin.cliente_id).first()
    
    hoy = datetime.now()
    
    if hoy > cuota.fecha_vencimiento:
        dias_atraso = (hoy - cuota.fecha_vencimiento).days
        dias_gracia = 3
        
        if dias_atraso > dias_gracia:
            nivel, config = calcular_nivel(cliente.score)
            tasa_mora = config["mora_diaria"]
            tasa = obtener_tasa_actual(db)
            
            dias_efectivos = dias_atraso - dias_gracia
            interes_bs = cuota.monto_base_bs * (tasa_mora / 100) * dias_efectivos
            interes_usd_ref = interes_bs / tasa
            
            cuota.monto_interes_mora_bs = round(interes_bs, 2)
            cuota.monto_interes_mora_usd = round(interes_usd_ref, 2)
            cuota.monto_total_bs = round(cuota.monto_base_bs + interes_bs, 2)
            cuota.monto_total_usd = round(cuota.monto_base_usd + interes_usd_ref, 2)
            cliente.cuotas_con_mora += 1
        else:
            cuota.monto_total_bs = cuota.monto_base_bs
            cuota.monto_total_usd = cuota.monto_base_usd
    else:
        cuota.monto_total_bs = cuota.monto_base_bs
        cuota.monto_total_usd = cuota.monto_base_usd
    
    cuota.estado = "pagada"
    cuota.fecha_pago = hoy
    
    pago = Pago(
        cuota_id=cuota.id,
        financiamiento_id=fin.id,
        metodo="efectivo",
        monto_reportado_bs=cuota.monto_total_bs,
        monto_confirmado_bs=cuota.monto_total_bs,
        estado="conciliado",
        fecha_confirmacion=hoy,
        conciliado_por="sistema"
    )
    db.add(pago)
    db.commit()
    
    cuotas_pendientes = db.query(Cuota).filter(
        Cuota.financiamiento_id == fin.id,
        Cuota.estado.in_(["pendiente", "conciliando"])
    ).count()
    
    if cuotas_pendientes == 0:
        fin.estado = "completado"
        fin.fecha_completado = hoy
        db.commit()
        actualizar_score_cliente(cliente, db)
    
    return {
        "cuota_pagada": cuota.numero,
        "monto_base_bs": cuota.monto_base_bs,
        "interes_mora_bs": cuota.monto_interes_mora_bs,
        "total_pagado_bs": cuota.monto_total_bs,
        "financiamiento_estado": fin.estado
    }

# ============ API APP MÓVIL ============
@app.post("/app/login")
def login_app(login: LoginApp, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.cedula == login.cedula).first()
    if not cliente:
        return {"error": "Cliente no encontrado"}
    
    if cliente.pin != login.pin:
        return {"error": "PIN incorrecto"}
    
    cliente.token_app = generar_token()
    cliente.ultimo_acceso = datetime.now()
    db.commit()
    
    return {
        "token": cliente.token_app,
        "cliente": {
            "id": cliente.id,
            "nombre": cliente.nombre,
            "nivel": cliente.nivel,
            "score": cliente.score
        }
    }

@app.get("/app/mis-datos")
def mis_datos(token: str, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.token_app == token).first()
    if not cliente:
        return {"error": "Sesión no válida"}
    
    tasa = obtener_tasa_actual(db)
    disponible = calcular_usado_disponible(cliente.id, db)
    
    activos = db.query(Financiamiento).filter(
        Financiamiento.cliente_id == cliente.id,
        Financiamiento.estado == "activo"
    ).all()
    
    financiamientos_data = []
    for fin in activos:
        cuotas = db.query(Cuota).filter(Cuota.financiamiento_id == fin.id).all()
        
        cuotas_pendientes = [c for c in cuotas if c.estado in ["pendiente", "conciliando"]]
        cuotas_atrasadas = [c for c in cuotas if c.estado == "pendiente" and datetime.now() > c.fecha_vencimiento]
        
        proxima_cuota = None
        if cuotas_pendientes:
            proxima = cuotas_pendientes[0]
            dias_para_vencer = (proxima.fecha_vencimiento - datetime.now()).days if proxima.fecha_vencimiento else 0
            
            proxima_cuota = {
                "id": proxima.id,
                "numero": proxima.numero,
                "monto_bs": round(proxima.monto_total_bs, 2),
                "monto_usd_ref": round(proxima.monto_total_usd, 2),
                "fecha_vencimiento": proxima.fecha_vencimiento.isoformat() if proxima.fecha_vencimiento else None,
                "dias_para_vencer": max(0, dias_para_vencer),
                "estado": proxima.estado
            }
        
        financiamientos_data.append({
            "id": fin.id,
            "codigo": fin.codigo,
            "descripcion": fin.descripcion,
            "monto_total_bs": round(fin.monto_total_bs, 2),
            "monto_total_usd_ref": round(fin.monto_total_usd, 2),
            "monto_entrada_bs": round(fin.monto_entrada_bs, 2),
            "monto_entrada_usd_ref": round(fin.monto_entrada_usd, 2),
            "cuotas_total": fin.cuotas_aprobadas,
            "cuotas_pagadas": len([c for c in cuotas if c.estado == "pagada"]),
            "cuotas_pendientes": len(cuotas_pendientes),
            "cuotas_atrasadas": len(cuotas_atrasadas),
            "proxima_cuota": proxima_cuota,
            "saldo_pendiente_bs": round(sum(c.monto_total_bs for c in cuotas_pendientes), 2),
            "saldo_pendiente_usd_ref": round(sum(c.monto_total_usd for c in cuotas_pendientes), 2)
        })
    
    config = db.query(ConfiguracionPago).first()
    
    return {
        "cliente": {
            "id": cliente.id,
            "nombre": cliente.nombre,
            "cedula": cliente.cedula,
            "nivel": cliente.nivel,
            "score": cliente.score,
            "telefono": cliente.telefono
        },
        "limite": disponible,
        "tasa_actual": tasa,
        "financiamientos_activos": financiamientos_data,
        "total_deuda_bs": round(sum(f["saldo_pendiente_bs"] for f in financiamientos_data), 2),
        "total_deuda_usd_ref": round(sum(f["saldo_pendiente_usd_ref"] for f in financiamientos_data), 2),
        "datos_pago": {
            "pago_movil": {
                "banco": config.banco_pago_movil if config else "",
                "telefono": config.telefono_pago_movil if config else "",
                "cedula": config.cedula_pago_movil if config else ""
            },
            "transferencia": {
                "banco": config.banco_transferencia if config else "",
                "cuenta": config.cuenta_transferencia if config else ""
            },
            "zelle": config.correo_zelle if config else None,
            "binance": config.correo_binance if config else None
        }
    }

@app.get("/app/mis-cuotas")
def mis_cuotas(token: str, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.token_app == token).first()
    if not cliente:
        return {"error": "Sesión no válida"}
    
    tasa = obtener_tasa_actual(db)
    
    financiamientos = db.query(Financiamiento).filter(
        Financiamiento.cliente_id == cliente.id
    ).all()
    
    todas_cuotas = []
    for fin in financiamientos:
        cuotas = db.query(Cuota).filter(Cuota.financiamiento_id == fin.id).order_by(Cuota.numero).all()
        
        for c in cuotas:
            hoy = datetime.now()
            dias_atraso = 0
            if c.estado == "pendiente" and hoy > c.fecha_vencimiento:
                dias_atraso = (hoy - c.fecha_vencimiento).days
            
            todas_cuotas.append({
                "financiamiento_id": fin.id,
                "financiamiento_codigo": fin.codigo,
                "financiamiento_descripcion": fin.descripcion,
                "cuota_id": c.id,
                "cuota_numero": c.numero,
                "monto_base_bs": round(c.monto_base_bs, 2),
                "monto_interes_bs": round(c.monto_interes_mora_bs, 2),
                "monto_total_bs": round(c.monto_total_bs, 2),
                "monto_base_usd_ref": round(c.monto_base_usd, 2),
                "monto_interes_usd_ref": round(c.monto_interes_mora_usd, 2),
                "monto_total_usd_ref": round(c.monto_total_usd, 2),
                "fecha_vencimiento": c.fecha_vencimiento.isoformat() if c.fecha_vencimiento else None,
                "estado": c.estado,
                "dias_atraso": dias_atraso,
                "puede_pagar": c.estado == "pendiente"
            })
    
    return {
        "cliente": cliente.nombre,
        "tasa_actual": tasa,
        "cuotas": todas_cuotas
    }

@app.get("/app/configuracion-pagos")
def configuracion_pagos_publica(db: Session = Depends(get_db)):
    config = db.query(ConfiguracionPago).first()
    if not config:
        return {"error": "Configuración no encontrada"}
    
    return {
        "pago_movil": {
            "banco": config.banco_pago_movil,
            "telefono": config.telefono_pago_movil,
            "cedula": config.cedula_pago_movil
        },
        "transferencia": {
            "banco": config.banco_transferencia,
            "cuenta": config.cuenta_transferencia
        },
        "zelle": config.correo_zelle,
        "binance": config.correo_binance
    }

# ============ INICIALIZACIÓN ============
@app.on_event("startup")
def startup():
    init_db()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)