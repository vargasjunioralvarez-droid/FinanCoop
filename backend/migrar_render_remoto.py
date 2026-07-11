# backend/migrar_render_remoto.py
import os
import sys
from sqlalchemy import create_engine, text

# ✅ URL DE CONEXIÓN A RENDER (REEMPLAZA CON LA TUYA)
RENDER_DATABASE_URL = "postgresql://financash_db_user:pp1yybmJC7ocxQzJFhwosg5rzuhaUOWT@dpg-d98g3tq8qa3s73fetq3g-a.oregon-postgres.render.com/financash_db"

def migrar():
    print("🔧 Conectando a la base de datos de RENDER...")
    print(f"📡 URL: {RENDER_DATABASE_URL}")
    
    try:
        # Crear conexión directa a Render
        engine = create_engine(RENDER_DATABASE_URL)
        
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
                
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        print("💡 Verifica que la URL de conexión sea correcta")

if __name__ == "__main__":
    migrar()