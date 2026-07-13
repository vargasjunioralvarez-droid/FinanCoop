# backend/app/routers/clientes.py
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
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
# ✅ SCHEMA PARA JSON
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

# ============================================================
# ✅ CONFIGURACIÓN DE CLOUDFLARE
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
# ✅ CREAR CLIENTE (RECIBE JSON) - PÚBLICO
# ============================================================
@router.post("")
async def crear_cliente(
    cliente_data: ClienteCreate,
    db: Session = Depends(get_db)
):
    try:
        print(f"📝 Registrando cliente: {cliente_data.cedula}")
        
        # Verificar si ya existe
        existe = db.query(Cliente).filter(Cliente.cedula == cliente_data.cedula).first()
        if existe:
            return {"error": f"Cliente con cédula {cliente_data.cedula} ya existe", "success": False}

        # Crear cliente
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
            token_app=generar_token()
        )
        
        db.add(db_cliente)
        db.commit()
        db.refresh(db_cliente)

        print(f"✅ Cliente registrado: {db_cliente.id} - {db_cliente.nombre}")

        # ✅ ENVIAR PIN (SMS)
        try:
            enviar_pin_cliente(
                telefono=db_cliente.telefono,
                nombre=db_cliente.nombre,
                cedula=db_cliente.cedula,
                pin=db_cliente.pin
            )
        except Exception as e:
            print(f"⚠️ Error enviando PIN: {e}")

        # ✅ RESPUESTA
        return {
            "success": True,
            "id": db_cliente.id,
            "mensaje": f"Cliente registrado exitosamente",
            "pin": db_cliente.pin,
            "cliente": {
                "id": db_cliente.id,
                "nombre": db_cliente.nombre,
                "cedula": db_cliente.cedula,
                "telefono": db_cliente.telefono,
                "email": db_cliente.email,
                "direccion": db_cliente.direccion,
                "nivel": db_cliente.nivel,
                "score": db_cliente.score
            }
        }

    except Exception as e:
        print(f"❌ Error en registro: {e}")
        return {"error": str(e), "success": False}

# ============================================================
# ✅ LISTAR CLIENTES - CUALQUIER USUARIO AUTENTICADO
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
            "score": c.score
        }
        for c in clientes
    ]

# ============================================================
# ✅ SUBIR FOTO DE CÉDULA (endpoint separado)
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
        url_cedula = await subir_imagen_cloudflare(contenido, cedula_foto.filename)
        
        if url_cedula:
            cliente.url_cedula = url_cedula
            db.commit()
            return {"success": True, "url": url_cedula}
        else:
            return {"success": False, "error": "No se pudo subir la imagen"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================================
# ✅ BUSCAR CLIENTE POR CÉDULA (PÚBLICO)
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

# El resto de funciones (obtener_cliente, editar_cliente, eliminar_cliente, etc.)
# se mantienen igual...