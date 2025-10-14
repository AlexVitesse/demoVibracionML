"""
Aplicación principal - MQTT Ubidots to Google Sheets
Sistema que recibe datos MQTT de Ubidots, procesa información con ML y almacena en Google Sheets
"""

import logging
from sheets import SheetsHandler
from mqtt_handler import MQTTHandler
from ml_predictor import MLPredictor

# Configurar sistema de logging para registro de eventos
logging.basicConfig(
    level=logging.INFO,  # Nivel de registro: INFO, DEBUG, WARNING, ERROR
    format='%(asctime)s - %(levelname)s - %(message)s',  # Formato de los mensajes
    handlers=[
        logging.FileHandler('mqtt_sheets.log'),  # Guardar logs en archivo
        logging.StreamHandler()  # Mostrar logs en consola
    ]
)

def main():
    """
    Función principal que coordina todo el sistema.
    
    Flujo de ejecución:
    1. Configura Google Sheets
    2. Carga modelo de Machine Learning
    3. Configura cliente MQTT
    4. Inicia la escucha de mensajes
    """
    print("=" * 60)
    print("     MQTT Ubidots to Google Sheets - Sistema de Logs")
    print("=" * 60)
    logging.info("[APP] Iniciando aplicacion...")
    
    # --- CONFIGURACIÓN DEL MODELO DE MACHINE LEARNING ---
    logging.info("\n--- Configurando Modelo de Machine Learning ---")
    ml_predictor = MLPredictor(
        model_path="random_forest_best_model.pkl",  # Ruta al modelo entrenado
        encoder_path="label_encoder.pkl"  # Ruta al encoder para preprocesamiento
    )
    
    # Intentar cargar el modelo ML
    if ml_predictor.load_model():
        logging.info("[APP] Modelo ML cargado exitosamente")
    else:
        logging.warning("[APP] ADVERTENCIA: No se pudo cargar el modelo ML")
        logging.warning("[APP] El sistema continuará sin predicciones")
        ml_predictor = None  # Desactivar predictor si no se puede cargar

    # --- CONFIGURACIÓN DE GOOGLE SHEETS ---
    logging.info("\n--- Configurando Google Sheets ---")
    sheets_handler = SheetsHandler(ml_predictor)
    if not sheets_handler.setup():
        logging.error("[APP] ERROR: No se pudo conectar con Google Sheets. Saliendo...")
        return  # Terminar ejecución si no hay conexión a Sheets
    
    # --- CONFIGURACIÓN DEL CLIENTE MQTT ---
    logging.info("\n--- Configurando Cliente MQTT ---")
    # Inicializar handler MQTT con acceso a Sheets y ML
    mqtt_handler = MQTTHandler(sheets_handler, ml_predictor)
    mqtt_handler.setup()  # Configurar parámetros MQTT
    
    # --- CONEXIÓN AL BROKER MQTT ---
    logging.info("\n--- Conectando al Broker MQTT ---")
    if not mqtt_handler.connect():
        logging.error("[APP] ERROR: No se pudo conectar al broker MQTT. Saliendo...")
        return  # Terminar ejecución si no hay conexión MQTT
    
    # --- INICIO DEL LOOP DE ESCUCHA ---
    logging.info("\n--- Iniciando escucha MQTT ---")
    try:
        # Iniciar loop infinito para escuchar mensajes MQTT
        mqtt_handler.start_listening()
        
    except KeyboardInterrupt:
        # Manejar interrupción por teclado (Ctrl+C)
        logging.info("[APP] Interrupción por usuario detectada")
        
    except Exception as e:
        # Manejar cualquier error inesperado
        logging.error(f"\n[APP] ERROR: Error inesperado: {e}")
        logging.exception("Detalles del error:")  # Log con traceback completo
        
    finally:
        # Bloque que siempre se ejecuta (limpieza)
        logging.info("[APP] Programa terminado correctamente")

# Punto de entrada principal
if __name__ == "__main__":
    main()