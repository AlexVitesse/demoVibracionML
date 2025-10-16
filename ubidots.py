import requests
import os
from dotenv import load_dotenv

load_dotenv()

UBIDOTS_TOKEN = os.getenv("UBIDOTS_TOKEN")
DEVICE_LABEL = os.getenv("DEVICE_LABEL")

def post_prediction(prediction):
    """
    Publica la predicción en Ubidots.
    """
    url = f"https://industrial.api.ubidots.com/api/v1.6/devices/{DEVICE_LABEL}"
    headers = {"X-Auth-Token": UBIDOTS_TOKEN, "Content-Type": "application/json"}
    payload = {"prediction": prediction}
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # Lanza una excepción para códigos de estado HTTP 4xx/5xx
        print(f"Datos enviados a Ubidots con éxito: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar datos a Ubidots: {e}")

if __name__ == '__main__':
    # Ejemplo de uso
    post_prediction(123)