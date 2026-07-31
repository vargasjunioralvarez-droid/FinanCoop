# app/modules/users/models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.crypto import EncryptedString

# ============================================================
# MODELO: TIENDA
# ============================================================
class Tienda(Base):
    __tablename__ = "tiendas"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False)
    codigo = Column(String(20), unique=True, nullable=False, index=True)
    direccion = Column(Text, nullable=True)
    telefono = Column(String(20), nullable=True)
    activo = Column(Boolean, default=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    
    usuarios = relationship("Usuario", back_populates="tienda")
    clientes = relationship("Cliente", back_populates="tienda")
    financiamientos = relationship("Financiamiento", back_populates="tienda")

# ============================================================
# MODELO: USUARIO
# ============================================================
class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    nombre = Column(String(200), nullable=True)
    email = Column(String(200), nullable=True)
    rol = Column(String(50), default="usuario")
    activo = Column(Boolean, default=True)
    tienda_id = Column(Integer, ForeignKey("tiendas.id"), nullable=True, index=True)
    creado_por = Column(String(100), nullable=True)
    ultimo_acceso = Column(DateTime(timezone=True), nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())
    
    tienda = relationship("Tienda", back_populates="usuarios")

# ============================================================
# MODELO: CLIENTE
# ============================================================
class Cliente(Base):
    __tablename__ = "clientes"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False)
    cedula = Column(EncryptedString(20), unique=True, nullable=False)
    cedula_hash = Column(String(64), unique=True, nullable=True, index=True)
    telefono = Column(EncryptedString(20), nullable=True)
    email = Column(EncryptedString(200), nullable=True)
    direccion = Column(EncryptedString(500), nullable=True)
    referencia_nombre = Column(String(200), nullable=True)
    referencia_telefono = Column(String(20), nullable=True)
    referencia_parentesco = Column(String(100), nullable=True)
    url_cedula = Column(String(500), nullable=True)
    score = Column(Integer, default=0)
    nivel = Column(String(50), default="bronce")
    total_compras = Column(Integer, default=0)
    total_monto_comprado_usd = Column(Float, default=0.0)
    cuotas_pagadas_tiempo = Column(Integer, default=0)
    cuotas_con_mora = Column(Integer, default=0)
    pin = Column(String(10), nullable=True)
    pin_hash = Column(String(255), nullable=True)
    token_app = Column(String(500), nullable=True)
    estado = Column(String(20), default="pendiente")
    tienda_id = Column(Integer, ForeignKey("tiendas.id"), nullable=True, index=True)
    ultimo_acceso = Column(DateTime(timezone=True), nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())
    
    tienda = relationship("Tienda", back_populates="clientes")