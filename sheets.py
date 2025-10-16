"""
Módulo para manejo de Google Sheets
Gestiona la conexión y operaciones con Google Sheets API
"""

from googleapiclient.discovery import build
from google.oauth2 import service_account
import logging
import os
from dotenv import load_dotenv

load_dotenv()

# Configuración de Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']  # Permisos para leer/escribir hojas de cálculo
KEY = 'key.json'  # Archivo de credenciales de Service Account
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")  # ID único de la hoja de cálculo
SHEET_NAME = "Hoja 1"  # Nombre de la pestaña dentro de la hoja

class SheetsHandler:
    """
    Maneja todas las operaciones con Google Sheets API
    
    Atributos:
        sheet_service: Cliente de Google Sheets API
        last_timestamp_written: Último timestamp escrito (para detección de duplicados)
    """
    
    def __init__(self, ml_predictor=None):
        """Inicializa el handler de Google Sheets"""
        self.sheet_service = None  # Servicio de Google Sheets (se inicializa en setup())
        self.last_timestamp_written = None  # Último timestamp escrito para control de duplicados
        self.ml_predictor = ml_predictor
        self.ml_class_names = []
        if self.ml_predictor and self.ml_predictor.label_encoder:
            self.ml_class_names = list(self.ml_predictor.label_encoder.classes_)
    
    def setup(self):
        """
        Configura la conexión con Google Sheets API
        
        Returns:
            bool: True si la configuración fue exitosa, False en caso contrario
        """
        try:
            logging.info("[SHEETS] Cargando credenciales desde key.json...")
            creds = service_account.Credentials.from_service_account_file(KEY, scopes=SCOPES)
            logging.info(f"[SHEETS] Service Account: {creds.service_account_email}")
            
            logging.info("[SHEETS] Construyendo servicio de Google Sheets...")
            service = build('sheets', 'v4', credentials=creds)
            self.sheet_service = service.spreadsheets()
            
            logging.info("[SHEETS] Conexion establecida exitosamente")
            self._update_headers()
            self._read_last_timestamp()
            
            return True
            
        except FileNotFoundError:
            logging.error("[SHEETS] ERROR: Archivo key.json no encontrado")
            return False
        except Exception as e:
            logging.error(f"[SHEETS] ERROR: No se pudo conectar con Google Sheets: {e}")
            return False

    def _update_headers(self):
        """Escribe/actualiza los encabezados en la primera fila de la hoja."""
        try:
            logging.info("[SHEETS] Actualizando encabezados...")
            base_headers = [
                'Date', 'Timestamp', 'CycleNumber', 'FillPercentage', 
                'Pressure', 'Temperature', 'Failure', 'Output'
            ]
            
            # Añadir encabezados de probabilidades
            if self.ml_class_names:
                headers = base_headers + [f'Prob_{name}' for name in self.ml_class_names]
            else:
                headers = base_headers

            body = {'values': [headers]}
            self.sheet_service.values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=f'{SHEET_NAME}!A1',
                valueInputOption='RAW',
                body=body
            ).execute()
            logging.info("[SHEETS] Encabezados actualizados exitosamente.")

        except Exception as e:
            logging.error(f"[SHEETS] ERROR: No se pudo actualizar los encabezados: {e}")
    
    def _read_last_timestamp(self):
        """
        Lee el último timestamp de la columna B de la hoja
        
        Método interno que se ejecuta durante el setup para determinar
        cuál fue el último dato escrito y evitar duplicados
        """
        try:
            logging.info("[SHEETS] Leyendo ultimo timestamp de la hoja...")
            # Obtener todos los valores de la columna B (timestamps)
            result = self.sheet_service.values().get(
                spreadsheetId=SPREADSHEET_ID,
                range=f'{SHEET_NAME}!B:B'  # Columna B contiene los timestamps
            ).execute()
            
            values = result.get('values', [])
            
            # Verificar si hay datos además del encabezado
            if values and len(values) > 1:  # Más de la fila de encabezado
                # Obtener el último timestamp (última fila con datos)
                last_row = values[-1]
                if last_row and last_row[0]:  # Verificar que la celda no esté vacía
                    self.last_timestamp_written = int(last_row[0])
                    logging.info(f"[SHEETS] Ultimo timestamp encontrado: {self.last_timestamp_written}")
                else:
                    logging.info("[SHEETS] No hay timestamp en la ultima fila")
                    self.last_timestamp_written = None
            else:
                logging.info("[SHEETS] Hoja vacia o solo con encabezados")
                self.last_timestamp_written = None
                
        except Exception as e:
            logging.warning(f"[SHEETS] No se pudo leer ultimo timestamp: {e}")
            self.last_timestamp_written = None
    
    def write_data(self, data, probabilities=None):
        """
        Escribe los datos procesados en Google Sheets
        
        Args:
            data (dict): Diccionario con los datos a escribir.
            probabilities (dict): Diccionario con las probabilidades de predicción.
        
        Returns:
            bool: True si la escritura fue exitosa, False en caso contrario
        """
        if not self.sheet_service:
            logging.error("[SHEETS] ERROR: No hay servicio de sheets inicializado")
            return False
        
        try:
            logging.info("[SHEETS] Preparando datos para escribir...")
            
            # Estructurar datos base
            row_values = [
                data.get('date', ''),
                data.get('timestamp', 0),
                data.get('cycle_number', 0),
                data.get('fill_percentage', 0),
                data.get('pressure', 0),
                data.get('temperature', 0),
                data.get('failure', 0),
                data.get('output', 'N/A')
            ]
            
            # Añadir probabilidades si están disponibles
            if probabilities and self.ml_class_names:
                for class_name in self.ml_class_names:
                    prob = probabilities.get(class_name, 0.0)
                    row_values.append(f"{prob * 100:.2f}%")
            
            values = [row_values]
            body = {'values': values}
            
            # Determinar el rango dinámicamente
            num_columns = len(row_values)
            end_column = chr(ord('A') + num_columns - 1)
            sheet_range = f'{SHEET_NAME}!A1:{end_column}1'
            
            logging.info(f"[SHEETS] Enviando datos a Google Sheets en rango {sheet_range}...")
            result = self.sheet_service.values().append(
                spreadsheetId=SPREADSHEET_ID,
                range=sheet_range,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            # Obtener estadísticas de la operación
            updated_cells = result.get('updates', {}).get('updatedCells', 0)
            logging.info(f"[SHEETS] OK: Datos guardados exitosamente: {values[0]}")
            logging.info(f"[SHEETS] Celdas actualizadas: {updated_cells}")
            
            # Actualizar el último timestamp escrito para control de duplicados
            self.last_timestamp_written = data['timestamp']
            logging.info(f"[SHEETS] Ultimo timestamp actualizado a: {self.last_timestamp_written}")
            
            return True
            
        except Exception as e:
            logging.error(f"[SHEETS] ERROR: No se pudo escribir en Google Sheets: {e}")
            logging.exception("Detalles del error:")
            return False
    
    def is_duplicate(self, timestamp):
        """
        Verifica si un timestamp ya existe en la hoja (detección de duplicados)
        
        Args:
            timestamp (int): Timestamp en milisegundos a verificar
            
        Returns:
            bool: True si es duplicado, False si es nuevo
        """
        # Si no hay último timestamp registrado, no puede ser duplicado
        if self.last_timestamp_written is None:
            return False
            
        # Si el timestamp es menor o igual al último escrito, es duplicado
        if timestamp <= self.last_timestamp_written:
            logging.debug(f"[SHEETS] Duplicado detectado: {timestamp} <= {self.last_timestamp_written}")
            return True
            
        return False