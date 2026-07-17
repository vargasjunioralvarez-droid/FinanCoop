# backend/crear_admin.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import bcrypt

# ✅ NUEVA URL DE LA BASE DE DATOS
DATABASE_URL = "postgresql://financash_user:nd4tC0TcZk1hytHbwhwT9VGGmbJce4it@dpg-d9d59jurnols73ct1qvg-a.oregon-postgres.render.com/financash_db_6ge7"

# Conectar a la base de datos
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

try:
    # Verificar si la tabla usuarios existe
    result = db.execute(text("SELECT 1 FROM usuarios LIMIT 1"))
    print("✅ La tabla usuarios ya existe")
except Exception as e:
    print("⚠️ La tabla usuarios no existe. Creándola...")
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(200) NOT NULL,
            rol VARCHAR(20) DEFAULT 'usuario',
            nombre VARCHAR(100),
            email VARCHAR(100),
            activo BOOLEAN DEFAULT TRUE,
            creado_en TIMESTAMP DEFAULT NOW()
        )
    """))
    db.commit()
    print("✅ Tabla usuarios creada")

# Verificar si el admin ya existe
admin = db.execute(text("SELECT * FROM usuarios WHERE username = 'admin'")).fetchone()
if admin:
    print("ℹ️ El usuario admin ya existe")
else:
    hashed_password = hash_password("admin123")
    db.execute(text("""
        INSERT INTO usuarios (username, password, rol, nombre, activo)
        VALUES ('admin', :password, 'admin', 'Administrador', TRUE)
    """), {"password": hashed_password})
    db.commit()
    print("✅ Usuario administrador creado: admin / admin123")

# Mostrar usuarios
usuarios = db.execute(text("SELECT id, username, rol, nombre, activo FROM usuarios")).fetchall()
print("\n📋 Usuarios en el sistema:")
for u in usuarios:
    print(f"  - ID: {u[0]}, Usuario: {u[1]}, Rol: {u[2]}, Nombre: {u[3]}, Activo: {u[4]}")

db.close()
print("\n✅ Proceso completado")