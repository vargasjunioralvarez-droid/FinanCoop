# backend/app/routers/clientes.py
from fastapi import APIRouter, Depends, HTTPException, Query, Form, File, UploadFile, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Cliente, Financiamiento, Cuota
from app.utils import (
    calcular_nivel, actualizar_score_cliente, generar_pin, 
    calcular_usado_disponible, obtener_tasa_actual, generar_token,
    enviar_pin_cliente
)
from app.auth import get_current_admin, get_current_cliente
from datetime import datetime
import httpx
import os

router = APIRouter(prefix="/clientes", tags=["Clientes"])

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
# ✅ CREAR CLIENTE (PÚBLICO - SIN AUTENTICACIÓN)
# ============================================================
@router.post("")
async def crear_cliente(
    nombre: str = Form(...),
    cedula: str = Form(...),
    telefono: str = Form(...),
    email: str = Form(""),
    direccion: str = Form(""),
    referencia_nombre: str = Form(""),
    referencia_telefono: str = Form(""),
    referencia_parentesco: str = Form(""),
    cedula_foto: UploadFile | None = File(None),
    db: Session = Depends(get_db)
):
    try:
        existe = db.query(Cliente).filter(Cliente.cedula == cedula).first()
        if existe:
            return {"error": f"Cliente con cédula {cedula} ya existe"}

        url_cedula = ""
        if cedula_foto and cedula_foto.filename:
            try:
                contenido = await cedula_foto.read()
                url_cedula = await subir_imagen_cloudflare(contenido, cedula_foto.filename)
            except Exception as e:
                print(f"❌ Error al subir foto a Cloudflare: {e}")

        db_cliente = Cliente(
            nombre=nombre, cedula=cedula, telefono=telefono,
            email=email, direccion=direccion,
            referencia_nombre=referencia_nombre,
            referencia_telefono=referencia_telefono,
            referencia_parentesco=referencia_parentesco,
            url_cedula=url_cedula,
            pin=generar_pin(),
            token_app=generar_token()
        )
        
        db.add(db_cliente)
        db.commit()
        db.refresh(db_cliente)

        try:
            enviado = enviar_pin_cliente(
                telefono=db_cliente.telefono,
                nombre=db_cliente.nombre,
                cedula=db_cliente.cedula,
                pin=db_cliente.pin
            )
        except Exception as e:
            print(f"❌ Error enviando PIN: {e}")

        return {
            "success": True,
            "cliente": {
                "id": db_cliente.id,
                "nombre": db_cliente.nombre,
                "cedula": db_cliente.cedula,
                "telefono": db_cliente.telefono,
                "email": db_cliente.email,
                "direccion": db_cliente.direccion,
                "nivel": db_cliente.nivel,
                "score": db_cliente.score,
                "url_cedula": db_cliente.url_cedula
            },
            "pin_generado": db_cliente.pin,
            "mensaje": f"✅ Cliente registrado. PIN: {db_cliente.pin}"
        }

    except Exception as e:
        print(f"❌ Error en registro: {e}")
        return {"error": str(e), "success": False}

