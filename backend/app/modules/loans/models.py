# app/modules/loans/models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

# ============================================================
# MODELO: FINANCIAMIENTO
# ============================================================
class Financiamiento(Base):
    __tablename__ = "financiamientos"
    
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    tienda_id = Column(Integer, ForeignKey("tiendas.id"), nullable=True, index=True)
    codigo = Column(String(20), unique=True, nullable=True)
    descripcion = Column(Text, nullable=True)
    url_factura = Column(String(500), nullable=True)
    numero_factura = Column(String(100), nullable=True)
    
    monto_total_bs = Column(Float, nullable=False, default=0)
    monto_entrada_bs = Column(Float, nullable=False, default=0)
    monto_financia_bs = Column(Float, nullable=False, default=0)
    monto_cuota_bs = Column(Float, nullable=False, default=0)
    monto_total_usd = Column(Float, nullable=False, default=0)
    monto_entrada_usd = Column(Float, nullable=False, default=0)
    monto_financia_usd = Column(Float, nullable=False, default=0)
    monto_cuota_usd = Column(Float, nullable=False, default=0)
    tasa_aplicada = Column(Float, nullable=False, default=0)
    nivel_aplicado = Column(String(50), nullable=True)
    cuotas_solicitadas = Column(Integer, nullable=False, default=0)
    cuotas_aprobadas = Column(Integer, nullable=False, default=0)
    requiere_aprobacion = Column(Boolean, default=False)
    aprobado_por = Column(String(50), nullable=True)
    entrada_pct = Column(Float, nullable=False, default=0)
    financia_pct = Column(Float, nullable=False, default=0)
    fecha_primera_cuota = Column(DateTime(timezone=True), nullable=True)
    fecha_completado = Column(DateTime(timezone=True), nullable=True)
    
    monto = Column(Float, nullable=False, default=0)
    monto_usd = Column(Float, nullable=False, default=0)
    tasa_dolar = Column(Float, nullable=False, default=0)
    plazo_meses = Column(Integer, nullable=False, default=0)
    entrada = Column(Float, nullable=False, default=0)
    entrada_usd = Column(Float, nullable=False, default=0)
    financia = Column(Float, nullable=False, default=0)
    financia_usd = Column(Float, nullable=False, default=0)
    cuota_mensual = Column(Float, nullable=False, default=0)
    cuota_mensual_usd = Column(Float, nullable=False, default=0)
    total_pagar = Column(Float, nullable=False, default=0)
    total_pagar_usd = Column(Float, nullable=False, default=0)
    estado = Column(String(50), default="activo")
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())
    
    cliente = relationship("Cliente", backref="financiamientos")
    tienda = relationship("Tienda", back_populates="financiamientos")
    cuotas = relationship("Cuota", backref="financiamiento", lazy="joined")

# ============================================================
# MODELO: CUOTA
# ============================================================
class Cuota(Base):
    __tablename__ = "cuotas"
    
    id = Column(Integer, primary_key=True, index=True)
    financiamiento_id = Column(Integer, ForeignKey("financiamientos.id"), nullable=False)
    numero = Column(Integer, nullable=False)
    
    monto_base_bs = Column(Float, nullable=False, default=0)
    monto_base_usd = Column(Float, nullable=False, default=0)
    monto_interes_mora_bs = Column(Float, default=0)
    monto_interes_mora_usd = Column(Float, default=0)
    monto_total_bs = Column(Float, nullable=False, default=0)
    monto_total_usd = Column(Float, nullable=False, default=0)
    
    monto = Column(Float, default=0)
    monto_usd = Column(Float, default=0)
    mora = Column(Float, default=0)
    mora_usd = Column(Float, default=0)
    monto_pagado = Column(Float, default=0)
    
    fecha_vencimiento = Column(DateTime(timezone=True), nullable=False)
    fecha_pago = Column(DateTime(timezone=True), nullable=True)
    estado = Column(String(50), default="pendiente")
    
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())