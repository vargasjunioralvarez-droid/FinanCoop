"""
Programador de tareas automáticas (Backups)
"""

import threading
import time
import logging
from datetime import datetime
from app.core.backup import crear_backup

logger = logging.getLogger(__name__)

class Scheduler:
    """
    Ejecuta tareas programadas en segundo plano.
    Usa un hilo (thread) separado para no bloquear el servidor.
    """
    
    def __init__(self):
        self.running = False
        self.thread = None
        self.last_backup = None
    
    def start(self):
        """Inicia el scheduler en un hilo separado"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info("⏰ Scheduler de backups iniciado")
    
    def stop(self):
        """Detiene el scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("⏰ Scheduler detenido")
    
    def _run(self):
        """
        Bucle principal del scheduler.
        Verifica cada minuto si es hora de hacer backup.
        """
        while self.running:
            now = datetime.now()
            
            # Backup diario a las 2:00 AM
            if not self.last_backup or (now - self.last_backup).days >= 1:
                if now.hour == 2 and now.minute < 5:
                    logger.info("⏰ Ejecutando backup diario programado...")
                    resultado = crear_backup()
                    if resultado:
                        self.last_backup = now
                        logger.info("✅ Backup diario completado")
                    else:
                        logger.error("❌ Backup diario falló")
                    time.sleep(300)
            
            time.sleep(60)

# Instancia única del scheduler
scheduler = Scheduler()

def iniciar_scheduler():
    """Función para iniciar el scheduler desde main.py"""
    scheduler.start()

def ejecutar_backup_manual():
    """Ejecuta un backup manualmente (desde API)"""
    return crear_backup()