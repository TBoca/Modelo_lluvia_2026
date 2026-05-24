"""
Script para descargar imágenes satelitales para monitoreo de recursos hídricos
Landsat, Sentinel-2, MODIS para análisis de lagunas, ríos, canales y napa freática

Útil para detectar cambios en cuerpos de agua y humedad superficial
"""

import os
from datetime import datetime, timedelta

class SentinelHubDownloader:
    """
    Acceso a imágenes Sentinel-2 y Landsat vía Sentinel Hub
    
    Requiere:
    - Cuenta en Sentinel Hub: https://www.sentinel-hub.com/
    - pip install sentinelhub
    """
    
    def __init__(self, client_id=None, client_secret=None):
        """
        Inicializa con credenciales de Sentinel Hub
        
        Obtén credenciales en:
        https://apps.sentinel-hub.com/dashboard/#/account/settings
        """
        
        self.client_id = client_id
        self.client_secret = client_secret
        
        if client_id and client_secret:
            try:
                from sentinelhub import SHConfig
                
                config = SHConfig()
                config.sh_client_id = client_id
                config.sh_client_secret = client_secret
                config.save()
                
                print("✓ Configuración de Sentinel Hub guardada")
                
            except ImportError:
                print("Error: Instala sentinelhub con: pip install sentinelhub")
    
    def descargar_sentinel2(self, bbox, fecha_inicio, fecha_fin, 
                           resolucion=10, max_cloud=20):
        """
        Descarga imágenes Sentinel-2
        
        Parámetros:
            bbox: [lon_min, lat_min, lon_max, lat_max]
            fecha_inicio, fecha_fin: strings 'YYYY-MM-DD'
            resolucion: metros por pixel (10, 20, 60)
            max_cloud: % máximo de nubes
        """
        
        try:
            from sentinelhub import (
                SHConfig, DataCollection, SentinelHubRequest,
                BBox, CRS, MimeType, bbox_to_dimensions
            )
            
            # Configurar bbox
            bbox_coords = BBox(bbox=bbox, crs=CRS.WGS84)
            size = bbox_to_dimensions(bbox_coords, resolution=resolucion)
            
            print(f"Buscando imágenes Sentinel-2:")
            print(f"  Área: {bbox}")
            print(f"  Período: {fecha_inicio} a {fecha_fin}")
            print(f"  Resolución: {resolucion}m")
            print(f"  Nubes máx: {max_cloud}%")
            print(f"  Dimensiones: {size}")
            
            # Script de evaluación para índices de agua
            evalscript = """
            //VERSION=3
            function setup() {
                return {
                    input: ["B02", "B03", "B04", "B08", "B11"],
                    output: { bands: 5 }
                };
            }
            
            function evaluatePixel(sample) {
                return [sample.B02, sample.B03, sample.B04, sample.B08, sample.B11];
            }
            """
            
            # Crear solicitud
            request = SentinelHubRequest(
                evalscript=evalscript,
                input_data=[{
                    "type": "S2L2A",
                    "dataFilter": {
                        "timeRange": (fecha_inicio, fecha_fin),
                        "maxCloudCoverage": max_cloud
                    }
                }],
                responses=[{
                    "identifier": "default",
                    "format": {
                        "type": "image/tiff"
                    }
                }],
                bbox=bbox_coords,
                size=size,
                config=SHConfig()
            )
            
            # Descargar
            data = request.get_data()
            
            print(f"✓ Descargadas {len(data)} imágenes")
            
            return data
            
        except ImportError:
            print("Error: Instala sentinelhub")
            print("pip install sentinelhub")
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None


