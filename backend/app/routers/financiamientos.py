# backend/app/routers/financiamientos.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models import Cliente, Financiamiento, Cuota, Pago
from app.schemas import FinanciamientoCreate, AprobacionExtra
from app.utils import calcular_nivel, actualizar_score_cliente, calcular_usado_disponible, obtener_tasa_actual
from app.auth import get_current_admin, get_current_user, get_current_tienda
from datetime import datetime, timedelta, timezone
import random
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/financiamientos", tags=["Financiamientos"])

MAX_CREDITOS_ACTIVOS = 3

@router.post("")
def crear_financiamiento(
    f: FinanciamientoCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        cliente = db.query(Cliente).filter(Cliente.id == f.cliente_id).first()
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
        # 🔥 VALIDACIÓN 1: Cliente debe estar aprobado
        if cliente.estado != "aprobado":
            raise HTTPException(status_code=400, detail="Cliente no está aprobado. Debe ser verificado por el administrador.")
        
        # ✅ VALIDACIÓN 2: Calcular nivel (puede ser "nuevo" con score 0)
        nivel, config = calcular_nivel(cliente.score)
        
        # ✅ VALIDACIÓN 3: Límite de créditos activos
        creditos_activos = db.query(Financiamiento).filter(
            Financiamiento.cliente_id == f.cliente_id,
            Financiamiento.estado == "activo"
        ).count()
        
        if creditos_activos >= MAX_CREDITOS_ACTIVOS:
            raise HTTPException(status_code=400, detail=f"Límite de {MAX_CREDITOS_ACTIVOS} créditos activos alcanzado")
        
        # ✅ VALIDACIÓN 4: Verificar cuotas vencidas
        hoy = datetime.now(timezone.utc)
        deudas_vencidas = db.query(Cuota).join(Financiamiento).filter(
            Financiamiento.cliente_id == f.cliente_id,
            Cuota.estado == "pendiente",
            Cuota.fecha_vencimiento < hoy
        ).count()
        
        if deudas_vencidas > 0:
            raise HTTPException(status_code=400, detail=f"Tiene {deudas_vencidas} cuota(s) vencida(s)")
        
        # ✅ VALIDACIÓN 5: Calcular disponible global
        disponible = calcular_usado_disponible(f.cliente_id, db)
        if not disponible["puede_comprar"]:
            raise HTTPException(status_code=400, detail="Límite de financiamiento agotado")
        
        # ✅ VALIDACIÓN 6: Verificar tasa y monto
        tasa = obtener_tasa_actual(db)
        monto_total_usd = f.monto_total_bs / tasa if tasa > 0 else 0
        
        # ✅ VALIDACIÓN 7: No exceder disponible
        if monto_total_usd > disponible["disponible_usd"]:
            raise HTTPException(status_code=400, detail=f"Monto excede disponible: ${disponible['disponible_usd']:.2f}")
        
        # ✅ VALIDACIÓN 8: No exceder límite del nivel
        logger.info(f"🔍 DEBUG: cliente={cliente.nombre}, nivel={nivel}, monto_usd={monto_total_usd:.2f}, limite={config['monto_max_usd']:.2f}")
        if monto_total_usd > config["monto_max_usd"]:
            raise HTTPException(status_code=400, detail=f"❌ Monto excede límite de nivel {nivel}: ${config['monto_max_usd']:.2f} USD (solicitado: ${monto_total_usd:.2f})")
        
        # ✅ VALIDACIÓN 9: Validar cuotas
        if f.cuotas_solicitadas > config["cuotas_max"]:
            raise HTTPException(status_code=400, detail=f"Cuotas exceden máximo de {config['cuotas_max']}")
        
        if f.cuotas_solicitadas < 1:
            raise HTTPException(status_code=400, detail="Debe solicitar al menos 1 cuota")
        
        # ✅ CALCULAR APROBACIÓN EXTRA
        requiere_aprobacion = f.cuotas_solicitadas > config["cuotas_base"] and config["aprobacion_extra"]
        cuotas_aprobadas = f.cuotas_solicitadas if not requiere_aprobacion else config["cuotas_base"]
        
        # ✅ CALCULAR MONTOS - PORCENTAJES CORRECTOS
        # entrada_pct y financia_pct vienen como enteros (30, 70, etc.)
        entrada_pct = config["entrada_pct"] / 100  # Convertir a decimal (30/100 = 0.30)
        financia_pct = config["financia_pct"] / 100  # Convertir a decimal (70/100 = 0.70)
        
        entrada_bs = f.monto_total_bs * entrada_pct  # 1000 * 0.30 = 300
        financia_bs = f.monto_total_bs * financia_pct  # 1000 * 0.70 = 700
        monto_cuota_bs = financia_bs / cuotas_aprobadas if cuotas_aprobadas > 0 else 0
        
        entrada_usd_ref = entrada_bs / tasa if tasa > 0 else 0
        financia_usd_ref = financia_bs / tasa if tasa > 0 else 0
        monto_cuota_usd_ref = monto_cuota_bs / tasa if tasa > 0 else 0
        
        # ✅ GENERAR CÓDIGO
        codigo = f"F-{random.randint(100000, 999999)}"
        fecha_primera = datetime.now(timezone.utc) + timedelta(days=15)
        
        # ✅ ASIGNAR TIENDA DEL USUARIO ACTUAL (quien vende)
        tienda_id = None
        if hasattr(current_user, 'tienda_id') and current_user.tienda_id:
            tienda_id = current_user.tienda_id
        
        # ✅ CREAR FINANCIAMIENTO
        fin = Financiamiento(
            cliente_id=f.cliente_id, 
            codigo=codigo, 
            descripcion=f.descripcion,
            monto_total_bs=f.monto_total_bs, 
            monto_entrada_bs=entrada_bs,
            monto_financia_bs=financia_bs, 
            monto_cuota_bs=monto_cuota_bs,
            monto_total_usd=monto_total_usd, 
            monto_entrada_usd=entrada_usd_ref,
            monto_financia_usd=financia_usd_ref, 
            monto_cuota_usd=monto_cuota_usd_ref,
            tasa_aplicada=tasa, 
            nivel_aplicado=nivel,
            cuotas_solicitadas=f.cuotas_solicitadas, 
            cuotas_aprobadas=cuotas_aprobadas,
            requiere_aprobacion=requiere_aprobacion,
            entrada_pct=config["entrada_pct"], 
            financia_pct=config["financia_pct"],
            fecha_primera_cuota=fecha_primera,
            estado="activo",
            tienda_id=tienda_id
        )
        db.add(fin)
        db.commit()
        db.refresh(fin)
        
        # ✅ CREAR CUOTAS
        for i in range(1, cuotas_aprobadas + 1):
            cuota = Cuota(
                financiamiento_id=fin.id, 
                numero=i,
                monto_base_bs=monto_cuota_bs, 
                monto_total_bs=monto_cuota_bs,
                monto_base_usd=monto_cuota_usd_ref, 
                monto_total_usd=monto_cuota_usd_ref,
                fecha_vencimiento=fecha_primera + timedelta(days=15 * (i - 1)),
                estado="pendiente"
            )
            db.add(cuota)
        db.commit()
        
        # ✅ ACTUALIZAR ESTADÍSTICAS DEL CLIENTE
        if hasattr(cliente, 'total_monto_comprado_usd'):
            cliente.total_monto_comprado_usd = (cliente.total_monto_comprado_usd or 0) + monto_total_usd
            db.commit()
        
        # ✅ ACTUALIZAR SCORE DEL CLIENTE
        actualizar_score_cliente(cliente, db)
        
        logger.info(f"✅ Financiamiento creado: {codigo} - Tienda: {tienda_id}")
        
        return {
            "success": True,
            "financiamiento": {
                "id": fin.id, 
                "codigo": fin.codigo,
                "monto_total_bs": round(fin.monto_total_bs, 2),
                "monto_total_usd": round(fin.monto_total_usd, 2),
                "monto_entrada_bs": round(fin.monto_entrada_bs, 2),
                "monto_cuota_bs": round(fin.monto_cuota_bs, 2),
                "tasa_aplicada": fin.tasa_aplicada,
                "cuotas_aprobadas": fin.cuotas_aprobadas,
                "requiere_aprobacion": fin.requiere_aprobacion,
                "tienda_id": tienda_id,
                "estado": fin.estado
            },
            "score_actualizado": cliente.score,
            "nivel_actual": cliente.nivel,
            "mensaje": f"Entrada: Bs {entrada_bs:,.2f}. {cuotas_aprobadas} cuotas de Bs {monto_cuota_bs:,.2f}",
            "advertencia": "Requiere aprobación adicional" if requiere_aprobacion else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ... (el resto de los endpoints quedan igual)


@router.post("/{id}/aprobar")
def aprobar_financiamiento(
    id: int, 
    aprobacion: AprobacionExtra, 
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    try:
        fin = db.query(Financiamiento).filter(Financiamiento.id == id).first()
        if not fin:
            raise HTTPException(status_code=404, detail="Financiamiento no encontrado")
        
        if not fin.requiere_aprobacion:
            raise HTTPException(status_code=400, detail="No requiere aprobación")
        
        fin.cuotas_aprobadas = aprobacion.cuotas_aprobadas
        fin.aprobado_por = aprobacion.aprobado_por
        fin.requiere_aprobacion = False
        
        db.query(Cuota).filter(Cuota.financiamiento_id == fin.id).delete()
        
        monto_cuota_bs = fin.monto_financia_bs / aprobacion.cuotas_aprobadas if aprobacion.cuotas_aprobadas > 0 else 0
        monto_cuota_usd = fin.monto_financia_usd / aprobacion.cuotas_aprobadas if aprobacion.cuotas_aprobadas > 0 else 0
        
        for i in range(1, aprobacion.cuotas_aprobadas + 1):
            cuota = Cuota(
                financiamiento_id=fin.id, 
                numero=i,
                monto_base_bs=monto_cuota_bs, 
                monto_total_bs=monto_cuota_bs,
                monto_base_usd=monto_cuota_usd, 
                monto_total_usd=monto_cuota_usd,
                fecha_vencimiento=fin.fecha_primera_cuota + timedelta(days=15 * (i - 1)),
                estado="pendiente"
            )
            db.add(cuota)
        
        fin.monto_cuota_bs = monto_cuota_bs
        fin.monto_cuota_usd = monto_cuota_usd
        db.commit()
        
        return {
            "success": True,
            "mensaje": f"Aprobado con {aprobacion.cuotas_aprobadas} cuotas",
            "aprobado_por": aprobacion.aprobado_por
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
def listar_financiamientos(
    skip: int = 0,
    limit: int = 50,
    estado: str = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tienda_id: Optional[int] = Depends(get_current_tienda)
):
    try:
        query = db.query(Financiamiento)
        
        if tienda_id:
            query = query.filter(Financiamiento.tienda_id == tienda_id)
        
        if estado:
            query = query.filter(Financiamiento.estado == estado)
        
        total = query.count()
        financiamientos = query.order_by(Financiamiento.id.desc()).offset(skip).limit(limit).all()
        
        resultado = []
        for fin in financiamientos:
            cliente = db.query(Cliente).filter(Cliente.id == fin.cliente_id).first()
            resultado.append({
                "id": fin.id,
                "codigo": fin.codigo,
                "cliente_id": fin.cliente_id,
                "cliente_nombre": cliente.nombre if cliente else "Desconocido",
                "descripcion": fin.descripcion,
                "monto_total_bs": round(fin.monto_total_bs, 2),
                "monto_total_usd": round(fin.monto_total_usd, 2),
                "cuotas_aprobadas": fin.cuotas_aprobadas,
                "estado": fin.estado,
                "tienda_id": fin.tienda_id,
                "tienda_nombre": fin.tienda.nombre if fin.tienda else None,
                "creado_en": fin.creado_en.isoformat() if fin.creado_en else None
            })
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "tienda_filtro": tienda_id,
            "financiamientos": resultado
        }
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{id}")
def obtener_financiamiento(
    id: int, 
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    try:
        fin = db.query(Financiamiento).filter(Financiamiento.id == id).first()
        if not fin:
            raise HTTPException(status_code=404, detail="Financiamiento no encontrado")
        
        cliente = db.query(Cliente).filter(Cliente.id == fin.cliente_id).first()
        cuotas = db.query(Cuota).filter(Cuota.financiamiento_id == fin.id).order_by(Cuota.numero).all()
        
        return {
            "id": fin.id,
            "codigo": fin.codigo,
            "cliente": {
                "id": cliente.id if cliente else None,
                "nombre": cliente.nombre if cliente else "Desconocido"
            },
            "monto_total_bs": round(fin.monto_total_bs, 2),
            "monto_total_usd": round(fin.monto_total_usd, 2),
            "tasa_aplicada": fin.tasa_aplicada,
            "cuotas_aprobadas": fin.cuotas_aprobadas,
            "estado": fin.estado,
            "tienda_nombre": fin.tienda.nombre if fin.tienda else None,
            "cuotas": [
                {
                    "id": c.id,
                    "numero": c.numero,
                    "monto_total_bs": round(c.monto_total_bs, 2),
                    "fecha_vencimiento": c.fecha_vencimiento.isoformat() if c.fecha_vencimiento else None,
                    "estado": c.estado
                }
                for c in cuotas
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{id}/cuotas")
def ver_cuotas(
    id: int, 
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    try:
        fin = db.query(Financiamiento).filter(Financiamiento.id == id).first()
        if not fin:
            raise HTTPException(status_code=404, detail="Financiamiento no encontrado")
        
        cuotas = db.query(Cuota).filter(Cuota.financiamiento_id == id).order_by(Cuota.numero).all()
        hoy = datetime.now(timezone.utc)
        
        return {
            "financiamiento_id": id,
            "codigo": fin.codigo,
            "cuotas": [
                {
                    "id": c.id,
                    "numero": c.numero,
                    "monto_base_bs": round(c.monto_base_bs, 2),
                    "monto_total_bs": round(c.monto_total_bs, 2),
                    "fecha_vencimiento": c.fecha_vencimiento.isoformat() if c.fecha_vencimiento else None,
                    "estado": c.estado,
                    "dias_atraso": (hoy - c.fecha_vencimiento).days if c.estado == "pendiente" and hoy > c.fecha_vencimiento else 0
                }
                for c in cuotas
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{id}")
def eliminar_financiamiento(
    id: int, 
    db: Session = Depends(get_db), 
    current_admin = Depends(get_current_admin)
):
    try:
        financiamiento = db.query(Financiamiento).filter(Financiamiento.id == id).first()
        if not financiamiento:
            raise HTTPException(status_code=404, detail="Financiamiento no encontrado")
        
        if financiamiento.estado == "completado":
            raise HTTPException(status_code=400, detail="No se puede eliminar un financiamiento completado")
        
        db.query(Pago).filter(Pago.financiamiento_id == id).delete(synchronize_session=False)
        db.query(Cuota).filter(Cuota.financiamiento_id == id).delete(synchronize_session=False)
        db.delete(financiamiento)
        db.commit()
        
        return {"success": True, "mensaje": f"Financiamiento #{id} eliminado"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
    # backend/app/routers/financiamientos.py

@router.get("")
def listar_financiamientos(
    skip: int = 0,
    limit: int = 50,
    estado: str = None,
    cliente_id: Optional[int] = None,  # ✅ NUEVO PARÁMETRO
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tienda_id: Optional[int] = Depends(get_current_tienda)
):
    try:
        query = db.query(Financiamiento)
        
        # ✅ FILTRO POR TIENDA
        if tienda_id:
            query = query.filter(Financiamiento.tienda_id == tienda_id)
        
        # ✅ FILTRO POR CLIENTE (NUEVO)
        if cliente_id:
            query = query.filter(Financiamiento.cliente_id == cliente_id)
        
        # ✅ FILTRO POR ESTADO
        if estado:
            query = query.filter(Financiamiento.estado == estado)
        
        total = query.count()
        financiamientos = query.order_by(Financiamiento.id.desc()).offset(skip).limit(limit).all()
        
        resultado = []
        for fin in financiamientos:
            cliente = db.query(Cliente).filter(Cliente.id == fin.cliente_id).first()
            
            # ✅ CONTAR CUOTAS PAGADAS
            cuotas_pagadas = db.query(Cuota).filter(
                Cuota.financiamiento_id == fin.id,
                Cuota.estado == "pagada"
            ).count()
            
            resultado.append({
                "id": fin.id,
                "codigo": fin.codigo,
                "cliente_id": fin.cliente_id,
                "cliente_nombre": cliente.nombre if cliente else "Desconocido",
                "descripcion": fin.descripcion,
                "monto_total_bs": round(fin.monto_total_bs, 2),
                "monto_total_usd": round(fin.monto_total_usd, 2),
                "cuotas_aprobadas": fin.cuotas_aprobadas,
                "cuotas_pagadas": cuotas_pagadas,  # ✅ NUEVO
                "estado": fin.estado,
                "tienda_id": fin.tienda_id,
                "tienda_nombre": fin.tienda.nombre if fin.tienda else None,
                "creado_en": fin.creado_en.isoformat() if fin.creado_en else None
            })
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "tienda_filtro": tienda_id,
            "cliente_filtro": cliente_id,  # ✅ NUEVO
            "financiamientos": resultado
        }
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))