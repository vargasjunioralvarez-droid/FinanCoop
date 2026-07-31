# backend/app/infrastructure/twilio.py
"""
📱 Infraestructura de mensajería - Twilio SMS/WhatsApp
Extraído de shared/utils.py para separar responsabilidades.
"""

import os
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# Importar utilidades puras desde shared (no crea dependencia circular porque shared no importa twilio)
from app.shared.helpers import normalizar_telefono, es_numero_valido

# ============ CONFIGURACIÓN TWILIO ============
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')
TWILIO_SMS_FROM = os.getenv('TWILIO_SMS_FROM')

twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    try:
        twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        print("✅ Twilio cliente inicializado")
    except Exception as e:
        print(f"❌ Error inicializando Twilio: {e}")

# ============ FUNCIONES DE ENVÍO DE MENSAJES ============

def enviar_whatsapp(telefono: str, mensaje: str):
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
            error_msg = "El usuario no ha iniciado conversación con el sandbox."
        elif "63018" in error_msg:
            error_msg = "El número de destino no tiene WhatsApp."
        elif "429" in str(e.status):
            error_msg = "Límite de mensajes diarios excedido."
        print(f"❌ Error WhatsApp: {error_msg}")
        return False, error_msg
    except Exception as e:
        print(f"❌ Error WhatsApp: {e}")
        return False, str(e)


def enviar_pin_sms(telefono: str, nombre: str, cedula: str, pin: str):
    telefono = normalizar_telefono(telefono)
    if not es_numero_valido(telefono):
        return {"success": False, "error": f"Número inválido: {telefono}", "sms_enviado": False}
    if not twilio_client:
        return {"success": False, "error": "Twilio no disponible", "sms_enviado": False}
    if not TWILIO_SMS_FROM:
        return {"success": False, "error": "TWILIO_SMS_FROM no configurado", "sms_enviado": False}
    
    mensaje_sms = f"""FinanCoop

¡Bienvenido {nombre}!

🔑 Tu PIN de acceso es: {pin}
🆔 Cédula: {cedula}

📱 Descarga la app e inicia sesión con tu cédula y este PIN.

⚠️ No compartas este PIN con nadie.

¡Gracias por confiar en FinanCoop!"""

    try:
        message = twilio_client.messages.create(body=mensaje_sms, from_=TWILIO_SMS_FROM, to=telefono)
        print(f"✅ SMS enviado a {telefono}. SID: {message.sid}")
        return {"success": True, "sid": message.sid, "sms_enviado": True, "mensaje": f"SMS enviado a {telefono}"}
    except TwilioRestException as e:
        error_msg = str(e)
        if "21211" in error_msg:
            error_msg = "Número de teléfono inválido"
        elif "21610" in error_msg:
            error_msg = "Número no tiene capacidad para recibir SMS"
        elif "429" in str(e.status):
            error_msg = "Límite de mensajes diarios excedido"
        elif "20003" in error_msg:
            error_msg = "Credenciales de Twilio inválidas"
        print(f"❌ Error SMS: {error_msg}")
        return {"success": False, "error": error_msg, "sms_enviado": False}
    except Exception as e:
        print(f"❌ Error SMS: {e}")
        return {"success": False, "error": str(e), "sms_enviado": False}


def enviar_pin_cliente(telefono: str, nombre: str, cedula: str, pin: str):
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
    
    resultado = {"whatsapp_enviado": False, "whatsapp_sid": None, "pin": pin, "mensaje": "", "telefono_normalizado": telefono}
    print(f"📱 Intentando WhatsApp a {telefono}...")
    exito_wa, sid_wa = enviar_whatsapp(telefono, mensaje_whatsapp)
    if exito_wa:
        resultado["whatsapp_enviado"] = True
        resultado["whatsapp_sid"] = sid_wa
        resultado["mensaje"] = f"✅ WhatsApp enviado a {telefono}"
        print(f"✅ WhatsApp exitoso: {sid_wa}")
    else:
        resultado["mensaje"] = f"⚠️ No se pudo enviar WhatsApp: {sid_wa}"
        print(f"⚠️ WhatsApp falló: {sid_wa}")
    return resultado


def enviar_pin_cliente_completo(telefono: str, nombre: str, cedula: str, pin: str):
    print(f"📱 Enviando PIN a {nombre} ({telefono})...")
    print("📤 Intentando SMS...")
    resultado_sms = enviar_pin_sms(telefono, nombre, cedula, pin)
    if resultado_sms["success"]:
        print(f"✅ PIN enviado por SMS a {telefono}")
        return {"success": True, "mensaje": "PIN enviado por SMS", "canal": "sms", "sid": resultado_sms.get("sid"), "pin": "****"}
    print(f"⚠️ SMS falló: {resultado_sms.get('error')}")
    print("📤 Intentando WhatsApp como fallback...")
    resultado_whatsapp = enviar_pin_cliente(telefono, nombre, cedula, pin)
    if resultado_whatsapp["whatsapp_enviado"]:
        print(f"✅ PIN enviado por WhatsApp a {telefono}")
        return {"success": True, "mensaje": "PIN enviado por WhatsApp (fallback)", "canal": "whatsapp", "sid": resultado_whatsapp.get("whatsapp_sid"), "pin": "****", "sms_error": resultado_sms.get("error")}
    print(f"❌ No se pudo enviar PIN por ningún canal")
    return {"success": False, "mensaje": "No se pudo enviar el PIN por ningún canal", "error_sms": resultado_sms.get("error"), "error_whatsapp": resultado_whatsapp.get("mensaje"), "pin": "****", "sms_info": resultado_sms}


def enviar_notificacion_generica(telefono: str, mensaje: str):
    telefono = normalizar_telefono(telefono)
    if twilio_client and TWILIO_SMS_FROM:
        try:
            message = twilio_client.messages.create(body=mensaje[:160], from_=TWILIO_SMS_FROM, to=telefono)
            print(f"✅ SMS genérico enviado: {message.sid}")
            return {"success": True, "canal": "sms", "sid": message.sid}
        except Exception as e:
            print(f"⚠️ SMS genérico falló: {e}")
    exito, sid = enviar_whatsapp(telefono, mensaje)
    if exito:
        return {"success": True, "canal": "whatsapp", "sid": sid}
    return {"success": False, "error": "No se pudo enviar por ningún canal"}