"""
🔒 FinanCoop - Router de Autenticación Ultra-Seguro
Login Admin (Frontend Vue) + Login Cliente (App Móvil) + Login Biométrico (Huella)
"""
import logging  # <-- AGREGAR ESTA LÍNEA
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import Optional
import re
import random
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jose import jwt, JWTError, ExpiredSignatureError

from app.core.database import get_db
from app.modules.users.models import Cliente, Usuario
from app.modules.auth.models import TokenBlacklist
from app.core.security import (
    get_current_user,
    get_current_admin,
    create_access_token,
    create_refresh_token,
    get_current_cliente,
    hash_password,
    hash_pin,
    verify_password,
    verify_pin,
    _check_rate_limit,
    _record_failed_attempt,
    _record_successful_attempt,
    _hash_token,
    blacklist_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    SECRET_KEY,
    ALGORITHM
)
from app.core.audit import audit_login, registrar_auditoria  # ✅ NUEVO

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Autenticación"])

DUMMY_HASH = "$2b$12$LJ3m4ys3GZfnYMz8kVsKaOmLp1GpGmB0qJX3PzV3QXjKtHqKw8m5u"

# ============================================================
# 📧 CONFIGURACIÓN SMTP
# ============================================================
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")

# ============================================================
# 📋 MODELOS Pydantic
# ============================================================

class LoginClienteRequest(BaseModel):
    """Login para app móvil - Cédula + PIN (6 caracteres alfanumérico)"""
    cedula: str = Field(..., min_length=6, max_length=20, pattern=r"^[0-9Vv-]+$")
    pin: str = Field(..., min_length=4, max_length=6, pattern=r"^[A-Z0-9]+$")
    
    @validator('cedula')
    def validate_cedula(cls, v):
        v = v.strip().upper()
        if not re.match(r"^[0-9Vv-]+$", v):
            raise ValueError("Cédula contiene caracteres inválidos")
        return v
    
    @validator('pin')
    def validate_pin(cls, v):
        if len(v) < 4:
            raise ValueError("PIN debe tener al menos 4 caracteres")
        return v.strip().upper()

