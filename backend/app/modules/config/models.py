# app/modules/config/models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text
from sqlalchemy.sql import func
from app.core.database import Base

# ============================================================
# MODELO: HISTORIAL DE ESTADOS
# ============================================================
class HistorialEstado(Base):
    __tablename__ = "historial_estados"
    
    id = Column(Integer, primary_key=True, index=True)
    entidad_tipo = Column(String(50), nullable=False)
    entidad_id = Column(Integer, nullable=False)
    estado_anterior = Column(String(50), nullable=True)
    estado_nuevo = Column(String(50), nullable=False)
    cambiado_por = Column(String(200), nullable=True)
    motivo = Column(Text, nullable=True)
    ip_origen = Column(String(50), nullable=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=True)
    fecha = Column(DateTime(timezone=True), server_default=func.now())

# ============================================================
# MODELO: TASA DOLAR
# ============================================================
class TasaDolar(Base):
    __tablename__ = "tasa_dolar"
    
    id = Column(Integer, primary_key=True, index=True)
    tasa = Column(Float, nullable=False)
    fuente = Column(String(100), default="manual")
    actualizado_por = Column(String(100), nullable=True)
    fecha = Column(DateTime(timezone=True), server_default=func.now())

# ============================================================
# MODELO: NIVEL CONFIG
# ============================================================
class NivelConfig(Base):
    __tablename__ = "niveles_config"
    
    id = Column(Integer, primary_key=True, index=True)
    nivel = Column(String(50), unique=True, nullable=False)
    min_score = Column(Integer, nullable=False)
    max_score = Column(Integer, nullable=False)
    monto_max_usd = Column(Float, nullable=False)
    entrada_pct = Column(Float, nullable=False)
    financia_pct = Column(Float, nullable=False)
    cuotas_base = Column(Integer, nullable=False)
    cuotas_max = Column(Integer, nullable=False)
    mora_diaria = Column(Float, nullable=False)
    aprobacion_extra = Column(Boolean, default=False)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())

# ============================================================
# MODELO: LOGS CONCILIACION
# ============================================================
class LogsConciliacion(Base):
    __tablename__ = "logs_conciliacion"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    referencia = Column(String(100))
    monto_banco = Column(Float)
    monto_reportado = Column(Float)
    estado = Column(String(50))
    respuesta_banco = Column(Text)
    fecha = Column(DateTime(timezone=True), server_default=func.now())