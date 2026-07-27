"""
Sistema de Backups Automáticos con Google Drive
"""

import os
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path
import zipfile
import re
import json
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURACIÓN
# ============================================================

BACKUP_DIR = os.getenv("BACKUP_DIR", "./backups")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://financash_user:nd4tC0TcZk1hytHbwhwT9VGGmbJce4it@dpg-d9d59jurnols73ct1qvg-a.oregon-postgres.render.com/financash_db_6ge7")
MAX_BACKUPS = int(os.getenv("MAX_BACKUPS", "30"))
GOOGLE_DRIVE_FOLDER = os.getenv("GOOGLE_DRIVE_FOLDER", "financoop_backups")

# Crear carpeta de backups si no existe
Path(BACKUP_DIR).mkdir(parents=True, exist_ok=True)

# ============================================================
# AUTENTICACIÓN CON GOOGLE DRIVE
# ============================================================

def autenticar_google_drive():
    """
    Autentica con Google Drive usando credenciales de cuenta de servicio
    """
    try:
        # Obtener credenciales desde variable de entorno
        creds_json = os.getenv("GOOGLE_CREDENTIALS")
        if not creds_json:
            logger.error("❌ GOOGLE_CREDENTIALS no está configurada")
            return None
        
        # Guardar credenciales temporalmente
        creds_file = "temp_credentials.json"
        with open(creds_file, "w") as f:
            f.write(creds_json)
        
        gauth = GoogleAuth()
        gauth.LoadCredentialsFile(creds_file)
        
        if gauth.credentials is None:
            gauth.ServiceAuth()
            gauth.SaveCredentialsFile(creds_file)
        elif gauth.access_token_expired:
            gauth.Refresh()
        else:
            gauth.Authorize()
        
        drive = GoogleDrive(gauth)
        logger.info("✅ Autenticación con Google Drive exitosa")
        
        # Limpiar archivo temporal
        os.remove(creds_file)
        
        return drive
    except Exception as e:
        logger.error(f"❌ Error autenticando con Google Drive: {e}")
        return None

# ============================================================
# SUBIR A GOOGLE DRIVE
# ============================================================

def subir_a_google_drive(drive, archivo_zip):
    """
    Sube un archivo a Google Drive
    """
    try:
        folder_id = buscar_o_crear_carpeta(drive)
        if not folder_id:
            return False
        
        file_drive = drive.CreateFile({
            'title': os.path.basename(archivo_zip),
            'parents': [{'id': folder_id}],
            'mimeType': 'application/zip'
        })
        file_drive.SetContentFile(archivo_zip)
        file_drive.Upload()
        
        logger.info(f"📤 Backup subido a Google Drive: {os.path.basename(archivo_zip)}")
        return True
    except Exception as e:
        logger.error(f"❌ Error subiendo a Google Drive: {e}")
        return False

def buscar_o_crear_carpeta(drive):
    """
    Busca o crea la carpeta de backups en Google Drive
    """
    try:
        file_list = drive.ListFile({
            'q': f"title='{GOOGLE_DRIVE_FOLDER}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        }).GetList()
        
        if file_list:
            folder_id = file_list[0]['id']
            logger.info(f"📁 Carpeta encontrada: {GOOGLE_DRIVE_FOLDER}")
            return folder_id
        
        folder = drive.CreateFile({
            'title': GOOGLE_DRIVE_FOLDER,
            'mimeType': 'application/vnd.google-apps.folder'
        })
        folder.Upload()
        logger.info(f"📁 Carpeta creada: {GOOGLE_DRIVE_FOLDER}")
        return folder['id']
    except Exception as e:
        logger.error(f"❌ Error buscando/creando carpeta: {e}")
        return None

# ============================================================
# FUNCIÓN PRINCIPAL: CREAR BACKUP
# ============================================================

def crear_backup():
    """
    Crea un backup completo de la base de datos y lo sube a Google Drive
    """
    try:
        drive = autenticar_google_drive()
        if not drive:
            logger.error("❌ No se pudo autenticar con Google Drive")
            return False
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_sql = f"{BACKUP_DIR}/financoop_backup_{timestamp}.sql"
        backup_zip = f"{BACKUP_DIR}/financoop_backup_{timestamp}.zip"
        
        logger.info(f"📦 Iniciando backup: {backup_sql}")
        
        match = re.match(r"postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)", DATABASE_URL)
        if not match:
            logger.error("❌ URL de base de datos no válida")
            return False
        
        user, password, host, port, dbname = match.groups()
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
        
        if subir_a_google_drive(drive, backup_zip):
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
        drive = autenticar_google_drive()
        if not drive:
            return []
        
        folder_id = buscar_o_crear_carpeta(drive)
        if not folder_id:
            return []
        
        file_list = drive.ListFile({
            'q': f"'{folder_id}' in parents and trashed=false"
        }).GetList()
        
        backups = []
        for file in file_list:
            backups.append({
                "nombre": file['title'],
                "tamaño_bytes": int(file['fileSize']),
                "tamaño_mb": round(int(file['fileSize']) / (1024 * 1024), 2),
                "fecha": file['createdDate']
            })
        return sorted(backups, key=lambda x: x["fecha"], reverse=True)
        
    except Exception as e:
        logger.error(f"❌ Error listando backups: {e}")
        return []

# ============================================================
# RESTAURAR BACKUP
# ============================================================

def restaurar_backup(backup_file: str):
    """
    Restaura un backup desde un archivo en Google Drive
    """
    try:
        logger.info(f"🔄 Iniciando restauración: {backup_file}")
        
        # 1. Verificar que el archivo existe
        if not os.path.exists(backup_file):
            logger.error(f"❌ Archivo no encontrado: {backup_file}")
            return False
        
        # 2. Parsear URL de la base de datos
        match = re.match(r"postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)", DATABASE_URL)
        if not match:
            logger.error("❌ URL de base de datos no válida")
            return False
        
        user, password, host, port, dbname = match.groups()
        
        # 3. Descomprimir si es .zip
        sql_file = backup_file
        if backup_file.endswith('.zip'):
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                sql_name = zipf.namelist()[0]
                zipf.extractall(BACKUP_DIR)
                sql_file = os.path.join(BACKUP_DIR, sql_name)
                logger.info(f"📦 Archivo descomprimido: {sql_file}")
        
        # 4. Configurar variable de entorno para la contraseña
        env = os.environ.copy()
        env["PGPASSWORD"] = password
        
        # 5. Ejecutar psql para restaurar
        cmd = [
            "psql",
            "-h", host,
            "-p", port,
            "-U", user,
            "-d", dbname,
            "-f", sql_file
        ]
        
        logger.info(f"🔄 Ejecutando: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"❌ Error restaurando: {result.stderr}")
            return False
        
        logger.info(f"✅ Backup restaurado exitosamente: {backup_file}")
        
        # 6. Limpiar archivo SQL extraído (si era zip)
        if backup_file.endswith('.zip') and os.path.exists(sql_file):
            os.remove(sql_file)
            logger.info(f"🗑️ Archivo SQL temporal eliminado: {sql_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error restaurando backup: {e}")
        return False