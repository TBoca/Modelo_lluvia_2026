"""
Script para acceder a datos de recursos hídricos de Argentina
Freatímetros, caudales, niveles de agua - INA, SSRH, organismos provinciales
"""

import requests
import pandas as pd
from datetime import datetime
import json

class INAHidroDownloader:
    """
    Acceso a datos hidrológicos del Instituto Nacional del Agua (INA)
    
    Sistemas disponibles:
    - SNIH: Sistema Nacional de Información Hídrica
    - BDH: Base de Datos Hidrológica
    """
    
    def __init__(self):
        self.base_url = "https://www.ina.gob.ar/"
        self.snih_url = "https://snih.hidricosargentina.gob.ar/"
        
    def informacion_acceso(self):
        """
        Información sobre cómo acceder a datos del INA
        """
        
        info = """
        ========================================================
        INSTITUTO NACIONAL DEL AGUA (INA) - DATOS HIDROLÓGICOS
        ========================================================
        
        1. SISTEMA NACIONAL DE INFORMACIÓN HÍDRICA (SNIH)
           URL: https://snih.hidricosargentina.gob.ar/
           
           Datos disponibles:
           - Niveles de agua en ríos y lagunas
           - Caudales
           - Precipitación
           - Evaporación
           - Calidad de agua
           
           ACCESO:
           a) Interfaz web:
              - Buscar estaciones por mapa o listado
              - Descargar datos en CSV/Excel
              - Visualizar series temporales
           
           b) Descarga manual:
              1. Ir a https://snih.hidricosargentina.gob.ar/
              2. Click en "Estaciones"
              3. Filtrar por provincia/cuenca
              4. Seleccionar estación
              5. Descargar datos históricos
        
        2. BASE DE DATOS HIDROLÓGICA (BDH)
           Contacto: bdh@ina.gob.ar
           
           Para acceso bulk o datos específicos, contactar:
           - Sistema más antiguo
           - Datos históricos extensos
           - Puede requerir solicitud formal
        
        3. DATOS DE NAPA FREÁTICA
           
           Fuentes principales:
           
           a) INA - Red de monitoreo de aguas subterráneas:
              - Freatímetros en cuencas principales
              - Datos no siempre publicados online
              - Contactar: subterraneas@ina.gob.ar
           
           b) Ministerio de Ambiente (ex MATE):
              - Datos de monitoreo ambiental
              - https://www.argentina.gob.ar/ambiente
           
           c) Organismos provinciales:
              - DPA Buenos Aires: http://www.dpaba.gba.gov.ar/
              - DIPAS Santa Fe
              - Cada provincia tiene su sistema
        
        4. ESTACIONES EN REGIÓN PAMPEANA
           
           Principales cuencas:
           - Cuenca del Río Salado (Buenos Aires)
           - Cuenca del Río Paraná
           - Cuenca del Río de la Plata
           - Lagunas encadenadas del oeste bonaerense
           
           Tipos de datos:
           - Niveles hidrométricos (m)
           - Caudales (m³/s)
           - Niveles freáticos (m bajo superficie)
           - Calidad de agua (parámetros físico-químicos)
        
        ========================================================
        EJEMPLO DE ESTACIONES EN PAMPA HÚMEDA:
        ========================================================
        
        Río Salado:
        - Junín
        - Gral. Belgrano
        - Guernica
        
        Lagunas:
        - Laguna Chascomús
        - Laguna de Lobos
        - Laguna La Salada (Gral. Madariaga)
        
        Para cada estación puedes obtener:
        - Nombre y código
        - Coordenadas (lat, lon)
        - Cuenca/subcuenca
        - Variables medidas
        - Período de datos
        - Frecuencia de medición
        """
        
        print(info)
        return info
    
    def generar_lista_estaciones(self):
        """
        Lista de estaciones hidrométricas importantes en región pampeana
        """
        
        estaciones = {
            'Rio_Salado': [
                {'nombre': 'Junín', 'lat': -34.58, 'lon': -60.95, 'cuenca': 'Río Salado'},
                {'nombre': 'Gral. Belgrano', 'lat': -35.77, 'lon': -58.50, 'cuenca': 'Río Salado'},
                {'nombre': 'Guernica', 'lat': -34.92, 'lon': -58.38, 'cuenca': 'Río Salado'},
            ],
            'Lagunas': [
                {'nombre': 'Chascomús', 'lat': -35.58, 'lon': -58.02, 'cuenca': 'Lagunas encadenadas'},
                {'nombre': 'Lobos', 'lat': -35.18, 'lon': -59.10, 'cuenca': 'Lagunas encadenadas'},
                {'nombre': 'La Salada', 'lat': -37.05, 'lon': -57.32, 'cuenca': 'Costa atlántica'},
            ],
            'Parana': [
                {'nombre': 'Rosario', 'lat': -32.95, 'lon': -60.64, 'cuenca': 'Río Paraná'},
                {'nombre': 'San Pedro', 'lat': -33.68, 'lon': -59.66, 'cuenca': 'Río Paraná'},
            ]
        }
        
        # Convertir a DataFrame
        todas = []
        for sistema, estacs in estaciones.items():
            for est in estacs:
                est['sistema'] = sistema
                todas.append(est)
        
        df = pd.DataFrame(todas)
        
        print("\nESTACIONES HIDROMÉTRICAS - REGIÓN PAMPEANA")
        print("="*60)
        print(df.to_string(index=False))
        
        # Guardar a CSV
        df.to_csv('estaciones_hidricas_pampeana.csv', index=False)
        print(f"\n✓ Guardado en: estaciones_hidricas_pampeana.csv")
        
        return df


