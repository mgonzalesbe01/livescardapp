# Servidor Backend en Python usando Flask y Mercado Pago SDK
# Versión con CORS habilitado y Rutas Relativas soportadas

import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS # 🚀 IMPORTANTE: Importamos CORS
from mercadopago import SDK
from werkzeug.exceptions import BadRequest

# --- CONFIGURACIÓN ---
MP_ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN", "APP_USR-1144922300830729-112020-5ea5bc88cad445723e167d84442662b9-3005078586")
mp = SDK(MP_ACCESS_TOKEN)

app = Flask(__name__, static_folder='public')
CORS(app) # 🚀 IMPORTANTE: Habilitamos CORS para toda la app

# --- RUTAS ---

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/obtener-estados', methods=['GET'])
def obtener_estados():
    return jsonify({'live': [], 'dead': []})

@app.route('/procesar-pago', methods=['POST'])
def procesar_pago():
    if not request.json:
        raise BadRequest('El cuerpo de la solicitud debe ser JSON')
        
    data = request.json
    
    token = data.get('token')
    payment_method_id = data.get('payment_method_id')
    issuer_id = data.get('issuer_id')
    installments = data.get('installments')
    transaction_amount = data.get('transaction_amount')
    cardholder_email = data.get('cardholderEmail')
    
    # Manejo robusto del nombre
    cardholder_name = data.get('cardholderName', 'Usuario Prueba')
    parts = cardholder_name.split()
    first_name = parts[0] if len(parts) > 0 else "Usuario"
    last_name = " ".join(parts[1:]) if len(parts) > 1 else "Prueba"

    try:
        payment_data = {
            "transaction_amount": float(transaction_amount),
            "token": token,
            "description": "Verificación de Tarjeta",
            "installments": int(installments),
            "payment_method_id": payment_method_id,
            "issuer_id": issuer_id,
            "currency_id": "PEN",
            "payer": {
                "email": cardholder_email,
                "first_name": first_name,
                "last_name": last_name,
                "identification": {
                    "type": "DNI",
                    "number": "44556677" 
                }
            }
        }
        
        api_result = mp.payment().create(payment_data)
        
        # DEBUG LOGGING
        http_status = api_result.get("status")
        response_data = api_result.get("response", {})
        
        print("\n--- DEBUG INFO ---")
        print(f"Status: {http_status}")
        print(json.dumps(response_data, indent=2))
        print("------------------\n")
        
        if http_status not in [200, 201]:
            # Extracción segura de mensajes de error de la API
            msg = response_data.get('message', 'Error API')
            return jsonify({"status": "error", "message": msg}), 400

        payment_status = response_data.get('status')
        status_detail = response_data.get('status_detail')

        if payment_status == 'approved':
            return jsonify({
                "status": "live",
                "message": "Tarjeta Aprobada (Live) ✅",
                "paymentId": response_data.get('id')
            })
        else:
            mensajes_error = {
                "cc_rejected_insufficient_amount": "Fondos insuficientes.",
                "cc_rejected_bad_filled_other": "Datos incorrectos.",
                "cc_rejected_bad_filled_card_number": "Número de tarjeta erróneo.",
                "cc_rejected_bad_filled_date": "Fecha de vencimiento errónea.",
                "cc_rejected_bad_filled_security_code": "CVV erróneo.",
                "cc_rejected_blacklist": "Tarjeta denegada.",
                "cc_rejected_call_for_authorize": "Requiere autorización del banco.",
                "cc_rejected_card_disabled": "Tarjeta inactiva.",
                "cc_rejected_card_error": "Error de tarjeta.",
                "cc_rejected_duplicated_payment": "Pago duplicado.",
                "cc_rejected_high_risk": "Rechazo por Riesgo/Seguridad.",
                "cc_rejected_invalid_installments": "Cuotas inválidas.",
                "cc_rejected_max_attempts": "Límite de intentos excedido.",
                "cc_rejected_other_reason": "Error genérico del banco."
            }
            mensaje = mensajes_error.get(status_detail, f"Rechazo: {status_detail}")
            return jsonify({"status": "dead", "message": mensaje})

    except Exception as e:
        print(f"Error crítico: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)