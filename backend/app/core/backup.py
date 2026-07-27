"""
Sistema de Backups Automáticos con Google Drive
Usa google-api-python-client directamente (sin pydrive2)
"""

import os
import subprocess
import logging
from datetime import datetime
from pathlib import Path
import zipfile
import re
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURACIÓN
# ============================================================

BACKUP_DIR = os.getenv("BACKUP_DIR", "./backups")
DATABASE_URL = os.getenv("DATABASE_URL", "")
MAX_BACKUPS = int(os.getenv("MAX_BACKUPS", "30"))
GOOGLE_DRIVE_FOLDER = os.getenv("GOOGLE_DRIVE_FOLDER", "financoop_backups")

# Crear carpeta de backups si no existe
Path(BACKUP_DIR).mkdir(parents=True, exist_ok=True)

# Log de configuración
logger.info(f"📁 BACKUP_DIR: {BACKUP_DIR}")
logger.info(f"🔍 DATABASE_URL: {'✅ Configurada' if DATABASE_URL else '❌ NO CONFIGURADA'}")
logger.info(f"📁 GOOGLE_DRIVE_FOLDER: {GOOGLE_DRIVE_FOLDER}")

# ============================================================
# AUTENTICACIÓN CON GOOGLE DRIVE
# ============================================================

def autenticar_google_drive():
    """
    Autentica con Google Drive usando credenciales de cuenta de servicio
    """
    try:
        creds_json = os.getenv("GOOGLE_CREDENTIALS")
        if not creds_json:
            logger.error("❌ GOOGLE_CREDENTIALS no está configurada")
            return None
        
        # Guardar credenciales temporalmente
        creds_file = "temp_credentials.json"
        with open(creds_file, "w") as f:
            f.write(creds_json)
        
        # Autenticar con Google
        credentials = service_account.Credentials.from_service_account_file(
            creds_file,
            scopes=['https://www.googleapis.com/auth/drive.file']
        )
        
        drive_service = build('drive', 'v3', credentials=credentials)
        
        # Limpiar archivo temporal
        os.remove(creds_file)
        
        logger.info("✅ Autenticación con Google Drive exitosa")
        return drive_service
        
    except Exception as e:
        logger.error(f"❌ Error autenticando con Google Drive: {e}")
        return None

# ============================================================
# SUBIR A GOOGLE DRIVE
# ============================================================

def subir_a_google_drive(drive_service, archivo_zip):
    """
    Sube un archivo a Google Drive
    """
    try:
        folder_id = buscar_o_crear_carpeta(drive_service)
        if not folder_id:
            return False
        
        file_metadata = {
            'name': os.path.basename(archivo_zip),
            'parents': [folder_id]
        }
        
        media = MediaFileUpload(archivo_zip, mimetype='application/zip')
        
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        logger.info(f"📤 Backup subido a Google Drive: {os.path.basename(archivo_zip)}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error subiendo a Google Drive: {e}")
        return False

