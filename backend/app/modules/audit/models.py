from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Text, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import hashlib
import json

class Auditoria(Base):
    """
    Tabla de auditoría - Registra TODAS las acciones importantes
    Con hash encadenado para inmutabilidad (H14)
    """
    __tablename__ = "auditoria"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 👤 Quién lo hizo
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    usuario_nombre = Column(String(100), nullable=True)
    usuario_rol = Column(String(50), nullable=True)
    
    # 📋 Qué hizo
    accion = Column(String(50), nullable=False)
    tabla = Column(String(50), nullable=True)
    registro_id = Column(Integer, nullable=True)
    
    # 📦 Datos
    datos_antes = Column(JSON, nullable=True)
    datos_despues = Column(JSON, nullable=True)
    detalles = Column(Text, nullable=True)
    
    # 🌐 Contexto
    ip = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    endpoint = Column(String(255), nullable=True)
    metodo_http = Column(String(10), nullable=True)
    
    # ⏰ Cuándo
    fecha = Column(DateTime(timezone=True), server_default=func.now())
    
    # 🔐 Hash encadenado para inmutabilidad (H14)
    hash_anterior = Column(String(64), nullable=True)
    hash_actual = Column(String(64), nullable=True)
    
    # Relaciones
    usuario = relationship("Usuario", foreign_keys=[usuario_id])
    
    # Índices para búsquedas rápidas
    __table_args__ = (
        Index('idx_auditoria_usuario', 'usuario_id'),
        Index('idx_auditoria_accion', 'accion'),
        Index('idx_auditoria_tabla_registro', 'tabla', 'registro_id'),
        Index('idx_auditoria_fecha', 'fecha'),
    )