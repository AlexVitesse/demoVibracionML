import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()

UBIDOTS_TOKEN = os.getenv("UBIDOTS_TOKEN")
DEVICE_LABEL = os.getenv("DEVICE_LABEL")

def post_prediction(prediction):
    """
    Publica la predicción en Ubidots.
    """
    url = f"https://industrial.api.ubidots.com/api/v1.6/devices/{DEVICE_LABEL}"
    headers = {
        "X-Auth-Token": UBIDOTS_TOKEN, 
        "Content-Type": "application/json"
    }
    
    # Mapear predicciones de texto a números
    prediction_value = prediction
    if isinstance(prediction, str):
        prediction_map = {
            "OK": 1,
            "NOK": 0,
            "DEFECTO": 0
        }
        prediction_value = prediction_map.get(prediction.upper(), 0)
    
    # Formato correcto para Ubidots
    payload = {
        "prediction": {
            "value": prediction_value,
            "timestamp": int(time.time() * 1000)  # Timestamp en milisegundos
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        print(f"✓ Datos enviados a Ubidots con éxito: {response.json()}")
        return True
    except requests.exceptions.HTTPError as e:
        print(f"✗ Error HTTP al enviar datos a Ubidots: {e}")
        print(f"  Respuesta del servidor: {response.text}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Error de conexión con Ubidots: {e}")
        return False

if __name__ == '__main__':
    # Ejemplos de uso
    post_prediction("OK")      # Se enviará como 1
    post_prediction("NOK")     # Se enviará como 0
    post_prediction(123)       # Se enviará como 123