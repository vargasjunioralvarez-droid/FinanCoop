# backend/app/routers/upload.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.auth import get_current_user
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Financiamiento
import httpx
import os
import uuid
from datetime import datetime

router = APIRouter(prefix="/upload", tags=["Upload"])

CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")

@router.post("/comprobante")
async def upload_comprobante(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    """
    Sube un comprobante de pago a Cloudflare Images
    Cualquier usuario autenticado puede subir comprobantes
    """
    try:
        print("=" * 50)
        print("📤 UPLOAD COMPROBANTE - INICIO")
        print(f"👤 Usuario: {current_user.username if hasattr(current_user, 'username') else 'Cliente'}")
        print(f"📸 Archivo: {file.filename}")
        print(f"📸 Tipo: {file.content_type}")
        
        # Validar que las credenciales estén configuradas
        if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
            print("❌ Cloudflare NO configurado")
            raise HTTPException(
                status_code=500, 
                detail="Cloudflare no configurado. Contacte al administrador."
            )
        
        print(f"✅ Cloudflare Account ID: {CLOUDFLARE_ACCOUNT_ID[:10]}...")
        print(f"✅ Cloudflare Token: {CLOUDFLARE_API_TOKEN[:10]}...")
        
        # Validar tipo de archivo
        if not file.content_type or not file.content_type.startswith('image/'):
            print(f"❌ Tipo de archivo inválido: {file.content_type}")
            raise HTTPException(
                status_code=400, 
                detail="Solo se permiten imágenes (jpg, png, jpeg, webp)"
            )
        
        # Validar tamaño (máximo 5MB)
        contenido = await file.read()
        tamaño_mb = len(contenido) / (1024 * 1024)
        print(f"📊 Tamaño: {tamaño_mb:.2f} MB")
        
        if len(contenido) > 5 * 1024 * 1024:
            print(f"❌ Archivo demasiado grande: {tamaño_mb:.2f} MB")
            raise HTTPException(
                status_code=400, 
                detail="La imagen no puede superar los 5MB"
            )
        
        # Generar nombre único para el archivo
        extension = file.filename.split('.')[-1] if file.filename else 'jpg'
        nombre_archivo = f"comprobante_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}.{extension}"
        
        print(f"📤 Subiendo a Cloudflare: {nombre_archivo}")
        
        # Subir a Cloudflare Images
        url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/images/v1"
        files = {'file': (nombre_archivo, contenido, file.content_type)}
        headers = {'Authorization': f'Bearer {CLOUDFLARE_API_TOKEN}'}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, files=files)
            
            print(f"📥 Respuesta Cloudflare: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    # Obtener la URL de la imagen (variants[0] es la URL completa)
                    image_url = result['result']['variants'][0]
                    print(f"✅ Comprobante subido exitosamente")
                    print(f"🔗 URL: {image_url}")
                    print("=" * 50)
                    return {
                        "success": True,
                        "url": image_url,
                        "message": "Comprobante subido exitosamente"
                    }
                else:
                    error = result.get('errors', [{'message': 'Error desconocido'}])[0]
                    print(f"❌ Error Cloudflare: {error}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Error de Cloudflare: {error.get('message')}"
                    )
            else:
                print(f"❌ Error HTTP: {response.status_code}")
                print(f"📄 Respuesta: {response.text[:200]}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Error subiendo a Cloudflare: {response.text[:100]}"
                )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error subiendo comprobante: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# 📸 SUBIR FACTURA (APP MÓVIL)
# ============================================================

@router.post("/factura/{financiamiento_id}")
async def upload_factura(
    financiamiento_id: int,
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sube foto de factura desde la app móvil a Cloudflare"""
    try:
        fin = db.query(Financiamiento).filter(Financiamiento.id == financiamiento_id).first()
        if not fin:
            raise HTTPException(status_code=404, detail="Financiamiento no encontrado")
        
        # Verificar que el cliente sea dueño del financiamiento
        if hasattr(current_user, 'id') and fin.cliente_id != current_user.id:
            raise HTTPException(status_code=403, detail="No autorizado")
        
        contenido = await file.read()
        if len(contenido) == 0:
            raise HTTPException(status_code=400, detail="Archivo vacío")
        
        # Validar tamaño (máximo 5MB)
        tamaño_mb = len(contenido) / (1024 * 1024)
        if tamaño_mb > 5:
            raise HTTPException(status_code=400, detail="La imagen no puede superar los 5MB")
        
        # Subir a Cloudflare
        nombre = f"factura_{financiamiento_id}_{uuid.uuid4().hex[:8]}.jpg"
        url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/images/v1"
        files = {'file': (nombre, contenido, file.content_type or 'image/jpeg')}
        headers = {'Authorization': f'Bearer {CLOUDFLARE_API_TOKEN}'}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, files=files)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    image_url = result['result']['variants'][0]
                    fin.url_factura = image_url
                    db.commit()
                    print(f"✅ Factura subida: {image_url}")
                    return {"success": True, "url": image_url}
        
        raise HTTPException(status_code=500, detail="Error subiendo factura a Cloudflare")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error subiendo factura: {e}")
        raise HTTPException(status_code=500, detail=str(e))