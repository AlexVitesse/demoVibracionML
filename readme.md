# 🔄 MQTT Ubidots to Google Sheets with ML Predictions

Sistema automatizado que recopila datos de sensores IoT desde Ubidots vía MQTT, realiza predicciones con Machine Learning y almacena los resultados en Google Sheets en tiempo real.

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Arquitectura](#-arquitectura)
- [Requisitos](#-requisitos)
- [Instalación](#-instalación)
- [Configuración](#-configuración)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Uso](#-uso)
- [Datos Procesados](#-datos-procesados)
- [Logs](#-logs)
- [Solución de Problemas](#-solución-de-problemas)

## ✨ Características

- 📡 **Conexión MQTT** con Ubidots para recepción de datos en tiempo real
- 🤖 **Predicciones ML** automáticas usando Random Forest
- 📊 **Almacenamiento automático** en Google Sheets
- 🔍 **Detección de duplicados** basada en timestamps
- 📝 **Sistema de logging** completo y detallado
- ⚡ **Procesamiento eficiente** con modelo cargado en memoria
- 🛡️ **Manejo robusto de errores** en todos los módulos
- 🌐 **Timezone México** (UTC-6) para timestamps

## 🏗️ Arquitectura

```
┌─────────────┐
│   Ubidots   │ (Sensores IoT)
│   MQTT      │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  mqtt_handler   │ (Recopila variables)
│   - rg_1 (Temp) │
│   - rg_2 (Pres) │
│   - rg_3 (Cycle)│
│   - rg_6 (Fill) │
│   - faultcode   │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  ml_predictor   │ (Random Forest)
│  - Predicción   │
│  - Confianza    │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ sheets_handler  │ (Google Sheets API)
│  - Escritura    │
│  - Anti-dupl.   │
└─────────────────┘
```

## 📦 Requisitos

### Software
- Python 3.8 o superior
- Cuenta de Google Cloud con Sheets API habilitada
- Cuenta de Ubidots con dispositivo configurado

### Librerías Python
```
paho-mqtt>=1.6.1
google-api-python-client>=2.0.0
google-auth>=2.0.0
google-auth-oauthlib>=0.5.0
google-auth-httplib2>=0.1.0
pandas>=1.3.0
scikit-learn>=1.0.0
joblib>=1.1.0
```

## 🚀 Instalación

### 1. Clonar el repositorio
```bash
git clone <tu-repositorio>
cd mqtt-ubidots-sheets-ml
```

### 2. Crear entorno virtual
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar archivos necesarios

Necesitas los siguientes archivos en el directorio raíz:

- `key.json` - Credenciales de Google Service Account
- `random_forest_best_model.pkl` - Modelo de ML entrenado
- `label_encoder.pkl` - Encoder de etiquetas

## ⚙️ Configuración

### 1. Google Sheets

#### Crear Service Account:
1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un proyecto nuevo o selecciona uno existente
3. Habilita la **Google Sheets API**
4. Ve a "Credenciales" → "Crear credenciales" → "Cuenta de servicio"
5. Descarga el archivo JSON de credenciales
6. Renómbralo a `key.json` y colócalo en la raíz del proyecto

#### Configurar spreadsheet:
1. Crea una hoja de cálculo en Google Sheets
2. Comparte la hoja con el email del service account (está en `key.json`)
3. Copia el ID de la hoja (está en la URL)
4. Actualiza el ID en `sheets.py`:

```python
SPREADSHEET_ID = "TU_SPREADSHEET_ID_AQUI"
```

### 2. Ubidots

Actualiza las credenciales en `mqtt_handler.py`:

```python
UBIDOTS_TOKEN = "TU_TOKEN_AQUI"
DEVICE_LABEL = "tu_dispositivo"
```

### 3. Modelo ML

Asegúrate de tener los archivos del modelo:
- `random_forest_best_model.pkl`
- `label_encoder.pkl`

Opcionalmente, cambia las rutas en `main.py`:

```python
ml_predictor = MLPredictor(
    model_path="ruta/a/tu/modelo.pkl",
    encoder_path="ruta/a/tu/encoder.pkl"
)
```

## 📁 Estructura del Proyecto

```
mqtt-ubidots-sheets-ml/
│
├── main.py                          # Aplicación principal
├── mqtt_handler.py                  # Manejo de MQTT/Ubidots
├── sheets.py                        # Manejo de Google Sheets
├── ml_predictor.py                  # Predicciones ML
│
├── key.json                         # Credenciales Google (NO subir a git)
├── random_forest_best_model.pkl     # Modelo ML entrenado
├── label_encoder.pkl                # Encoder de etiquetas
│
├── requirements.txt                 # Dependencias
├── README.md                        # Este archivo
├── .gitignore                       # Archivos a ignorar
└── mqtt_sheets.log                  # Log generado (auto)
```

## 🎮 Uso

### Ejecutar el programa

```bash
python main.py
```

### Salida esperada

```
============================================================
     MQTT Ubidots to Google Sheets - Sistema de Logs
============================================================
2025-10-09 10:00:00 - INFO - [APP] Iniciando aplicacion...

--- Configurando Google Sheets ---
2025-10-09 10:00:01 - INFO - [SHEETS] Conexion establecida exitosamente

--- Configurando Modelo de Machine Learning ---
2025-10-09 10:00:02 - INFO - [ML] Modelo cargado exitosamente

--- Configurando cliente MQTT ---
2025-10-09 10:00:03 - INFO - [MQTT] Conectado al broker de Ubidots exitosamente

============================================================
[APP] Escuchando mensajes MQTT (Presiona Ctrl+C para detener)
============================================================
```

### Detener el programa

Presiona `Ctrl+C` para detener el programa de forma segura.

## 📊 Datos Procesados

### Variables MQTT recopiladas:
| Variable | Descripción | Unidad |
|----------|-------------|--------|
| `rg_1` | Temperatura | °C |
| `rg_2` | Presión | Pa |
| `rg_3` | Número de Ciclo | - |
| `rg_6` | Porcentaje de Llenado | % |
| `faultcode` | Código de Falla | - |

### Columnas en Google Sheets:
| Columna | Tipo | Ejemplo | Descripción |
|---------|------|---------|-------------|
| Date | String | 2025-10-09 18:06:25.085000-06:00 | Fecha/hora con timezone |
| Timestamp | Integer | 1757635585085 | Timestamp en milisegundos |
| CycleNumber | Float | 13.0 | Número de ciclo |
| FillPercentage | Float | 105.0 | Porcentaje de llenado |
| Pressure | Float | 2102.0 | Presión del sistema |
| Temperature | Float | 33.0 | Temperatura |
| Failure | Float | 0.0 | Código de falla |
| Output | String | Normal / Anormal | Predicción del ML |

## 📝 Logs

El sistema genera logs detallados en:
- **Consola**: Salida en tiempo real
- **Archivo**: `mqtt_sheets.log`

### Niveles de log:
- `INFO`: Operaciones normales
- `WARNING`: Advertencias (ej: confianza baja en predicción)
- `ERROR`: Errores recuperables
- `DEBUG`: Información detallada para debugging

### Ejemplo de log:
```
2025-10-09 10:05:23 - INFO - [MQTT] Variable: rg_6 = 105.0
2025-10-09 10:05:23 - INFO - [MQTT] Todas las variables recibidas, procesando...
2025-10-09 10:05:23 - INFO - [ML] Realizando predicción...
2025-10-09 10:05:23 - INFO - [ML] Predicción: Normal
2025-10-09 10:05:23 - INFO - [ML]   Normal          :  95.34%
2025-10-09 10:05:23 - INFO - [ML]   Anormal         :   4.66%
2025-10-09 10:05:24 - INFO - [SHEETS] OK: Datos guardados exitosamente
```

## 🔧 Solución de Problemas

### Error: "key.json no encontrado"
**Solución**: Verifica que el archivo `key.json` esté en el directorio raíz del proyecto.

### Error: "Conexión rechazada MQTT"
**Solución**: 
- Verifica el token de Ubidots
- Verifica el nombre del dispositivo
- Revisa tu conexión a internet

### Error: "Permission denied" en Google Sheets
**Solución**: 
- Comparte la hoja con el email del service account
- Verifica que tenga permisos de edición

### Error: "Modelo no encontrado"
**Solución**: 
- Verifica que los archivos `.pkl` estén en el directorio
- El sistema puede funcionar sin ML (campo Output quedará vacío)

### Duplicados en Google Sheets
**Solución**: El sistema detecta automáticamente duplicados por timestamp. Si ves duplicados:
- Revisa el log para ver si hay advertencias
- Verifica que el sistema no se haya reiniciado durante una transmisión

### Predicciones con confianza baja
**Solución**: 
- Revisa el log, verás: `[ML] ADVERTENCIA: Confianza baja`
- Considera reentrenar el modelo con más datos
- Ajusta el umbral de confianza en `ml_predictor.py`:
```python
prediction, confidence, probs = ml_predictor.predict_with_confidence(
    ...,
    threshold=0.6  # Cambiar de 0.7 a 0.6
)
```

## 🔒 Seguridad

⚠️ **IMPORTANTE**: NO subas a Git:
- `key.json`
- Archivos con tokens o credenciales
- Archivos `.pkl` si contienen datos sensibles

Agrega al `.gitignore`:
```
key.json
*.pkl
*.log
venv/
__pycache__/
```

## 📈 Mejoras Futuras

- [ ] Dashboard web en tiempo real
- [ ] Alertas por email/SMS en anomalías
- [ ] Base de datos local para backup
- [ ] API REST para consultas
- [ ] Docker container
- [ ] Tests unitarios
- [ ] Múltiples dispositivos simultáneos

## 👥 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo `LICENSE` para más detalles.

## 📧 Contacto

Para preguntas o sugerencias, abre un issue en el repositorio.

---

**Hecho con ❤️ para IoT + ML + Cloud Integration**