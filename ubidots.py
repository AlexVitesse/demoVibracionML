import requests
import os
import time
import math
from dotenv import load_dotenv

load_dotenv()

UBIDOTS_TOKEN = os.getenv("UBIDOTS_TOKEN")
DEVICE_LABEL = os.getenv("DEVICE_LABEL")

def post_prediction(prediction):
    """
    Publica la predicción en Ubidots usando context para el texto.
    El value siempre será 1 (indica que hay datos), y el texto real va en context.
    """
    # Validar que prediction no sea None, NaN o vacío
    if prediction is None or prediction == "":
        print(f"✗ Valor inválido detectado: {prediction}. No se enviará a Ubidots.")
        return False
    
    # Verificar si es NaN
    try:
        if isinstance(prediction, float) and math.isnan(prediction):
            print(f"✗ Valor NaN detectado. No se enviará a Ubidots.")
            return False
    except (ValueError, TypeError):
        pass
    
    url = f"https://industrial.api.ubidots.com/api/v1.6/devices/{DEVICE_LABEL}"
    headers = {
        "X-Auth-Token": UBIDOTS_TOKEN, 
        "Content-Type": "application/json"
    }
    
    # Mapear predicciones a mensajes descriptivos
    mensajes_contexto = {
        "OK": "PROCESO FUNCIONANDO CORRECTAMENTE",
        "NOK": "ANOMALIA DETECTADA",
        "LP": "LINEA PRESURIZADA",
        "VACIO": "LINEA VACIANDO",
        "APAGADO": "EQUIPO DETENIDO"
    }
    
    # Mapear a valores numéricos para gráficas
    valores_numericos = {
        "OK": 1,
        "NOK": 0,
        "LP": 2,
        "VACIO": 3,
        "APAGADO": 4
    }
    
    prediction_upper = str(prediction).upper()
    mensaje = mensajes_contexto.get(prediction_upper, str(prediction))
    valor = valores_numericos.get(prediction_upper, 1)
    
    # Formato correcto: value numérico + contexto con mensaje descriptivo
    payload = {
        "prediction": {
            "value": valor,  # Valor numérico para gráficas
            "context": {
                "estado": prediction_upper,  # Estado original (OK, NOK, etc)
                "mensaje": mensaje,  # Mensaje descriptivo
                "timestamp_legible": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "timestamp": int(time.time() * 1000)
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        print(f"✓ Predicción enviada: '{prediction}'")
        print(f"  Respuesta: {response.json()}")
        return True
    except requests.exceptions.HTTPError as e:
        print(f"✗ Error HTTP: {e}")
        print(f"  Respuesta: {response.text}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Error de conexión: {e}")
        return False

if __name__ == '__main__':
    # Ejemplos: el texto va en context, value siempre es 1
    post_prediction("OK")           # context: {"resultado": "OK"}
    post_prediction("NOK")          # context: {"resultado": "NOK"}
    post_prediction("DEFECTO")      # context: {"resultado": "DEFECTO"}
    post_prediction("Pieza dañada") # context: {"resultado": "Pieza dañada"}