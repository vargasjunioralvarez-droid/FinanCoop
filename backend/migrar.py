# backend/migrar.py
from app.database import engine
from sqlalchemy import text

def migrar():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE clientes ADD COLUMN IF NOT EXISTS url_cedula VARCHAR(500)"))
            print("✅ url_cedula agregada")
        except Exception as e:
            print(f"⚠️ Error al agregar url_cedula: {e}")
        
        try:
            conn.execute(text("ALTER TABLE clientes DROP COLUMN IF EXISTS foto_cedula"))
            print("✅ foto_cedula eliminada")
        except Exception as e:
            print(f"⚠️ Error al eliminar foto_cedula: {e}")
        
        conn.commit()
        print("✅ Migración completada")

if __name__ == "__main__":
    migrar()