"""
Módulo para manejo de MQTT con Ubidots
Recibe datos de sensores desde Ubidots IoT platform y los procesa
"""

import paho.mqtt.client as mqtt
import json
import logging
from datetime import datetime, timezone, timedelta
from ubidots import post_prediction
import os
from dotenv import load_dotenv

load_dotenv()

# Configuración de Ubidots - Credenciales y endpoints
UBIDOTS_TOKEN = os.getenv("UBIDOTS_TOKEN")  # Token de autenticación
DEVICE_LABEL = os.getenv("DEVICE_LABEL")  # Identificador del dispositivo en Ubidots
BROKER = "industrial.api.ubidots.com"  # Servidor MQTT de Ubidots
PORT = 1883  # Puerto MQTT estándar
TOPIC = f"/v1.6/devices/{DEVICE_LABEL}"  # Tópico base para el dispositivo

class MQTTHandler:
    """
    Maneja la comunicación MQTT con Ubidots y procesa datos de sensores
    
    Atributos:
        sheets_handler: Instancia para escribir en Google Sheets
        ml_predictor: Instancia para predicciones de ML (opcional)
        data_buffer: Diccionario para acumular datos de diferentes variables
        client: Cliente MQTT de paho
    """
    
    def __init__(self, sheets_handler, ml_predictor=None):
        """
        Inicializa el handler MQTT
        
        Args:
            sheets_handler: Instancia de SheetsHandler para guardar datos
            ml_predictor: Instancia de MLPredictor (opcional) para análisis predictivo
        """
        self.sheets_handler = sheets_handler  # Maneja escritura en Google Sheets
        self.ml_predictor = ml_predictor  # Predictor ML (puede ser None)
        self.data_buffer = {}  # Buffer para acumular datos de variables
        self.client = None  # Cliente MQTT (se inicializa en setup())
    
    def setup(self):
        """Configura el cliente MQTT con credenciales y callbacks"""
        logging.info("\n--- Configurando cliente MQTT ---")
        # Crear instancia del cliente MQTT
        self.client = mqtt.Client()
        # Configurar autenticación con token Ubidots
        self.client.username_pw_set(UBIDOTS_TOKEN, "")
        logging.info("[APP] Credenciales MQTT configuradas")
        
        # Asignar funciones callback para eventos MQTT
        self.client.on_connect = self._on_connect  # Cuando se conecta al broker
        self.client.on_message = self._on_message  # Cuando recibe mensaje
        logging.info("[APP] Callbacks asignados")
    
    def connect(self):
        """
        Conecta al broker MQTT de Ubidots
        
        Returns:
            bool: True si la conexión fue exitosa, False en caso contrario
        """
        try:
            logging.info(f"\n[APP] Intentando conectar a {BROKER}:{PORT}...")
            # Intentar conexión (keepalive: 60 segundos)
            self.client.connect(BROKER, PORT, 60)
            logging.info("[APP] Conexion MQTT establecida")
            return True
        except ConnectionRefusedError:
            logging.error("\n[APP] ERROR: Conexion rechazada. Verifica el broker y el puerto")
            return False
        except Exception as e:
            logging.error(f"\n[APP] ERROR: Error al conectar: {e}")
            logging.exception("Detalles del error:")
            return False
    
    def start_listening(self):
        """Inicia el loop infinito de escucha de mensajes MQTT"""
        try:
            logging.info("\n" + "=" * 60)
            logging.info("[APP] Escuchando mensajes MQTT (Presiona Ctrl+C para detener)")
            logging.info("=" * 60 + "\n")
            # Loop bloqueante que escucha mensajes continuamente
            self.client.loop_forever()
        except KeyboardInterrupt:
            # Manejar interrupción por teclado (Ctrl+C)
            logging.info("\n\n[APP] Interrupcion de usuario detectada")
            self.disconnect()
    
    def disconnect(self):
        """Desconecta del broker MQTT de manera limpia"""
        logging.info("[APP] Desconectando del broker MQTT...")
        self.client.disconnect()
        logging.info("[APP] Desconexion exitosa")
    
    def _on_connect(self, client, userdata, flags, rc):
        """
        Callback que se ejecuta cuando se conecta al broker MQTT
        
        Args:
            client: Cliente MQTT
            userdata: Datos de usuario
            flags: Banderas de conexión
            rc: Código de resultado de conexión (0 = éxito)
        """
        if rc == 0:
            logging.info("[MQTT] Conectado al broker de Ubidots exitosamente")
            
            # Lista de variables a suscribir (sensores específicos)
            variables_needed = ['rg_1', 'rg_2', 'rg_3', 'rg_6', 'faultcode']
            
            # Suscribirse a cada variable individualmente
            for var in variables_needed:
                topic = f"{TOPIC}/{var}"  # Tópico específico para cada variable
                client.subscribe(topic)
                logging.info(f"[MQTT] Suscrito a: {topic}")
            
            logging.info("[MQTT] Suscripciones completadas exitosamente")
        else:
            # Diccionario de códigos de error MQTT
            error_messages = {
                1: "Protocolo incorrecto",
                2: "ID de cliente rechazado",
                3: "Servidor no disponible",
                4: "Usuario/contrasena incorrectos",
                5: "No autorizado"
            }
            logging.error(f"[MQTT] ERROR: Conexion fallida. Codigo: {rc} - {error_messages.get(rc, 'Error desconocido')}")
    
    def _on_message(self, client, userdata, msg):
        """
        Callback que se ejecuta cuando se recibe un mensaje MQTT
        
        Args:
            client: Cliente MQTT
            userdata: Datos de usuario
            msg: Mensaje MQTT recibido
        """
        try:
            # Extraer el nombre de la variable del tópico MQTT
            # Ejemplo: /v1.6/devices/pt_space/rg_1 → variable_name = 'rg_1'
            topic_parts = msg.topic.split('/')
            
            if topic_parts[-1] == 'lv':  # Caso especial para last value
                variable_name = topic_parts[-2]
            else:
                variable_name = topic_parts[-1]
            
            logging.debug(f"[MQTT] Mensaje recibido en topico: {msg.topic}")
            logging.debug(f"[MQTT] Variable extraida: {variable_name}")
            
            # Decodificar el payload de bytes a string
            payload_raw = msg.payload.decode()
            logging.debug(f"[MQTT] Payload raw: {payload_raw}")
            
            # Parsear el JSON del payload
            payload = json.loads(payload_raw)
            logging.info(f"[MQTT] Payload decodificado para {variable_name}: {payload}")
            
            # Extraer valor y timestamp del payload
            if isinstance(payload, dict):
                value = payload.get('value', 0)  # Valor del sensor
                timestamp = payload.get('timestamp', None)  # Timestamp del dato
                
                logging.info(f"[MQTT] Variable: {variable_name} = {value}")
                if timestamp:
                    logging.info(f"[MQTT] Timestamp de {variable_name}: {timestamp}")
                
                # Guardar el valor en el buffer
                self.data_buffer[variable_name] = value
                
                # Guardar timestamp específico para esta variable
                if timestamp is not None:
                    self.data_buffer[f'timestamp_{variable_name}'] = timestamp
                    logging.info(f"[MQTT] Timestamp guardado como 'timestamp_{variable_name}': {timestamp}")
                
            elif isinstance(payload, (int, float)):
                # Caso donde el payload es directamente un número
                value = payload
                logging.info(f"[MQTT] Variable: {variable_name} = {value} (numero directo)")
                self.data_buffer[variable_name] = value
            else:
                logging.error(f"[MQTT] ERROR: Tipo de payload no esperado: {type(payload)}")
                logging.error(f"[MQTT] Contenido: {payload}")
                return
            
            logging.debug(f"[MQTT] Buffer actualizado: {self.data_buffer}")
            
            # Verificar si tenemos todas las variables necesarias para procesar
            expected_vars = {'rg_1', 'rg_2', 'rg_3', 'rg_6'}  # Variables requeridas
            received_vars = set(k for k in self.data_buffer.keys() if not k.startswith('timestamp_'))
            missing_vars = expected_vars - received_vars  # Variables faltantes
            
            if missing_vars:
                logging.info(f"[MQTT] Esperando variables: {', '.join(missing_vars)}")
                logging.info(f"[MQTT] Variables recibidas hasta ahora: {', '.join(received_vars)}")
            else:
                logging.info("[MQTT] Todas las variables recibidas, procesando...")
                self._process_data()  # Procesar datos completos
                
        except json.JSONDecodeError as e:
            logging.error(f"[MQTT] ERROR: No se pudo decodificar JSON: {e}")
            logging.error(f"[MQTT] Payload recibido: {msg.payload}")
        except Exception as e:
            logging.error(f"[MQTT] ERROR: Error al procesar mensaje: {e}")
            logging.exception("Detalles del error completo:")
    
    def _process_data(self):
        """
        Procesa los datos cuando se reciben todas las variables necesarias
        Realiza validación, conversión de timestamp y escritura en Sheets
        """
        logging.info("[PROCESS] Procesando datos recibidos...")
        logging.debug(f"Buffer actual: {self.data_buffer}")
        
        # Configurar timezone para México (UTC-6)
        mexico_tz = timezone(timedelta(hours=-6))
        
        # Obtener timestamp de la variable principal (rg_6)
        timestamp_ms = self.data_buffer.get('timestamp_rg_6', None)
        
        if timestamp_ms:
            logging.info(f"[PROCESS] Timestamp de rg_6 encontrado: {timestamp_ms}")
            
            # Verificar si es un duplicado (comparar con último timestamp escrito)
            if self.sheets_handler.is_duplicate(timestamp_ms):
                logging.warning(f"[PROCESS] DUPLICADO DETECTADO: Timestamp {timestamp_ms} <= ultimo escrito {self.sheets_handler.last_timestamp_written}")
                logging.warning("[PROCESS] Saltando escritura de datos duplicados")
                self.data_buffer.clear()  # Limpiar buffer sin procesar
                return
            else:
                logging.info(f"[PROCESS] Timestamp es nuevo: {timestamp_ms} > {self.sheets_handler.last_timestamp_written}")
            
            # Convertir timestamp de milisegundos a datetime
            try:
                timestamp_sec = timestamp_ms / 1000  # Convertir a segundos
                dt = datetime.fromtimestamp(timestamp_sec, tz=mexico_tz)
                logging.info(f"[PROCESS] Timestamp convertido: {dt}")
            except Exception as e:
                logging.warning(f"[PROCESS] Error al convertir timestamp: {e}")
                # Fallback: usar hora actual si hay error en conversión
                dt = datetime.now(mexico_tz)
                timestamp_ms = int(dt.timestamp() * 1000)
        else:
            # Fallback: si no hay timestamp, usar hora actual
            logging.warning("[PROCESS] No se encontró timestamp de rg_6, usando hora actual")
            dt = datetime.now(mexico_tz)
            timestamp_ms = int(dt.timestamp() * 1000)
        
        # Formatear fecha/hora con microsegundos y timezone
        # Ejemplo: 2024-01-15 14:30:25.123456-06:00
        date_str = dt.strftime('%Y-%m-%d %H:%M:%S.%f') + dt.strftime('%z')
        date_str = date_str[:-2] + ':' + date_str[-2:]  # Formato ISO con ":"
        
        logging.info(f"[PROCESS] Fecha/hora formateada: {date_str}")
        logging.info(f"[PROCESS] Timestamp (ms): {timestamp_ms}")
        
        # Estructurar datos para Google Sheets
        processed_data = {
            'date': date_str,  # Fecha formateada
            'timestamp': timestamp_ms,  # Timestamp en ms
            'cycle_number': self.data_buffer.get('rg_3', 0),  # Número de ciclo
            'fill_percentage': self.data_buffer.get('rg_6', 0),  # Porcentaje de llenado
            'pressure': self.data_buffer.get('rg_2', 0),  # Presión
            'temperature': self.data_buffer.get('rg_1', 0),  # Temperatura
            'failure': self.data_buffer.get('faultcode', 0),  # Código de falla
            'output': ''  # Salida de ML (se llena después)
        }
        
        # Realizar predicción con ML si está disponible
        if self.ml_predictor:
            try:
                logging.info("[PROCESS] Realizando predicción con ML...")
                prediction, confidence, probabilities = self.ml_predictor.predict_with_confidence(
                    timestamp=timestamp_ms,
                    cycle=processed_data['cycle_number'],
                    fill=processed_data['fill_percentage'],
                    pressure=processed_data['pressure'],
                    temperature=processed_data['temperature'],
                    failure=processed_data['failure']
                )
                
                # Agregar la predicción al output
                processed_data['output'] = prediction
                post_prediction(prediction)  # Enviar predicción a Ubidots
                logging.info(f"[PROCESS] Predicción agregada: {prediction} (Confianza: {confidence*100:.2f}%)")
                
            except Exception as e:
                logging.error(f"[PROCESS] ERROR en predicción ML: {e}")
                processed_data['output'] = 'ERROR_ML'  # Marcar error en ML
        else:
            logging.warning("[PROCESS] No hay predictor ML disponible, output vacío")
        
        # Log de datos procesados
        logging.info("[PROCESS] Datos procesados:")
        for key, value in processed_data.items():
            logging.info(f"[PROCESS]   - {key}: {value}")
        
        # Escribir en Google Sheets
        self.sheets_handler.write_data(processed_data, probabilities)
        
        # Limpiar buffer para siguiente conjunto de datos
        logging.info("[PROCESS] Limpiando buffer de datos...")
        self.data_buffer.clear()