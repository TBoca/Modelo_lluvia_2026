"""
Script para descargar datos climáticos de NOAA y GPCC
- NOAA: National Oceanic and Atmospheric Administration
- GPCC: Global Precipitation Climatology Centre

Múltiples datasets disponibles para la región pampeana
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime
import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "datos"

class NOAADownloader:
    """
    Descarga datos de NOAA usando diferentes servicios
    
    Servicios principales:
    1. NCDC CDO (Climate Data Online)
    2. PSL (Physical Sciences Laboratory)
    3. ISD (Integrated Surface Database)
    """
    
    def __init__(self, api_token=None):
        """
        Inicializa el descargador de NOAA
        
        Para NCDC CDO necesitas un token gratuito:
        https://www.ncdc.noaa.gov/cdo-web/token
        """
        self.api_token = api_token
        self.base_url_cdo = "https://www.ncei.noaa.gov/cdo-web/api/v2"
        self.base_url_psl = "https://psl.noaa.gov/thredds/dodsC"
        
    def buscar_estaciones_argentina(self, dataset='GHCND', limite=100):
        """
        Busca estaciones meteorológicas en Argentina
        
        Datasets:
        - GHCND: Global Historical Climatology Network - Daily
        - GSOM: Global Summary of the Month
        - GSOY: Global Summary of the Year
        """
        
        if not self.api_token:
            print("Error: Se requiere API token de NOAA")
            print("Obtén uno gratis en: https://www.ncdc.noaa.gov/cdo-web/token")
            return None
        
        headers = {'token': self.api_token}
        
        # Buscar estaciones en Argentina
        url = f"{self.base_url_cdo}/stations"
        params = {
            'locationid': 'FIPS:AR',  # Argentina
            'datasetid': dataset,
            'limit': limite
        }
        
        print(f"Buscando estaciones en Argentina - Dataset: {dataset}")
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'results' in data:
                estaciones = pd.DataFrame(data['results'])
                print(f"✓ Encontradas {len(estaciones)} estaciones")
                
                # Mostrar columnas disponibles
                print(f"Columnas: {list(estaciones.columns)}")
                
                return estaciones
            else:
                print("No se encontraron estaciones")
                return None
                
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def descargar_datos_estacion(self, station_id, fecha_inicio, fecha_fin,
                                 dataset='GHCND', datatypes=None):
        """
        Descarga datos de una estación específica
        
        Datatypes comunes:
        - PRCP: Precipitación
        - TMAX: Temperatura máxima
        - TMIN: Temperatura mínima
        - TAVG: Temperatura promedio
        - AWND: Velocidad promedio del viento
        """
        
        if not self.api_token:
            print("Error: Se requiere API token")
            return None
        
        if datatypes is None:
            datatypes = ['PRCP', 'TMAX', 'TMIN', 'TAVG']
        
        headers = {'token': self.api_token}
        
        url = f"{self.base_url_cdo}/data"
        params = {
            'datasetid': dataset,
            'stationid': station_id,
            'startdate': fecha_inicio,
            'enddate': fecha_fin,
            'datatypeid': datatypes,
            'limit': 1000,  # Máximo por solicitud
            'units': 'metric'
        }
        
        print(f"Descargando datos de {station_id}")
        print(f"Período: {fecha_inicio} a {fecha_fin}")
        
        try:
            all_data = []
            offset = 1
            
            while True:
                params['offset'] = offset
                response = requests.get(url, headers=headers, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                if 'results' in data:
                    all_data.extend(data['results'])
                    print(f"  Descargados {len(all_data)} registros...")
                    
                    # Si hay más datos, continuar
                    if len(data['results']) == 1000:
                        offset += 1000
                    else:
                        break
                else:
                    break
            
            if all_data:
                df = pd.DataFrame(all_data)
                df['date'] = pd.to_datetime(df['date'])
                print(f"✓ Total descargado: {len(df)} registros")
                return df
            else:
                print("No se encontraron datos")
                return None
                
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def descargar_noaa_psl_grillado(self, variable='air', año_inicio=2020, año_fin=2023):
        """
        Información para acceder a datos grillados de NOAA PSL
        
        Variables disponibles:
        - air: Temperatura del aire
        - precip: Precipitación (CMAP, GPCP)
        - slp: Presión a nivel del mar
        - uwnd, vwnd: Componentes del viento
        """
        
        print("="*60)
        print("DATOS GRILLADOS DE NOAA PSL")
        print("="*60)
        
        datasets_info = {
            'NCEP/NCAR Reanalysis': {
                'url': 'https://psl.noaa.gov/data/gridded/data.ncep.reanalysis.html',
                'resolucion': '2.5° x 2.5°',
                'periodo': '1948-presente',
                'variables': 'Temperatura, presión, viento, humedad'
            },
            'CPC Global Unified Precipitation': {
                'url': 'https://psl.noaa.gov/data/gridded/data.cpc.globalprecip.html',
                'resolucion': '0.5° x 0.5°',
                'periodo': '1979-presente',
                'variables': 'Precipitación'
            },
            'GPCP Precipitation': {
                'url': 'https://psl.noaa.gov/data/gridded/data.gpcp.html',
                'resolucion': '2.5° x 2.5°',
                'periodo': '1979-presente',
                'variables': 'Precipitación combinada sat/estaciones'
            }
        }
        
        for nombre, info in datasets_info.items():
            print(f"\n{nombre}:")
            for key, value in info.items():
                print(f"  {key}: {value}")
        
        print("\n" + "="*60)
        print("ACCESO A DATOS:")
        print("="*60)
        print("""
        Opciones para descargar:
        
        1. Descargar directamente desde el navegador:
           https://psl.noaa.gov/data/gridded/
        
        2. Usar OPeNDAP/THREDDS para acceso programático
        
        3. Usar xarray para leer datos remotamente:
           
           import xarray as xr
           
           # Ejemplo: NCEP Reanalysis temperatura
           url = 'https://psl.noaa.gov/thredds/dodsC/Datasets/ncep.reanalysis/surface/air.sig995.2023.nc'
           ds = xr.open_dataset(url)
           
           # Seleccionar región pampeana
           ds_pampeana = ds.sel(lat=slice(-30, -37), lon=slice(-65+360, -58+360))
        
        Ver script separado para ejemplos completos con xarray.
        """)


class GPCCDownloader:
    """
    Descarga datos de precipitación de GPCC
    Global Precipitation Climatology Centre
    
    Resoluciones disponibles:
    - 0.25° (~27 km)
    - 0.5° (~55 km)
    - 1.0° (~111 km)
    - 2.5° (~275 km)
    """
    
    def __init__(self):
        self.base_url = "https://opendata.dwd.de/climate_environment/GPCC/full_data_monthly_v2022"
        
    def generar_url_datos(self, resolucion='025', version='2022'):
        """
        Genera URLs para descargar datos GPCC
        
        Parámetros:
            resolucion: '025', '05', '10', '25' (grados)
            version: año de la versión del dataset
        """
        
        urls = {
            '025': f"{self.base_url}/025/full_data_monthly_v{version}_025.nc.gz",
            '05': f"https://opendata.dwd.de/climate_environment/GPCC/full_data_monthly_v{version}/05/full_data_monthly_v{version}_05.nc.gz",
            '10': f"https://opendata.dwd.de/climate_environment/GPCC/full_data_monthly_v{version}/10/full_data_monthly_v{version}_10.nc.gz",
            '25': f"https://opendata.dwd.de/climate_environment/GPCC/full_data_monthly_v{version}/25/full_data_monthly_v{version}_25.nc.gz",
        }
        
        return urls.get(resolucion)
    
    def descargar_gpcc(self, resolucion='05', directorio='gpcc_data'):
        """
        Descarga datos GPCC completos (ADVERTENCIA: archivos muy grandes)
        """
        
        os.makedirs(directorio, exist_ok=True)
        
        url = self.generar_url_datos(resolucion)
        
        if not url:
            print(f"Resolución {resolucion} no válida")
            return None
        
        nombre_archivo = os.path.join(directorio, url.split('/')[-1])
        
        print(f"Descargando GPCC resolución {resolucion}°")
        print(f"URL: {url}")
        print("ADVERTENCIA: Este archivo puede ser de varios GB")
        print("La descarga puede tardar mucho tiempo...")
        
        try:
            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()
            
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
                            size_mb = downloaded / (1024 * 1024)
                            print(f"\rDescargado: {size_mb:.1f} MB ({progress:.1f}%)", end='')
            
            print(f"\n✓ Descargado: {nombre_archivo}")
            
            # Descomprimir
            if nombre_archivo.endswith('.gz'):
                return self.descomprimir_gz(nombre_archivo)
            
            return nombre_archivo
            
        except Exception as e:
            print(f"\nError: {e}")
            return None
    
    def descomprimir_gz(self, archivo_gz):
        """Descomprime archivo .gz"""
        import gzip
        import shutil
        
        archivo_out = archivo_gz.replace('.gz', '')
        
        print(f"Descomprimiendo {archivo_gz}...")
        
        try:
            with gzip.open(archivo_gz, 'rb') as f_in:
                with open(archivo_out, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            print(f"✓ Descomprimido: {archivo_out}")
            os.remove(archivo_gz)
            
            return archivo_out
            
        except Exception as e:
            print(f"Error al descomprimir: {e}")
            return None
    
    def procesar_netcdf_region(self, archivo_nc, lat_min=-37, lat_max=-30,
                               lon_min=-65, lon_max=-58):
        """
        Procesa NetCDF de GPCC y extrae región pampeana
        """
        
        try:
            import xarray as xr  # type: ignore[import-not-found]
            
            print(f"Procesando {archivo_nc}...")
            
            ds = xr.open_dataset(archivo_nc)
            
            # Seleccionar región
            ds_region = ds.sel(lat=slice(lat_min, lat_max), 
                              lon=slice(lon_min, lon_max))
            
            print(f"\nDatos de región pampeana extraídos:")
            print(f"  Dimensiones: {dict(ds_region.dims)}")
            print(f"  Variables: {list(ds_region.data_vars)}")
            print(f"  Período: {ds_region.time.values[0]} a {ds_region.time.values[-1]}")
            
            return ds_region
            
        except ImportError:
            print("Error: Necesitas instalar xarray y netCDF4")
            print("Ejecuta: pip install xarray netCDF4")
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None


def guardar_muestra_datos_publicos_csv(ruta_csv=DATA_DIR / "muestra_noaa_psl_pampeana_2023.csv"):
    """Descarga una muestra pública de NOAA PSL y la guarda como CSV."""

    try:
        import xarray as xr
    except ImportError:
        print("Error: Necesitas instalar xarray para guardar la muestra de datos")
        print("Ejecuta: pip install xarray netCDF4")
        return None

    url = "https://psl.noaa.gov/thredds/dodsC/Datasets/ncep.reanalysis/surface/air.sig995.2023.nc"

    print("Descargando muestra pública de NOAA PSL...")
    ds = xr.open_dataset(url)

    ds_pampeana = ds.sel(lat=slice(-30, -37), lon=slice(295, 302))

    if "air" not in ds_pampeana:
        print("Error: No se encontró la variable 'air' en el dataset")
        return None

    serie = ds_pampeana["air"].mean(dim=["lat", "lon"]).to_dataframe().reset_index()
    serie.to_csv(ruta_csv, index=False, encoding="utf-8-sig")

    print(f"CSV de muestra guardado: {ruta_csv}")
    return ruta_csv


def generar_datos_ejemplo_pampeana(ruta_csv=DATA_DIR / "precipitacion_pampeana_ejemplo.csv"):
    """Genera datos de ejemplo realistas de precipitación para la región pampeana."""
    
    np.random.seed(42)
    
    # Grilla de puntos en la región pampeana
    lats = np.linspace(-37, -30, 8)
    lons = np.linspace(-65, -58, 8)
    
    # Fechas mensuales
    fechas = pd.date_range(start='2020-01-01', end='2023-12-31', freq='ME')
    
    filas = []
    for lat in lats:
        for lon in lons:
            # Precipitación con variabilidad realista (media ~100mm, rango 0-300mm)
            for fecha in fechas:
                # Patrón estacional + variabilidad
                mes = fecha.month
                prec_base = 100 * (1 + 0.3 * np.sin(2 * np.pi * mes / 12))
                prec = max(0, prec_base + np.random.normal(0, 50))
                
                filas.append({
                    'fecha': fecha.strftime('%Y-%m-%d'),
                    'latitud': round(lat, 2),
                    'longitud': round(lon, 2),
                    'precipitacion_mm': round(prec, 1),
                    'fuente': 'NOAA PSL (ejemplo)'
                })
    
    df = pd.DataFrame(filas)
    df.to_csv(ruta_csv, index=False, encoding="utf-8-sig")
    return ruta_csv


def guardar_resumen_csv(ruta_csv=DATA_DIR / "resumen_noaa_gpcc_recursos.csv"):
    """Guarda un resumen tabular de recursos públicos NOAA y GPCC."""

    gpcc = GPCCDownloader()

    filas = [
        {
            "fuente": "NOAA PSL",
            "dataset": "NCEP/NCAR Reanalysis",
            "url": "https://psl.noaa.gov/data/gridded/data.ncep.reanalysis.html",
            "resolucion": "2.5° x 2.5°",
            "periodo": "1948-presente",
            "variables": "Temperatura, presión, viento, humedad",
        },
        {
            "fuente": "NOAA PSL",
            "dataset": "CPC Global Unified Precipitation",
            "url": "https://psl.noaa.gov/data/gridded/data.cpc.globalprecip.html",
            "resolucion": "0.5° x 0.5°",
            "periodo": "1979-presente",
            "variables": "Precipitación",
        },
        {
            "fuente": "NOAA PSL",
            "dataset": "GPCP Precipitation",
            "url": "https://psl.noaa.gov/data/gridded/data.gpcp.html",
            "resolucion": "2.5° x 2.5°",
            "periodo": "1979-presente",
            "variables": "Precipitación combinada sat/estaciones",
        },
    ]

    for resolucion in ["025", "05", "10", "25"]:
        filas.append(
            {
                "fuente": "GPCC",
                "dataset": f"full_data_monthly_v2022_{resolucion}",
                "url": gpcc.generar_url_datos(resolucion),
                "resolucion": resolucion,
                "periodo": "Mensual",
                "variables": "Precipitación",
            }
        )

    df = pd.DataFrame(filas)
    df.to_csv(ruta_csv, index=False, encoding="utf-8-sig")
    return ruta_csv


# EJEMPLOS DE USO
if __name__ == "__main__":
    
    print("="*60)
    print("SCRIPT DE DESCARGA NOAA Y GPCC - MODO SIN TOKEN")
    print("="*60)
    
    print("\nEste modo usa solo fuentes públicas y no requiere token de NOAA.")
    
    # NOAA PSL
    print("\n" + "="*60)
    print("EJEMPLO 1: NOAA PSL - Datos grillados")
    print("="*60)
    
    noaa_psl = NOAADownloader()
    noaa_psl.descargar_noaa_psl_grillado()

    print("\n" + "="*60)
    print("GENERANDO ARCHIVOS DE SALIDA...")
    print("="*60)
    
    archivo_datos = generar_datos_ejemplo_pampeana()
    print(f"\n[OK] Datos de ejemplo exportados: {archivo_datos}")
    
    archivo_csv = guardar_resumen_csv()
    print(f"[OK] Inventario de recursos guardado: {archivo_csv}")

    archivo_muestra = guardar_muestra_datos_publicos_csv()
    if archivo_muestra:
        print(f"CSV de datos guardado: {archivo_muestra}")
    
    
    # GPCC
    print("\n" + "="*60)
    print("EJEMPLO 2: GPCC - Precipitación global")
    print("="*60)
    
    gpcc = GPCCDownloader()
    
    print("URLs disponibles para GPCC:")
    for res in ['025', '05', '10', '25']:
        url = gpcc.generar_url_datos(res)
        print(f"  {res}°: {url}")
    
    # Descomenta para descargar (archivos grandes!)
    """
    archivo = gpcc.descargar_gpcc(resolucion='10', directorio='gpcc_data')
    
    if archivo:
        ds_region = gpcc.procesar_netcdf_region(archivo)
        
        if ds_region is not None:
            # Guardar región extraída
            ds_region.to_netcdf('gpcc_pampeana.nc')
            
            # Convertir a DataFrame
            df = ds_region['precip'].mean(dim=['lat', 'lon']).to_pandas()
            df.to_csv('gpcc_pampeana_serie.csv')
    """
    
    
    print("\n" + "="*60)
    print("OTROS RECURSOS DE DATOS:")
    print("="*60)
    print("""
    SERVICIOS METEOROLÓGICOS NACIONALES:
    
    1. SMN Argentina (Servicio Meteorológico Nacional):
       https://www.smn.gob.ar/
       - Datos de estaciones argentinas
       - Históricos y tiempo real
       
    2. INTA (Instituto Nacional de Tecnología Agropecuaria):
       https://siga.inta.gob.ar/
       - Red de estaciones agrometeorológicas
       - Datos específicos para agricultura
    
    3. INA (Instituto Nacional del Agua):
       https://www.ina.gob.ar/
       - Datos hidrológicos
       - Niveles freáticos y caudales
    
    OTROS DATASETS GLOBALES:
    
    4. MERRA-2 (NASA):
       https://gmao.gsfc.nasa.gov/reanalysis/MERRA-2/
       - Reanálisis global de alta calidad
       - Requiere registro en Earthdata
    
    5. TerraClimate:
       https://www.climatologylab.org/terraclimate.html
       - Datos climáticos mensuales 1958-presente
       - Resolución 4 km
       - Incluye variables hidrológicas
    
    6. WorldClim:
       https://www.worldclim.org/
       - Climatologías de alta resolución
       - Ideal para modelado de nicho
    """)
