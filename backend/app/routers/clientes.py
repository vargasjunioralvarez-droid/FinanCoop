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
from app.auth import get_current_admin, get_current_user, hash_pin
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
        logger.warning("Cloudflare no configurado")
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
        logger.error(f"Error subiendo a Cloudflare: {e}")
        return None

async def subir_imagen_cloudflare_base64(base64_string: str, nombre_archivo: str) -> Optional[str]:
    try:
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        archivo_bytes = base64.b64decode(base64_string)
        return await subir_imagen_cloudflare(archivo_bytes, nombre_archivo)
    except Exception as e:
        logger.error(f"Error decodificando base64: {e}")
        return None

# ============================================================
# ✅ CREAR CLIENTE (PIN HASHEADO)
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
    db: Session = Depends(get_db)
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
            except Exception as e:
                logger.warning(f"Error procesando foto: {e}")
        elif cedula_foto_base64 and len(cedula_foto_base64) > 100:
            try:
                url_cedula = await subir_imagen_cloudflare_base64(cedula_foto_base64, f"cedula_{cedula}_{uuid.uuid4().hex[:8]}.jpg")
            except Exception as e:
                logger.warning(f"Error procesando foto base64: {e}")

        pin_generado = generar_pin()
        pin_hasheado = hash_pin(pin_generado)

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
            score=0
        )
        
        db.add(db_cliente)
        db.commit()
        db.refresh(db_cliente)

        logger.info(f"✅ Cliente registrado (PENDIENTE): ID {db_cliente.id} - {db_cliente.nombre}")

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
# CREAR CLIENTE VIA JSON (BACKUP)
# ============================================================
@router.post("/json")
async def crear_cliente_json(
    cliente_data: ClienteCreate,
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"📝 Registrando cliente (JSON): {cliente_data.cedula}")
        
        existe = db.query(Cliente).filter(Cliente.cedula == cliente_data.cedula).first()
        if existe:
            raise HTTPException(status_code=409, detail=f"Cliente con cédula {cliente_data.cedula} ya existe")

        pin_generado = generar_pin()
        pin_hasheado = hash_pin(pin_generado)

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
            score=0
        )
        
        db.add(db_cliente)
        db.commit()
        db.refresh(db_cliente)

        logger.info(f"✅ Cliente registrado (JSON): ID {db_cliente.id}")

        return {
            "success": True,
            "id": db_cliente.id,
            "mensaje": "Registro exitoso. Tu cuenta está en verificación.",
            "pin": pin_generado,
            "cliente": {
                "id": db_cliente.id,
                "nombre": db_cliente.nombre,
                "cedula": db_cliente.cedula,
                "estado": "pendiente"
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error en registro JSON: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# APROBAR CLIENTE Y ENVIAR PIN
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
        
        logger.info(f"✅ Cliente aprobado: {cliente.nombre}")
        
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
# LISTAR CLIENTES (CON PAGINACIÓN)
# ============================================================
@router.get("")
def listar_clientes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    estado: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(Cliente)
    
    if estado:
        query = query.filter(Cliente.estado == estado)
    
    total = query.count()
    clientes = query.order_by(Cliente.id.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
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
        "ultimo_acceso": cliente.ultimo_acceso.isoformat() if cliente.ultimo_acceso else None,
        "creado_en": cliente.creado_en.isoformat() if cliente.creado_en else None
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
    
    # Eliminar en cascada
    financiamientos = db.query(Financiamiento).filter(Financiamiento.cliente_id == id).all()
    for fin in financiamientos:
        db.query(Pago).filter(Pago.financiamiento_id == fin.id).delete(synchronize_session=False)
        db.query(Cuota).filter(Cuota.financiamiento_id == fin.id).delete(synchronize_session=False)
        db.delete(fin)
    
    db.delete(cliente)
    db.commit()
    
    logger.info(f"🗑️ Cliente eliminado: {nombre} (ID: {id})")
    
    return {
        "success": True,
        "mensaje": f"Cliente {nombre} eliminado correctamente"
    }

# ============================================================
# SUBIR FOTO CÉDULA
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
        if len(contenido) == 0:
            raise HTTPException(status_code=400, detail="Archivo vacío")
        
        url_cedula = await subir_imagen_cloudflare(contenido, f"cedula_{cliente.cedula}_{uuid.uuid4().hex[:8]}.jpg")
        
        if url_cedula:
            cliente.url_cedula = url_cedula
            db.commit()
            return {"success": True, "url": url_cedula}
        else:
            raise HTTPException(status_code=500, detail="No se pudo subir la imagen")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error subiendo foto: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# BUSCAR CLIENTE POR CÉDULA
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

# ============================================================
# OBTENER ESTADO DE CUENTA DEL CLIENTE
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
        financiamientos_activos = 0
        financiamientos_completados = 0
        financiamientos_atrasados = 0
        
        financiamientos_detalle = []
        hoy = datetime.now(timezone.utc)
        
        for fin in financiamientos:
            cuotas = db.query(Cuota).filter(Cuota.financiamiento_id == fin.id).all()
            
            pagadas = [c for c in cuotas if c.estado == "pagada"]
            pendientes = [c for c in cuotas if c.estado != "pagada"]
            atrasadas = [c for c in cuotas if c.estado == "pendiente" and c.fecha_vencimiento and c.fecha_vencimiento < hoy]
            
            monto_financiado = fin.monto_total_bs or 0
            monto_pagado = sum(c.monto_total_bs or c.monto or c.monto_base_bs or 0 for c in pagadas)
            monto_deuda = sum(c.monto_total_bs or c.monto or c.monto_base_bs or 0 for c in pendientes)
            
            total_financiado += monto_financiado
            total_pagado += monto_pagado
            total_deuda += monto_deuda
            total_cuotas += len(cuotas)
            cuotas_pagadas += len(pagadas)
            cuotas_pendientes += len(pendientes)
            
            if fin.estado in ["activo", "aprobado"]:
                financiamientos_activos += 1
                if len(atrasadas) > 0:
                    financiamientos_atrasados += 1
            elif fin.estado == "completado":
                financiamientos_completados += 1
            
            financiamientos_detalle.append({
                "id": fin.id,
                "codigo": fin.codigo,
                "monto_total_bs": round(monto_financiado, 2),
                "monto_total_usd": round(fin.monto_total_usd or 0, 2),
                "monto_pagado_bs": round(monto_pagado, 2),
                "deuda_restante_bs": round(monto_deuda, 2),
                "estado": fin.estado,
                "cuotas_totales": len(cuotas),
                "cuotas_pagadas": len(pagadas),
                "cuotas_pendientes": len(pendientes),
                "cuotas_atrasadas": len(atrasadas),
                "descripcion": fin.descripcion or ""
            })
        
        nivel, config = calcular_nivel(cliente.score)
        tasa = obtener_tasa_actual(db)
        disponible = calcular_usado_disponible(cliente.id, db)
        
        porcentaje_cumplimiento = round((cuotas_pagadas / total_cuotas) * 100, 2) if total_cuotas > 0 else 0
        
        return {
            "success": True,
            "cliente": {
                "id": cliente.id,
                "nombre": cliente.nombre,
                "cedula": cliente.cedula,
                "telefono": cliente.telefono,
                "email": cliente.email,
                "nivel": cliente.nivel,
                "score": cliente.score,
                "estado": cliente.estado
            },
            "resumen_financiero": {
                "total_financiado_bs": round(total_financiado, 2),
                "total_pagado_bs": round(total_pagado, 2),
                "deuda_pendiente_bs": round(total_deuda, 2),
                "total_cuotas": total_cuotas,
                "cuotas_pagadas": cuotas_pagadas,
                "cuotas_pendientes": cuotas_pendientes,
                "porcentaje_cumplimiento": porcentaje_cumplimiento,
                "financiamientos_activos": financiamientos_activos,
                "financiamientos_completados": financiamientos_completados,
                "financiamientos_atrasados": financiamientos_atrasados
            },
            "financiamientos": financiamientos_detalle[:10],
            "tasa_dolar_actual": tasa,
            "fecha_consulta": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo estado de cuenta: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener estado de cuenta: {str(e)}")

# ============================================================
# CALCULAR PROPUESTA DE NIVEL Y FINANCIAMIENTO
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
        limite_max_bs = round(limite_max_usd * tasa, 2) if tasa > 0 else 0
        excede_limite = monto_total_usd > limite_max_usd
        
        disponible_usd = disponible.get("disponible_usd", 0) if isinstance(disponible, dict) else disponible
        disponible_bs = disponible_usd * tasa if tasa > 0 else 0
        
        entrada_pct = config["entrada_pct"]
        financia_pct = config["financia_pct"]
        
        entrada_bs = monto_total_bs * (entrada_pct / 100)
        financia_bs = monto_total_bs - entrada_bs
        entrada_usd = entrada_bs / tasa if tasa > 0 else 0
        financia_usd = financia_bs / tasa if tasa > 0 else 0
        
        cuotas_base = config["cuotas_base"]
        cuotas_max = config["cuotas_max"]
        requiere_aprobacion = config["aprobacion_extra"]
        
        monto_cuota_base_bs = financia_bs / cuotas_base if cuotas_base > 0 else 0
        monto_cuota_base_usd = financia_usd / cuotas_base if cuotas_base > 0 else 0
        monto_cuota_max_bs = financia_bs / cuotas_max if cuotas_max > 0 else 0
        monto_cuota_max_usd = financia_usd / cuotas_max if cuotas_max > 0 else 0
        
        return {
            "success": True,
            "cliente": {
                "id": cliente.id,
                "nombre": cliente.nombre,
                "cedula": cliente.cedula,
                "nivel": cliente.nivel,
                "score": cliente.score
            },
            "propuesta": {
                "monto_solicitado_bs": round(monto_total_bs, 2),
                "monto_solicitado_usd": round(monto_total_usd, 2),
                "limite_maximo_bs": limite_max_bs,
                "limite_maximo_usd": limite_max_usd,
                "disponible_bs": round(disponible_bs, 2),
                "disponible_usd": round(disponible_usd, 2),
                "excede_limite": excede_limite,
                "entrada_bs": round(entrada_bs, 2),
                "entrada_usd": round(entrada_usd, 2),
                "entrada_pct": entrada_pct,
                "financia_bs": round(financia_bs, 2),
                "financia_usd": round(financia_usd, 2),
                "financia_pct": financia_pct,
                "cuotas_base": cuotas_base,
                "cuotas_max": cuotas_max,
                "monto_cuota_base_bs": round(monto_cuota_base_bs, 2),
                "monto_cuota_max_bs": round(monto_cuota_max_bs, 2),
                "requiere_aprobacion_extra": requiere_aprobacion
            },
            "configuracion_nivel": {
                "min_score": config["min_score"],
                "max_score": config["max_score"],
                "monto_max_usd": config["monto_max_usd"],
                "entrada_pct": config["entrada_pct"],
                "financia_pct": config["financia_pct"],
                "cuotas_base": config["cuotas_base"],
                "cuotas_max": config["cuotas_max"],
                "mora_diaria": config["mora_diaria"],
                "aprobacion_extra": config["aprobacion_extra"]
            },
            "tasa_dolar_actual": tasa,
            "fecha_consulta": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error calculando propuesta: {e}")
        raise HTTPException(status_code=500, detail=f"Error al calcular propuesta: {str(e)}")