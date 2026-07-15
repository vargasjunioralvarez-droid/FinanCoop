# backend/app/routers/clientes.py
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Cliente, Financiamiento, Cuota
from app.utils import (
    calcular_nivel, actualizar_score_cliente, generar_pin, 
    calcular_usado_disponible, obtener_tasa_actual, generar_token,
    enviar_pin_cliente
)
from app.auth import get_current_admin, get_current_user
from datetime import datetime
import httpx
import os

router = APIRouter(prefix="/clientes", tags=["Clientes"])

# ============================================================
# SCHEMAS
# ============================================================
class ClienteCreate(BaseModel):
    nombre: str
    cedula: str
    telefono: str
    email: Optional[str] = ""
    direccion: Optional[str] = ""
    referencia_nombre: Optional[str] = ""
    referencia_telefono: Optional[str] = ""
    referencia_parentesco: Optional[str] = ""

class ClienteAprobar(BaseModel):
    cliente_id: int

class ClienteUpdate(BaseModel):
    nombre: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    direccion: Optional[str] = None

# ============================================================
# CLOUDFLARE
# ============================================================
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")

async def subir_imagen_cloudflare(archivo_bytes: bytes, nombre_archivo: str) -> str | None:
    try:
        url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/images/v1"
        files = {'file': (nombre_archivo, archivo_bytes, 'image/jpeg')}
        headers = {'Authorization': f'Bearer {CLOUDFLARE_API_TOKEN}'}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, files=files, timeout=30.0)
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    image_url = result['result']['variants'][0]
                    print(f"✅ Imagen subida a Cloudflare: {image_url}")
                    return image_url
            return None
    except Exception as e:
        print(f"❌ Error subiendo a Cloudflare: {e}")
        return None

