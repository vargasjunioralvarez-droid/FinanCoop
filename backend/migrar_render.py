# backend/migrar_render.py
import os
import sys

# Agregar la ruta del proyecto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine
from sqlalchemy import text

def migrar():
    print("🔧 Conectando a la base de datos...")
    with engine.connect() as conn:
        # 1. Verificar si la columna existe
        print("📋 Verificando columnas existentes...")
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'clientes'"))
        columnas = [row[0] for row in result]
        print(f"📋 Columnas actuales: {columnas}")
        
        # 2. Agregar url_cedula si no existe
        if 'url_cedula' not in columnas:
            print("➕ Agregando columna url_cedula...")
            try:
                conn.execute(text("ALTER TABLE clientes ADD COLUMN url_cedula VARCHAR(500)"))
                conn.commit()
                print("✅ Columna url_cedula agregada correctamente")
            except Exception as e:
                print(f"❌ Error al agregar url_cedula: {e}")
        else:
            print("ℹ️ La columna url_cedula ya existe")
        
        # 3. Verificar que la columna existe ahora
        print("📋 Verificando columnas finales...")
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'clientes'"))
        columnas_finales = [row[0] for row in result]
        print(f"📋 Columnas finales: {columnas_finales}")
        
        if 'url_cedula' in columnas_finales:
            print("✅ ¡Migración completada con éxito!")
        else:
            print("❌ La columna url_cedula NO se agregó correctamente")

if __name__ == "__main__":
    migrar()