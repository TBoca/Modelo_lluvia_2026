# GUÍA DE INSTALACIÓN Y CONFIGURACIÓN
# Scripts para descarga de datos climáticos e hidrológicos
# Región Agro-Pampeana Argentina

## REQUISITOS DEL SISTEMA

- Python 3.8 o superior
- Conexión a Internet
- Espacio en disco: Mínimo 10 GB libre (más si descargas muchas imágenes satelitales)

---

## INSTALACIÓN DE PYTHON Y LIBRERÍAS

### Paso 1: Instalar Python
Si no tienes Python instalado:
- Windows: Descarga desde https://www.python.org/downloads/
- Marca la opción "Add Python to PATH" durante instalación

### Paso 2: Instalar librerías básicas

```powershell
# Librerías esenciales para todos los scripts
pip install pandas numpy requests

# Para procesamiento de datos espaciales
pip install xarray netCDF4 rasterio geopandas

# Para análisis y visualización
pip install matplotlib seaborn scipy
```

### Paso 3: Librerías específicas por fuente de datos

```powershell
# Para ERA5 (Copernicus)
pip install cdsapi

# Para Google Earth Engine
pip install earthengine-api

# Para Sentinel Hub (opcional)
pip install sentinelhub
```

---

## CONFIGURACIÓN DE CREDENCIALES

### 1. NASA POWER
✓ NO requiere registro
✓ Acceso directo y gratuito
✓ Listo para usar

### 2. COPERNICUS CDS (ERA5)

**a) Registrarse:**
   - Ir a: https://cds.climate.copernicus.eu/user/register
   - Completar formulario
   - Verificar email

**b) Obtener API key:**
   - Login en: https://cds.climate.copernicus.eu/
   - Ir a: https://cds.climate.copernicus.eu/user
   - Copiar UID y API key

**c) Configurar archivo .cdsapirc:**
   
   Windows: Crear archivo en `C:\Users\<tu_usuario>\.cdsapirc`
   
   Contenido:
   ```
   url: https://cds.climate.copernicus.eu/api/v2
   key: <UID>:<API-key>
   ```
   
   Ejemplo:
   ```
   url: https://cds.climate.copernicus.eu/api/v2
   key: 12345:abcdef12-3456-7890-abcd-ef1234567890
   ```

**d) Aceptar términos:**
   - Ir a: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels
   - Click en "Download data" > "Terms of use" > Aceptar

### 3. CHIRPS
✓ NO requiere registro
✓ Descarga directa
✓ Listo para usar

### 4. NOAA CDO (opcional)

**a) Solicitar token:**
   - Ir a: https://www.ncdc.noaa.gov/cdo-web/token
   - Ingresar email
   - Recibirás token por email (puede tardar 10-15 min)

**b) Usar token en script:**
   ```python
   noaa = NOAADownloader(api_token='TU_TOKEN_AQUI')
   ```

### 5. GOOGLE EARTH ENGINE (Recomendado)

**a) Registrarse:**
   - Ir a: https://earthengine.google.com/signup/
   - Usar cuenta Google
   - Esperar aprobación (puede tardar 1-2 días)

**b) Autenticar en Python:**
   ```powershell
   earthengine authenticate
   ```
   
   O en Python:
   ```python
   import ee
   ee.Authenticate()
   ee.Initialize()
   ```

**c) Usar Code Editor (más fácil):**
   - https://code.earthengine.google.com/
   - Pegar scripts de ejemplo directamente
   - Ejecutar en la nube sin instalación

### 6. SENTINEL HUB (opcional)

**a) Registrarse:**
   - Ir a: https://www.sentinel-hub.com/
   - Crear cuenta gratuita (1000 requests/mes)

**b) Crear configuración:**
   - Dashboard: https://apps.sentinel-hub.com/dashboard/
   - "User Settings" > "OAuth clients" > Create

**c) Guardar credenciales en script**

---

## VERIFICAR INSTALACIÓN

Ejecuta este script de prueba:

```python
# test_instalacion.py

print("Verificando instalación...")

# Test librerías básicas
try:
    import pandas as pd
    import numpy as np
    import requests
    print("✓ Pandas, NumPy, Requests: OK")
except ImportError as e:
    print(f"✗ Error: {e}")

# Test librerías espaciales
try:
    import xarray as xr
    import netCDF4
    print("✓ Xarray, NetCDF4: OK")
except ImportError as e:
    print(f"✗ Xarray/NetCDF4 no instalado (opcional)")

try:
    import rasterio
    print("✓ Rasterio: OK")
except ImportError:
    print("✗ Rasterio no instalado (opcional para GeoTIFF)")

# Test NASA POWER
try:
    url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    params = {
        'parameters': 'T2M',
        'latitude': -34,
        'longitude': -60,
        'start': '20230101',
        'end': '20230102',
        'format': 'JSON'
    }
    r = requests.get(url, params=params, timeout=10)
    if r.status_code == 200:
        print("✓ NASA POWER: Acceso OK")
    else:
        print(f"✗ NASA POWER: Error {r.status_code}")
except Exception as e:
    print(f"✗ NASA POWER: {e}")

# Test CDS API
try:
    import cdsapi
    print("✓ CDS API instalado")
    # Intentar inicializar (fallará si no está configurado)
    try:
        client = cdsapi.Client()
        print("✓ CDS API configurado correctamente")
    except:
        print("⚠ CDS API instalado pero no configurado (ver guía)")
except ImportError:
    print("⚠ CDS API no instalado (pip install cdsapi)")

# Test Google Earth Engine
try:
    import ee
    print("✓ Earth Engine API instalado")
    try:
        ee.Initialize()
        print("✓ Earth Engine autenticado")
    except:
        print("⚠ Earth Engine no autenticado (ejecuta: earthengine authenticate)")
except ImportError:
    print("⚠ Earth Engine no instalado (pip install earthengine-api)")

print("\nVerificación completada!")
```