# ============================================================
# ✅ CREAR CLIENTE - CON SOPORTE PARA FORM DATA Y FOTO
# ============================================================
@router.post("")
async def crear_cliente(
    nombre: str = Form(...),
    cedula: str = Form(...),
    telefono: str = Form(...),
    email: Optional[str] = Form(""),
    direccion: Optional[str] = Form(""),
    referencia_nombre: Optional[str] = Form(""),
    referencia_telefono: Optional[str] = Form(""),
    referencia_parentesco: Optional[str] = Form(""),
    cedula_foto: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    try:
        print(f"📝 Registrando cliente: {cedula}")
        print(f"📸 Foto recibida: {cedula_foto.filename if cedula_foto else 'No'}")

        # Verificar si ya existe
        existe = db.query(Cliente).filter(Cliente.cedula == cedula).first()
        if existe:
            return {"error": f"Cliente con cédula {cedula} ya existe", "success": False}

        # Procesar foto si existe
        url_cedula = None
        if cedula_foto and cedula_foto.size > 0:
            try:
                contenido = await cedula_foto.read()
                url_cedula = await subir_imagen_cloudflare(contenido, f"cedula_{cedula}.jpg")
                if url_cedula:
                    print(f"✅ Foto subida: {url_cedula}")
                else:
                    print("⚠️ No se pudo subir la foto a Cloudflare")
            except Exception as e:
                print(f"⚠️ Error procesando foto: {e}")

        # Crear cliente
        db_cliente = Cliente(
            nombre=nombre,
            cedula=cedula,
            telefono=telefono,
            email=email or "",
            direccion=direccion or "",
            referencia_nombre=referencia_nombre or "",
            referencia_telefono=referencia_telefono or "",
            referencia_parentesco=referencia_parentesco or "",
            url_cedula=url_cedula,
            pin=generar_pin(),
            token_app=generar_token(),
            estado="pendiente",
            nivel="nuevo",
            score=0
        )
        
        db.add(db_cliente)
        db.commit()
        db.refresh(db_cliente)

        print(f"✅ Cliente registrado (PENDIENTE): ID {db_cliente.id} - {db_cliente.nombre}")

        return {
            "success": True,
            "id": db_cliente.id,
            "mensaje": "✅ Registro exitoso. Tu cuenta está en verificación. Recibirás un SMS cuando sea aprobada.",
            "cliente": {
                "id": db_cliente.id,
                "nombre": db_cliente.nombre,
                "cedula": db_cliente.cedula,
                "telefono": db_cliente.telefono,
                "email": db_cliente.email,
                "estado": "pendiente",
                "url_cedula": url_cedula
            }
        }

    except Exception as e:
        print(f"❌ Error en registro: {e}")
        db.rollback()
        return {"error": str(e), "success": False}

# ============================================================
# CREAR CLIENTE VIA JSON (BACKUP)
# ============================================================
@router.post("/json")
async def crear_cliente_json(
    cliente_data: ClienteCreate,
    db: Session = Depends(get_db)
):
    try:
        print(f"📝 Registrando cliente (JSON): {cliente_data.cedula}")
        
        existe = db.query(Cliente).filter(Cliente.cedula == cliente_data.cedula).first()
        if existe:
            return {"error": f"Cliente con cédula {cliente_data.cedula} ya existe", "success": False}

        db_cliente = Cliente(
            nombre=cliente_data.nombre,
            cedula=cliente_data.cedula,
            telefono=cliente_data.telefono,
            email=cliente_data.email or "",
            direccion=cliente_data.direccion or "",
            referencia_nombre=cliente_data.referencia_nombre or "",
            referencia_telefono=cliente_data.referencia_telefono or "",
            referencia_parentesco=cliente_data.referencia_parentesco or "",
            pin=generar_pin(),
            token_app=generar_token(),
            estado="pendiente",
            nivel="nuevo",
            score=0
        )
        
        db.add(db_cliente)
        db.commit()
        db.refresh(db_cliente)

        print(f"✅ Cliente registrado (PENDIENTE): {db_cliente.id}")

        return {
            "success": True,
            "id": db_cliente.id,
            "mensaje": "Registro exitoso. Tu cuenta está en verificación.",
            "cliente": {
                "id": db_cliente.id,
                "nombre": db_cliente.nombre,
                "cedula": db_cliente.cedula,
                "estado": "pendiente"
            }
        }

    except Exception as e:
        print(f"❌ Error en registro: {e}")
        return {"error": str(e), "success": False}

# ============================================================
# APROBAR CLIENTE Y ENVIAR PIN (SOLO ADMIN)
# ============================================================
@router.post("/aprobar")
async def aprobar_cliente(
    data: ClienteAprobar,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    try:
        cliente = db.query(Cliente).filter(Cliente.id == data.cliente_id).first()
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
        if cliente.estado == "aprobado":
            return {"error": "Cliente ya está aprobado", "success": False}
        
        if not cliente.pin:
            cliente.pin = generar_pin()
        
        cliente.estado = "aprobado"
        db.commit()
        
        try:
            enviar_pin_cliente(
                telefono=cliente.telefono,
                nombre=cliente.nombre,
                cedula=cliente.cedula,
                pin=cliente.pin
            )
            sms_enviado = True
        except Exception as e:
            print(f"⚠️ Error enviando PIN: {e}")
            sms_enviado = False
        
        return {
            "success": True,
            "mensaje": f"Cliente {cliente.nombre} aprobado.",
            "sms_enviado": sms_enviado,
            "cliente": {
                "id": cliente.id,
                "nombre": cliente.nombre,
                "cedula": cliente.cedula,
                "telefono": cliente.telefono,
                "estado": "aprobado",
                "pin": cliente.pin
            }
        }
        
    except Exception as e:
        print(f"❌ Error aprobando cliente: {e}")
        return {"error": str(e), "success": False}

# ============================================================
# LISTAR CLIENTES
# ============================================================
@router.get("")
def listar_clientes(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    clientes = db.query(Cliente).all()
    return [
        {
            "id": c.id,
            "nombre": c.nombre,
            "cedula": c.cedula,
            "telefono": c.telefono,
            "email": c.email,
            "direccion": c.direccion,
            "nivel": c.nivel,
            "score": c.score,
            "estado": c.estado or "pendiente",
            "url_cedula": c.url_cedula,
            "pin": c.pin if current_user.rol == "admin" else None
        }
        for c in clientes
    ]

# ============================================================
# OBTENER CLIENTE POR ID
# ============================================================
@router.get("/{id}")
def obtener_cliente(
    id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    cliente = db.query(Cliente).filter(Cliente.id == id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    return {
        "id": cliente.id,
        "nombre": cliente.nombre,
        "cedula": cliente.cedula,
        "telefono": cliente.telefono,
        "email": cliente.email,
        "direccion": cliente.direccion,
        "referencia_nombre": cliente.referencia_nombre,
        "referencia_telefono": cliente.referencia_telefono,
        "referencia_parentesco": cliente.referencia_parentesco,
        "score": cliente.score,
        "nivel": cliente.nivel,
        "total_compras": cliente.total_compras,
        "url_cedula": cliente.url_cedula,
        "estado": cliente.estado or "pendiente",
        "pin": cliente.pin if current_user.rol == "admin" else None
    }

# ============================================================
# ACTUALIZAR CLIENTE
# ============================================================
@router.put("/{id}")
def actualizar_cliente(
    id: int,
    cliente_data: ClienteUpdate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    cliente = db.query(Cliente).filter(Cliente.id == id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    if cliente_data.nombre is not None:
        cliente.nombre = cliente_data.nombre
    if cliente_data.telefono is not None:
        cliente.telefono = cliente_data.telefono
    if cliente_data.email is not None:
        cliente.email = cliente_data.email
    if cliente_data.direccion is not None:
        cliente.direccion = cliente_data.direccion
    
    db.commit()
    db.refresh(cliente)
    
    return {
        "success": True,
        "mensaje": "Cliente actualizado",
        "cliente": {
            "id": cliente.id,
            "nombre": cliente.nombre,
            "cedula": cliente.cedula,
            "telefono": cliente.telefono,
            "email": cliente.email,
            "direccion": cliente.direccion
        }
    }

# ============================================================
# ELIMINAR CLIENTE
# ============================================================
@router.delete("/{id}")
def eliminar_cliente(
    id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    cliente = db.query(Cliente).filter(Cliente.id == id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    nombre = cliente.nombre
    
    # Eliminar financiamientos y cuotas asociadas
    financiamientos = db.query(Financiamiento).filter(Financiamiento.cliente_id == id).all()
    for fin in financiamientos:
        db.query(Cuota).filter(Cuota.financiamiento_id == fin.id).delete()
        db.delete(fin)
    
    db.delete(cliente)
    db.commit()
    
    return {
        "success": True,
        "mensaje": f"Cliente {nombre} eliminado correctamente"
    }

# ============================================================
# SUBIR FOTO (ENDOPOINT SEPARADO)
# ============================================================
@router.post("/{id}/foto")
async def subir_foto_cedula(
    id: int,
    cedula_foto: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    cliente = db.query(Cliente).filter(Cliente.id == id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    try:
        contenido = await cedula_foto.read()
        url_cedula = await subir_imagen_cloudflare(contenido, f"cedula_{cliente.cedula}.jpg")
        
        if url_cedula:
            cliente.url_cedula = url_cedula
            db.commit()
            return {"success": True, "url": url_cedula}
        else:
            return {"success": False, "error": "No se pudo subir la imagen"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================================
# BUSCAR CLIENTE POR CÉDULA
# ============================================================
@router.get("/buscar/{cedula}")
def buscar_cliente_por_cedula(cedula: str, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.cedula == cedula).first()
    if not cliente:
        return {"error": "Cliente no encontrado", "encontrado": False}
    
    actualizar_score_cliente(cliente, db)
    db.refresh(cliente)
    
    nivel, config = calcular_nivel(cliente.score)
    tasa = obtener_tasa_actual(db)
    disponible = calcular_usado_disponible(cliente.id, db)
    
    return {
        "encontrado": True,
        "id": cliente.id,
        "nombre": cliente.nombre,
        "cedula": cliente.cedula,
        "telefono": cliente.telefono,
        "email": cliente.email,
        "direccion": cliente.direccion,
        "referencia_nombre": cliente.referencia_nombre,
        "referencia_telefono": cliente.referencia_telefono,
        "referencia_parentesco": cliente.referencia_parentesco,
        "score": cliente.score,
        "nivel": cliente.nivel,
        "total_compras": cliente.total_compras,
        "url_cedula": cliente.url_cedula,
        "estado": cliente.estado or "pendiente",
        "limite_disponible": disponible,
        "nivel_config": {
            "monto_max_usd": config["monto_max_usd"],
            "monto_max_bs": round(config["monto_max_usd"] * tasa, 2),
            "entrada_pct": config["entrada_pct"],
            "financia_pct": config["financia_pct"],
            "cuotas_base": config["cuotas_base"],
            "cuotas_max": config["cuotas_max"],
            "mora_diaria": config["mora_diaria"],
            "aprobacion_extra": config["aprobacion_extra"]
        }
    }