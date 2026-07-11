# backend/app/utils.py
import os
import random
import uuid
from datetime import datetime
from twilio.rest import Client
from app.config import NIVELES_CONFIG, NIVELES_CONFIG_DEFAULT
from app.models import Cliente, Financiamiento, Cuota, NivelConfig, TasaDolar

# ============ CONFIGURACIÓN TWILIO ============
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')
TWILIO_SMS_NUMBER = os.getenv('TWILIO_SMS_NUMBER', '+14155238886')

twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    try:
        twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        print("✅ Twilio cliente inicializado")
    except Exception as e:
        print(f"❌ Error inicializando Twilio: {e}")

# ============ FUNCIONES DE ENVÍO DE MENSAJES ============

def enviar_whatsapp(telefono: str, mensaje: str):
    """Envía mensaje por WhatsApp usando Twilio"""
    if not twilio_client:
        print("❌ Twilio no disponible")
        return False, "Twilio no disponible"
    
    try:
        if not telefono.startswith('+'):
            telefono = '+58' + telefono.lstrip('0')
        
        message = twilio_client.messages.create(
            body=mensaje,
            from_=TWILIO_WHATSAPP_NUMBER,
            to=f'whatsapp:{telefono}'
        )
        
        print(f"✅ WhatsApp enviado a {telefono}. SID: {message.sid}")
        return True, message.sid
        
    except Exception as e:
        print(f"❌ Error enviando WhatsApp: {e}")
        return False, str(e)

def enviar_sms(telefono: str, mensaje: str):
    """Envía mensaje por SMS usando Twilio"""
    if not twilio_client:
        print("❌ Twilio no disponible")
        return False, "Twilio no disponible"
    
    try:
        if not telefono.startswith('+'):
            telefono = '+58' + telefono.lstrip('0')
        
        message = twilio_client.messages.create(
            body=mensaje,
            from_=TWILIO_SMS_NUMBER,
            to=telefono
        )
        
        print(f"✅ SMS enviado a {telefono}. SID: {message.sid}")
        return True, message.sid
        
    except Exception as e:
        print(f"❌ Error enviando SMS: {e}")
        return False, str(e)

def enviar_pin_cliente(telefono: str, nombre: str, cedula: str, pin: str):
    """
    Envía el PIN al cliente.
    1. Primero intenta SMS (más confiable en Venezuela)
    2. Luego intenta WhatsApp
    3. Siempre devuelve el PIN para mostrar en pantalla
    """
    mensaje_sms = f"FinanCoop: Tu PIN es {pin}. Usa tu cedula {cedula} para ingresar a la app."
    
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
        "sms_enviado": False,
        "whatsapp_enviado": False,
        "sms_sid": None,
        "whatsapp_sid": None,
        "pin": pin,
        "mensaje": ""
    }
    
    # 1. Intentar SMS primero (más confiable)
    print(f"📱 Intentando SMS a {telefono}...")
    exito_sms, sid_sms = enviar_sms(telefono, mensaje_sms)
    
    if exito_sms:
        resultado["sms_enviado"] = True
        resultado["sms_sid"] = sid_sms
        resultado["mensaje"] = f"✅ SMS enviado a {telefono}"
        print(f"✅ SMS exitoso: {sid_sms}")
    else:
        print(f"⚠️ SMS falló, intentando WhatsApp...")
    
    # 2. Intentar WhatsApp (incluso si SMS funcionó, para asegurar)
    print(f"📱 Intentando WhatsApp a {telefono}...")
    exito_wa, sid_wa = enviar_whatsapp(telefono, mensaje_whatsapp)
    
    if exito_wa:
        resultado["whatsapp_enviado"] = True
        resultado["whatsapp_sid"] = sid_wa
        if resultado["sms_enviado"]:
            resultado["mensaje"] += f" | WhatsApp también enviado: {sid_wa}"
        else:
            resultado["mensaje"] = f"✅ WhatsApp enviado: {sid_wa}"
        print(f"✅ WhatsApp exitoso: {sid_wa}")
    else:
        if not resultado["sms_enviado"]:
            resultado["mensaje"] = f"⚠️ No se pudo enviar SMS ni WhatsApp. PIN: {pin}"
            print(f"❌ Todos los canales fallaron")
        else:
            resultado["mensaje"] += " | WhatsApp no disponible"
    
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