---

## USO DE LOS SCRIPTS

### Orden recomendado de uso:

1. **01_nasa_power_datos.py**
   - Más fácil, sin configuración
   - Prueba primero este

2. **03_chirps_precipitacion.py**
   - También fácil, descarga directa
   - Buenos para empezar

3. **06_datos_hidricos_argentina.py**
   - Información y guías
   - Generar inventarios

4. **02_era5_datos.py**
   - Requiere configuración CDS
   - Datos de alta calidad

5. **05_imagenes_satelitales.py**
   - Mejor usar Google Earth Engine
   - Scripts listos para copiar/pegar

### Ejemplo de flujo básico:

```powershell
# 1. Ejecutar script NASA POWER
python 01_nasa_power_datos.py

# 2. Ver datos hidrológicos disponibles
python 06_datos_hidricos_argentina.py

# 3. Descargar CHIRPS para período específico
python 03_chirps_precipitacion.py

# 4. Usar Google Earth Engine para imágenes
# (abrir https://code.earthengine.google.com/ y pegar scripts)
```

---

## ESTRUCTURA DE ARCHIVOS

```
Lluvia nuevo/
├── 01_nasa_power_datos.py          # Datos climáticos NASA
├── 02_era5_datos.py                 # Reanálisis ERA5
├── 03_chirps_precipitacion.py      # Precipitación CHIRPS
├── 04_noaa_gpcc_datos.py            # NOAA y GPCC
├── 05_imagenes_satelitales.py      # Sentinel, Landsat, MODIS
├── 06_datos_hidricos_argentina.py  # INA, DPA, recursos hídricos
├── README.md                        # Esta guía
├── requirements.txt                 # Librerías necesarias
│
├── datos/                           # Carpeta para datos descargados
│   ├── nasa_power/
│   ├── era5/
│   ├── chirps/
│   └── satelital/
│
└── resultados/                      # Carpeta para resultados
    ├── mapas/
    └── series_temporales/
```

---

## SOLUCIÓN DE PROBLEMAS COMUNES

### Error: "Module not found"
```powershell
# Reinstalar la librería
pip install --upgrade <nombre_libreria>
```

### Error CDS API: "Client has not been properly configured"
- Verificar que el archivo .cdsapirc existe
- Verificar que las credenciales son correctas
- Verificar que aceptaste términos de uso del dataset

### Error Google Earth Engine: "User not registered"
- Esperar aprobación de cuenta (1-2 días)
- Verificar email de confirmación

### Descargas muy lentas
- Usar resolución espacial más gruesa
- Descargar períodos más cortos
- Considerar usar Google Earth Engine (procesamiento en nube)

### Archivos NetCDF muy grandes
- Extraer solo región de interés
- Seleccionar menos variables
- Usar resolución temporal más gruesa (mensual vs diaria)

---

## RECURSOS ADICIONALES

### Documentación oficial:
- NASA POWER: https://power.larc.nasa.gov/docs/
- Copernicus CDS: https://cds.climate.copernicus.eu/api-how-to
- CHIRPS: https://www.chc.ucsb.edu/data/chirps
- Google Earth Engine: https://developers.google.com/earth-engine/

### Tutoriales:
- Python para ciencias de la tierra: https://carpentries-lab.github.io/python-aos-lesson/
- Xarray tutorial: https://tutorial.xarray.dev/
- Google Earth Engine guides: https://developers.google.com/earth-engine/guides

### Comunidades:
- GIS Stack Exchange: https://gis.stackexchange.com/
- Earth Science Stack Exchange: https://earthscience.stackexchange.com/

---

## CONTACTO Y AYUDA

Para problemas específicos con estos scripts:
- Revisar comentarios en cada archivo .py
- Consultar documentación oficial de cada fuente
- Buscar errores específicos en Stack Overflow

Para datos de Argentina:
- INA: bdh@ina.gob.ar
- DPA Buenos Aires: hidraulica@dposs.gba.gov.ar
- INTA: Consultar en oficinas regionales

---

## LICENCIA Y USO

Estos scripts son de código abierto para uso académico y de investigación.

Al usar datos de terceros, citar apropiadamente:
- NASA POWER: Cite los papers relevantes
- ERA5: Cite Hersbach et al. (2020)
- CHIRPS: Cite Funk et al. (2015)

---

Última actualización: Noviembre 2025
Versión: 1.0
