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
import shutil
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Importar init_db desde main
from app.main import init_db

logger = logging.getLogger(__name__)

# ============================================================
# UTILIDADES DE SEGURIDAD
# ============================================================

def sanitize_url(url: str) -> str:
    """
    Oculta las credenciales en una URL de base de datos para logs
    """
    if not url:
        return "URL no configurada"
    
    try:
        # Ocultar contraseña y usuario
        match = re.match(r"postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)", url)
        if match:
            user, password, host, port, dbname = match.groups()
            user_short = user[:3] + "..." if len(user) > 3 else user
            return f"postgresql://{user_short}:****@...:{port}/{dbname}"
        
        match = re.match(r"postgresql://([^:]+):([^@]+)@([^/]+)/(.+)", url)
        if match:
            user, password, host, dbname = match.groups()
            user_short = user[:3] + "..." if len(user) > 3 else user
            return f"postgresql://{user_short}:****@.../{dbname}"
        
        return "URL con formato no reconocido"
    except Exception:
        return "Error al sanitizar URL"

# ============================================================
# CONFIGURACIÓN
# ============================================================

BACKUP_DIR = os.getenv("BACKUP_DIR", "./backups")
DATABASE_URL = os.getenv("DATABASE_URL", "")
MAX_BACKUPS = int(os.getenv("MAX_BACKUPS", "30"))
GOOGLE_DRIVE_FOLDER = os.getenv("GOOGLE_DRIVE_FOLDER", "financoop_backups")

# Crear carpeta de backups si no existe
Path(BACKUP_DIR).mkdir(parents=True, exist_ok=True)

# Log de configuración (seguro)
logger.info(f"📁 BACKUP_DIR: {BACKUP_DIR}")
if DATABASE_URL:
    logger.info(f"🔍 DATABASE_URL: Configurada (host: {sanitize_url(DATABASE_URL)})")
else:
    logger.info("🔍 DATABASE_URL: ❌ NO CONFIGURADA")
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
            logger.warning("⚠️ GOOGLE_CREDENTIALS no está configurada (backup local solamente)")
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
        logger.warning(f"⚠️ No se pudo autenticar con Google Drive: {e}")
        return None

# ============================================================
# SUBIR A GOOGLE DRIVE
# ============================================================

def subir_a_google_drive(drive_service, archivo_zip):
    """
    Sube un archivo a Google Drive (si es posible)
    """
    if not drive_service:
        return False
        
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
            fields='id',
            supportsAllDrives=True
        ).execute()
        
        logger.info(f"📤 Backup subido a Google Drive: {os.path.basename(archivo_zip)}")
        return True
        
    except Exception as e:
        logger.warning(f"⚠️ No se pudo subir a Google Drive: {e}")
        return False

