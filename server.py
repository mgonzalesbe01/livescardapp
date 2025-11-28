# Servidor Backend en Python usando Flask y Mercado Pago SDK
# Este servidor reemplaza al antiguo server.js

import os
import json
from flask import Flask, request, jsonify, send_from_directory
from mercadopago import SDK

# --- CONFIGURACIÓN DEL ENTORNO ---
# El Access Token se lee de la variable de entorno de Render (MP_ACCESS_TOKEN)
# Si no existe (localmente), usa un placeholder.
MP_ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN", "TEST-1144922300830729-112020-c3714d198cb79e9f236ea77c1278cb54-3005078586")

# Inicializar el SDK de Mercado Pago
mp = SDK(MP_ACCESS_TOKEN)

# Inicializar la aplicación Flask
# static_folder='public' le dice a Flask dónde buscar archivos HTML/JS
app = Flask(__name__, static_folder='public')

# Almacenamiento en memoria para las tarjetas (para fines de demostración)
tarjetas_live = []
tarjetas_dead = []

# --- RUTAS DE LA APLICACIÓN ---

# 1. Ruta para servir archivos estáticos (Frontend)
@app.route('/')
def serve_index():
    """Sirve el archivo index.html."""
    return send_from_directory(app.static_folder, 'index.html')

# 2. Endpoint para obtener las listas de tarjetas (GET)
@app.route('/obtener-estados', methods=['GET'])
def obtener_estados():
    """Retorna las listas de tarjetas live y dead."""
    return jsonify({
        'live': tarjetas_live,
        'dead': tarjetas_dead
    })

# 3. Endpoint para procesar el pago (POST)
@app.route('/procesar-pago', methods=['POST'])
def procesar_pago():
    """Procesa el pago usando el SDK de Mercado Pago."""
    data = request.json
    
    token = data.get('token')
    payment_method_id = data.get('payment_method_id')
    issuer_id = data.get('issuer_id')
    installments = data.get('installments')
    transaction_amount = data.get('transaction_amount')
    cardholder_email = data.get('cardholderEmail')

    ultimos_4 = token[-4:] if token else "N/A"

    try:
        # 💡 SDK de Python usa la estructura de la API V1
        payment_data = {
            # Monto debe ser float
            "transaction_amount": float(transaction_amount), 
            "token": token,
            "description": "Prueba de tarjeta de crédito",
            "installments": int(installments),
            "payment_method_id": payment_method_id,
            "issuer_id": issuer_id,
            
            # 🚀 Forzamos 'currency_id' ya que la API lo requirió en el último error
            "currency_id": "PEN", 

            # Datos del pagador (para el Policy Agent)
            "payer": {
                "email": cardholder_email,
                "first_name": "Test",
                "last_name": "User",
                "identification": {
                    "type": "DNI",
                    "number": "999999999", 
                }
            }
        }
        
        # Crear el pago
        payment_response = mp.payment().create(payment_data)
        response_status = payment_response['response']['status']
        
        if response_status == 'approved':
            tarjetas_live.append({
                'ultimos4': ultimos_4, 
                'status': response_status, 
                'id': payment_response['response']['id']
            })
            return jsonify({
                "status": "live",
                "message": "Tarjeta aprobada (Live)",
                "paymentId": payment_response['response']['id']
            })
        else:
            # Capturar detalles del rechazo
            status_detail = payment_response['response'].get('status_detail', 'Unknown')
            tarjetas_dead.append({
                'ultimos4': ultimos_4, 
                'status': response_status, 
                'detail': status_detail
            })
            return jsonify({
                "status": "dead",
                "message": f"Tarjeta rechazada: {status_detail}"
            }), 400

    except Exception as e:
        app.logger.error(f"Error al procesar el pago: {e}")
        error_message = str(e)
        tarjetas_dead.append({'ultimos4': ultimos_4, 'status': 'error', 'detail': error_message})
        return jsonify({"status": "dead", "message": error_message}), 400

# --- EJECUCIÓN DEL SERVIDOR ---
if __name__ == '__main__':
    # Render usa la variable de entorno PORT; localmente usa 5000 
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)