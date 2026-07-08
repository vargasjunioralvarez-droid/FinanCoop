# app/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

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

    financiamientos = relationship("Financiamiento", back_populates="cliente")

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
    
    cliente = relationship("Cliente", back_populates="financiamientos")
    cuotas = relationship("Cuota", back_populates="financiamiento")
    pagos = relationship("Pago", back_populates="financiamiento")

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
    
    financiamiento = relationship("Financiamiento", back_populates="cuotas")
    pagos = relationship("Pago", back_populates="cuota")

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

    cuota = relationship("Cuota", back_populates="pagos")
    financiamiento = relationship("Financiamiento", back_populates="pagos")

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