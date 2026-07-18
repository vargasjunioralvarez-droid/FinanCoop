# backend/app/routers/clientes.py
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Cliente, Financiamiento, Cuota, Pago
from app.utils import (
    calcular_nivel, actualizar_score_cliente, generar_pin, 
    calcular_usado_disponible, obtener_tasa_actual, generar_token,
    enviar_pin_cliente_completo
)
from app.auth import get_current_admin, get_current_user, get_current_user_optional, get_current_tienda, hash_pin
from datetime import datetime, timezone
import httpx
import os
import base64
import uuid
import logging

logger = logging.getLogger(__name__)
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

async def subir_imagen_cloudflare(archivo_bytes: bytes, nombre_archivo: str) -> Optional[str]:
    if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
        return None
    try:
        url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/images/v1"
        files = {'file': (nombre_archivo, archivo_bytes, 'image/jpeg')}
        headers = {'Authorization': f'Bearer {CLOUDFLARE_API_TOKEN}'}
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, files=files)
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    variants = result.get('result', {}).get('variants', [])
                    if variants:
                        return variants[0]
                    image_id = result.get('result', {}).get('id')
                    if image_id:
                        return f"https://imagedelivery.net/{CLOUDFLARE_ACCOUNT_ID}/{image_id}/public"
            return None
    except Exception as e:
        logger.error(f"Error Cloudflare: {e}")
        return None

async def subir_imagen_cloudflare_base64(base64_string: str, nombre_archivo: str) -> Optional[str]:
    try:
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        archivo_bytes = base64.b64decode(base64_string)
        return await subir_imagen_cloudflare(archivo_bytes, nombre_archivo)
    except:
        return None