class GoogleEarthEngineDownloader:
    """
    Acceso a imágenes satelitales vía Google Earth Engine
    
    Ventajas:
    - Procesamiento en la nube
    - Acceso a colecciones completas sin descargas masivas
    - Análisis de series temporales
    
    Requiere:
    - Cuenta GEE: https://earthengine.google.com/signup/
    - pip install earthengine-api
    """
    
    def __init__(self):
        try:
            import ee
            
            # Intentar autenticar
            try:
                ee.Initialize()
                print("✓ Google Earth Engine inicializado")
            except:
                print("Necesitas autenticar Google Earth Engine")
                print("Ejecuta: earthengine authenticate")
                print("O en Python: ee.Authenticate()")
                
        except ImportError:
            print("Error: Instala earthengine-api")
            print("pip install earthengine-api")
    
    def analizar_agua_superficie(self, bbox, fecha_inicio, fecha_fin):
        """
        Analiza cambios en cuerpos de agua usando índices espectrales
        
        Usa:
        - NDWI (Normalized Difference Water Index)
        - MNDWI (Modified NDWI)
        
        Parámetros:
            bbox: [lon_min, lat_min, lon_max, lat_max]
            fecha_inicio, fecha_fin: strings 'YYYY-MM-DD'
        """
        
        codigo_gee = f"""
        // Script para Google Earth Engine Code Editor
        // https://code.earthengine.google.com/
        
        // Definir región de interés (Región Pampeana)
        var bbox = ee.Geometry.Rectangle({bbox});
        
        // Cargar colección Sentinel-2
        var s2 = ee.ImageCollection('COPERNICUS/S2_SR')
            .filterDate('{fecha_inicio}', '{fecha_fin}')
            .filterBounds(bbox)
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20));
        
        // Función para calcular índices de agua
        function calcularIndices(image) {{
            // NDWI = (Green - NIR) / (Green + NIR)
            var ndwi = image.normalizedDifference(['B3', 'B8']).rename('NDWI');
            
            // MNDWI = (Green - SWIR) / (Green + SWIR)
            var mndwi = image.normalizedDifference(['B3', 'B11']).rename('MNDWI');
            
            return image.addBands([ndwi, mndwi]);
        }}
        
        // Aplicar función a todas las imágenes
        var s2ConIndices = s2.map(calcularIndices);
        
        // Calcular mediana temporal
        var mediana = s2ConIndices.median().clip(bbox);
        
        // Clasificar agua (MNDWI > 0)
        var agua = mediana.select('MNDWI').gt(0);
        
        // Visualizar
        Map.centerObject(bbox, 8);
        
        Map.addLayer(mediana, {{
            bands: ['B4', 'B3', 'B2'],
            min: 0,
            max: 3000
        }}, 'RGB Natural');
        
        Map.addLayer(mediana.select('NDWI'), {{
            min: -1,
            max: 1,
            palette: ['red', 'yellow', 'green', 'cyan', 'blue']
        }}, 'NDWI');
        
        Map.addLayer(agua.selfMask(), {{
            palette: ['blue']
        }}, 'Cuerpos de Agua');
        
        // Calcular área de agua
        var areaAgua = agua.multiply(ee.Image.pixelArea())
            .reduceRegion({{
                reducer: ee.Reducer.sum(),
                geometry: bbox,
                scale: 10,
                maxPixels: 1e13
            }});
        
        print('Área de agua (m²):', areaAgua.get('MNDWI'));
        
        // Exportar resultado
        Export.image.toDrive({{
            image: agua,
            description: 'agua_pampeana',
            scale: 10,
            region: bbox,
            maxPixels: 1e13
        }});
        """
        
        print("="*60)
        print("CÓDIGO PARA GOOGLE EARTH ENGINE")
        print("="*60)
        print("\nCopia y pega este código en:")
        print("https://code.earthengine.google.com/")
        print("\n" + codigo_gee)
        
        return codigo_gee
    
    def analizar_humedad_suelo(self, bbox, fecha_inicio, fecha_fin):
        """
        Analiza humedad del suelo usando productos SMAP/SMOS
        """
        
        codigo_gee = f"""
        // Análisis de humedad del suelo - NASA SMAP
        
        var bbox = ee.Geometry.Rectangle({bbox});
        
        // SMAP Soil Moisture (resolución ~9km)
        var smap = ee.ImageCollection('NASA/SMAP/SPL4SMGP/007')
            .filterDate('{fecha_inicio}', '{fecha_fin}')
            .filterBounds(bbox)
            .select('sm_surface');  // Humedad superficial
        
        // Calcular promedio temporal
        var humedadMedia = smap.mean().clip(bbox);
        
        // Visualizar
        Map.centerObject(bbox, 8);
        
        Map.addLayer(humedadMedia, {{
            min: 0.1,
            max: 0.5,
            palette: ['red', 'yellow', 'green', 'blue']
        }}, 'Humedad del Suelo (m³/m³)');
        
        // Serie temporal
        var grafico = ui.Chart.image.seriesByRegion(
            smap,
            bbox,
            ee.Reducer.mean(),
            'sm_surface',
            9000,
            'system:time_start'
        ).setOptions({{
            title: 'Humedad del Suelo - Serie Temporal',
            vAxis: {{title: 'Humedad (m³/m³)'}},
            hAxis: {{title: 'Fecha'}}
        }});
        
        print(grafico);
        
        // Exportar serie temporal
        var serie = smap.map(function(img) {{
            var media = img.reduceRegion({{
                reducer: ee.Reducer.mean(),
                geometry: bbox,
                scale: 9000
            }});
            return ee.Feature(null, {{
                'fecha': img.date().format('YYYY-MM-dd'),
                'humedad': media.get('sm_surface')
            }});
        }});
        
        Export.table.toDrive({{
            collection: ee.FeatureCollection(serie),
            description: 'humedad_suelo_serie',
            fileFormat: 'CSV'
        }});
        """
        
        print("="*60)
        print("CÓDIGO GEE - HUMEDAD DEL SUELO")
        print("="*60)
        print("\n" + codigo_gee)
        
        return codigo_gee