def buscar_o_crear_carpeta(drive_service):
    """
    Busca o crea la carpeta de backups en Google Drive
    """
    try:
        # Buscar carpeta existente
        results = drive_service.files().list(
            q=f"name='{GOOGLE_DRIVE_FOLDER}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        files = results.get('files', [])
        
        if files:
            folder_id = files[0]['id']
            logger.info(f"📁 Carpeta encontrada: {GOOGLE_DRIVE_FOLDER}")
            return folder_id
        
        # Crear carpeta si no existe
        file_metadata = {
            'name': GOOGLE_DRIVE_FOLDER,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        file = drive_service.files().create(body=file_metadata, fields='id').execute()
        folder_id = file.get('id')
        
        logger.info(f"📁 Carpeta creada: {GOOGLE_DRIVE_FOLDER}")
        return folder_id
        
    except Exception as e:
        logger.error(f"❌ Error buscando/creando carpeta: {e}")
        return None

# ============================================================
# PARSEAR URL DE BASE DE DATOS
# ============================================================

def parsear_db_url(url):
    """
    Parsea una URL de PostgreSQL y devuelve sus componentes
    """
    match = re.match(r"postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)", url)
    if match:
        return match.groups()
    
    match = re.match(r"postgresql://([^:]+):([^@]+)@([^/]+)/(.+)", url)
    if match:
        user, password, host, dbname = match.groups()
        return (user, password, host, "5432", dbname)
    
    return None

# ============================================================
# FUNCIÓN PRINCIPAL: CREAR BACKUP
# ============================================================

def crear_backup():
    """
    Crea un backup completo de la base de datos y lo sube a Google Drive
    """
    try:
        if not DATABASE_URL:
            logger.error("❌ DATABASE_URL no está configurada en el entorno")
            return False
        
        drive_service = autenticar_google_drive()
        if not drive_service:
            logger.error("❌ No se pudo autenticar con Google Drive")
            return False
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_sql = f"{BACKUP_DIR}/financoop_backup_{timestamp}.sql"
        backup_zip = f"{BACKUP_DIR}/financoop_backup_{timestamp}.zip"
        
        logger.info(f"📦 Iniciando backup: {backup_sql}")
        
        parsed = parsear_db_url(DATABASE_URL)
        if not parsed:
            logger.error(f"❌ URL de base de datos no válida: {DATABASE_URL}")
            return False
        
        user, password, host, port, dbname = parsed
        logger.info(f"📊 Conectando a: {host}:{port}/{dbname} como {user}")
        
        env = os.environ.copy()
        env["PGPASSWORD"] = password
        
        cmd = ["pg_dump", "-h", host, "-p", port, "-U", user, "-d", dbname, "-F", "p", "-f", backup_sql]
        logger.info(f"🔄 Ejecutando: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"❌ Error en pg_dump: {result.stderr}")
            return False
        
        if not os.path.exists(backup_sql) or os.path.getsize(backup_sql) == 0:
            logger.error("❌ El archivo de backup no se creó correctamente")
            return False
        
        with zipfile.ZipFile(backup_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(backup_sql, os.path.basename(backup_sql))
        
        os.remove(backup_sql)
        
        if subir_a_google_drive(drive_service, backup_zip):
            os.remove(backup_zip)
            logger.info("🗑️ Archivo local eliminado después de subir a Google Drive")
            logger.info("✅ Backup completado y guardado en Google Drive")
            return True
        else:
            logger.warning("⚠️ Backup guardado localmente (falló subida a Google Drive)")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error creando backup: {e}")
        return False

# ============================================================
# LISTAR BACKUPS DESDE GOOGLE DRIVE
# ============================================================

def listar_backups():
    """
    Lista los backups disponibles en Google Drive
    """
    try:
        drive_service = autenticar_google_drive()
        if not drive_service:
            return []
        
        folder_id = buscar_o_crear_carpeta(drive_service)
        if not folder_id:
            return []
        
        results = drive_service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            spaces='drive',
            fields='files(id, name, size, createdTime)',
            orderBy='createdTime desc'
        ).execute()
        
        files = results.get('files', [])
        
        backups = []
        for file in files:
            backups.append({
                "nombre": file['name'],
                "tamaño_bytes": int(file.get('size', 0)),
                "tamaño_mb": round(int(file.get('size', 0)) / (1024 * 1024), 2),
                "fecha": file['createdTime']
            })
        return backups
        
    except Exception as e:
        logger.error(f"❌ Error listando backups: {e}")
        return []

# ============================================================
# RESTAURAR BACKUP
# ============================================================

def restaurar_backup(backup_file: str):
    """
    Restaura un backup desde un archivo
    """
    try:
        if not DATABASE_URL:
            logger.error("❌ DATABASE_URL no está configurada en el entorno")
            return False
        
        logger.info(f"🔄 Iniciando restauración: {backup_file}")
        
        if not os.path.exists(backup_file):
            logger.error(f"❌ Archivo no encontrado: {backup_file}")
            return False
        
        parsed = parsear_db_url(DATABASE_URL)
        if not parsed:
            logger.error(f"❌ URL de base de datos no válida: {DATABASE_URL}")
            return False
        
        user, password, host, port, dbname = parsed
        
        sql_file = backup_file
        if backup_file.endswith('.zip'):
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                sql_name = zipf.namelist()[0]
                zipf.extractall(BACKUP_DIR)
                sql_file = os.path.join(BACKUP_DIR, sql_name)
                logger.info(f"📦 Archivo descomprimido: {sql_file}")
        
        env = os.environ.copy()
        env["PGPASSWORD"] = password
        
        cmd = ["psql", "-h", host, "-p", port, "-U", user, "-d", dbname, "-f", sql_file]
        logger.info(f"🔄 Ejecutando: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"❌ Error restaurando: {result.stderr}")
            return False
        
        logger.info(f"✅ Backup restaurado exitosamente: {backup_file}")
        
        if backup_file.endswith('.zip') and os.path.exists(sql_file):
            os.remove(sql_file)
            logger.info(f"🗑️ Archivo SQL temporal eliminado: {sql_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error restaurando backup: {e}")
        return False