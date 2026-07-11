# backend/app/utils.py
import os
import random
import uuid
from datetime import datetime
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from app.config import NIVELES_CONFIG, NIVELES_CONFIG_DEFAULT
from app.models import Cliente, Financiamiento, Cuota, NivelConfig, TasaDolar

# ============ CONFIGURACIÓN TWILIO ============
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')

twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    try:
        twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        print("✅ Twilio cliente inicializado")
    except Exception as e:
        print(f"❌ Error inicializando Twilio: {e}")

# ============ FUNCIONES AUXILIARES ============

def normalizar_telefono(telefono: str) -> str:
    """
    Normaliza un número de teléfono venezolano al formato internacional.
    """
    if not telefono:
        return ""
    
    limpio = ''.join(c for c in telefono if c.isdigit() or c == '+')
    
    if limpio.startswith('+58') and len(limpio) == 13:
        return limpio
    
    if limpio.startswith('+580') and len(limpio) == 14:
        return '+58' + limpio[4:]
    
    if limpio.startswith('0') and len(limpio) == 11:
        return '+58' + limpio[1:]
    
    if limpio.startswith('4') and len(limpio) == 10:
        return '+58' + limpio
    
    if limpio.startswith('+'):
        return limpio
    
    if len(limpio) == 10 and limpio.startswith('4'):
        return '+58' + limpio
    
    return limpio

def es_numero_valido(telefono: str) -> bool:
    """Verifica si el número tiene formato válido para Venezuela."""
    if not telefono:
        return False
    
    if telefono.startswith('+58') and len(telefono) == 13:
        operadora = telefono[3:5]
        return operadora in ['41', '42', '412', '414', '416', '424', '426']
    
    return False

# ============ FUNCIONES DE ENVÍO DE MENSAJES ============

def enviar_whatsapp(telefono: str, mensaje: str):
    """Envía mensaje por WhatsApp usando Twilio."""
    if not twilio_client:
        print("❌ Twilio no disponible")
        return False, "Twilio no disponible"
    
    telefono = normalizar_telefono(telefono)
    
    if not es_numero_valido(telefono):
        print(f"❌ Número inválido: {telefono}")
        return False, f"Número inválido: {telefono}"
    
    try:
        message = twilio_client.messages.create(
            body=mensaje,
            from_=TWILIO_WHATSAPP_NUMBER,
            to=f'whatsapp:{telefono}'
        )
        
        print(f"✅ WhatsApp enviado a {telefono}. SID: {message.sid}")
        return True, message.sid
        
    except TwilioRestException as e:
        error_msg = str(e)
        if "63016" in error_msg:
            error_msg = "El usuario no ha iniciado conversación con el sandbox. Debe enviar 'join <palabra>' primero."
        elif "63018" in error_msg:
            error_msg = "El número de destino no tiene WhatsApp o no es válido."
        elif "429" in str(e.status):
            error_msg = "Límite de mensajes diarios excedido."
        
        print(f"❌ Error WhatsApp: {error_msg}")
        return False, error_msg
    except Exception as e:
        print(f"❌ Error WhatsApp: {e}")
        return False, str(e)

def enviar_pin_cliente(telefono: str, nombre: str, cedula: str, pin: str):
    """
    Envía el PIN al cliente por WhatsApp.
    Si falla, siempre devuelve el PIN para mostrar en pantalla.
    """
    telefono = normalizar_telefono(telefono)
    
    mensaje_whatsapp = f"""🎉 *¡Bienvenido a FinanCoop, {nombre}!*

🔑 *Tu PIN de acceso es:* {pin}

📋 *Tus datos:*
🆔 Cédula: {cedula}
📞 Teléfono: {telefono}

✅ *Próximos pasos:*
1. Descarga la app FinanCoop
2. Ingresa con tu cédula y PIN
3. Comienza a comprar en tiendas afiliadas

⚠️ *Importante:*
- Tu deuda se mantiene en USD
- Pagas en Bs al tipo de cambio del día
- Tienes 3 días de gracia

📱 *¿Dudas?* Visita tu tienda Cecosesola más cercana.

¡Gracias por confiar en FinanCoop! 🚀"""
    
    resultado = {
        "whatsapp_enviado": False,
        "whatsapp_sid": None,
        "pin": pin,
        "mensaje": "",
        "telefono_normalizado": telefono
    }
    
    # Intentar WhatsApp
    print(f"📱 Intentando WhatsApp a {telefono}...")
    exito_wa, sid_wa = enviar_whatsapp(telefono, mensaje_whatsapp)
    
    if exito_wa:
        resultado["whatsapp_enviado"] = True
        resultado["whatsapp_sid"] = sid_wa
        resultado["mensaje"] = f"✅ WhatsApp enviado a {telefono}"
        print(f"✅ WhatsApp exitoso: {sid_wa}")
    else:
        resultado["mensaje"] = (
            f"⚠️ No se pudo enviar WhatsApp: {sid_wa}. "
            f"El PIN es: {pin}. Por favor, guárdalo o comunícalo al cliente."
        )
        print(f"⚠️ WhatsApp falló: {sid_wa}")
    
    # Siempre devolver el PIN para mostrar en pantalla
    return resultado

