# app/modules/payments/models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

# ============================================================
# MODELO: CONFIGURACIÓN PAGO
# ============================================================
class ConfiguracionPago(Base):
    __tablename__ = "configuracion_pago"
    
    id = Column(Integer, primary_key=True, index=True)
    banco_pago_movil = Column(String(100), nullable=True)
    telefono_pago_movil = Column(String(20), nullable=True)
    cedula_pago_movil = Column(String(20), nullable=True)
    banco_transferencia = Column(String(100), nullable=True)
    cuenta_transferencia = Column(String(50), nullable=True)
    correo_zelle = Column(String(200), nullable=True)
    correo_binance = Column(String(200), nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())

# ============================================================
# MODELO: PAGO
# ============================================================
class Pago(Base):
    __tablename__ = "pagos"
    
    id = Column(Integer, primary_key=True, index=True)
    financiamiento_id = Column(Integer, ForeignKey("financiamientos.id"), nullable=False)
    cuota_id = Column(Integer, ForeignKey("cuotas.id"), nullable=True)
    
    monto = Column(Float, nullable=False, default=0)
    monto_usd = Column(Float, nullable=False, default=0)
    metodo = Column(String(50), nullable=False, default="efectivo")
    referencia = Column(String(100), nullable=True)
    
    monto_reportado_bs = Column(Float, nullable=True)
    monto_confirmado_bs = Column(Float, nullable=True)
    monto_original_bs = Column(Float, nullable=True)
    banco_origen = Column(String(100), nullable=True)
    telefono_pago = Column(String(20), nullable=True)
    cedula_pago = Column(String(20), nullable=True)
    comprobante = Column(String(500), nullable=True)
    
    modo_pago = Column(String(50), default="cuota")
    cuotas_incluidas = Column(Text, nullable=True)
    pago_padre_id = Column(Integer, nullable=True)
    
    estado = Column(String(50), default="pendiente")
    fecha_reporte = Column(DateTime(timezone=True), server_default=func.now())
    fecha_confirmacion = Column(DateTime(timezone=True), nullable=True)
    fecha_rechazo = Column(DateTime(timezone=True), nullable=True)
    conciliado_por = Column(String(100), nullable=True)
    rechazado_por = Column(String(100), nullable=True)
    
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    
    financiamiento = relationship("Financiamiento", backref="pagos")
    cuota = relationship("Cuota", backref="pagos")