class LandsatDownloader:
    """
    Descarga imágenes Landsat desde USGS Earth Explorer
    
    Landsat 8/9: Resolución 30m (15m pancromática)
    Útil para análisis histórico (desde 1972)
    """
    
    def __init__(self):
        self.base_url = "https://earthexplorer.usgs.gov/"
        
    def generar_instrucciones_descarga(self):
        """
        Genera instrucciones para descarga manual de Landsat
        """
        
        instrucciones = """
        ======================================================
        DESCARGA DE IMÁGENES LANDSAT DESDE USGS EARTH EXPLORER
        ======================================================
        
        1. REGISTRO:
           - Ir a: https://earthexplorer.usgs.gov/
           - Crear cuenta gratuita si no tienes una
        
        2. BÚSQUEDA:
           a) En "Search Criteria", definir área de interés:
              - Usar "Polygon" o "Circle" para región pampeana
              - O ingresar coordenadas:
                Latitud: -37° a -30°
                Longitud: -65° a -58°
           
           b) En "Date Range", seleccionar período
           
           c) Click en "Data Sets"
           
        3. SELECCIONAR PRODUCTOS:
           - Landsat > Landsat Collection 2 Level-2
           - Landsat 8-9 OLI/TIRS C2 L2 (más reciente)
           - Landsat 7 ETM+ C2 L2 (histórico)
           - Landsat 4-5 TM C2 L2 (muy histórico)
        
        4. FILTROS ADICIONALES:
           - Click en "Additional Criteria"
           - Land Cloud Cover: 0-20% (ajustar según necesidad)
        
        5. RESULTADOS:
           - Click en "Results"
           - Revisar miniaturas y metadatos
           - Descargar productos individuales o hacer pedido bulk
        
        6. BANDAS ÚTILES PARA AGUA:
           - Banda 2 (Blue): 0.45-0.51 μm
           - Banda 3 (Green): 0.53-0.59 μm
           - Banda 5 (NIR): 0.85-0.88 μm
           - Banda 6 (SWIR1): 1.57-1.65 μm
           - Banda 7 (SWIR2): 2.11-2.29 μm
        
        ÍNDICES PARA DETECCIÓN DE AGUA:
        
        NDWI = (Green - NIR) / (Green + NIR)
        MNDWI = (Green - SWIR1) / (Green + SWIR1)
        
        Agua típicamente: MNDWI > 0, NDWI > 0
        
        ======================================================
        ALTERNATIVA: Google Earth Engine
        ======================================================
        
        Para procesamiento más eficiente, usa Google Earth Engine
        que tiene todo el catálogo Landsat disponible sin descargas:
        
        https://code.earthengine.google.com/
        
        Ver script en la clase GoogleEarthEngineDownloader
        """
        
        print(instrucciones)
        return instrucciones


