"""
Módulo para manejo de Google Sheets
Gestiona la conexión y operaciones con Google Sheets API
"""

from googleapiclient.discovery import build
from google.oauth2 import service_account
import logging

# Configuración de Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']  # Permisos para leer/escribir hojas de cálculo
KEY = 'key.json'  # Archivo de credenciales de Service Account
SPREADSHEET_ID = "18nhbg8wQWJes3ItBfrOi3Qtaw5cchrpmELY_oVoisgY"  # ID único de la hoja de cálculo
SHEET_NAME = "Hoja 1"  # Nombre de la pestaña dentro de la hoja

class SheetsHandler:
    """
    Maneja todas las operaciones con Google Sheets API
    
    Atributos:
        sheet_service: Cliente de Google Sheets API
        last_timestamp_written: Último timestamp escrito (para detección de duplicados)
    """
    
    def __init__(self):
        """Inicializa el handler de Google Sheets"""
        self.sheet_service = None  # Servicio de Google Sheets (se inicializa en setup())
        self.last_timestamp_written = None  # Último timestamp escrito para control de duplicados
    
    def setup(self):
        """
        Configura la conexión con Google Sheets API
        
        Returns:
            bool: True si la configuración fue exitosa, False en caso contrario
            
        Steps:
            1. Carga credenciales desde archivo JSON
            2. Construye el servicio de Google Sheets
            3. Lee el último timestamp existente
        """
        try:
            logging.info("[SHEETS] Cargando credenciales desde key.json...")
            # Cargar credenciales de Service Account desde archivo JSON
            creds = service_account.Credentials.from_service_account_file(KEY, scopes=SCOPES)
            logging.info(f"[SHEETS] Service Account: {creds.service_account_email}")
            
            logging.info("[SHEETS] Construyendo servicio de Google Sheets...")
            # Construir el cliente de Google Sheets API v4
            service = build('sheets', 'v4', credentials=creds)
            self.sheet_service = service.spreadsheets()  # Servicio para operaciones con hojas
            
            logging.info("[SHEETS] Conexion establecida exitosamente")
            logging.info(f"[SHEETS] Spreadsheet ID: {SPREADSHEET_ID}")
            logging.info(f"[SHEETS] Hoja: {SHEET_NAME}")
            
            # Leer el último timestamp de la hoja para control de duplicados
            self._read_last_timestamp()
            
            return True
            
        except FileNotFoundError:
            logging.error("[SHEETS] ERROR: Archivo key.json no encontrado en el directorio actual")
            logging.error("[SHEETS] Asegúrate de que el archivo key.json esté en el mismo directorio")
            return False
        except Exception as e:
            logging.error(f"[SHEETS] ERROR: No se pudo conectar con Google Sheets: {e}")
            logging.exception("Detalles del error:")
            return False
    
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
    
    def write_data(self, data):
        """
        Escribe los datos procesados en Google Sheets
        
        Args:
            data (dict): Diccionario con los datos a escribir. Debe contener:
                - date: Fecha formateada
                - timestamp: Timestamp en milisegundos
                - cycle_number: Número de ciclo
                - fill_percentage: Porcentaje de llenado
                - pressure: Presión
                - temperature: Temperatura
                - failure: Código de falla
                - output: Predicción ML o estado
        
        Returns:
            bool: True si la escritura fue exitosa, False en caso contrario
        """
        if not self.sheet_service:
            logging.error("[SHEETS] ERROR: No hay servicio de sheets inicializado")
            logging.error("[SHEETS] Ejecuta setup() primero")
            return False
        
        try:
            logging.info("[SHEETS] Preparando datos para escribir...")
            logging.debug(f"Datos a escribir: {data}")
            
            # Estructurar datos en el orden de columnas esperado:
            # A: Date, B: Timestamp, C: CycleNumber, D: FillPercentage, 
            # E: Pressure, F: Temperature, G: Failure, H: Output
            values = [[
                data['date'],           # Columna A - Fecha formateada
                data['timestamp'],      # Columna B - Timestamp en ms
                data['cycle_number'],   # Columna C - Número de ciclo
                data['fill_percentage'], # Columna D - Porcentaje de llenado
                data['pressure'],       # Columna E - Presión
                data['temperature'],    # Columna F - Temperatura
                data['failure'],        # Columna G - Código de falla
                data['output']          # Columna H - Predicción ML/Estado
            ]]
            
            # Estructura del cuerpo para la API
            body = {
                'values': values  # Datos a escribir
            }
            
            logging.info("[SHEETS] Enviando datos a Google Sheets...")
            # Ejecutar operación de append (agregar fila al final)
            result = self.sheet_service.values().append(
                spreadsheetId=SPREADSHEET_ID,      # ID de la hoja
                range=f'{SHEET_NAME}!A1:H1',       # Rango base (se auto-expande)
                valueInputOption='USER_ENTERED',   # Procesar datos como si usuario los escribiera
                body=body                          # Datos a escribir
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