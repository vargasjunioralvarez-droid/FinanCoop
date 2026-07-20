# backend/app/models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

# ============================================================
# MODELO: TIENDA (NUEVO)
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
    rol = Column(String(50), default="usuario")  # "admin", "tienda", "cajero"
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
    cedula = Column(String(20), unique=True, nullable=False)
    telefono = Column(String(20), nullable=True)
    email = Column(String(200), nullable=True)
    direccion = Column(Text, nullable=True)
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
# MODELO: FINANCIAMIENTO
# ============================================================
class Financiamiento(Base):
    __tablename__ = "financiamientos"
    
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    tienda_id = Column(Integer, ForeignKey("tiendas.id"), nullable=True, index=True)
    codigo = Column(String(20), unique=True, nullable=True)
    descripcion = Column(Text, nullable=True)
    
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

# ============================================================
# MODELO: TOKEN BLACKLIST
# ============================================================
class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"
    
    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String(255), unique=True, index=True, nullable=False)
    expira_en = Column(DateTime(timezone=True), nullable=False)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

class LogsConciliacion(Base):
    __tablename__ = "logs_conciliacion"
    
    id = Column(Integer, primary_key=True, index=True)
    referencia = Column(String(100))
    monto_banco = Column(Float)
    monto_reportado = Column(Float)
    estado = Column(String(50))
    respuesta_banco = Column(Text)
    fecha = Column(DateTime(timezone=True), server_default=func.now())

# ============================================================
# MODELO: LOGS CONCILIACION (NUEVO)
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