# ============================================================
# ✅ LISTAR CLIENTES (SOLO ADMIN)
# ============================================================
@router.get("")
def listar_clientes(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    return db.query(Cliente).all()

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

# ============================================================
# ✅ OBTENER CLIENTE POR ID (SOLO ADMIN)
# ============================================================
@router.get("/{id}")
def obtener_cliente(
    id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    cliente = db.query(Cliente).filter(Cliente.id == id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    actualizar_score_cliente(cliente, db)
    db.refresh(cliente)
    
    nivel, config = calcular_nivel(cliente.score)
    tasa = obtener_tasa_actual(db)
    disponible = calcular_usado_disponible(cliente.id, db)
    
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
# ✅ EDITAR CLIENTE (SOLO ADMIN)
# ============================================================
@router.put("/{id}")
def editar_cliente(
    id: int,
    nombre: str = Form(None),
    telefono: str = Form(None),
    email: str = Form(None),
    direccion: str = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    cliente = db.query(Cliente).filter(Cliente.id == id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    if nombre:
        cliente.nombre = nombre
    if telefono:
        cliente.telefono = telefono
    if email:
        cliente.email = email
    if direccion:
        cliente.direccion = direccion
    
    db.commit()
    db.refresh(cliente)
    return {"mensaje": "Cliente actualizado", "cliente": cliente}

# ============================================================
# ✅ ELIMINAR CLIENTE (SOLO ADMIN)
# ============================================================
@router.delete("/{id}")
def eliminar_cliente(
    id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    cliente = db.query(Cliente).filter(Cliente.id == id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    db.delete(cliente)
    db.commit()
    return {"mensaje": "Cliente eliminado", "id": id}

# ============================================================
# ✅ ESTADO DE CUENTA (PÚBLICO)
# ============================================================
@router.get("/{id}/estado-cuenta")
def estado_cuenta_cliente(id: int, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    hoy = datetime.now()
    cuotas_vencidas = db.query(Cuota).join(Financiamiento).filter(
        Financiamiento.cliente_id == id,
        Cuota.estado == "pendiente",
        Cuota.fecha_vencimiento < hoy
    ).all()
    
    deuda_vencida_bs = sum(c.monto_total_bs for c in cuotas_vencidas)
    deuda_vencida_usd = sum(c.monto_total_usd for c in cuotas_vencidas)
    bloqueado = len(cuotas_vencidas) > 0
    
    riesgo = "bajo"
    if len(cuotas_vencidas) >= 3:
        riesgo = "alto"
    elif len(cuotas_vencidas) >= 1:
        riesgo = "medio"
    
    disponible = calcular_usado_disponible(id, db)
    
    return {
        "cliente_id": id,
        "nombre": cliente.nombre,
        "bloqueado": bloqueado,
        "riesgo": riesgo,
        "deudas_vencidas": len(cuotas_vencidas),
        "deuda_vencida_bs": round(deuda_vencida_bs, 2),
        "deuda_vencida_usd": round(deuda_vencida_usd, 2),
        "limite_disponible": disponible,
        "cuotas_vencidas": [
            {
                "id": c.id,
                "numero": c.numero,
                "financiamiento_codigo": c.financiamiento.codigo,
                "monto_bs": round(c.monto_total_bs, 2),
                "fecha_vencimiento": c.fecha_vencimiento.isoformat() if c.fecha_vencimiento else None,
                "dias_vencida": (hoy - c.fecha_vencimiento).days if c.fecha_vencimiento else 0
            } for c in cuotas_vencidas
        ],
        "puede_comprar": not bloqueado and disponible["disponible_usd"] > 0,
        "mensaje": "Tiene deudas vencidas" if bloqueado else "Cliente al día"
    }

# ============================================================
# ✅ PROPUESTA DE FINANCIAMIENTO (PÚBLICO)
# ============================================================
@router.get("/{id}/nivel-propuesta")
def propuesta_financiamiento(
    id: int, 
    monto_total_bs: float = Query(..., gt=0, description="Monto total en Bolívares"),
    db: Session = Depends(get_db)
):
    cliente = db.query(Cliente).filter(Cliente.id == id).first()
    if not cliente:
        return {"error": "Cliente no encontrado"}
    
    tasa = obtener_tasa_actual(db)
    actualizar_score_cliente(cliente, db)
    nivel, config = calcular_nivel(cliente.score)
    disponible = calcular_usado_disponible(id, db)
    monto_total_usd = monto_total_bs / tasa
    
    if not disponible["puede_comprar"]:
        return {
            "error": "LÍMITE AGOTADO",
            "mensaje": "Ha usado todo su límite disponible. Debe pagar financiamientos activos.",
            "limite_usd": disponible["limite_usd"],
            "usado_usd": disponible["usado_usd"],
            "disponible_usd": disponible["disponible_usd"]
        }
    
    if monto_total_usd > disponible["disponible_usd"]:
        return {
            "error": "Monto excede límite disponible",
            "monto_solicitado_usd": round(monto_total_usd, 2),
            "disponible_usd": disponible["disponible_usd"],
            "disponible_bs": disponible["disponible_bs"],
            "mensaje": f"Solo puede financiar hasta ${disponible['disponible_usd']:.2f} USD más (BS {disponible['disponible_bs']:.2f})"
        }
    
    if monto_total_usd > config["monto_max_usd"]:
        return {
            "error": "Monto excede el límite del nivel",
            "monto_maximo_permitido_usd": config["monto_max_usd"],
            "monto_maximo_permitido_bs": round(config["monto_max_usd"] * tasa, 2),
            "mensaje": f"Su nivel {nivel} permite máximo ${config['monto_max_usd']} USD por operación"
        }
    
    entrada_bs = monto_total_bs * (config["entrada_pct"] / 100)
    financia_bs = monto_total_bs - entrada_bs
    monto_total_usd_ref = monto_total_bs / tasa
    entrada_usd_ref = entrada_bs / tasa
    financia_usd_ref = financia_bs / tasa
    
    opciones = []
    for cuotas_num in range(config["cuotas_base"], config["cuotas_max"] + 1):
        monto_cuota_bs = financia_bs / cuotas_num
        monto_cuota_usd_ref = monto_cuota_bs / tasa
        opciones.append({
            "cuotas": cuotas_num,
            "monto_cuota_bs": round(monto_cuota_bs, 2),
            "monto_cuota_usd": round(monto_cuota_usd_ref, 2),
            "requiere_aprobacion": cuotas_num > config["cuotas_base"],
            "frecuencia": "quincenal",
            "label": f"{cuotas_num} cuotas - BS {round(monto_cuota_bs, 2)} cada una"
        })
    
    return {
        "cliente": {
            "id": cliente.id,
            "nombre": cliente.nombre,
            "nivel": nivel,
            "score": cliente.score
        },
        "limite": {
            "total_usd": disponible["limite_usd"],
            "usado_usd": disponible["usado_usd"],
            "disponible_usd": disponible["disponible_usd"],
            "disponible_bs": disponible["disponible_bs"]
        },
        "tasa_aplicada": tasa,
        "monto_total_bs": round(monto_total_bs, 2),
        "monto_total_usd": round(monto_total_usd_ref, 2),
        "entrada_pct": config["entrada_pct"],
        "monto_entrada_bs": round(entrada_bs, 2),
        "monto_entrada_usd": round(entrada_usd_ref, 2),
        "financia_pct": config["financia_pct"],
        "monto_financia_bs": round(financia_bs, 2),
        "monto_financia_usd": round(financia_usd_ref, 2),
        "cuotas_base": config["cuotas_base"],
        "cuotas_max": config["cuotas_max"],
        "cuotas_sugeridas": config["cuotas_base"],
        "mora_diaria": config["mora_diaria"],
        "aprobacion_extra": config["aprobacion_extra"],
        "requiere_aprobacion": False,
        "opciones_cuotas": opciones
    }