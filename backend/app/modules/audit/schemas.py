from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any, Dict

class AuditoriaResponse(BaseModel):
    """Schema para mostrar registros de auditoría"""
    id: int
    usuario_id: Optional[int]
    usuario_nombre: Optional[str]
    usuario_rol: Optional[str]
    accion: str
    tabla: Optional[str]
    registro_id: Optional[int]
    datos_antes: Optional[Dict[str, Any]]
    datos_despues: Optional[Dict[str, Any]]
    detalles: Optional[str]
    ip: Optional[str]
    user_agent: Optional[str]
    endpoint: Optional[str]
    metodo_http: Optional[str]
    fecha: datetime
    
    class Config:
        from_attributes = True

class AuditoriaFiltros(BaseModel):
    """Filtros para consultar auditoría"""
    usuario_id: Optional[int] = None
    accion: Optional[str] = None
    tabla: Optional[str] = None
    registro_id: Optional[int] = None
    fecha_desde: Optional[datetime] = None
    fecha_hasta: Optional[datetime] = None
    limite: int = 100
    offset: int = 0

class EstadisticasAuditoria(BaseModel):
    """Estadísticas de auditoría"""
    total_acciones: int
    por_accion: Dict[str, int]
    por_usuario: Dict[str, int]
    por_tabla: Dict[str, int]
    ultima_semana: int
    hoy: int