# ============ FUNCIONES DE NEGOCIO ============

def calcular_nivel(score: int):
    for nivel, config in NIVELES_CONFIG.items():
        if config["min_score"] <= score <= config["max_score"]:
            return nivel, config
    return "nuevo", NIVELES_CONFIG["nuevo"]

def actualizar_score_cliente(cliente: Cliente, db):
    financiamientos_completados = db.query(Financiamiento).filter(
        Financiamiento.cliente_id == cliente.id,
        Financiamiento.estado == "completado"
    ).count()
    
    cliente.score = financiamientos_completados
    cliente.total_compras = db.query(Financiamiento).filter(
        Financiamiento.cliente_id == cliente.id
    ).count()
    
    nuevo_nivel, config = calcular_nivel(cliente.score)
    cliente.nivel = nuevo_nivel
    
    db.commit()

def generar_pin():
    return str(random.randint(1000, 9999))

def generar_token():
    return str(uuid.uuid4())

def obtener_tasa_actual(db):
    tasa = db.query(TasaDolar).order_by(TasaDolar.id.desc()).first()
    if not tasa:
        tasa = TasaDolar(tasa=40.0)
        db.add(tasa)
        db.commit()
    return tasa.tasa

def recalcular_cuotas_pendientes(db, nueva_tasa: float):
    financiamientos = db.query(Financiamiento).filter(
        Financiamiento.estado == "activo"
    ).all()
    
    recalculados = 0
    for fin in financiamientos:
        fin.monto_total_bs = fin.monto_total_usd * nueva_tasa
        fin.monto_entrada_bs = fin.monto_entrada_usd * nueva_tasa
        fin.monto_financia_bs = fin.monto_financia_usd * nueva_tasa
        fin.monto_cuota_bs = fin.monto_cuota_usd * nueva_tasa
        
        cuotas = db.query(Cuota).filter(
            Cuota.financiamiento_id == fin.id,
            Cuota.estado.in_(["pendiente", "conciliando"])
        ).all()
        
        for c in cuotas:
            c.monto_base_bs = c.monto_base_usd * nueva_tasa
            c.monto_interes_mora_bs = c.monto_interes_mora_usd * nueva_tasa
            c.monto_total_bs = c.monto_total_usd * nueva_tasa
        
        recalculados += len(cuotas)
    
    db.commit()
    return recalculados

def calcular_usado_disponible(cliente_id: int, db):
    tasa = obtener_tasa_actual(db)
    
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        return {}
    
    nivel, config = calcular_nivel(cliente.score)
    
    limite_usd = config["monto_max_usd"]
    limite_bs = limite_usd * tasa
    
    activos = db.query(Financiamiento).filter(
        Financiamiento.cliente_id == cliente_id,
        Financiamiento.estado == "activo"
    ).all()
    
    usado_usd = sum(f.monto_total_usd for f in activos)
    usado_bs = sum(f.monto_total_bs for f in activos)
    
    disponible_usd = max(0, limite_usd - usado_usd)
    disponible_bs = max(0, limite_bs - usado_bs)
    
    return {
        "nivel": nivel,
        "limite_usd": round(limite_usd, 2),
        "limite_bs": round(limite_bs, 2),
        "usado_usd": round(usado_usd, 2),
        "usado_bs": round(usado_bs, 2),
        "disponible_usd": round(disponible_usd, 2),
        "disponible_bs": round(disponible_bs, 2),
        "cantidad_activos": len(activos),
        "puede_comprar": disponible_usd > 0
    }

def init_niveles_db(db):
    for nivel_key, config in NIVELES_CONFIG_DEFAULT.items():
        existe = db.query(NivelConfig).filter(NivelConfig.nivel == nivel_key).first()
        if not existe:
            nc = NivelConfig(
                nivel=nivel_key,
                min_score=config["min_score"],
                max_score=config["max_score"],
                monto_max_usd=config["monto_max_usd"],
                entrada_pct=config["entrada_pct"],
                financia_pct=config["financia_pct"],
                cuotas_base=config["cuotas_base"],
                cuotas_max=config["cuotas_max"],
                mora_diaria=config["mora_diaria"],
                aprobacion_extra=config["aprobacion_extra"]
            )
            db.add(nc)
    db.commit()

def get_niveles_config(db):
    global NIVELES_CONFIG
    niveles = db.query(NivelConfig).all()
    if niveles:
        NIVELES_CONFIG = {}
        for n in niveles:
            NIVELES_CONFIG[n.nivel] = {
                "min_score": n.min_score,
                "max_score": n.max_score,
                "monto_max_usd": n.monto_max_usd,
                "entrada_pct": n.entrada_pct,
                "financia_pct": n.financia_pct,
                "cuotas_base": n.cuotas_base,
                "cuotas_max": n.cuotas_max,
                "mora_diaria": n.mora_diaria,
                "aprobacion_extra": n.aprobacion_extra
            }
    return NIVELES_CONFIG