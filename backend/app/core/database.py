# app/core/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# ============================================================
# 🔥 CONFIGURACIÓN DE BASE DE DATOS (mantenemos tu lógica)
# ============================================================

# Usar variable de entorno o fallback para desarrollo local
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:postgres@localhost:5432/financash_db"
)

# Configuración del engine (mejorada)
# Añadimos opciones de rendimiento y manejo de conexiones
engine = create_engine(
    DATABASE_URL,
    # Opciones para mejor rendimiento
    pool_pre_ping=True,  # Verificar conexión antes de usarla
    pool_recycle=3600,   # Reciclar conexiones cada hora
    pool_size=10,        # Tamaño del pool de conexiones
    max_overflow=20,     # Conexiones adicionales si el pool está lleno
    echo=False,          # Para depuración (cambiar a True para ver SQL)
)

# Sesión local
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos
Base = declarative_base()

# ============================================================
# 🆕 FUNCIONES ADICIONALES (mejoras)
# ============================================================

def get_db():
    """Dependencia para FastAPI - Obtener sesión de BD"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()  # Rollback automático en caso de error
        raise e
    finally:
        db.close()

def init_db():
    """Crear todas las tablas si no existen"""
    Base.metadata.create_all(bind=engine)

def drop_db():
    """Eliminar todas las tablas (SOLO PARA DESARROLLO)"""
    Base.metadata.drop_all(bind=engine)

# ============================================================
# 🔥 MANTENER COMPATIBILIDAD CON CÓDIGO EXISTENTE
# ============================================================
# Para que `from app.database import get_db` siga funcionando
# No necesitamos hacer nada extra porque ya exportamos todo