class DPABuenosAiresDownloader:
    """
    Dirección Provincial de Recursos Hídricos - Buenos Aires
    Datos de agua superficial y subterránea de la provincia
    """
    
    def __init__(self):
        self.url = "http://www.dpaba.gba.gov.ar/"
        
    def informacion_acceso(self):
        """
        Información sobre datos de Buenos Aires
        """
        
        info = """
        ========================================================
        DIRECCIÓN PROVINCIAL DE RECURSOS HÍDRICOS - BUENOS AIRES
        ========================================================
        
        URL: http://www.dpaba.gba.gov.ar/
        
        DATOS DISPONIBLES:
        
        1. Red de Monitoreo de Agua Subterránea:
           - Freatímetros en todo el territorio bonaerense
           - Niveles piezométricos
           - Calidad de agua subterránea
           
        2. Red Hidrométrica Provincial:
           - Niveles de ríos y arroyos
           - Lagunas pampeanas
           - Canales de drenaje
        
        3. Precipitación:
           - Red de pluviómetros
           - Datos diarios/mensuales
        
        ACCESO A DATOS:
        
        - Web: Visualizador de datos
        - Descarga: Formularios de solicitud
        - Contacto: hidraulica@dposs.gba.gov.ar
        
        PARA ESTUDIOS ACADÉMICOS:
        - Generalmente se facilitan datos con carta institucional
        - Especificar región, período y variables
        - Tiempo de respuesta: 1-4 semanas
        
        ========================================================
        IMPORTANTES PARA PAMPA HÚMEDA:
        ========================================================
        
        Sistema de lagunas:
        - Lagunas encadenadas del oeste
        - Depresión del Salado
        - Lagunas costeras
        
        Nivel freático:
        - Freatímetros en zona agrícola núcleo
        - Zona de recarga del acuífero Pampeano
        - Área de descarga (bajos inundables)
        """
        
        print(info)


