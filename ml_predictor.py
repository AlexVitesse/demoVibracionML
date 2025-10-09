"""
Módulo para predicciones con Machine Learning
Procesa datos de sensores y realiza clasificación usando modelos entrenados
"""

import joblib
import pandas as pd
import logging

class MLPredictor:
    """
    Clase para manejar predicciones de Machine Learning
    
    Atributos:
        model: Modelo de ML entrenado (Random Forest, etc.)
        label_encoder: Encoder para transformar etiquetas categóricas
        model_path: Ruta al archivo del modelo serializado
        encoder_path: Ruta al archivo del label encoder
    """
    
    def __init__(self, model_path="random_forest_best_model.pkl", encoder_path="label_encoder.pkl"):
        """
        Inicializa el predictor de ML
        
        Args:
            model_path (str): Ruta al archivo .pkl del modelo entrenado
            encoder_path (str): Ruta al archivo .pkl del label encoder
        """
        self.model = None  # Modelo de ML (Random Forest, etc.)
        self.label_encoder = None  # Encoder para etiquetas categóricas
        self.model_path = model_path  # Ruta del archivo del modelo
        self.encoder_path = encoder_path  # Ruta del archivo del encoder
    
    def load_model(self):
        """
        Carga el modelo y el encoder desde archivos serializados
        
        Returns:
            bool: True si la carga fue exitosa, False en caso contrario
            
        Raises:
            FileNotFoundError: Si no se encuentran los archivos .pkl
            Exception: Para otros errores durante la carga
        """
        try:
            logging.info("[ML] Cargando modelo de Machine Learning...")
            # Cargar modelo entrenado usando joblib
            self.model = joblib.load(self.model_path)
            logging.info(f"[ML] Modelo cargado desde: {self.model_path}")
            
            logging.info("[ML] Cargando Label Encoder...")
            # Cargar encoder para transformar etiquetas numéricas a categóricas
            self.label_encoder = joblib.load(self.encoder_path)
            logging.info(f"[ML] Label Encoder cargado desde: {self.encoder_path}")
            
            # Mostrar las clases que el modelo puede predecir
            logging.info(f"[ML] Clases disponibles: {list(self.label_encoder.classes_)}")
            return True
            
        except FileNotFoundError as e:
            logging.error(f"[ML] ERROR: Archivo no encontrado: {e}")
            logging.error("[ML] Asegúrate de que los archivos .pkl estén en el directorio")
            return False
        except Exception as e:
            logging.error(f"[ML] ERROR: No se pudo cargar el modelo: {e}")
            logging.exception("Detalles del error:")
            return False
    
    def predict(self, timestamp, cycle, fill, pressure, temperature, failure):
        """
        Realiza una predicción basada en los datos de entrada del sensor
        
        Args:
            timestamp (int/float): Timestamp en milisegundos
            cycle (int): Número de ciclo del proceso
            fill (float): Porcentaje de llenado (0-100)
            pressure (float): Presión del sistema
            temperature (float): Temperatura del sistema
            failure (int): Código de falla (si aplica)
            
        Returns:
            tuple: (etiqueta_predicha, diccionario_probabilidades)
                - etiqueta_predicha (str): Clase predicha (ej: "Normal", "Falla")
                - diccionario_probabilidades (dict): Probabilidades para cada clase
                
        Ejemplo:
            >>> predictor.predict(1640995200000, 5, 85.5, 2.3, 25.0, 0)
            ("Normal", {"Normal": 0.85, "Falla_Presion": 0.10, "Falla_Temperatura": 0.05})
        """
        # Validar que el modelo esté cargado
        if not self.model or not self.label_encoder:
            logging.error("[ML] ERROR: Modelo no cargado. Llama a load_model() primero")
            return "ERROR", {}
        
        try:
            logging.info("[ML] Preparando datos para predicción...")
            logging.info(f"[ML] Inputs: Timestamp={timestamp}, Cycle={cycle}, Fill={fill}, "
                        f"Pressure={pressure}, Temp={temperature}, Failure={failure}")
            
            # Crear DataFrame con la estructura esperada por el modelo
            x_new = pd.DataFrame([{
                'Timestamp': timestamp,
                'CycleNumber': cycle,
                'FillPercentage': fill,
                'Pressure': pressure,
                'Temperature': temperature,
                'Failure': failure
            }])
            
            logging.debug(f"[ML] DataFrame creado:\n{x_new}")
            
            # Realizar predicción de clase
            logging.info("[ML] Realizando predicción...")
            y_pred_num = self.model.predict(x_new)  # Predicción numérica
            y_pred_label = self.label_encoder.inverse_transform(y_pred_num)[0]  # Convertir a etiqueta
        
            logging.info(f"[ML] Predicción: {y_pred_label}")
            
            # Obtener probabilidades para cada clase
            y_pred_proba = self.model.predict_proba(x_new)[0]
            # Crear diccionario {clase: probabilidad}
            prob_dict = {clase: float(prob) for clase, prob in zip(self.label_encoder.classes_, y_pred_proba)}
            
            # Log detallado de probabilidades ordenadas
            logging.info("[ML] Probabilidades:")
            for clase, prob in sorted(prob_dict.items(), key=lambda x: x[1], reverse=True):
                logging.info(f"[ML]   {clase:15s} : {prob*100:6.2f}%")
            
            return y_pred_label, prob_dict
            
        except Exception as e:
            logging.error(f"[ML] ERROR: Error durante la predicción: {e}")
            logging.exception("Detalles del error:")
            return "ERROR", {}
    
    def predict_with_confidence(self, timestamp, cycle, fill, pressure, temperature, failure, threshold=0.7):
        """
        Realiza predicción con filtro de confianza mínima
        
        Útil para evitar predicciones inciertas cuando la confianza es baja
        
        Args:
            timestamp (int/float): Timestamp en milisegundos
            cycle (int): Número de ciclo del proceso
            fill (float): Porcentaje de llenado (0-100)
            pressure (float): Presión del sistema
            temperature (float): Temperatura del sistema
            failure (int): Código de falla
            threshold (float): Umbral mínimo de confianza (0-1, default: 0.7)
            
        Returns:
            tuple: (etiqueta_predicha, confianza, diccionario_probabilidades)
                - etiqueta_predicha (str): Clase predicha o "ERROR"
                - confianza (float): Nivel de confianza de la predicción (0-1)
                - diccionario_probabilidades (dict): Probabilidades para todas las clases
                
        Ejemplo:
            >>> predictor.predict_with_confidence(..., threshold=0.8)
            ("Normal", 0.85, {"Normal": 0.85, "Falla_Presion": 0.10, ...})
        """
        # Obtener predicción básica
        label, probs = self.predict(timestamp, cycle, fill, pressure, temperature, failure)
        
        if label == "ERROR":
            return "ERROR", 0.0, {}
        
        # Obtener la confianza de la clase predicha
        confidence = probs.get(label, 0.0)
        
        # Validar contra el umbral de confianza
        if confidence < threshold:
            logging.warning(f"[ML] ADVERTENCIA: Confianza baja ({confidence*100:.2f}%) - Umbral: {threshold*100:.2f}%")
        else:
            logging.info(f"[ML] Confianza alta: {confidence*100:.2f}%")
        
        return label, confidence, probs