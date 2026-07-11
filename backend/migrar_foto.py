# backend/migrar_foto.py
from app.database import engine
from sqlalchemy import text

def migrar():
    with engine.connect() as conn:
        # Ver columnas actuales
        print("📋 Columnas actuales:")
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'clientes'"))
        for row in result:
            print(f"  - {row[0]}")

        # Eliminar cedula_foto (la columna que guarda la imagen en base64)
        try:
            conn.execute(text("ALTER TABLE clientes DROP COLUMN IF EXISTS cedula_foto"))
            conn.commit()
            print("✅ cedula_foto eliminada")
        except Exception as e:
            print(f"⚠️ Error al eliminar cedula_foto: {e}")

        # Ver columnas finales
        print("📋 Columnas finales:")
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'clientes'"))
        for row in result:
            print(f"  - {row[0]}")

if __name__ == "__main__":
    migrar()