class LoginAdminRequest(BaseModel):
    """Login para panel admin - Username + Password (JSON)"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)

class LoginBiometricoRequest(BaseModel):
    """Login con huella dactilar - Cédula + confirmación biométrica del dispositivo"""
    cedula: str = Field(..., min_length=6, max_length=20, pattern=r"^[0-9Vv-]+$")
    biometric_verified: bool = True
    device_id: Optional[str] = None
    
    @validator('cedula')
    def validate_cedula(cls, v):
        v = v.strip().upper()
        if not re.match(r"^[0-9Vv-]+$", v):
            raise ValueError("Cédula contiene caracteres inválidos")
        return v

class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=20)

class PasswordChangeRequest(BaseModel):
    old_password: str = Field(..., min_length=8, max_length=128)
    new_password: str = Field(..., min_length=12, max_length=128)
    
    @validator('new_password')
    def validate_password_strength(cls, v):
        if not re.search(r"[A-Z]", v):
            raise ValueError("Debe contener al menos una mayúscula")
        if not re.search(r"[a-z]", v):
            raise ValueError("Debe contener al menos una minúscula")
        if not re.search(r"[0-9]", v):
            raise ValueError("Debe contener al menos un número")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Debe contener al menos un carácter especial")
        return v

class RegistroAdminRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(..., min_length=12, max_length=128)
    rol: str = Field(default="cajero", pattern=r"^(admin_central|admin_tienda|cajero)$")
    nombre: str = Field(..., min_length=2, max_length=100)
    email: str = Field(default="", max_length=200)
    tienda_id: int = None

# ✅ MODELOS PARA RECUPERACIÓN DE PIN (6 caracteres)
class SolicitarCodigoRequest(BaseModel):
    """Solicitar código de recuperación por correo"""
    cedula: str = Field(..., min_length=6, max_length=20, pattern=r"^[0-9Vv-]+$")

class VerificarCodigoRequest(BaseModel):
    """Verificar código de recuperación"""
    cedula: str = Field(..., min_length=6, max_length=20)
    codigo: str = Field(..., min_length=4, max_length=6)

class CambiarPinRequest(BaseModel):
    """Cambiar PIN después de verificar código (6 caracteres alfanumérico)"""
    nuevo_pin: str = Field(..., min_length=4, max_length=6, pattern=r"^[A-Z0-9]+$")

# Almacenamiento temporal de códigos
codigos_recuperacion = {}

# ============================================================
# 📧 FUNCIÓN DE ENVÍO DE CORREO (SMTP GMAIL)
# ============================================================

def enviar_correo_recuperacion(destinatario: str, nombre: str, codigo: str) -> bool:
    """Envía un correo con el código de recuperación usando SMTP Gmail"""
    try:
        if not SMTP_USER or not SMTP_PASS:
            logger.error("❌ SMTP no configurado (SMTP_USER o SMTP_PASS vacíos)")
            return False
        
        msg = MIMEMultipart()
        msg["From"] = f"FinanCoop <{SMTP_USER}>"
        msg["To"] = destinatario
        msg["Subject"] = "🔐 Recuperación de PIN - FinanCoop"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background: #0a0e1a; padding: 20px; margin: 0;">
            <div style="max-width: 400px; margin: auto; background: #1a1f3a; border-radius: 20px; overflow: hidden; border: 1px solid rgba(255,255,255,0.08);">
                <div style="background: linear-gradient(135deg, #4facfe, #6366f1); padding: 20px; text-align: center;">
                    <h1 style="color: white; margin: 0; font-size: 22px;">🔐 FinanCoop</h1>
                    <p style="color: rgba(255,255,255,0.8); margin: 5px 0 0; font-size: 13px;">Recuperación de PIN</p>
                </div>
                <div style="padding: 25px;">
                    <p style="color: #fff; font-size: 14px;">Hola <strong>{nombre}</strong>,</p>
                    <p style="color: #ccc; font-size: 13px;">Has solicitado recuperar tu PIN de acceso a la app FinanCoop.</p>
                    <div style="background: #0a0e1a; padding: 20px; border-radius: 12px; text-align: center; margin: 20px 0; border: 1px solid rgba(79,172,254,0.2);">
                        <p style="color: #888; font-size: 11px; margin: 0 0 8px;">TU CÓDIGO DE RECUPERACIÓN</p>
                        <span style="font-size: 36px; font-weight: bold; color: #4facfe; letter-spacing: 8px;">{codigo}</span>
                    </div>
                    <p style="color: #888; font-size: 11px;">⏰ Este código expira en <strong style="color: #ffd54f;">30 minutos</strong>.</p>
                    <p style="color: #666; font-size: 10px; margin-top: 20px;">Si no solicitaste esto, ignora este mensaje.</p>
                </div>
                <div style="background: rgba(0,0,0,0.2); padding: 12px; text-align: center;">
                    <p style="color: #555; font-size: 10px; margin: 0;">FinanCoop • Cecosesola • v2.0</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, "html"))
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        
        logger.info(f"📧 Correo enviado a {destinatario}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error enviando correo: {e}")
        return False

# ============================================================
# 🔐 LOGIN ADMIN - JSON
# ============================================================

@router.post("/login-json")
@audit_login()  # ✅ NUEVO
def login_admin_json(
    request_data: LoginAdminRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Login para administradores del panel web (JSON)."""
    username = request_data.username.lower().strip()
    password = request_data.password
    
    client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    rate_key = f"admin:{username}:{client_ip}"
    
    if not _check_rate_limit(rate_key):
        raise HTTPException(status_code=429, detail="Demasiados intentos fallidos. Intente más tarde.")
    
    usuario = db.query(Usuario).filter(Usuario.username == username).first()
    
    if not usuario:
        verify_password(password, DUMMY_HASH)
        _record_failed_attempt(rate_key)
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    if not verify_password(password, usuario.password):
        _record_failed_attempt(rate_key)
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    if not usuario.activo:
        _record_failed_attempt(rate_key)
        raise HTTPException(status_code=403, detail="Usuario inactivo")
    
    _record_successful_attempt(rate_key)
    usuario.ultimo_acceso = datetime.now(timezone.utc)
    db.commit()
    
    access_token = create_access_token(data={"sub": usuario.username, "rol": usuario.rol})
    refresh_token = create_refresh_token(usuario.username, usuario.rol)
    
    return {
        "access_token": access_token, "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60, "refresh_token": refresh_token,
        "rol": usuario.rol, "username": usuario.username, "nombre": usuario.nombre,
        "tienda_id": usuario.tienda_id,
        "tienda_nombre": usuario.tienda.nombre if usuario.tienda else None
    }

# ============================================================
# 🔐 LOGIN ADMIN - FORM
# ============================================================