class DataIntegradoraHidrica:
    """
    Clase para integrar datos de múltiples fuentes
    """
    
    def __init__(self):
        self.fuentes = []
        
    def crear_inventario_datos(self):
        """
        Crea un inventario de todas las fuentes de datos disponibles
        """
        
        inventario = {
            'Climáticos': {
                'NASA POWER': {
                    'url': 'https://power.larc.nasa.gov/',
                    'variables': ['Precipitación', 'Temperatura', 'ET', 'Viento', 'Radiación'],
                    'resolucion_espacial': '0.5° (~55 km)',
                    'resolucion_temporal': 'Diaria',
                    'periodo': '1981-presente',
                    'acceso': 'API gratuita',
                    'script': '01_nasa_power_datos.py'
                },
                'ERA5': {
                    'url': 'https://cds.climate.copernicus.eu/',
                    'variables': ['Multi-variable (atmósfera, suelo)'],
                    'resolucion_espacial': '0.25° (~31 km)',
                    'resolucion_temporal': 'Horaria',
                    'periodo': '1940-presente',
                    'acceso': 'API con registro',
                    'script': '02_era5_datos.py'
                },
                'CHIRPS': {
                    'url': 'https://www.chc.ucsb.edu/data/chirps',
                    'variables': ['Precipitación'],
                    'resolucion_espacial': '0.05° (~5 km)',
                    'resolucion_temporal': 'Diaria',
                    'periodo': '1981-presente',
                    'acceso': 'Descarga directa',
                    'script': '03_chirps_precipitacion.py'
                },
                'NOAA-GPCC': {
                    'url': 'https://www.ncdc.noaa.gov/',
                    'variables': ['Multi-variable'],
                    'resolucion_espacial': 'Variable',
                    'resolucion_temporal': 'Variable',
                    'periodo': 'Histórico extenso',
                    'acceso': 'API y descarga',
                    'script': '04_noaa_gpcc_datos.py'
                }
            },
            'Satelitales': {
                'Sentinel-2': {
                    'url': 'https://scihub.copernicus.eu/',
                    'variables': ['Reflectancia multiespectral'],
                    'resolucion_espacial': '10-60 m',
                    'resolucion_temporal': '5 días',
                    'periodo': '2015-presente',
                    'acceso': 'Copernicus Open Access Hub / Google Earth Engine',
                    'script': '05_imagenes_satelitales.py',
                    'uso': 'NDWI, MNDWI para agua superficial'
                },
                'Landsat 8/9': {
                    'url': 'https://earthexplorer.usgs.gov/',
                    'variables': ['Reflectancia multiespectral'],
                    'resolucion_espacial': '30 m (15 m pan)',
                    'resolucion_temporal': '16 días',
                    'periodo': '2013-presente (L8), histórico desde 1972',
                    'acceso': 'USGS Earth Explorer / Google Earth Engine',
                    'script': '05_imagenes_satelitales.py',
                    'uso': 'Índices de agua, cambios históricos'
                },
                'MODIS': {
                    'url': 'https://modis.gsfc.nasa.gov/',
                    'variables': ['Reflectancia, índices de vegetación, agua'],
                    'resolucion_espacial': '250-1000 m',
                    'resolucion_temporal': 'Diaria',
                    'periodo': '2000-presente',
                    'acceso': 'NASA Earthdata / Google Earth Engine',
                    'script': '05_imagenes_satelitales.py',
                    'uso': 'Monitoreo continuo de grandes áreas'
                },
                'SMAP': {
                    'url': 'https://smap.jpl.nasa.gov/',
                    'variables': ['Humedad del suelo'],
                    'resolucion_espacial': '9 km',
                    'resolucion_temporal': '2-3 días',
                    'periodo': '2015-presente',
                    'acceso': 'NASA Earthdata / Google Earth Engine',
                    'script': '05_imagenes_satelitales.py',
                    'uso': 'Proxy de napa freática'
                }
            },
            'Hidrologicos': {
                'INA-SNIH': {
                    'url': 'https://snih.hidricosargentina.gob.ar/',
                    'variables': ['Niveles, caudales, calidad'],
                    'resolucion_espacial': 'Red de estaciones',
                    'resolucion_temporal': 'Diaria/Horaria',
                    'periodo': 'Variable por estación',
                    'acceso': 'Descarga web',
                    'script': '06_datos_hidricos_argentina.py',
                    'uso': 'Ríos, lagunas, validación'
                },
                'DPA Buenos Aires': {
                    'url': 'http://www.dpaba.gba.gov.ar/',
                    'variables': ['Niveles freáticos, hidrométricos'],
                    'resolucion_espacial': 'Red provincial',
                    'resolucion_temporal': 'Variable',
                    'periodo': 'Variable',
                    'acceso': 'Solicitud',
                    'script': '06_datos_hidricos_argentina.py',
                    'uso': 'Freatímetros, validación napa'
                }
            }
        }
        
        # Guardar inventario
        with open('inventario_fuentes_datos.json', 'w', encoding='utf-8') as f:
            json.dump(inventario, f, indent=2, ensure_ascii=False)
        
        print("="*60)
        print("INVENTARIO DE FUENTES DE DATOS")
        print("="*60)
        
        for categoria, fuentes in inventario.items():
            print(f"\n{categoria.upper()}:")
            print("-"*60)
            for nombre, info in fuentes.items():
                print(f"\n  {nombre}:")
                for key, value in info.items():
                    if key != 'script':
                        print(f"    • {key}: {value}")
        
        print(f"\n✓ Inventario guardado en: inventario_fuentes_datos.json")
        
        return inventario
    
    def generar_flujo_trabajo(self):
        """
        Genera un flujo de trabajo sugerido para el análisis
        """
        
        flujo = """
        ========================================================
        FLUJO DE TRABAJO SUGERIDO - ANÁLISIS ESPACIAL PAMPEANA
        ========================================================
        
        FASE 1: PREPARACIÓN Y EXPLORACIÓN (Semanas 1-2)
        ------------------------------------------------
        
        1. Definir región de estudio exacta
           - Delimitar polígono de área pampeana
           - Definir resolución espacial objetivo
           - Definir período temporal de análisis
        
        2. Inventario de datos disponibles
           - Revisar este inventario
           - Identificar gaps de datos
           - Priorizar fuentes según disponibilidad
        
        3. Setup de herramientas
           □ Instalar Python y librerías:
             pip install pandas numpy xarray rasterio geopandas
             pip install earthengine-api cdsapi sentinelhub
           
           □ Crear cuentas necesarias:
             □ Google Earth Engine
             □ Copernicus CDS
             □ NASA Earthdata
             □ NOAA (opcional)
           
           □ Configurar credenciales en scripts
        
        
        FASE 2: DESCARGA DE DATOS (Semanas 2-4)
        ----------------------------------------
        
        1. Datos climáticos base
           □ NASA POWER (script 01): Variables agrometeorológicas
           □ CHIRPS (script 03): Precipitación alta resolución
           □ ERA5 (script 02): Variables adicionales si necesario
        
        2. Imágenes satelitales
           □ Google Earth Engine: Exploración rápida
           □ Sentinel-2 (script 05): Períodos clave para agua
           □ SMAP/MODIS: Humedad del suelo
        
        3. Datos hidrológicos
           □ INA-SNIH (script 06): Estaciones en región
           □ DPA Buenos Aires: Solicitar freatímetros
           □ Validar coordenadas de estaciones
        
        
        FASE 3: PROCESAMIENTO Y LIMPIEZA (Semanas 4-6)
        -----------------------------------------------
        
        1. Estandarizar formatos
           - Mismo sistema de coordenadas (WGS84)
           - Mismas unidades
           - Mismo período temporal
        
        2. Control de calidad
           - Detectar outliers
           - Rellenar gaps con interpolación
           - Validar coherencia entre fuentes
        
        3. Crear base de datos unificada
           - Estructura espacial (grilla o vectorial)
           - Serie temporal completa
           - Metadatos documentados
        
        
        FASE 4: ANÁLISIS EXPLORATORIO (Semanas 6-8)
        --------------------------------------------
        
        1. Estadísticas descriptivas
           - Medias, varianzas, tendencias
           - Estacionalidad
           - Correlaciones entre variables
        
        2. Visualizaciones
           - Mapas de distribución espacial
           - Series temporales
           - Correlogramas
        
        3. Identificar patrones
           - Zonas de recarga/descarga
           - Relación precipitación-napa
           - Variabilidad interanual
        
        
        FASE 5: MODELADO ESPACIAL (Semanas 8-12)
        -----------------------------------------
        
        1. Selección de variables predictoras
           - Análisis de componentes principales
           - Selección por correlación
           - Importancia de variables
        
        2. Modelos espaciales
           - Regresión espacial
           - Kriging / geoestadística
           - Machine Learning espacial
           - Modelos de balance hídrico
        
        3. Validación
           - Cross-validation espacial
           - Validación temporal
           - Comparación con freatímetros
        
        
        FASE 6: RESULTADOS Y PRODUCTOS (Semanas 12-14)
        -----------------------------------------------
        
        1. Mapas finales
           - Distribución espacial de variables
           - Predicciones de napa
           - Incertidumbre
        
        2. Series temporales
           - Evolución de napa
           - Tendencias
           - Anomalías
        
        3. Documentación
           - Metodología
           - Limitaciones
           - Recomendaciones
        
        
        ========================================================
        TIPS Y MEJORES PRÁCTICAS
        ========================================================
        
        1. Empieza con área piloto pequeña
           - Valida metodología en subregión
           - Escala a toda la pampa después
        
        2. Usa Google Earth Engine cuando sea posible
           - Evita descargas masivas
           - Procesamiento más rápido
           - Acceso a todo el catálogo
        
        3. Documenta TODO
           - Scripts comentados
           - Cuaderno de campo digital
           - Control de versiones (Git)
        
        4. Valida continuamente
           - Compara con datos in-situ
           - Verifica coherencia física
           - Consulta con expertos locales
        
        5. Considera limitaciones
           - Resolución espacial/temporal
           - Errores de sensores
           - Gaps de datos
           - Autocorrelación espacial
        
        6. Colabora
           - INA, INTA, universidades
           - Comparte datos y métodos
           - Valida con conocimiento local
        """
        
        print(flujo)
        
        # Guardar a archivo
        with open('flujo_trabajo_analisis.txt', 'w', encoding='utf-8') as f:
            f.write(flujo)
        
        print(f"\n✓ Flujo de trabajo guardado en: flujo_trabajo_analisis.txt")


