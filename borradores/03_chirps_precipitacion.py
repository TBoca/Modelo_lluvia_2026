"""
Script para descargar datos de precipitación CHIRPS
Climate Hazards Group InfraRed Precipitation with Station data

CHIRPS: Datos de precipitación diaria con resolución ~5 km para 1981-presente
https://www.chc.ucsb.edu/data/chirps
"""

import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os

class CHIRPSDownloader:
    """
    Descarga datos de precipitación CHIRPS
    
    Resoluciones disponibles:
    - 0.05° (~5 km) - Mejor resolución
    - 0.25° (~25 km) - Resolución estándar
    
    Formatos:
    - GeoTIFF (.tif)
    - NetCDF (.nc)
    - BIL (.bil)
    """
    
    def __init__(self):
        self.base_url_data = "https://data.chc.ucsb.edu/products/CHIRPS-2.0"
        self.base_url_ftp = "https://data.chc.ucsb.edu/products/CHIRPS-2.0"
        
    def generar_url_diaria(self, fecha, resolucion='0.05'):
        """
        Genera URL para datos diarios de CHIRPS
        
        Parámetros:
            fecha: objeto datetime o string 'YYYY-MM-DD'
            resolucion: '0.05' o '0.25'
        """
        
        if isinstance(fecha, str):
            fecha = datetime.strptime(fecha, '%Y-%m-%d')
        
        año = fecha.year
        mes = fecha.month
        dia = fecha.day
        
        # Formato del nombre del archivo
        fecha_str = fecha.strftime('%Y.%m.%d')
        
        # URL para datos diarios globales
        url = (f"{self.base_url_data}/global_daily/tifs/p{resolucion}/"
               f"{año}/chirps-v2.0.{fecha_str}.tif.gz")
        
        return url
    
    def descargar_archivo(self, url, nombre_archivo=None):
        """
        Descarga un archivo de CHIRPS
        """
        
        if nombre_archivo is None:
            nombre_archivo = url.split('/')[-1]
        
        print(f"Descargando: {nombre_archivo}")
        print(f"URL: {url}")
        
        try:
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            # Descargar con barra de progreso
            total_size = int(response.headers.get('content-length', 0))
            
            with open(nombre_archivo, 'wb') as f:
                if total_size == 0:
                    f.write(response.content)
                else:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            progress = (downloaded / total_size) * 100
                            print(f"\rProgreso: {progress:.1f}%", end='')
            
            print(f"\n✓ Descargado: {nombre_archivo}")
            return nombre_archivo
            
        except requests.exceptions.RequestException as e:
            print(f"\nError en descarga: {e}")
            return None
    
    def descargar_periodo_diario(self, fecha_inicio, fecha_fin, 
                                 directorio='chirps_data', resolucion='0.05'):
        """
        Descarga datos diarios para un período
        """
        
        if isinstance(fecha_inicio, str):
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        if isinstance(fecha_fin, str):
            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
        
        # Crear directorio si no existe
        os.makedirs(directorio, exist_ok=True)
        
        # Lista de fechas
        fechas = []
        fecha_actual = fecha_inicio
        while fecha_actual <= fecha_fin:
            fechas.append(fecha_actual)
            fecha_actual += timedelta(days=1)
        
        print(f"Descargando CHIRPS para {len(fechas)} días")
        print(f"Período: {fecha_inicio.date()} a {fecha_fin.date()}")
        print(f"Resolución: {resolucion}°")
        
        archivos_descargados = []
        
        for i, fecha in enumerate(fechas):
            print(f"\n[{i+1}/{len(fechas)}] Fecha: {fecha.date()}")
            
            url = self.generar_url_diaria(fecha, resolucion)
            nombre_archivo = os.path.join(directorio, url.split('/')[-1])
            
            archivo = self.descargar_archivo(url, nombre_archivo)
            
            if archivo:
                archivos_descargados.append(archivo)
                
                # Descomprimir si es .gz
                if archivo.endswith('.gz'):
                    self.descomprimir_gz(archivo)
        
        print(f"\n✓ Descarga completada: {len(archivos_descargados)} archivos")
        return archivos_descargados
    
    def descomprimir_gz(self, archivo_gz):
        """
        Descomprime archivos .gz
        """
        
        import gzip
        import shutil
        
        archivo_out = archivo_gz.replace('.gz', '')
        
        try:
            with gzip.open(archivo_gz, 'rb') as f_in:
                with open(archivo_out, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            print(f"  ✓ Descomprimido: {archivo_out}")
            
            # Eliminar archivo comprimido
            os.remove(archivo_gz)
            
            return archivo_out
            
        except Exception as e:
            print(f"  Error al descomprimir: {e}")
            return None
    
    def leer_geotiff_region(self, archivo_tif, lat_min, lat_max, lon_min, lon_max):
        """
        Lee un GeoTIFF de CHIRPS y extrae datos para una región
        
        Requiere: pip install rasterio
        """
        
        try:
            import rasterio
            from rasterio.windows import from_bounds
            
            with rasterio.open(archivo_tif) as src:
                
                # Obtener ventana para la región de interés
                window = from_bounds(lon_min, lat_min, lon_max, lat_max, 
                                    src.transform)
                
                # Leer datos de la ventana
                data = src.read(1, window=window)
                
                # Obtener coordenadas
                transform = src.window_transform(window)
                
                print(f"\nDatos extraídos de: {archivo_tif}")
                print(f"Región: lat [{lat_min}, {lat_max}], lon [{lon_min}, {lon_max}]")
                print(f"Dimensiones: {data.shape}")
                print(f"Precipitación - Min: {data.min():.2f} mm, Max: {data.max():.2f} mm, Promedio: {data.mean():.2f} mm")
                
                return data, transform
                
        except ImportError:
            print("Error: Necesitas instalar rasterio")
            print("Ejecuta: pip install rasterio")
            return None, None
        except Exception as e:
            print(f"Error al leer GeoTIFF: {e}")
            return None, None
    
    def generar_url_mensual(self, año, mes, resolucion='0.05'):
        """
        Genera URL para datos mensuales acumulados
        """
        
        # Formato del nombre del archivo mensual
        url = (f"{self.base_url_data}/global_monthly/tifs/"
               f"chirps-v2.0.{año}.{mes:02d}.tif.gz")
        
        return url
    
    def generar_url_anual(self, año, resolucion='0.05'):
        """
        Genera URL para datos anuales acumulados
        """
        
        url = (f"{self.base_url_data}/global_annual/tifs/"
               f"chirps-v2.0.{año}.tif.gz")
        
        return url


# EJEMPLOS DE USO
if __name__ == "__main__":
    
    print("="*60)
    print("SCRIPT DE DESCARGA CHIRPS - PRECIPITACIÓN")
    print("="*60)
    
    downloader = CHIRPSDownloader()
    
    # EJEMPLO 1: Descargar datos de un día específico
    print("\n" + "="*60)
    print("EJEMPLO 1: Descargar datos de un día")
    print("="*60)
    
    url_dia = downloader.generar_url_diaria('2023-01-15', resolucion='0.05')
    print(f"URL generada: {url_dia}")
    
    # Descomenta para descargar
    """
    archivo = downloader.descargar_archivo(url_dia, 'chirps_2023_01_15.tif.gz')
    if archivo and archivo.endswith('.gz'):
        downloader.descomprimir_gz(archivo)
    """
    
    
    # EJEMPLO 2: Descargar período (CUIDADO: puede ser mucho volumen)
    print("\n" + "="*60)
    print("EJEMPLO 2: Descargar período de 7 días")
    print("="*60)
    
    # Descomenta para descargar
    """
    archivos = downloader.descargar_periodo_diario(
        fecha_inicio='2023-01-01',
        fecha_fin='2023-01-07',
        directorio='chirps_enero_2023',
        resolucion='0.05'
    )
    """
    
    
    # EJEMPLO 3: Leer datos de región pampeana de un archivo
    print("\n" + "="*60)
    print("EJEMPLO 3: Leer GeoTIFF para región pampeana")
    print("="*60)
    
    # Límites de la región pampeana
    lat_min, lat_max = -37, -30
    lon_min, lon_max = -65, -58
    
    print(f"Región pampeana: lat [{lat_min}, {lat_max}], lon [{lon_min}, {lon_max}]")
    
    # Descomenta si tienes un archivo descargado
    """
    archivo_ejemplo = 'chirps_data/chirps-v2.0.2023.01.15.tif'
    if os.path.exists(archivo_ejemplo):
        data, transform = downloader.leer_geotiff_region(
            archivo_ejemplo,
            lat_min, lat_max, lon_min, lon_max
        )
    """
    
    
    # EJEMPLO 4: URLs para datos mensuales y anuales
    print("\n" + "="*60)
    print("EJEMPLO 4: URLs para datos agregados")
    print("="*60)
    
    url_mensual = downloader.generar_url_mensual(2023, 1, resolucion='0.05')
    print(f"Datos mensuales (enero 2023):\n{url_mensual}")
    
    url_anual = downloader.generar_url_anual(2023, resolucion='0.05')
    print(f"\nDatos anuales (2023):\n{url_anual}")
    
    
    # INFORMACIÓN ADICIONAL
    print("\n" + "="*60)
    print("INFORMACIÓN SOBRE CHIRPS:")
    print("="*60)
    print("""
    CARACTERÍSTICAS:
    - Resolución espacial: 0.05° (~5 km) o 0.25° (~25 km)
    - Resolución temporal: Diaria, mensual, anual
    - Período: 1981 - presente (actualizado ~3 semanas después)
    - Cobertura: 50°S - 50°N (incluye toda Argentina)
    - Variables: Solo precipitación
    
    VENTAJAS:
    - Alta resolución espacial
    - Combina datos satelitales con estaciones terrestres
    - Ideal para estudios de sequía e hidrología
    - Acceso libre y gratuito
    - Formato GeoTIFF fácil de procesar
    
    DATOS COMPLEMENTARIOS:
    - CHIRPS-GEFS: Pronósticos de precipitación
    - CHPclim: Climatología de precipitación
    
    HERRAMIENTAS RECOMENDADAS:
    - Python: rasterio, xarray, geopandas
    - R: raster, terra, sf
    - QGIS: Para visualización
    - Google Earth Engine: Acceso cloud a CHIRPS
    
    ENLACES ÚTILES:
    - Página principal: https://www.chc.ucsb.edu/data/chirps
    - Documentación: https://www.chc.ucsb.edu/data/chirps#documentation
    - Servidor de datos: https://data.chc.ucsb.edu/products/CHIRPS-2.0/
    - Paper: Funk et al. (2015) Scientific Data
    """)
    
    print("\n" + "="*60)
    print("EJEMPLO DE FLUJO DE TRABAJO:")
    print("="*60)
    print("""
    1. Descargar datos diarios para tu período de interés
    2. Descomprimir archivos .gz
    3. Leer GeoTIFF y extraer región pampeana
    4. Calcular estadísticas (media, suma, percentiles)
    5. Exportar a CSV o NetCDF para análisis
    6. Visualizar mapas y series temporales
    
    NOTA: Para análisis espaciales avanzados, considera usar
    Google Earth Engine que tiene CHIRPS precargado y permite
    procesamiento en la nube sin descargar archivos grandes.
    """)
