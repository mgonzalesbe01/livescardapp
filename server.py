# Servidor Backend en Python usando Flask y Mercado Pago SDK
# Versión con diccionario de errores expandido para evitar "Desconocido"

import os
import json
from flask import Flask, request, jsonify, send_from_directory
from mercadopago import SDK
from werkzeug.exceptions import BadRequest

# --- CONFIGURACIÓN DE SEGURIDAD ---
# Intenta leer el Access Token de la variable de entorno de Render.
# Si no la encuentra (localmente), usa el valor por defecto.
# IMPORTANTE: En Render, configura la variable MP_ACCESS_TOKEN con tu token de Producción.
MP_ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN", "TU_TOKEN_DE_PRODUCCION_AQUI")

# Inicializar el SDK de Mercado Pago
mp = SDK(MP_ACCESS_TOKEN)

# Inicializar la aplicación Flask. 
# static_folder='public' indica dónde están los archivos HTML/JS
app = Flask(__name__, static_folder='public')

# --- RUTAS DE LA APLICACIÓN ---

# 1. Ruta raíz: Sirve el archivo index.html
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

# 2. Endpoint para obtener las listas de tarjetas (GET)
# En una app real, esto vendría de una base de datos.
@app.route('/obtener-estados', methods=['GET'])
def obtener_estados():
    # Retornamos listas vacías por defecto para esta demo
    return jsonify({'live': [], 'dead': []})

# 3. Endpoint principal: Procesar el Pago (POST)
@app.route('/procesar-pago', methods=['POST'])
def procesar_pago():
    """Recibe los datos del frontend y crea el pago en Mercado Pago."""
    
    if not request.json:
        raise BadRequest('El cuerpo de la solicitud debe ser JSON')
        
    data = request.json
    
    # Extraer datos del formulario
    token = data.get('token')
    payment_method_id = data.get('payment_method_id')
    issuer_id = data.get('issuer_id')
    installments = data.get('installments')
    transaction_amount = data.get('transaction_amount')
    cardholder_email = data.get('cardholderEmail')
    
    # Obtener el nombre real para mejorar la aprobación antifraude
    cardholder_name = data.get('cardholderName', 'Usuario Prueba')
    
    # Separar nombre y apellido (Lógica simple)
    parts = cardholder_name.split()
    first_name = parts[0] if len(parts) > 0 else "Usuario"
    last_name = " ".join(parts[1:]) if len(parts) > 1 else "Prueba"

    try:
        # Construir el objeto de pago
        payment_data = {
            "transaction_amount": float(transaction_amount),
            "token": token,
            "description": "Verificación de Tarjeta",
            "installments": int(installments),
            "payment_method_id": payment_method_id,
            "issuer_id": issuer_id,
            
            # Usamos 'currency_id' (PEN) para asegurar compatibilidad con la API
            "currency_id": "PEN",

            "payer": {
                "email": cardholder_email,
                "first_name": first_name,
                "last_name": last_name,
                # DNI genérico necesario para el entorno de pagos
                "identification": {
                    "type": "DNI",
                    "number": "44556677" 
                }
            }
        }
        
        # Llamar a la API de Mercado Pago
        payment_response = mp.payment().create(payment_data)
        response_data = payment_response.get('response', {})
        response_status = response_data.get('status')
        status_detail = response_data.get('status_detail', 'sin_detalle')
        
        # 🚀 LOGGING: Imprimir respuesta en la consola de Render para depuración
        print("\n--- RESPUESTA DE MERCADO PAGO ---")
        print(f"Status: {response_status}")
        print(f"Status Detail: {status_detail}")
        print("---------------------------------\n")
        
        # Manejar respuesta APROBADA
        if response_status == 'approved':
            return jsonify({
                "status": "live",
                "message": "Tarjeta Aprobada (Live) ✅",
                "paymentId": response_data.get('id')
            })
        
        # Manejar respuesta RECHAZADA u OTROS
        else:
            # Diccionario para traducir códigos de error a mensajes amigables
            mensajes_error = {
                "cc_rejected_bad_filled_card_number": "Revisa el número de tarjeta.",
                "cc_rejected_bad_filled_date": "Revisa la fecha de vencimiento.",
                "cc_rejected_bad_filled_other": "Revisa los datos de la tarjeta.",
                "cc_rejected_bad_filled_security_code": "Revisa el código de seguridad.",
                "cc_rejected_blacklist": "No pudimos procesar tu pago.",
                "cc_rejected_call_for_authorize": "Debes autorizar el pago llamando a tu banco.",
                "cc_rejected_card_disabled": "Tarjeta inactiva o deshabilitada. Llama a tu banco.",
                "cc_rejected_card_error": "Error general de la tarjeta.",
                "cc_rejected_duplicated_payment": "Pago duplicado. Espera unos minutos.",
                "cc_rejected_high_risk": "Rechazado por Prevención de Fraude (Alto Riesgo).",
                "cc_rejected_insufficient_amount": "Tu tarjeta no tiene fondos suficientes.",
                "cc_rejected_invalid_installments": "La tarjeta no procesa pagos en cuotas.",
                "cc_rejected_max_attempts": "Llegaste al límite de intentos permitidos.",
                "cc_rejected_other_reason": "El banco no procesó el pago.",
                "cc_rejected_processor_error": "Error del procesador de pagos.",
                "sin_detalle": "No se recibió detalle del error."
            }
            
            # Obtener el mensaje traducido o mostrar el técnico si no existe
            mensaje_amigable = mensajes_error.get(status_detail, f"Rechazo del Banco: {status_detail}")

            return jsonify({
                "status": "dead",
                "message": mensaje_amigable
            })

    except Exception as e:
        # Captura errores críticos (como fallos de conexión o configuración)
        print(f"Error crítico en el servidor: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400

# 4. Ruta para servir archivos estáticos adicionales (JS, CSS, Imágenes)
# Esto permite que el navegador encuentre 'app_v2.js' y 'favicon.ico'
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

# --- INICIO DEL SERVIDOR ---
if __name__ == '__main__':
    # Render asigna el puerto en la variable de entorno PORT
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)