# EJEMPLOS DE USO
if __name__ == "__main__":
    
    print("="*60)
    print("DATOS HÍDRICOS ARGENTINA - RECURSOS Y ACCESO")
    print("="*60)
    
    # INA
    print("\n1. INSTITUTO NACIONAL DEL AGUA (INA)")
    print("="*60)
    ina = INAHidroDownloader()
    ina.informacion_acceso()
    
    print("\n")
    estaciones = ina.generar_lista_estaciones()
    
    
    # DPA Buenos Aires
    print("\n\n2. DIRECCIÓN PROVINCIAL AGUA - BUENOS AIRES")
    print("="*60)
    dpa = DPABuenosAiresDownloader()
    dpa.informacion_acceso()
    
    
    # Integración
    print("\n\n3. INVENTARIO INTEGRADO DE FUENTES")
    print("="*60)
    integrador = DataIntegradoraHidrica()
    inventario = integrador.crear_inventario_datos()
    
    
    # Flujo de trabajo
    print("\n\n4. FLUJO DE TRABAJO COMPLETO")
    print("="*60)
    integrador.generar_flujo_trabajo()
    
    
    print("\n" + "="*60)
    print("ARCHIVOS GENERADOS")
    print("="*60)
    print("""
    ✓ estaciones_hidricas_pampeana.csv
    ✓ inventario_fuentes_datos.json
    ✓ flujo_trabajo_analisis.txt
    
    SCRIPTS DISPONIBLES:
    ✓ 01_nasa_power_datos.py
    ✓ 02_era5_datos.py
    ✓ 03_chirps_precipitacion.py
    ✓ 04_noaa_gpcc_datos.py
    ✓ 05_imagenes_satelitales.py
    ✓ 06_datos_hidricos_argentina.py (este archivo)
    """)
