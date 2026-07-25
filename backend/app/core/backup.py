"""
Sistema de Backups Automáticos
"""

import os
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path
import zipfile
import re

logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURACIÓN
# ============================================================

# Carpeta donde se guardan los backups
BACKUP_DIR = os.getenv("BACKUP_DIR", "./backups")

# URL de la base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Número máximo de backups a mantener
MAX_BACKUPS = int(os.getenv("MAX_BACKUPS", "30"))

# Crear carpeta de backups si no existe
Path(BACKUP_DIR).mkdir(parents=True, exist_ok=True)

# ============================================================
# FUNCIÓN PRINCIPAL: CREAR BACKUP
# ============================================================

def crear_backup():
    """
    Crea un backup completo de la base de datos.
    Usa pg_dump de PostgreSQL para exportar la BD.
    """
    try:
        # 1. Generar nombre de archivo con fecha/hora
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_sql = f"{BACKUP_DIR}/financoop_backup_{timestamp}.sql"
        backup_zip = f"{BACKUP_DIR}/financoop_backup_{timestamp}.zip"
        
        logger.info(f"📦 Iniciando backup: {backup_sql}")
        
        # 2. Parsear la URL de la base de datos
        # Ejemplo: postgresql://usuario:password@host:5432/database
        match = re.match(r"postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)", DATABASE_URL)
        
        if not match:
            logger.error("❌ URL de base de datos no válida")
            return False
        
        user, password, host, port, dbname = match.groups()
        logger.info(f"📊 Conectando a: {host}:{port}/{dbname} como {user}")
        
        # 3. Configurar variable de entorno para la contraseña
        env = os.environ.copy()
        env["PGPASSWORD"] = password
        
        # 4. Ejecutar pg_dump
        cmd = [
            "pg_dump",
            "-h", host,
            "-p", port,
            "-U", user,
            "-d", dbname,
            "-F", "p",      # Formato: plain text (SQL)
            "-f", backup_sql
        ]
        
        logger.info(f"🔄 Ejecutando: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        # 5. Verificar que el backup fue exitoso
        if result.returncode != 0:
            logger.error(f"❌ Error en pg_dump: {result.stderr}")
            return False
        
        # 6. Verificar que el archivo se creó correctamente
        if not os.path.exists(backup_sql) or os.path.getsize(backup_sql) == 0:
            logger.error("❌ El archivo de backup no se creó correctamente")
            return False
        
        # 7. Comprimir el archivo SQL
        with zipfile.ZipFile(backup_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(backup_sql, os.path.basename(backup_sql))
        
        # 8. Eliminar el archivo SQL (solo guardamos el .zip)
        os.remove(backup_sql)
        
        # 9. Limpiar backups antiguos
        limpiar_backups_antiguos()
        
        # 10. Calcular tamaño del backup
        size_mb = os.path.getsize(backup_zip) / (1024 * 1024)
        
        logger.info(f"✅ Backup completado: {os.path.basename(backup_zip)} ({size_mb:.2f} MB)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creando backup: {e}")
        return False

# ============================================================
# LIMPIAR BACKUPS ANTIGUOS
# ============================================================

def limpiar_backups_antiguos():
    """
    Elimina los backups que tengan más de MAX_BACKUPS días
    """
    try:
        now = datetime.now()
        cutoff = now - timedelta(days=MAX_BACKUPS)
        
        for file in Path(BACKUP_DIR).glob("*.zip"):
            # Obtener la fecha de modificación del archivo
            file_time = datetime.fromtimestamp(file.stat().st_mtime)
            
            if file_time < cutoff:
                file.unlink()
                logger.info(f"🗑️ Backup antiguo eliminado: {file.name}")
                
    except Exception as e:
        logger.error(f"❌ Error limpiando backups antiguos: {e}")

# ============================================================
# LISTAR BACKUPS DISPONIBLES
# ============================================================

def listar_backups():
    """
    Lista todos los backups disponibles
    """
    backups = []
    for file in Path(BACKUP_DIR).glob("*.zip"):
        backups.append({
            "nombre": file.name,
            "tamaño_bytes": file.stat().st_size,
            "tamaño_mb": round(file.stat().st_size / (1024 * 1024), 2),
            "fecha": datetime.fromtimestamp(file.stat().st_mtime).isoformat()
        })
    return sorted(backups, key=lambda x: x["fecha"], reverse=True)

# ============================================================
# RESTAURAR BACKUP
# ============================================================

def restaurar_backup(backup_file: str):
    """
    Restaura un backup usando psql
    """
    try:
        if not os.path.exists(backup_file):
            logger.error(f"❌ Archivo no encontrado: {backup_file}")
            return False
        
        logger.info(f"🔄 Restaurando backup: {backup_file}")
        
        # Parsear URL de la BD
        match = re.match(r"postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)", DATABASE_URL)
        
        if not match:
            logger.error("❌ URL de base de datos no válida")
            return False
        
        user, password, host, port, dbname = match.groups()
        
        # Descomprimir si es .zip
        sql_file = backup_file
        if backup_file.endswith('.zip'):
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                sql_name = zipf.namelist()[0]
                zipf.extractall(BACKUP_DIR)
                sql_file = os.path.join(BACKUP_DIR, sql_name)
        
        # Configurar variable de entorno
        env = os.environ.copy()
        env["PGPASSWORD"] = password
        
        # Ejecutar psql para restaurar
        cmd = [
            "psql",
            "-h", host,
            "-p", port,
            "-U", user,
            "-d", dbname,
            "-f", sql_file
        ]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"❌ Error restaurando: {result.stderr}")
            return False
        
        logger.info(f"✅ Backup restaurado: {backup_file}")
        
        # Limpiar archivo SQL extraído (si era zip)
        if backup_file.endswith('.zip') and os.path.exists(sql_file):
            os.remove(sql_file)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error restaurando backup: {e}")
        return False