@router.post("/login")
@audit_login()  # ✅ NUEVO
def login_admin_form(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login admin con form-urlencoded (Swagger UI / compatibilidad)."""
    username = form_data.username.lower().strip()
    password = form_data.password
    
    client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    rate_key = f"admin:{username}:{client_ip}"
    
    if not _check_rate_limit(rate_key):
        raise HTTPException(status_code=429, detail="Demasiados intentos fallidos")
    
    usuario = db.query(Usuario).filter(Usuario.username == username).first()
    
    if not usuario:
        verify_password(password, DUMMY_HASH)
        _record_failed_attempt(rate_key)
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    if not verify_password(password, usuario.password):
        _record_failed_attempt(rate_key)
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    if not usuario.activo:
        _record_failed_attempt(rate_key)
        raise HTTPException(status_code=403, detail="Usuario inactivo")
    
    _record_successful_attempt(rate_key)
    usuario.ultimo_acceso = datetime.now(timezone.utc)
    db.commit()
    
    access_token = create_access_token(data={"sub": usuario.username, "rol": usuario.rol})
    refresh_token = create_refresh_token(usuario.username, usuario.rol)
    
    return {
        "access_token": access_token, "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60, "refresh_token": refresh_token,
        "rol": usuario.rol, "username": usuario.username, "nombre": usuario.nombre,
        "tienda_id": usuario.tienda_id,
        "tienda_nombre": usuario.tienda.nombre if usuario.tienda else None
    }

# ============================================================
# 🔐 LOGIN CLIENTE (App Móvil)
# ============================================================

@router.post("/login-cliente")
@audit_login()  # ✅ NUEVO
def login_cliente(
    request_data: LoginClienteRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Login para clientes de la app móvil con cédula + PIN."""
    cedula = request_data.cedula
    pin = request_data.pin
    
    client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    rate_key = f"cliente:{cedula}:{client_ip}"
    
    if not _check_rate_limit(rate_key):
        raise HTTPException(status_code=429, detail="Demasiados intentos fallidos")
    
    cliente = db.query(Cliente).filter(Cliente.cedula == cedula).first()
    
    if not cliente:
        verify_pin(pin, DUMMY_HASH)
        _record_failed_attempt(rate_key)
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    if cliente.estado != "aprobado":
        _record_failed_attempt(rate_key)
        raise HTTPException(status_code=403, detail="Cuenta pendiente de aprobación")
    
    if not cliente.pin_hash:
        if cliente.pin and cliente.pin == pin:
            cliente.pin_hash = hash_pin(pin)
            cliente.pin = None
            db.commit()
        else:
            _record_failed_attempt(rate_key)
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    else:
        if not verify_pin(pin, cliente.pin_hash):
            _record_failed_attempt(rate_key)
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    _record_successful_attempt(rate_key)
    cliente.ultimo_acceso = datetime.now(timezone.utc)
    db.commit()
    
    access_token = create_access_token(data={"sub": str(cliente.id), "rol": "cliente"})
    refresh_token = create_refresh_token(str(cliente.id), "cliente")
    
    return {
        "access_token": access_token, "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60, "refresh_token": refresh_token,
        "cliente": {
            "id": cliente.id, "nombre": cliente.nombre,
            "cedula": cliente.cedula[:4] + "****", "nivel": cliente.nivel,
            "score": cliente.score, "telefono": cliente.telefono
        }
    }

# ============================================================
# 🔐 LOGIN BIOMÉTRICO (Huella Dactilar)
# ============================================================

@router.post("/login-biometrico")
@audit_login()  # ✅ NUEVO
def login_biometrico(
    request_data: LoginBiometricoRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Login con autenticación biométrica verificada por el dispositivo.
    La huella ya fue validada por el sistema operativo del teléfono.
    Solo se requiere la cédula para identificar al usuario.
    """
    cedula = request_data.cedula
    
    client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    rate_key = f"biometric:{cedula}:{client_ip}"
    
    if not _check_rate_limit(rate_key):
        raise HTTPException(status_code=429, detail="Demasiados intentos fallidos")
    
    cliente = db.query(Cliente).filter(Cliente.cedula == cedula).first()
    
    if not cliente:
        _record_failed_attempt(rate_key)
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    if cliente.estado != "aprobado":
        _record_failed_attempt(rate_key)
        raise HTTPException(status_code=403, detail="Cuenta pendiente de aprobación")
    
    _record_successful_attempt(rate_key)
    cliente.ultimo_acceso = datetime.now(timezone.utc)
    db.commit()
    
    access_token = create_access_token(data={"sub": str(cliente.id), "rol": "cliente"})
    refresh_token = create_refresh_token(str(cliente.id), "cliente")
    
    logger.info(f"✅ Login biométrico exitoso: {cliente.nombre} (dispositivo: {request_data.device_id or 'desconocido'})")
    
    return {
        "access_token": access_token, "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60, "refresh_token": refresh_token,
        "cliente": {
            "id": cliente.id, "nombre": cliente.nombre,
            "cedula": cliente.cedula[:4] + "****", "nivel": cliente.nivel,
            "score": cliente.score, "telefono": cliente.telefono
        }
    }

# ============================================================
# 🔄 REFRESH TOKEN
# ============================================================

@router.post("/refresh")
def refresh_token(request_data: RefreshTokenRequest, db: Session = Depends(get_db)):
    from app.auth import _decode_and_validate_token
    
    try:
        payload = _decode_and_validate_token(request_data.refresh_token, db)
    except HTTPException:
        raise HTTPException(status_code=401, detail="Refresh token inválido")
    
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Token no es refresh")
    
    sub = payload.get("sub")
    rol = payload.get("rol")
    
    blacklist_token(payload["jti"], datetime.fromtimestamp(payload["exp"], tz=timezone.utc), db)
    
    new_access = create_access_token(data={"sub": sub, "rol": rol})
    new_refresh = create_refresh_token(sub, rol)
    
    return {
        "access_token": new_access, "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60, "refresh_token": new_refresh
    }

# ============================================================
# 🔍 VERIFICAR TOKEN
# ============================================================

@router.get("/verificar")
def verificar_token(current_user: Usuario = Depends(get_current_admin)):
    return {
        "valid": True, "username": current_user.username,
        "rol": current_user.rol, "nombre": current_user.nombre,
        "tienda_id": current_user.tienda_id,
        "tienda_nombre": current_user.tienda.nombre if current_user.tienda else None
    }

# ============================================================
# 📝 REGISTRO DE ADMIN
# ============================================================

@router.post("/registro")
def registrar_admin(
    request_data: RegistroAdminRequest,
    current_admin: Usuario = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    existe = db.query(Usuario).filter(Usuario.username == request_data.username.lower()).first()
    if existe:
        raise HTTPException(status_code=409, detail="El usuario ya existe")
    
    nuevo = Usuario(
        username=request_data.username.lower(),
        password=hash_password(request_data.password),
        rol=request_data.rol, nombre=request_data.nombre,
        email=request_data.email, tienda_id=request_data.tienda_id,
        activo=True, creado_por=current_admin.username
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    
    return {
        "mensaje": "Usuario creado", "username": nuevo.username,
        "rol": nuevo.rol, "nombre": nuevo.nombre, "tienda_id": nuevo.tienda_id
    }

# ============================================================
# 🔒 CAMBIAR CONTRASEÑA
# ============================================================

@router.post("/cambiar-password")
def cambiar_password(
    request_data: PasswordChangeRequest,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(request_data.old_password, current_user.password):
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")
    
    if request_data.old_password == request_data.new_password:
        raise HTTPException(status_code=400, detail="La nueva contraseña debe ser diferente")
    
    current_user.password = hash_password(request_data.new_password)
    db.commit()
    
    return {"mensaje": "Contraseña actualizada"}

# ============================================================
# 🚪 LOGOUT
# ============================================================

@router.post("/logout")
@audit_login(logout=True)  # ✅ NUEVO
def logout(
    request: Request,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], 
                            audience="financoop-api", issuer="financoop-backend")
        blacklist_token(payload["jti"], datetime.fromtimestamp(payload["exp"], tz=timezone.utc), db)
        return {"mensaje": "Sesión cerrada"}
    except:
        return {"mensaje": "Sesión cerrada"}

# ============================================================
# 📧 RECUPERACIÓN DE PIN POR CORREO
# ============================================================

@router.post("/recuperar-pin/solicitar-codigo")
def solicitar_codigo_recuperacion(
    request_data: SolicitarCodigoRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Solicitar código de recuperación de PIN por correo electrónico."""
    cedula = request_data.cedula.strip().upper()
    
    client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    rate_key = f"recuperar_pin:{cedula}:{client_ip}"
    
    if not _check_rate_limit(rate_key):
        raise HTTPException(status_code=429, detail="Demasiados intentos. Intente en 15 minutos.")
    
    cliente = db.query(Cliente).filter(Cliente.cedula == cedula).first()
    
    if not cliente:
        import time
        time.sleep(0.5)
        return {"mensaje": "Si la cédula está registrada, recibirás un código en tu correo", "success": True}
    
    if not cliente.email:
        raise HTTPException(
            status_code=400, 
            detail="No tienes un correo electrónico registrado. Visita tu cooperativa más cercana para recuperar tu PIN."
        )
    
    codigo = str(random.randint(100000, 999999))
    
    codigos_recuperacion[cedula] = {
        "codigo": codigo,
        "cliente_id": cliente.id,
        "expiracion": datetime.now(timezone.utc) + timedelta(minutes=30),
        "intentos": 0
    }
    
    correo_enviado = enviar_correo_recuperacion(cliente.email, cliente.nombre, codigo)
    
    if not correo_enviado:
        logger.warning(f"⚠️ No se pudo enviar correo. Código para {cliente.nombre}: {codigo}")
        print(f"\n{'='*50}")
        print(f"📧 RECUPERACIÓN PIN - {cliente.nombre}")
        print(f"📧 Email: {cliente.email}")
        print(f"🔑 Código: {codigo}")
        print(f"{'='*50}\n")
    
    _record_failed_attempt(rate_key)
    
    email_mascarado = cliente.email[0:3] + "***" + cliente.email[cliente.email.index("@")-2:]
    
    return {
        "mensaje": f"Código enviado a {email_mascarado}. Revisa tu bandeja de entrada.",
        "success": True
    }


@router.post("/recuperar-pin/verificar-codigo")
def verificar_codigo_recuperacion(
    request_data: VerificarCodigoRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Verificar código de recuperación y devolver token temporal."""
    cedula = request_data.cedula.strip().upper()
    codigo = request_data.codigo.strip()
    
    datos = codigos_recuperacion.get(cedula)
    
    if not datos:
        raise HTTPException(status_code=400, detail="Código no solicitado o expirado")
    
    if datetime.now(timezone.utc) > datos["expiracion"]:
        del codigos_recuperacion[cedula]
        raise HTTPException(status_code=400, detail="Código expirado. Solicite uno nuevo.")
    
    if datos["intentos"] >= 3:
        del codigos_recuperacion[cedula]
        raise HTTPException(status_code=400, detail="Demasiados intentos. Solicite un nuevo código.")
    
    datos["intentos"] += 1
    
    if datos["codigo"] != codigo:
        raise HTTPException(status_code=400, detail="Código incorrecto")
    
    cliente = db.query(Cliente).filter(Cliente.id == datos["cliente_id"]).first()
    
    if not cliente:
        raise HTTPException(status_code=400, detail="Cliente no encontrado")
    
    token_temp = create_access_token(
        data={
            "sub": str(cliente.id),
            "rol": "cliente",
            "type": "pin_reset",
            "cedula": cedula
        },
        expires_delta=timedelta(minutes=5)
    )
    
    del codigos_recuperacion[cedula]
    
    return {
        "mensaje": "Código verificado correctamente",
        "token_temp": token_temp,
        "success": True
    }


@router.post("/recuperar-pin/cambiar")
def cambiar_pin_recuperacion(
    request_data: CambiarPinRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Cambiar PIN usando token temporal de recuperación."""
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "")
    
    if not token:
        raise HTTPException(status_code=401, detail="Token requerido")
    
    try:
        payload = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM],
            audience="financoop-api", issuer="financoop-backend"
        )
        
        if payload.get("type") != "pin_reset":
            raise HTTPException(status_code=401, detail="Token no válido para esta operación")
        
        cliente_id = payload.get("sub")
        
        if not cliente_id:
            raise HTTPException(status_code=401, detail="Token inválido")
        
        cliente = db.query(Cliente).filter(Cliente.id == int(cliente_id)).first()
        
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
        nuevo_pin = request_data.nuevo_pin.strip().upper()
        cliente.pin_hash = hash_pin(nuevo_pin)
        db.commit()
        
        logger.info(f"🔐 PIN actualizado para {cliente.nombre}")
        
        blacklist_token(
            payload["jti"], 
            datetime.fromtimestamp(payload["exp"], tz=timezone.utc), 
            db
        )
        
        return {
            "mensaje": "PIN actualizado correctamente",
            "success": True
        }
        
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado. Solicite un nuevo código.")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
    except Exception as e:
        logger.error(f"Error cambiando PIN: {e}")
        raise HTTPException(status_code=500, detail="Error interno")