class MODISDownloader:
    """
    Información sobre productos MODIS para monitoreo de agua
    
    MODIS: Resolución temporal diaria, resolución espacial 250m-1km
    Ideal para monitoreo continuo de grandes áreas
    """
    
    def __init__(self):
        self.productos_utiles = {
            'MOD09': 'Reflectancia superficial',
            'MOD13': 'Índices de vegetación (NDVI, EVI)',
            'MOD44W': 'Máscara de agua',
            'MOD16': 'Evapotranspiración',
        }
    
    def informacion_productos(self):
        """
        Muestra información sobre productos MODIS útiles
        """
        
        info = """
        ======================================================
        PRODUCTOS MODIS PARA MONITOREO HÍDRICO
        ======================================================
        
        1. MOD44W - Water Mask
           - Clasificación tierra/agua
           - Resolución: 250m
           - Actualización: Anual
           - Útil para: Mapeo de cuerpos de agua permanentes
        
        2. MOD09A1 - Surface Reflectance (8-day)
           - Bandas espectrales para calcular índices
           - Resolución: 500m
           - Frecuencia: 8 días
           - Útil para: Calcular NDWI, MNDWI
        
        3. MOD13Q1 - Vegetation Indices (16-day)
           - NDVI, EVI
           - Resolución: 250m
           - Útil para: Diferenciar vegetación de agua
        
        4. MOD16A2 - Evapotranspiration (8-day)
           - ET, PET
           - Resolución: 500m
           - Útil para: Balance hídrico
        
        ACCESO A DATOS MODIS:
        
        Opción 1: NASA Earthdata
        - https://search.earthdata.nasa.gov/
        - Requiere registro gratuito
        - Descarga directa
        
        Opción 2: Google Earth Engine
        - Acceso a todo el catálogo MODIS
        - Procesamiento en la nube
        - Sin necesidad de descargas
        
        Opción 3: AppEEARS
        - https://appeears.earthdatacloud.nasa.gov/
        - Extracción de series temporales por punto/área
        - Formato tabular listo para análisis
        
        EJEMPLO DE CÓDIGO GEE PARA MODIS:
        """
        
        codigo_gee = """
        // Análisis MODIS agua - Google Earth Engine
        
        var bbox = ee.Geometry.Rectangle([-65, -37, -58, -30]);
        
        // Cargar máscara de agua MODIS
        var agua = ee.ImageCollection('MODIS/006/MOD44W')
            .filterDate('2020-01-01', '2021-01-01')
            .first()
            .select('water_mask')
            .clip(bbox);
        
        // Visualizar
        Map.centerObject(bbox, 7);
        Map.addLayer(agua, {min: 0, max: 1, palette: ['white', 'blue']}, 'Agua');
        
        // Calcular área
        var areaAgua = agua.eq(1).multiply(ee.Image.pixelArea())
            .reduceRegion({
                reducer: ee.Reducer.sum(),
                geometry: bbox,
                scale: 250,
                maxPixels: 1e10
            });
        
        print('Área de agua (km²):', ee.Number(areaAgua.get('water_mask')).divide(1e6));
        """
        
        print(info)
        print("\n" + codigo_gee)


