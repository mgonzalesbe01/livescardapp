# Servidor Backend en Python usando Flask y Mercado Pago SDK
import os
import json
from flask import Flask, request, jsonify, send_from_directory
from mercadopago import SDK
from werkzeug.exceptions import BadRequest

# --- CONFIGURACIÓN DE SEGURIDAD ---
# Lee la variable de entorno de Render.
# Si estás probando localmente y no tienes la variable, puedes poner tu token aquí temporalmente,
# pero para PRODUCCIÓN en Render, usa la variable de entorno.
MP_ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN", "TU_TOKEN_DE_PRODUCCION_AQUI")

# Inicializar el SDK
mp = SDK(MP_ACCESS_TOKEN)

app = Flask(__name__, static_folder='public')

# --- RUTAS ---

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/obtener-estados', methods=['GET'])
def obtener_estados():
    # Retorna listas vacías por defecto. En una app real, esto vendría de una BD.
    return jsonify({'live': [], 'dead': []})

@app.route('/procesar-pago', methods=['POST'])
def procesar_pago():
    if not request.json:
        raise BadRequest('El cuerpo de la solicitud debe ser JSON')
        
    data = request.json
    
    # Extracción de datos
    token = data.get('token')
    payment_method_id = data.get('payment_method_id')
    issuer_id = data.get('issuer_id')
    installments = data.get('installments')
    transaction_amount = data.get('transaction_amount')
    cardholder_email = data.get('cardholderEmail')

    try:
        payment_data = {
            "transaction_amount": float(transaction_amount),
            "token": token,
            "description": "Verificación de Tarjeta",
            "installments": int(installments),
            "payment_method_id": payment_method_id,
            "issuer_id": issuer_id,
            
            # 🚀 USAMOS 'currency_id' (Convención API v1 requerida por compatibilidad)
            "currency_id": "PEN",

            "payer": {
                "email": cardholder_email,
                "first_name": "Usuario",
                "last_name": "Prueba",
                "identification": {
                    "type": "DNI",
                    "number": "44556677" 
                }
            }
        }
        
        # Crear el pago
        payment_response = mp.payment().create(payment_data)
        response_data = payment_response.get('response', {})
        response_status = response_data.get('status')
        
        if response_status == 'approved':
            return jsonify({
                "status": "live",
                "message": "Tarjeta Aprobada (Live)",
                "paymentId": response_data.get('id')
            })
        else:
            status_detail = response_data.get('status_detail', 'desconocido')
            # Devolvemos 200 OK incluso si es rechazada para manejarlo en el frontend
            return jsonify({
                "status": "dead",
                "message": f"Tarjeta Rechazada: {status_detail}"
            })

    except Exception as e:
        print(f"Error procesando el pago: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)