def buscar_o_crear_carpeta(drive_service):
    """
    Busca o crea la carpeta de backups en Google Drive
    """
    try:
        results = drive_service.files().list(
            q=f"name='{GOOGLE_DRIVE_FOLDER}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
            spaces='drive',
            fields='files(id, name)',
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        
        files = results.get('files', [])
        
        if files:
            folder_id = files[0]['id']
            logger.info(f"📁 Carpeta encontrada: {GOOGLE_DRIVE_FOLDER}")
            return folder_id
        
        # Si no existe, intentar crearla
        file_metadata = {
            'name': GOOGLE_DRIVE_FOLDER,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        file = drive_service.files().create(
            body=file_metadata,
            fields='id',
            supportsAllDrives=True
        ).execute()
        folder_id = file.get('id')
        
        logger.info(f"📁 Carpeta creada: {GOOGLE_DRIVE_FOLDER}")
        return folder_id
        
    except Exception as e:
        logger.warning(f"⚠️ No se pudo buscar/crear carpeta: {e}")
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
    Crea un backup completo de la base de datos
    """
    try:
        if not DATABASE_URL:
            logger.error("❌ DATABASE_URL no está configurada en el entorno")
            return False
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_sql = f"{BACKUP_DIR}/financoop_backup_{timestamp}.sql"
        backup_zip = f"{BACKUP_DIR}/financoop_backup_{timestamp}.zip"
        
        logger.info(f"📦 Iniciando backup: {backup_sql}")
        
        # ============================================================
        # VERIFICAR QUE pg_dump EXISTE
        # ============================================================
        if not shutil.which('pg_dump'):
            logger.error("❌ pg_dump NO está instalado en el sistema")
            logger.error("💡 Solución: Agregar 'postgresql-client' al Dockerfile o variable BUILD_PACKAGES")
            return False
        
        # ============================================================
        # OPCIÓN 1: USAR pg_dump (recomendado)
        # ============================================================
        parsed = parsear_db_url(DATABASE_URL)
        if not parsed:
            logger.error(f"❌ URL de base de datos no válida: {sanitize_url(DATABASE_URL)}")
            return False
        
        user, password, host, port, dbname = parsed
        logger.info(f"📊 Conectando a: {host}:{port}/{dbname}")
        
        env = os.environ.copy()
        env["PGPASSWORD"] = password
        
        # Usar la URL completa para pg_dump
        cmd = ["pg_dump", DATABASE_URL, "-F", "p", "-f", backup_sql]
        logger.info(f"🔄 Ejecutando: pg_dump {sanitize_url(DATABASE_URL)} -F p -f {backup_sql}")
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        # Logs de depuración (sin credenciales)
        logger.info(f"🔍 Código de retorno: {result.returncode}")
        if result.stderr:
            # Sanitizar posibles credenciales en stderr
            stderr_safe = result.stderr.replace(DATABASE_URL, sanitize_url(DATABASE_URL))
            logger.warning(f"⚠️ stderr: {stderr_safe[:500]}")
        if result.stdout:
            logger.info(f"✅ stdout: {result.stdout[:500]}")
        
        # ============================================================
        # VERIFICAR TAMAÑO DEL BACKUP
        # ============================================================
        if not os.path.exists(backup_sql):
            logger.error("❌ El archivo SQL no se creó")
            return False
        
        sql_size = os.path.getsize(backup_sql)
        logger.info(f"📄 Tamaño del archivo SQL: {sql_size} bytes ({sql_size/1024:.2f} KB)")
        
        if sql_size < 100:
            logger.error("❌ El archivo SQL está vacío o es demasiado pequeño")
            
            # ============================================================
            # OPCIÓN 2: FALLBACK - USAR psycopg2
            # ============================================================
            logger.info("🔄 Intentando método alternativo con psycopg2...")
            try:
                import psycopg2
                conn = psycopg2.connect(DATABASE_URL)
                cur = conn.cursor()
                
                with open(backup_sql, 'w') as f:
                    # Obtener todas las tablas
                    cur.execute("""
                        SELECT tablename FROM pg_tables 
                        WHERE schemaname = 'public'
                    """)
                    tables = cur.fetchall()
                    
                    logger.info(f"📊 Tablas encontradas: {len(tables)}")
                    
                    for table in tables:
                        table_name = table[0]
                        f.write(f"\n-- Datos de la tabla: {table_name}\n")
                        
                        # Obtener datos de la tabla
                        cur.execute(f"SELECT * FROM {table_name}")
                        rows = cur.fetchall()
                        
                        if rows:
                            # Obtener nombres de columnas
                            col_names = [desc[0] for desc in cur.description]
                            f.write(f"INSERT INTO {table_name} ({', '.join(col_names)}) VALUES\n")
                            
                            for i, row in enumerate(rows):
                                f.write("(")
                                for j, val in enumerate(row):
                                    if val is None:
                                        f.write("NULL")
                                    elif isinstance(val, str):
                                        # Escapar comillas simples
                                        val_escaped = val.replace("'", "''")
                                        f.write(f"'{val_escaped}'")
                                    elif isinstance(val, bool):
                                        f.write("true" if val else "false")
                                    elif isinstance(val, datetime):
                                        f.write(f"'{val.isoformat()}'")
                                    else:
                                        f.write(str(val))
                                    if j < len(row) - 1:
                                        f.write(", ")
                                f.write(")")
                                if i < len(rows) - 1:
                                    f.write(",\n")
                                else:
                                    f.write(";\n")
                            logger.info(f"✅ Tabla {table_name}: {len(rows)} registros")
                
                conn.close()
                
                # Verificar tamaño del backup generado con psycopg2
                sql_size = os.path.getsize(backup_sql)
                logger.info(f"📄 Tamaño del SQL (psycopg2): {sql_size} bytes ({sql_size/1024:.2f} KB)")
                
                if sql_size < 100:
                    logger.error("❌ El backup con psycopg2 también está vacío")
                    return False
                    
            except ImportError:
                logger.error("❌ psycopg2 no está instalado. Instalar con: pip install psycopg2-binary")
                return False
            except Exception as e:
                logger.error(f"❌ Error en método alternativo: {e}")
                return False
        
        # ============================================================
        # COMPRIMIR EL ARCHIVO SQL
        # ============================================================
        logger.info(f"📦 Comprimiendo: {backup_sql} -> {backup_zip}")
        
        with zipfile.ZipFile(backup_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(backup_sql, os.path.basename(backup_sql))
        
        # Verificar que el ZIP se creó correctamente
        if not os.path.exists(backup_zip) or os.path.getsize(backup_zip) == 0:
            logger.error("❌ El archivo ZIP no se creó correctamente")
            return False
        
        zip_size = os.path.getsize(backup_zip)
        logger.info(f"📦 Tamaño del ZIP: {zip_size} bytes ({zip_size/1024:.2f} KB)")
        
        # Eliminar el SQL temporal
        os.remove(backup_sql)
        logger.info("🗑️ Archivo SQL temporal eliminado")
        
        # ============================================================
        # INTENTAR SUBIR A GOOGLE DRIVE (OPCIONAL)
        # ============================================================
        drive_service = autenticar_google_drive()
        if drive_service:
            if subir_a_google_drive(drive_service, backup_zip):
                os.remove(backup_zip)
                logger.info("🗑️ Archivo local eliminado después de subir a Google Drive")
                logger.info("✅ Backup completado y guardado en Google Drive")
                return True
            else:
                logger.warning("⚠️ Backup guardado localmente (falló subida a Google Drive)")
                return True
        else:
            logger.info(f"ℹ️ Backup guardado localmente: {backup_zip}")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error creando backup: {e}")
        return False

# ============================================================
# LISTAR BACKUPS
# ============================================================

def listar_backups():
    """
    Lista los backups disponibles localmente
    """
    try:
        backups = []
        for file in Path(BACKUP_DIR).glob("*.zip"):
            size_bytes = file.stat().st_size
            backups.append({
                "nombre": file.name,
                "tamaño_bytes": size_bytes,
                "tamaño_mb": round(size_bytes / (1024 * 1024), 2),
                "fecha": datetime.fromtimestamp(file.stat().st_mtime).isoformat()
            })
        logger.info(f"📋 {len(backups)} backups encontrados")
        return sorted(backups, key=lambda x: x["fecha"], reverse=True)
        
    except Exception as e:
        logger.error(f"❌ Error listando backups: {e}")
        return []

# ============================================================
# RESTAURAR BACKUP (VERSIÓN MEJORADA CON INICIALIZACIÓN)
# ============================================================

def restaurar_backup(backup_file: str):
    """
    Restaura un backup desde un archivo local
    Versión mejorada con limpieza previa, timeout e inicialización de datos
    """
    try:
        if not DATABASE_URL:
            logger.error("❌ DATABASE_URL no está configurada en el entorno")
            return False
        
        logger.info(f"🔄 Iniciando restauración: {backup_file}")
        
        if not os.path.exists(backup_file):
            logger.error(f"❌ Archivo no encontrado: {backup_file}")
            return False
        
        # ============================================================
        # DESCOMPRIMIR SI ES ZIP
        # ============================================================
        sql_file = backup_file
        if backup_file.endswith('.zip'):
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                sql_name = zipf.namelist()[0]
                zipf.extractall(BACKUP_DIR)
                sql_file = os.path.join(BACKUP_DIR, sql_name)
                logger.info(f"📦 Archivo descomprimido: {sql_file}")
        
        # Verificar que el SQL existe
        if not os.path.exists(sql_file):
            logger.error(f"❌ Archivo SQL no encontrado: {sql_file}")
            return False
        
        # ============================================================
        # LIMPIAR BASE DE DATOS ANTES DE RESTAURAR
        # ============================================================
        logger.info("🧹 Limpiando base de datos antes de restaurar...")
        try:
            import psycopg2
            conn = psycopg2.connect(DATABASE_URL)
            conn.autocommit = True
            cur = conn.cursor()
            
            # Obtener todas las tablas
            cur.execute("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public'
            """)
            tables = cur.fetchall()
            
            logger.info(f"📊 Tablas encontradas: {len(tables)}")
            
            # Eliminar todas las tablas en orden inverso (para respetar FK)
            for table in tables:
                try:
                    cur.execute(f"DROP TABLE IF EXISTS {table[0]} CASCADE")
                    logger.info(f"🗑️ Tabla eliminada: {table[0]}")
                except Exception as e:
                    logger.warning(f"⚠️ No se pudo eliminar {table[0]}: {e}")
            
            # Eliminar secuencias
            cur.execute("""
                SELECT sequence_name FROM information_schema.sequences 
                WHERE sequence_schema = 'public'
            """)
            sequences = cur.fetchall()
            for seq in sequences:
                try:
                    cur.execute(f"DROP SEQUENCE IF EXISTS {seq[0]} CASCADE")
                    logger.info(f"🗑️ Secuencia eliminada: {seq[0]}")
                except Exception as e:
                    logger.warning(f"⚠️ No se pudo eliminar secuencia {seq[0]}: {e}")
            
            conn.close()
            logger.info("✅ Base de datos limpiada correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error limpiando base de datos: {e}")
            return False
        
        # ============================================================
        # USAR LA URL COMPLETA (más estable)
        # ============================================================
        env = os.environ.copy()
        
        # Usar la URL completa en lugar de parámetros separados
        cmd = [
            "psql",
            DATABASE_URL,
            "-f", sql_file,
            "--quiet",
            "--set", "ON_ERROR_STOP=on"
        ]
        
        logger.info(f"🔄 Ejecutando: psql {sanitize_url(DATABASE_URL)} -f {sql_file}")
        
        # Ejecutar con timeout de 5 minutos para evitar que se cuelgue
        result = subprocess.run(
            cmd, 
            env=env, 
            capture_output=True, 
            text=True,
            timeout=300  # 5 minutos máximo
        )
        
        if result.returncode != 0:
            logger.error(f"❌ Error restaurando: {result.stderr}")
            return False
        
        logger.info(f"✅ Backup restaurado exitosamente: {backup_file}")
        
        # ============================================================
        # INICIALIZAR DATOS MÍNIMOS DESPUÉS DE RESTAURAR
        # ============================================================
        logger.info("🔄 Inicializando datos de configuración mínimos...")
        try:
            # Llamar a la función de inicialización de la base de datos
            # que crea registros como la tasa de cambio y los niveles.
            init_db()
            logger.info("✅ Datos de configuración inicializados correctamente.")
        except Exception as e:
            logger.error(f"❌ Error crítico inicializando datos después de restauración: {e}")
            # La restauración fue exitosa pero la inicialización falló
            # Devolvemos False para que el endpoint sepa que hubo un problema
            return False
        
        # ============================================================
        # LIMPIAR ARCHIVOS TEMPORALES
        # ============================================================
        if backup_file.endswith('.zip') and os.path.exists(sql_file):
            os.remove(sql_file)
            logger.info(f"🗑️ Archivo SQL temporal eliminado: {sql_file}")
        
        # ============================================================
        # FORZAR CIERRE DE CONEXIONES
        # ============================================================
        try:
            import psycopg2
            conn = psycopg2.connect(DATABASE_URL)
            conn.close()
            logger.info("🔌 Conexión temporal cerrada")
        except Exception as e:
            logger.warning(f"⚠️ No se pudo cerrar conexión temporal: {e}")
        
        logger.info(f"✅ Proceso de restauración y post-inicialización completado.")
        return True
        
    except subprocess.TimeoutExpired:
        logger.error("❌ La restauración excedió el tiempo límite (5 minutos)")
        return False
    except Exception as e:
        logger.error(f"❌ Error restaurando backup: {e}")
        return False