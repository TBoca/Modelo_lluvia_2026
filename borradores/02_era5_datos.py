"""
Script para descargar datos climáticos de ERA5 (Copernicus Climate Data Store)
Para la región Agro-Pampeana de Argentina

ERA5: Reanálisis climático de ECMWF con resolución ~31 km
https://cds.climate.copernicus.eu/
"""

import cdsapi
import numpy as np
import xarray as xr
from datetime import datetime

class ERA5Downloader:
    """
    Descarga datos de ERA5 usando la API de Copernicus
    
    REQUISITOS:
    1. Registrarse en: https://cds.climate.copernicus.eu/user/register
    2. Instalar: pip install cdsapi
    3. Configurar credenciales en: ~/.cdsapirc o C:\\Users\\<username>\\.cdsapirc
       
       Formato del archivo .cdsapirc:
       url: https://cds.climate.copernicus.eu/api/v2
       key: <UID>:<API-key>
    
    Obtén tu API key en: https://cds.climate.copernicus.eu/user
    """
    
    def __init__(self):
        try:
            self.client = cdsapi.Client()
            print("✓ Cliente CDS API inicializado correctamente")
        except Exception as e:
            print(f"Error al inicializar CDS API: {e}")
            print("\nAsegúrate de:")
            print("1. Tener una cuenta en https://cds.climate.copernicus.eu/")
            print("2. Configurar el archivo .cdsapirc con tus credenciales")
            print("3. Haber instalado: pip install cdsapi")
            raise
    
    def descargar_era5_regional(self, año, meses, variables=None, 
                               lat_norte=-30, lat_sur=-37, 
                               lon_oeste=-65, lon_este=-58,
                               nombre_archivo=None):
        """
        Descarga datos ERA5 para la región pampeana
        
        Parámetros:
            año: año a descargar (ej: 2023)
            meses: lista de meses ['01', '02', ...] o '01' para un mes
            variables: lista de variables a descargar
            lat_norte, lat_sur, lon_oeste, lon_este: límites de la región
            nombre_archivo: nombre del archivo de salida (sin extensión)
        """
        
        if variables is None:
            variables = [
                '2m_temperature',           # Temperatura a 2m
                '2m_dewpoint_temperature',  # Punto de rocío
                'total_precipitation',      # Precipitación total
                '10m_u_component_of_wind',  # Viento componente U
                '10m_v_component_of_wind',  # Viento componente V
                'surface_pressure',         # Presión superficial
                'soil_temperature_level_1', # Temperatura del suelo nivel 1
                'volumetric_soil_water_layer_1', # Humedad del suelo
            ]
        
        if isinstance(meses, str):
            meses = [meses]
        
        if nombre_archivo is None:
            nombre_archivo = f'era5_pampeana_{año}_{"_".join(meses)}'
        
        # Todos los días del mes
        dias = [f'{i:02d}' for i in range(1, 32)]
        
        # Horas (cada 3 horas para reducir tamaño)
        horas = [f'{i:02d}:00' for i in range(0, 24, 3)]
        
        print(f"Descargando ERA5 para región pampeana:")
        print(f"  Año: {año}")
        print(f"  Meses: {', '.join(meses)}")
        print(f"  Variables: {len(variables)}")
        print(f"  Área: N:{lat_norte}° S:{lat_sur}° W:{lon_oeste}° E:{lon_este}°")
        print(f"\nEsto puede tardar varios minutos...")
        
        try:
            self.client.retrieve(
                'reanalysis-era5-single-levels',
                {
                    'product_type': 'reanalysis',
                    'variable': variables,
                    'year': str(año),
                    'month': meses,
                    'day': dias,
                    'time': horas,
                    'area': [lat_norte, lon_oeste, lat_sur, lon_este],  # Norte, Oeste, Sur, Este
                    'format': 'netcdf',
                },
                f'{nombre_archivo}.nc'
            )
            
            print(f"\n✓ Datos descargados exitosamente: {nombre_archivo}.nc")
            return f'{nombre_archivo}.nc'
            
        except Exception as e:
            print(f"\nError en la descarga: {e}")
            return None
    
    def procesar_netcdf(self, archivo_nc):
        """
        Procesa el archivo NetCDF descargado y muestra información
        """
        
        try:
            ds = xr.open_dataset(archivo_nc)
            
            print(f"\nInformación del archivo: {archivo_nc}")
            print("="*60)
            print(f"Dimensiones: {dict(ds.dims)}")
            print(f"\nVariables disponibles:")
            for var in ds.data_vars:
                print(f"  - {var}: {ds[var].attrs.get('long_name', 'N/A')}")
                print(f"    Unidades: {ds[var].attrs.get('units', 'N/A')}")
            
            print(f"\nRango temporal: {ds.time.values[0]} a {ds.time.values[-1]}")
            print(f"Rango latitud: {ds.latitude.values.min():.2f}° a {ds.latitude.values.max():.2f}°")
            print(f"Rango longitud: {ds.longitude.values.min():.2f}° a {ds.longitude.values.max():.2f}°")
            
            return ds
            
        except Exception as e:
            print(f"Error al procesar NetCDF: {e}")
            return None
    
    def extraer_serie_temporal_punto(self, archivo_nc, lat, lon, variables=None):
        """
        Extrae serie temporal para un punto específico del archivo NetCDF
        """
        
        import pandas as pd
        
        try:
            ds = xr.open_dataset(archivo_nc)
            
            # Seleccionar punto más cercano
            punto = ds.sel(latitude=lat, longitude=lon, method='nearest')
            
            # Convertir a DataFrame
            df = punto.to_dataframe()
            
            if variables:
                df = df[variables]
            
            print(f"\nSerie temporal extraída para lat={lat}, lon={lon}")
            print(f"Registros: {len(df)}")
            
            return df
            
        except Exception as e:
            print(f"Error al extraer serie temporal: {e}")
            return None
    
    def convertir_a_csv(self, archivo_nc, archivo_csv=None):
        """
        Convierte NetCDF a CSV (promedio espacial por tiempo)
        """
        
        import pandas as pd
        
        if archivo_csv is None:
            archivo_csv = archivo_nc.replace('.nc', '.csv')
        
        try:
            ds = xr.open_dataset(archivo_nc)
            
            # Calcular promedio espacial para cada tiempo
            df_list = []
            
            for var in ds.data_vars:
                serie = ds[var].mean(dim=['latitude', 'longitude']).to_pandas()
                df_list.append(serie.rename(var))
            
            df = pd.concat(df_list, axis=1)
            df.to_csv(archivo_csv)
            
            print(f"✓ Datos convertidos a CSV: {archivo_csv}")
            print(f"  Promedio espacial de toda la región por tiempo")
            
            return df
            
        except Exception as e:
            print(f"Error al convertir a CSV: {e}")
            return None


