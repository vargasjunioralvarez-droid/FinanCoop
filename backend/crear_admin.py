# crear_admin.py
from app.core.database import SessionLocal
from app.modules.users.models import Usuario
from app.core.security import hash_password

db = SessionLocal()
admin = Usuario(
    username="admin",
    password=hash_password("junior123*"),
    nombre="Administrador",
    rol="admin_central",
    activo=True
)
db.add(admin)
db.commit()
print("✅ Usuario admin creado")
db.close()