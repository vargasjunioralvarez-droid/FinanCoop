# backend/app/routers/upload.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.auth import get_current_user
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
    """
    try:
        # Validar que las credenciales estén configuradas
        if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
            raise HTTPException(
                status_code=500, 
                detail="Cloudflare no configurado. Contacte al administrador."
            )
        
        # Validar tipo de archivo
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400, 
                detail="Solo se permiten imágenes (jpg, png, jpeg, webp)"
            )
        
        # Validar tamaño (máximo 5MB)
        contenido = await file.read()
        if len(contenido) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=400, 
                detail="La imagen no puede superar los 5MB"
            )
        
        # Generar nombre único para el archivo
        extension = file.filename.split('.')[-1] if file.filename else 'jpg'
        nombre_archivo = f"comprobante_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}.{extension}"
        
        # Subir a Cloudflare Images
        url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/images/v1"
        files = {'file': (nombre_archivo, contenido, file.content_type)}
        headers = {'Authorization': f'Bearer {CLOUDFLARE_API_TOKEN}'}
        
        print(f"📤 Subiendo comprobante a Cloudflare: {nombre_archivo}")
        print(f"📤 Account ID: {CLOUDFLARE_ACCOUNT_ID}")
        print(f"📤 Token: {CLOUDFLARE_API_TOKEN[:10]}...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, files=files)
            
            print(f"📥 Respuesta Cloudflare: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    # Obtener la URL de la imagen (variants[0] es la URL completa)
                    image_url = result['result']['variants'][0]
                    print(f"✅ Comprobante subido: {image_url}")
                    return {
                        "success": True,
                        "url": image_url,
                        "message": "Comprobante subido exitosamente"
                    }
                else:
                    error = result.get('errors', [{'message': 'Error desconocido'}])[0]
                    raise HTTPException(
                        status_code=500,
                        detail=f"Error de Cloudflare: {error.get('message')}"
                    )
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Error subiendo a Cloudflare: {response.text}"
                )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error subiendo comprobante: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))