# EJEMPLOS DE USO
if __name__ == "__main__":
    
    print("="*60)
    print("MONITOREO DE RECURSOS HÍDRICOS CON IMÁGENES SATELITALES")
    print("="*60)
    
    # Definir región pampeana
    bbox_pampeana = [-65, -37, -58, -30]  # [lon_min, lat_min, lon_max, lat_max]
    
    print("\nREGIÓN DE ESTUDIO: Pampa Argentina")
    print(f"Bounding box: {bbox_pampeana}")
    
    
    # Google Earth Engine (Recomendado)
    print("\n" + "="*60)
    print("OPCIÓN 1: GOOGLE EARTH ENGINE (Recomendado)")
    print("="*60)
    
    gee = GoogleEarthEngineDownloader()
    
    print("\nScript para análisis de agua superficial:")
    gee.analizar_agua_superficie(
        bbox=bbox_pampeana,
        fecha_inicio='2023-01-01',
        fecha_fin='2023-12-31'
    )
    
    print("\n\nScript para análisis de humedad del suelo:")
    gee.analizar_humedad_suelo(
        bbox=bbox_pampeana,
        fecha_inicio='2023-01-01',
        fecha_fin='2023-12-31'
    )
    
    
    # Landsat
    print("\n" + "="*60)
    print("OPCIÓN 2: LANDSAT (Alta resolución, histórico)")
    print("="*60)
    
    landsat = LandsatDownloader()
    landsat.generar_instrucciones_descarga()
    
    
    # MODIS
    print("\n" + "="*60)
    print("OPCIÓN 3: MODIS (Monitoreo continuo)")
    print("="*60)
    
    modis = MODISDownloader()
    modis.informacion_productos()
    
    
    # Sentinel Hub (requiere cuenta)
    print("\n" + "="*60)
    print("OPCIÓN 4: SENTINEL HUB (API comercial)")
    print("="*60)
    print("""
    Sentinel Hub ofrece acceso a:
    - Sentinel-1 (radar, atraviesa nubes)
    - Sentinel-2 (óptico, 10m resolución)
    - Sentinel-3 (océanos, tierra)
    - Landsat
    
    Ventajas:
    - API bien documentada
    - Procesamiento bajo demanda
    - Historial completo
    
    Desventajas:
    - Requiere suscripción (tiene plan gratuito limitado)
    
    Más info: https://www.sentinel-hub.com/
    """)
    
    
    print("\n" + "="*60)
    print("RESUMEN Y RECOMENDACIONES")
    print("="*60)
    print("""
    PARA MONITOREO DE NAPA FREÁTICA (proxies):
    
    1. Cuerpos de agua superficial (lagunas):
       - Sentinel-2 (10m, cada 5 días)
       - Landsat 8/9 (30m, cada 16 días)
       - MODIS (250m, diario)
       - Calcular MNDWI, NDWI
       - Detectar cambios en área y número de lagunas
    
    2. Vegetación (indicador de humedad):
       - NDVI de Sentinel-2 o Landsat
       - Vegetación verde indica disponibilidad de agua
       - Cambios estacionales correlacionan con napa
    
    3. Humedad del suelo:
       - SMAP (9km, cada 2-3 días)
       - SMOS (25km, cada 3 días)
       - Sentinel-1 radar (proxy de humedad)
    
    4. Análisis de canales y ríos:
       - Sentinel-2 para detectar agua en canales
       - Clasificación supervisada
       - Análisis de series temporales
    
    FLUJO DE TRABAJO SUGERIDO:
    
    1. Usar Google Earth Engine para exploración inicial
    2. Identificar períodos y áreas de interés
    3. Descargar imágenes específicas si necesitas procesamiento local
    4. Correlacionar con datos de freatímetros (si disponibles)
    5. Desarrollar modelos predictivos
    
    COMPLEMENTAR CON:
    - Datos climáticos (NASA POWER, ERA5, CHIRPS)
    - Datos hidrológicos (INA, caudales)
    - Modelo digital de elevación (DEM) para topografía
    - Mapas de suelos
    """)
