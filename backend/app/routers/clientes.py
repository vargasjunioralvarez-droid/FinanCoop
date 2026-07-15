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
    enviar_pin_cliente
)
from app.auth import get_current_admin, get_current_user
from datetime import datetime, timezone
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

        existe = db.query(Cliente).filter(Cliente.cedula == cedula).first()
        if existe:
            return {"error": f"Cliente con cédula {cedula} ya existe", "success": False}

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

        print(f"✅ Cliente registrado (PENDIENTE): ID {db_cliente.id}")

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
        
        from app.utils import enviar_pin_cliente_completo
        
        resultado_envio = enviar_pin_cliente_completo(
            telefono=cliente.telefono,
            nombre=cliente.nombre,
            cedula=cliente.cedula,
            pin=cliente.pin
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
# ✅ ELIMINAR CLIENTE
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
    
    financiamientos = db.query(Financiamiento).filter(Financiamiento.cliente_id == id).all()
    for fin in financiamientos:
        db.query(Pago).filter(Pago.financiamiento_id == fin.id).delete(synchronize_session=False)
        db.query(Cuota).filter(Cuota.financiamiento_id == fin.id).delete(synchronize_session=False)
        db.delete(fin)
    
    db.delete(cliente)
    db.commit()
    
    return {
        "success": True,
        "mensaje": f"Cliente {nombre} eliminado correctamente"
    }

# ============================================================
# SUBIR FOTO
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

# ============================================================
# ✅ OBTENER ESTADO DE CUENTA DEL CLIENTE (CORREGIDO)
# ============================================================
@router.get("/{id}/estado-cuenta")
def obtener_estado_cuenta(
    id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Obtiene el estado de cuenta completo de un cliente
    Incluye: resumen financiero, financiamientos activos, historial de pagos
    """
    try:
        # Verificar que el cliente existe
        cliente = db.query(Cliente).filter(Cliente.id == id).first()
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
        # Obtener todos los financiamientos del cliente
        financiamientos = db.query(Financiamiento).filter(
            Financiamiento.cliente_id == id
        ).order_by(Financiamiento.id.desc()).all()
        
        # Variables para resumen financiero
        total_financiado = 0
        total_pagado = 0
        total_deuda = 0
        total_cuotas = 0
        cuotas_pagadas = 0
        cuotas_pendientes = 0
        financiamientos_activos = 0
        financiamientos_completados = 0
        financiamientos_atrasados = 0
        cuotas_con_deuda = 0
        
        # Lista para financiamientos con detalles
        financiamientos_detalle = []
        hoy = datetime.now(timezone.utc)
        
        for fin in financiamientos:
            # Obtener cuotas de este financiamiento
            cuotas = db.query(Cuota).filter(Cuota.financiamiento_id == fin.id).all()
            
            # Contar cuotas por estado
            pagadas = [c for c in cuotas if c.estado == "pagada"]
            pendientes = [c for c in cuotas if c.estado != "pagada"]
            atrasadas = [c for c in cuotas if c.estado == "pendiente" and c.fecha_vencimiento and c.fecha_vencimiento < hoy]
            
            # Calcular montos
            monto_financiado = fin.monto_total_bs or 0
            
            # ✅ CORREGIDO: Calcular monto pagado correctamente (sin usar monto_pagado)
            monto_pagado = 0
            for c in pagadas:
                if c.monto_total_bs:
                    monto_pagado += c.monto_total_bs
                elif c.monto:
                    monto_pagado += c.monto
                elif c.monto_base_bs:
                    monto_pagado += c.monto_base_bs
                else:
                    monto_pagado += 0
            
            # Calcular deuda pendiente
            monto_deuda = 0
            for c in pendientes:
                if c.monto_total_bs:
                    monto_deuda += c.monto_total_bs
                elif c.monto:
                    monto_deuda += c.monto
                elif c.monto_base_bs:
                    monto_deuda += c.monto_base_bs
                else:
                    monto_deuda += 0
            
            total_financiado += monto_financiado
            total_pagado += monto_pagado
            total_deuda += monto_deuda
            total_cuotas += len(cuotas)
            cuotas_pagadas += len(pagadas)
            cuotas_pendientes += len(pendientes)
            cuotas_con_deuda += len([c for c in pendientes if (c.monto_total_bs or 0) > 0 or (c.monto_base_bs or 0) > 0])
            
            # Estado del financiamiento
            if fin.estado in ["activo", "aprobado"]:
                financiamientos_activos += 1
                if len(atrasadas) > 0:
                    financiamientos_atrasados += 1
            elif fin.estado == "completado":
                financiamientos_completados += 1
            
            # Fecha de creación
            fecha_creacion = None
            if fin.fecha_primera_cuota:
                fecha_creacion = fin.fecha_primera_cuota.isoformat()
            
            # Crear detalle del financiamiento
            financiamientos_detalle.append({
                "id": fin.id,
                "codigo": fin.codigo,
                "monto_total_bs": round(fin.monto_total_bs or 0, 2),
                "monto_total_usd": round(fin.monto_total_usd or 0, 2),
                "monto_pagado_bs": round(monto_pagado, 2),
                "monto_pagado_usd": round(monto_pagado / (fin.tasa_aplicada or 1), 2) if fin.tasa_aplicada else 0,
                "deuda_restante_bs": round(monto_deuda, 2),
                "deuda_restante_usd": round(monto_deuda / (fin.tasa_aplicada or 1), 2) if fin.tasa_aplicada else 0,
                "fecha_creacion": fecha_creacion,
                "estado": fin.estado,
                "cuotas_totales": len(cuotas),
                "cuotas_pagadas": len(pagadas),
                "cuotas_pendientes": len(pendientes),
                "cuotas_atrasadas": len(atrasadas),
                "descripcion": fin.descripcion or "",
                "tasa_interes": fin.tasa_aplicada or 0,
                "nivel_aplicado": fin.nivel_aplicado
            })
        
        # Calcular nivel y tasa
        nivel, config = calcular_nivel(cliente.score)
        tasa = obtener_tasa_actual(db)
        disponible = calcular_usado_disponible(cliente.id, db)
        
        # Calcular porcentaje de cumplimiento
        porcentaje_cumplimiento = 0
        if total_cuotas > 0:
            porcentaje_cumplimiento = round((cuotas_pagadas / total_cuotas) * 100, 2)
        
        return {
            "success": True,
            "cliente": {
                "id": cliente.id,
                "nombre": cliente.nombre,
                "cedula": cliente.cedula,
                "telefono": cliente.telefono,
                "email": cliente.email,
                "direccion": cliente.direccion,
                "nivel": cliente.nivel,
                "score": cliente.score,
                "estado": cliente.estado,
                "fecha_registro": cliente.fecha_creacion.isoformat() if cliente.fecha_creacion else None
            },
            "resumen_financiero": {
                "total_financiado_bs": round(total_financiado, 2),
                "total_financiado_usd": round(total_financiado / tasa, 2) if tasa > 0 else 0,
                "total_pagado_bs": round(total_pagado, 2),
                "total_pagado_usd": round(total_pagado / tasa, 2) if tasa > 0 else 0,
                "deuda_pendiente_bs": round(total_deuda, 2),
                "deuda_pendiente_usd": round(total_deuda / tasa, 2) if tasa > 0 else 0,
                "limite_disponible_bs": disponible.get("disponible_bs", 0) if isinstance(disponible, dict) else disponible,
                "limite_disponible_usd": disponible.get("disponible_usd", 0) if isinstance(disponible, dict) else round(disponible / tasa, 2) if tasa > 0 else 0,
                "total_cuotas": total_cuotas,
                "cuotas_pagadas": cuotas_pagadas,
                "cuotas_pendientes": cuotas_pendientes,
                "cuotas_con_deuda": cuotas_con_deuda,
                "porcentaje_cumplimiento": porcentaje_cumplimiento,
                "financiamientos_activos": financiamientos_activos,
                "financiamientos_completados": financiamientos_completados,
                "financiamientos_atrasados": financiamientos_atrasados,
                "total_financiamientos": len(financiamientos)
            },
            "financiamientos": financiamientos_detalle[:10],
            "tasa_dolar_actual": tasa,
            "fecha_consulta": datetime.now(timezone.utc).isoformat(),
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
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error obteniendo estado de cuenta: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al obtener estado de cuenta: {str(e)}")

# ============================================================
# ✅ CALCULAR PROPUESTA DE NIVEL Y FINANCIAMIENTO
# ============================================================
@router.get("/{id}/nivel-propuesta")
def calcular_propuesta_nivel(
    id: int,
    monto_total_bs: float,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Calcula la propuesta de financiamiento basada en el nivel del cliente
    y el monto solicitado en Bs
    """
    try:
        # Verificar que el cliente existe
        cliente = db.query(Cliente).filter(Cliente.id == id).first()
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
        # Obtener tasa actual
        tasa = obtener_tasa_actual(db)
        
        # Calcular nivel y configuración
        nivel, config = calcular_nivel(cliente.score)
        
        # Obtener disponible del cliente
        disponible = calcular_usado_disponible(cliente.id, db)
        
        # Convertir monto a USD para validaciones
        monto_total_usd = monto_total_bs / tasa if tasa > 0 else 0
        
        # Calcular límites
        limite_max_usd = config["monto_max_usd"]
        limite_max_bs = round(limite_max_usd * tasa, 2) if tasa > 0 else 0
        
        # Verificar si el monto excede el límite
        excede_limite = monto_total_usd > limite_max_usd
        
        # Verificar si tiene disponible
        disponible_usd = disponible.get("disponible_usd", 0) if isinstance(disponible, dict) else disponible
        disponible_bs = disponible_usd * tasa if tasa > 0 else 0
        
        # Calcular entrada, financiamiento y cuotas
        entrada_pct = config["entrada_pct"]
        financia_pct = config["financia_pct"]
        
        entrada_bs = monto_total_bs * (entrada_pct / 100)
        financia_bs = monto_total_bs - entrada_bs
        entrada_usd = entrada_bs / tasa if tasa > 0 else 0
        financia_usd = financia_bs / tasa if tasa > 0 else 0
        
        # Calcular cuotas base y máximas
        cuotas_base = config["cuotas_base"]
        cuotas_max = config["cuotas_max"]
        
        # Determinar si requiere aprobación extra
        requiere_aprobacion = config["aprobacion_extra"]
        
        # Calcular monto de cuota base
        monto_cuota_base_bs = financia_bs / cuotas_base if cuotas_base > 0 else 0
        monto_cuota_base_usd = financia_usd / cuotas_base if cuotas_base > 0 else 0
        
        # Calcular monto de cuota máxima
        monto_cuota_max_bs = financia_bs / cuotas_max if cuotas_max > 0 else 0
        monto_cuota_max_usd = financia_usd / cuotas_max if cuotas_max > 0 else 0
        
        return {
            "success": True,
            "cliente": {
                "id": cliente.id,
                "nombre": cliente.nombre,
                "cedula": cliente.cedula,
                "nivel": cliente.nivel,
                "score": cliente.score,
                "estado": cliente.estado
            },
            "propuesta": {
                "monto_solicitado_bs": round(monto_total_bs, 2),
                "monto_solicitado_usd": round(monto_total_usd, 2),
                "limite_maximo_bs": limite_max_bs,
                "limite_maximo_usd": limite_max_usd,
                "disponible_bs": round(disponible_bs, 2) if isinstance(disponible_bs, (int, float)) else 0,
                "disponible_usd": round(disponible_usd, 2) if isinstance(disponible_usd, (int, float)) else 0,
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
                "monto_cuota_base_usd": round(monto_cuota_base_usd, 2),
                "monto_cuota_max_bs": round(monto_cuota_max_bs, 2),
                "monto_cuota_max_usd": round(monto_cuota_max_usd, 2),
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
        print(f"❌ Error calculando propuesta: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al calcular propuesta: {str(e)}")