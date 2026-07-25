from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Text, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Auditoria(Base):
    """
    Tabla de auditoría - Registra TODAS las acciones importantes
    """
    __tablename__ = "auditoria"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 👤 Quién lo hizo
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    usuario_nombre = Column(String(100), nullable=True)  # Backup por si se borra el usuario
    usuario_rol = Column(String(50), nullable=True)      # Backup del rol
    
    # 📋 Qué hizo
    accion = Column(String(50), nullable=False)  # CREATE, UPDATE, DELETE, LOGIN, LOGOUT, VIEW, APPROVE, REJECT, CONCILIAR
    tabla = Column(String(50), nullable=True)    # Tabla afectada
    registro_id = Column(Integer, nullable=True) # ID del registro afectado
    
    # 📦 Datos
    datos_antes = Column(JSON, nullable=True)    # Estado anterior (como JSON)
    datos_despues = Column(JSON, nullable=True)  # Estado posterior (como JSON)
    detalles = Column(Text, nullable=True)       # Información adicional
    
    # 🌐 Contexto
    ip = Column(String(45), nullable=True)       # IPv4 o IPv6
    user_agent = Column(String(255), nullable=True)  # Navegador/Dispositivo
    endpoint = Column(String(255), nullable=True)    # Endpoint al que se llamó
    metodo_http = Column(String(10), nullable=True)  # GET, POST, PUT, DELETE
    
    # ⏰ Cuándo
    fecha = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    usuario = relationship("Usuario", foreign_keys=[usuario_id])
    
    # Índices para búsquedas rápidas
    __table_args__ = (
        Index('idx_auditoria_usuario', 'usuario_id'),
        Index('idx_auditoria_accion', 'accion'),
        Index('idx_auditoria_tabla_registro', 'tabla', 'registro_id'),
        Index('idx_auditoria_fecha', 'fecha'),
    )