# EJEMPLOS DE USO
if __name__ == "__main__":
    
    print("="*60)
    print("SCRIPT DE DESCARGA ERA5 - REGIÓN PAMPEANA")
    print("="*60)
    
    # IMPORTANTE: Primero debes configurar tus credenciales
    print("\nPASOS PREVIOS REQUERIDOS:")
    print("1. Registrarse en: https://cds.climate.copernicus.eu/user/register")
    print("2. Aceptar los términos de uso del dataset ERA5")
    print("3. Obtener tu API key en: https://cds.climate.copernicus.eu/user")
    print("4. Crear archivo .cdsapirc con tus credenciales")
    print("5. Instalar: pip install cdsapi xarray netcdf4")
    
    print("\n" + "="*60)
    print("EJEMPLO: Descargar datos de enero 2023")
    print("="*60)
    
    # Descomenta para usar (después de configurar credenciales)
    """
    try:
        downloader = ERA5Downloader()
        
        # Descargar datos
        archivo = downloader.descargar_era5_regional(
            año=2023,
            meses=['01'],  # Enero
            variables=[
                '2m_temperature',
                'total_precipitation',
                '10m_u_component_of_wind',
                '10m_v_component_of_wind',
            ],
            nombre_archivo='era5_pampeana_2023_01'
        )
        
        if archivo:
            # Procesar archivo descargado
            ds = downloader.procesar_netcdf(archivo)
            
            # Extraer serie para un punto
            df_punto = downloader.extraer_serie_temporal_punto(
                archivo,
                lat=-33.89,  # Pergamino
                lon=-60.57,
                variables=['t2m', 'tp']
            )
            
            if df_punto is not None:
                print("\nPrimeras filas del punto:")
                print(df_punto.head())
                df_punto.to_csv('era5_punto_pergamino.csv')
            
            # Convertir a CSV (promedio regional)
            df_regional = downloader.convertir_a_csv(archivo)
            
    except Exception as e:
        print(f"\nError: {e}")
        print("\nVerifica que hayas configurado correctamente tus credenciales.")
    """
    
    print("\n" + "="*60)
    print("VARIABLES PRINCIPALES DISPONIBLES EN ERA5:")
    print("="*60)
    print("""
    TEMPERATURA:
    - 2m_temperature: Temperatura a 2m sobre superficie
    - 2m_dewpoint_temperature: Punto de rocío a 2m
    - skin_temperature: Temperatura de la piel de la superficie
    - soil_temperature_level_1/2/3/4: Temperatura del suelo (4 niveles)
    
    PRECIPITACIÓN:
    - total_precipitation: Precipitación total acumulada
    - convective_precipitation: Precipitación convectiva
    
    VIENTO:
    - 10m_u_component_of_wind: Componente U del viento a 10m
    - 10m_v_component_of_wind: Componente V del viento a 10m
    
    HUMEDAD:
    - volumetric_soil_water_layer_1/2/3/4: Humedad volumétrica del suelo
    - soil_type: Tipo de suelo
    
    RADIACIÓN:
    - surface_solar_radiation_downwards: Radiación solar descendente
    - surface_net_solar_radiation: Radiación solar neta
    - surface_thermal_radiation_downwards: Radiación térmica descendente
    
    PRESIÓN Y EVAPORACIÓN:
    - surface_pressure: Presión superficial
    - mean_sea_level_pressure: Presión a nivel del mar
    - evaporation: Evaporación
    - potential_evaporation: Evaporación potencial
    
    OTROS:
    - total_cloud_cover: Cobertura nubosa total
    - leaf_area_index_low_vegetation: Índice de área foliar
    - leaf_area_index_high_vegetation: Índice de área foliar (veg. alta)
    
    Lista completa: https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-single-levels
    """)
    
    print("\n" + "="*60)
    print("NOTAS IMPORTANTES:")
    print("="*60)
    print("""
    - Resolución espacial: ~31 km (0.25° x 0.25°)
    - Resolución temporal: Horaria (puedes descargar cada 1, 3, 6 o 12 horas)
    - Período disponible: 1940 - presente (actualizado con ~5 días de retraso)
    - Formato: NetCDF (se puede convertir a CSV)
    - Las descargas pueden tardar desde minutos hasta horas dependiendo del volumen
    - Los archivos NetCDF pueden ser grandes (varios GB para años completos)
    """)
