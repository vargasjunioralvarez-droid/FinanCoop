# backend/app/shared/utils.py
import os
import random
import uuid
import string
from datetime import datetime, timezone
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# ============================================================
# 🔥 IMPORTS ACTUALIZADOS (NUEVA ESTRUCTURA)
# ============================================================

from app.core.config import NIVELES_CONFIG, NIVELES_CONFIG_DEFAULT
from app.modules.users.models import Cliente
from app.modules.loans.models import Financiamiento, Cuota
from app.modules.config.models import NivelConfig, TasaDolar

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

# ============ FUNCIONES AUXILIARES ============

def normalizar_telefono(telefono: str) -> str:
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
    if len(limpio) == 11 and limpio.startswith('4'):
        return '+58' + limpio
    return limpio

def es_numero_valido(telefono: str) -> bool:
    if not telefono:
        return False
    if telefono.startswith('+58') and len(telefono) == 13:
        operadora = telefono[3:5]
        return operadora in ['41', '42', '412', '414', '416', '424', '426']
    return False

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

# ============ FUNCIONES DE NEGOCIO ============

def calcular_nivel(score: int, db=None):
    if db:
        niveles_db = db.query(NivelConfig).order_by(NivelConfig.min_score).all()
        if niveles_db:
            for n in niveles_db:
                if n.min_score <= score <= n.max_score:
                    return n.nivel, {
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
    
    niveles_ordenados = sorted(NIVELES_CONFIG.items(), key=lambda x: x[1]["min_score"])
    for nivel, config in niveles_ordenados:
        if config["min_score"] <= score <= config["max_score"]:
            return nivel, config
    return "nuevo", NIVELES_CONFIG.get("nuevo", NIVELES_CONFIG_DEFAULT["nuevo"])

def actualizar_score_cliente(cliente: Cliente, db):
    puntos = 0
    
    financiamientos_completados = db.query(Financiamiento).filter(
        Financiamiento.cliente_id == cliente.id,
        Financiamiento.estado == "completado"
    ).all()
    
    puntos += len(financiamientos_completados) * 33
    
    cuotas_pagadas = db.query(Cuota).join(Financiamiento).filter(
        Financiamiento.cliente_id == cliente.id,
        Cuota.estado == "pagada",
        Cuota.fecha_pago != None
    ).all()
    
    for cuota in cuotas_pagadas:
        if cuota.fecha_pago and cuota.fecha_vencimiento:
            dias_diferencia = (cuota.fecha_vencimiento.date() - cuota.fecha_pago.date()).days
            
            if dias_diferencia >= 3:
                puntos += 15
            elif dias_diferencia >= 0:
                puntos += 10
            else:
                puntos -= 5
    
    hoy = datetime.now(timezone.utc)
    cuotas_vencidas = db.query(Cuota).join(Financiamiento).filter(
        Financiamiento.cliente_id == cliente.id,
        Cuota.estado == "pendiente",
        Cuota.fecha_vencimiento < hoy
    ).count()
    
    if cuotas_vencidas == 0 and len(financiamientos_completados) > 0:
        puntos += 5
    
    puntos = max(0, int(puntos))
    
    cliente.score = puntos
    cliente.total_compras = len(financiamientos_completados)
    
    nuevo_nivel, config = calcular_nivel(cliente.score, db)
    cliente.nivel = nuevo_nivel
    
    db.commit()
    
    print(f"🎯 Score: {cliente.nombre} | {cliente.score} pts | Nivel: {cliente.nivel} | Compras: {cliente.total_compras}")
    return puntos

def generar_pin():
    """Genera PIN de 6 caracteres (números + letras mayúsculas, sin 0/O/1/I/L)"""
    caracteres = string.digits + string.ascii_uppercase
    caracteres = caracteres.replace('0','').replace('O','').replace('1','').replace('I','').replace('L','')
    return ''.join(random.choices(caracteres, k=6))

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
    financiamientos = db.query(Financiamiento).filter(Financiamiento.estado == "activo").all()
    recalculados = 0
    for fin in financiamientos:
        fin.monto_total_bs = fin.monto_total_usd * nueva_tasa
        fin.monto_entrada_bs = fin.monto_entrada_usd * nueva_tasa
        fin.monto_financia_bs = fin.monto_financia_usd * nueva_tasa
        fin.monto_cuota_bs = fin.monto_cuota_usd * nueva_tasa
        cuotas = db.query(Cuota).filter(Cuota.financiamiento_id == fin.id, Cuota.estado.in_(["pendiente", "conciliando"])).all()
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
    nivel, config = calcular_nivel(cliente.score, db)
    limite_usd = config["monto_max_usd"]
    limite_bs = limite_usd * tasa
    activos = db.query(Financiamiento).filter(Financiamiento.cliente_id == cliente_id, Financiamiento.estado == "activo").all()
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