# ============================================================
# ✅ CREAR CLIENTE (CON TIENDA AUTOMÁTICA)
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
    cedula_foto_base64: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    try:
        logger.info(f"📝 Registrando cliente: {cedula}")

        existe = db.query(Cliente).filter(Cliente.cedula == cedula).first()
        if existe:
            raise HTTPException(status_code=409, detail=f"Cliente con cédula {cedula} ya existe")

        url_cedula = None
        if cedula_foto and cedula_foto.size and cedula_foto.size > 0:
            try:
                contenido = await cedula_foto.read()
                if len(contenido) > 0:
                    url_cedula = await subir_imagen_cloudflare(contenido, f"cedula_{cedula}_{uuid.uuid4().hex[:8]}.jpg")
            except:
                pass
        elif cedula_foto_base64 and len(cedula_foto_base64) > 100:
            try:
                url_cedula = await subir_imagen_cloudflare_base64(cedula_foto_base64, f"cedula_{cedula}_{uuid.uuid4().hex[:8]}.jpg")
            except:
                pass

        pin_generado = generar_pin()
        pin_hasheado = hash_pin(pin_generado)

        tienda_id = None
        if current_user and hasattr(current_user, 'tienda_id') and current_user.tienda_id:
           tienda_id = current_user.tienda_id

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
            pin_hash=pin_hasheado,
            pin=None,
            token_app=generar_token(),
            estado="pendiente",
            nivel="nuevo",
            score=0,
            tienda_id=tienda_id
        )
        
        db.add(db_cliente)
        db.commit()
        db.refresh(db_cliente)

        logger.info(f"✅ Cliente registrado: ID {db_cliente.id} - Tienda: {tienda_id}")

        return {
            "success": True,
            "id": db_cliente.id,
            "mensaje": "✅ Registro exitoso. Tu cuenta está en verificación.",
            "pin": pin_generado,
            "cliente": {
                "id": db_cliente.id,
                "nombre": db_cliente.nombre,
                "cedula": db_cliente.cedula,
                "telefono": db_cliente.telefono,
                "email": db_cliente.email,
                "estado": "pendiente",
                "tienda_id": tienda_id,
                "url_cedula": url_cedula
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error en registro: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# CREAR CLIENTE VIA JSON
# ============================================================
@router.post("/json")
async def crear_cliente_json(
    cliente_data: ClienteCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        logger.info(f"📝 Registrando cliente (JSON): {cliente_data.cedula}")
        
        existe = db.query(Cliente).filter(Cliente.cedula == cliente_data.cedula).first()
        if existe:
            raise HTTPException(status_code=409, detail=f"Cliente con cédula {cliente_data.cedula} ya existe")

        pin_generado = generar_pin()
        pin_hasheado = hash_pin(pin_generado)

        tienda_id = None
        if hasattr(current_user, 'tienda_id') and current_user.tienda_id:
            tienda_id = current_user.tienda_id

        db_cliente = Cliente(
            nombre=cliente_data.nombre,
            cedula=cliente_data.cedula,
            telefono=cliente_data.telefono,
            email=cliente_data.email or "",
            direccion=cliente_data.direccion or "",
            referencia_nombre=cliente_data.referencia_nombre or "",
            referencia_telefono=cliente_data.referencia_telefono or "",
            referencia_parentesco=cliente_data.referencia_parentesco or "",
            pin_hash=pin_hasheado,
            pin=None,
            token_app=generar_token(),
            estado="pendiente",
            nivel="nuevo",
            score=0,
            tienda_id=tienda_id
        )
        
        db.add(db_cliente)
        db.commit()
        db.refresh(db_cliente)

        return {
            "success": True,
            "id": db_cliente.id,
            "mensaje": "Registro exitoso.",
            "pin": pin_generado,
            "cliente": {
                "id": db_cliente.id,
                "nombre": db_cliente.nombre,
                "cedula": db_cliente.cedula,
                "estado": "pendiente",
                "tienda_id": tienda_id
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error en registro JSON: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# APROBAR CLIENTE (SOLO admin_central)
# ============================================================
@router.post("/aprobar")
async def aprobar_cliente(
    data: ClienteAprobar,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    # 🔥 SOLO admin_central puede aprobar clientes
    if current_user.rol != "admin_central":
        raise HTTPException(status_code=403, detail="Solo el administrador central puede aprobar clientes")
    
    try:
        cliente = db.query(Cliente).filter(Cliente.id == data.cliente_id).first()
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
        if cliente.estado == "aprobado":
            raise HTTPException(status_code=400, detail="Cliente ya está aprobado")
        
        pin_generado = generar_pin()
        cliente.pin_hash = hash_pin(pin_generado)
        cliente.pin = None
        cliente.estado = "aprobado"
        db.commit()
        
        resultado_envio = enviar_pin_cliente_completo(
            telefono=cliente.telefono,
            nombre=cliente.nombre,
            cedula=cliente.cedula,
            pin=pin_generado
        )
        
        return {
            "success": True,
            "mensaje": f"Cliente {cliente.nombre} aprobado.",
            "envio": resultado_envio,
            "cliente": {
                "id": cliente.id,
                "nombre": cliente.nombre,
                "cedula": cliente.cedula,
                "telefono": cliente.telefono,
                "estado": "aprobado",
                "pin": pin_generado
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error aprobando cliente: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# LISTAR CLIENTES (CON FILTRO POR TIENDA)
# ============================================================
@router.get("")
def listar_clientes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    estado: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tienda_id: Optional[int] = Depends(get_current_tienda)
):
    query = db.query(Cliente)
    
    if tienda_id:
        query = query.filter(Cliente.tienda_id == tienda_id)
    
    if estado:
        query = query.filter(Cliente.estado == estado)
    
    total = query.count()
    clientes = query.order_by(Cliente.id.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "tienda_filtro": tienda_id,
        "clientes": [
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
                "tienda_id": c.tienda_id,
                "tienda_nombre": c.tienda.nombre if c.tienda else None,
                "pin": c.pin if current_user.rol == "admin_central" else "****",
                "ultimo_acceso": c.ultimo_acceso.isoformat() if c.ultimo_acceso else None,
                "creado_en": c.creado_en.isoformat() if c.creado_en else None
            }
            for c in clientes
        ]
    }

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
        "tienda_id": cliente.tienda_id,
        "tienda_nombre": cliente.tienda.nombre if cliente.tienda else None
    }

# ============================================================
# ACTUALIZAR CLIENTE (SOLO admin_central)
# ============================================================
@router.put("/{id}")
def actualizar_cliente(
    id: int,
    cliente_data: ClienteUpdate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    # 🔥 SOLO admin_central
    if current_admin.rol != "admin_central":
        raise HTTPException(status_code=403, detail="Solo el administrador central puede editar clientes")
    
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
# ELIMINAR CLIENTE (SOLO admin_central)
# ============================================================
@router.delete("/{id}")
def eliminar_cliente(
    id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    # 🔥 SOLO admin_central
    if current_admin.rol != "admin_central":
        raise HTTPException(status_code=403, detail="Solo el administrador central puede eliminar clientes")
    
    cliente = db.query(Cliente).filter(Cliente.id == id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    nombre = cliente.nombre
    
    financiamientos = db.query(Financiamiento).filter(Financiamiento.cliente_id == id).all()
    for fin in financiamientos:
        db.query(Pago).filter(Pago.financiamiento_id == fin.id).delete(synchronize_session=False)
        db.query(Cuota).filter(Cuota.financiamiento_id == fin.id).delete(synchronize_session=False)
        db.delete(fin)
    
    db.delete(cliente)
    db.commit()
    
    return {"success": True, "mensaje": f"Cliente {nombre} eliminado"}

# ============================================================
# BUSCAR CLIENTE POR CÉDULA (TODOS PUEDEN BUSCAR)
# ============================================================
@router.get("/buscar/{cedula}")
def buscar_cliente_por_cedula(cedula: str, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.cedula == cedula).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
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
        "score": cliente.score,
        "nivel": cliente.nivel,
        "total_compras": cliente.total_compras,
        "url_cedula": cliente.url_cedula,
        "estado": cliente.estado or "pendiente",
        "tienda_id": cliente.tienda_id,
        "tienda_nombre": cliente.tienda.nombre if cliente.tienda else None,
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

# ============================================================
# ESTADO DE CUENTA
# ============================================================
@router.get("/{id}/estado-cuenta")
def obtener_estado_cuenta(
    id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        cliente = db.query(Cliente).filter(Cliente.id == id).first()
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
        financiamientos = db.query(Financiamiento).filter(
            Financiamiento.cliente_id == id
        ).order_by(Financiamiento.id.desc()).all()
        
        total_financiado = 0
        total_pagado = 0
        total_deuda = 0
        total_cuotas = 0
        cuotas_pagadas = 0
        cuotas_pendientes = 0
        
        financiamientos_detalle = []
        hoy = datetime.now(timezone.utc)
        
        for fin in financiamientos:
            cuotas = db.query(Cuota).filter(Cuota.financiamiento_id == fin.id).all()
            pagadas = [c for c in cuotas if c.estado == "pagada"]
            pendientes = [c for c in cuotas if c.estado != "pagada"]
            
            monto_financiado = fin.monto_total_bs or 0
            monto_pagado = sum(c.monto_total_bs or c.monto or c.monto_base_bs or 0 for c in pagadas)
            monto_deuda = sum(c.monto_total_bs or c.monto or c.monto_base_bs or 0 for c in pendientes)
            
            total_financiado += monto_financiado
            total_pagado += monto_pagado
            total_deuda += monto_deuda
            total_cuotas += len(cuotas)
            cuotas_pagadas += len(pagadas)
            cuotas_pendientes += len(pendientes)
            
            financiamientos_detalle.append({
                "id": fin.id,
                "codigo": fin.codigo,
                "monto_total_bs": round(monto_financiado, 2),
                "monto_pagado_bs": round(monto_pagado, 2),
                "deuda_restante_bs": round(monto_deuda, 2),
                "estado": fin.estado,
                "cuotas_totales": len(cuotas),
                "cuotas_pagadas": len(pagadas),
                "cuotas_pendientes": len(pendientes),
                "tienda_nombre": fin.tienda.nombre if fin.tienda else None,
                "descripcion": fin.descripcion or ""
            })
        
        porcentaje_cumplimiento = round((cuotas_pagadas / total_cuotas) * 100, 2) if total_cuotas > 0 else 0
        
        return {
            "success": True,
            "cliente": {
                "id": cliente.id,
                "nombre": cliente.nombre,
                "cedula": cliente.cedula,
                "nivel": cliente.nivel,
                "score": cliente.score,
                "estado": cliente.estado,
                "tienda_nombre": cliente.tienda.nombre if cliente.tienda else None
            },
            "resumen_financiero": {
                "total_financiado_bs": round(total_financiado, 2),
                "total_pagado_bs": round(total_pagado, 2),
                "deuda_pendiente_bs": round(total_deuda, 2),
                "total_cuotas": total_cuotas,
                "cuotas_pagadas": cuotas_pagadas,
                "cuotas_pendientes": cuotas_pendientes,
                "porcentaje_cumplimiento": porcentaje_cumplimiento
            },
            "financiamientos": financiamientos_detalle[:10],
            "fecha_consulta": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# PROPUESTA DE NIVEL
# ============================================================
@router.get("/{id}/nivel-propuesta")
def calcular_propuesta_nivel(
    id: int,
    monto_total_bs: float,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        cliente = db.query(Cliente).filter(Cliente.id == id).first()
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
        tasa = obtener_tasa_actual(db)
        nivel, config = calcular_nivel(cliente.score)
        disponible = calcular_usado_disponible(cliente.id, db)
        
        monto_total_usd = monto_total_bs / tasa if tasa > 0 else 0
        limite_max_usd = config["monto_max_usd"]
        
        entrada_bs = monto_total_bs * (config["entrada_pct"] / 100)
        financia_bs = monto_total_bs - entrada_bs
        
        return {
            "success": True,
            "cliente": {
                "id": cliente.id,
                "nombre": cliente.nombre,
                "nivel": cliente.nivel,
                "score": cliente.score
            },
            "propuesta": {
                "monto_solicitado_bs": round(monto_total_bs, 2),
                "monto_solicitado_usd": round(monto_total_usd, 2),
                "limite_maximo_usd": limite_max_usd,
                "disponible_usd": disponible.get("disponible_usd", 0),
                "entrada_bs": round(entrada_bs, 2),
                "entrada_pct": config["entrada_pct"],
                "financia_bs": round(financia_bs, 2),
                "financia_pct": config["financia_pct"],
                "cuotas_base": config["cuotas_base"],
                "cuotas_max": config["cuotas_max"],
                "requiere_aprobacion_extra": config["aprobacion_extra"]
            },
            "configuracion_nivel": config,
            "tasa_dolar_actual": tasa
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))