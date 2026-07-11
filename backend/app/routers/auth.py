# backend/app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models import Usuario, Cliente
from app.auth import create_access_token, get_current_cliente, get_current_admin, hash_password, verify_password
import bcrypt
import os

# ✅ EL ROUTER DEBE LLAMARSE "router"
router = APIRouter(prefix="/auth", tags=["Autenticación"])

# ============================================================
# ✅ LOGIN PARA CLIENTES (APP MÓVIL)
# ============================================================
@router.post("/login-cliente")
def login_cliente(cedula: str, pin: str, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.cedula == cedula).first()
    if not cliente or cliente.pin != pin:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    # Actualizar último acceso
    cliente.ultimo_acceso = datetime.now()
    db.commit()
    
    # Crear token
    token = create_access_token(data={"sub": str(cliente.id), "rol": "cliente"})
    return {
        "access_token": token,
        "token_type": "bearer",
        "cliente": {
            "id": cliente.id,
            "nombre": cliente.nombre,
            "cedula": cliente.cedula,
            "nivel": cliente.nivel,
            "score": cliente.score
        }
    }

# ============================================================
# ✅ LOGIN PARA ADMINISTRADORES (PANEL WEB)
# ============================================================
@router.post("/login")
def login_admin(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.username == form_data.username).first()
    if not usuario or not verify_password(form_data.password, usuario.password):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    if not usuario.activo:
        raise HTTPException(status_code=403, detail="Usuario inactivo")
    
    token = create_access_token(data={"sub": usuario.username, "rol": usuario.rol})
    return {
        "access_token": token,
        "token_type": "bearer",
        "rol": usuario.rol,
        "username": usuario.username,
        "nombre": usuario.nombre
    }

# ============================================================
# ✅ REGISTRO DE ADMINISTRADOR (SOLO PARA PRIMERA VEZ)
# ============================================================
@router.post("/registro")
def registrar_usuario(username: str, password: str, rol: str = "usuario", db: Session = Depends(get_db)):
    existe = db.query(Usuario).filter(Usuario.username == username).first()
    if existe:
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    
    nuevo = Usuario(
        username=username,
        password=hash_password(password),
        rol=rol,
        nombre=username
    )
    db.add(nuevo)
    db.commit()
    return {"mensaje": "Usuario creado", "username": username, "rol": rol}

# ============================================================
# ✅ VERIFICAR TOKEN
# ============================================================
@router.get("/verificar")
def verificar_token(current_user: Usuario = Depends(get_current_admin)):
    return {"valid": True, "username": current_user.username, "rol": current_user.rol}