"""
Script simple: Descargar datos CHIRPS de precipitación mensual
Extrae valores para coordenadas específicas desde 2014 hasta hoy
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime
import tempfile
import gzip
import os

try:
    import rasterio
except ImportError:
    print("Instalando rasterio...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'rasterio'])
    import rasterio


def descargar_chirps_mensual(lat, lon, fecha_inicio, fecha_fin):
    """
    Descarga datos MENSUALES de precipitación CHIRPS para un punto
    
    Parámetros:
        lat: Latitud (ej: -34.0)
        lon: Longitud (ej: -61.0)
        fecha_inicio: String 'YYYYMMDD' (ej: '20140101')
        fecha_fin: String 'YYYYMMDD' (ej: '20241231')
    
    Retorna:
        DataFrame con precipitación mensual (mm/mes), Latitud, Longitud
    """
    
    # Extraer años
    anio_inicio = int(fecha_inicio[:4])
    anio_fin = int(fecha_fin[:4])
    mes_inicio = int(fecha_inicio[4:6])
    mes_fin = int(fecha_fin[4:6])
    
    base_url = "https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_monthly/tifs"
    
    datos = []
    
    for anio in range(anio_inicio, anio_fin + 1):
        # Determinar rango de meses
        if anio == anio_inicio:
            inicio = mes_inicio
        else:
            inicio = 1
            
        if anio == anio_fin:
            fin = mes_fin
        else:
            fin = 12
        
        for mes in range(inicio, fin + 1):
            fecha = f"{anio}-{mes:02d}-01"
            url = f"{base_url}/chirps-v2.0.{anio}.{mes:02d}.tif.gz"
            
            try:
                # Descargar archivo
                response = requests.get(url, timeout=60)
                response.raise_for_status()
                
                # Guardar temporalmente y descomprimir
                with tempfile.NamedTemporaryFile(delete=False, suffix='.tif.gz') as tmp_gz:
                    tmp_gz.write(response.content)
                    tmp_gz_path = tmp_gz.name
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.tif') as tmp_tif:
                    tmp_tif_path = tmp_tif.name
                
                # Descomprimir
                with gzip.open(tmp_gz_path, 'rb') as f_in:
                    with open(tmp_tif_path, 'wb') as f_out:
                        f_out.write(f_in.read())
                
                # Leer el valor en la coordenada
                with rasterio.open(tmp_tif_path) as src:
                    # Obtener el valor en la coordenada
                    row, col = src.index(lon, lat)
                    valor = src.read(1)[row, col]
                    
                    # -9999 es NoData en CHIRPS
                    if valor == -9999:
                        valor = np.nan
                
                datos.append({
                    'Fecha': fecha,
                    'Precipitacion': valor,
                    'Latitud': lat,
                    'Longitud': lon
                })
                
                # Limpiar archivos temporales
                os.unlink(tmp_gz_path)
                os.unlink(tmp_tif_path)
                
            except Exception as e:
                print(f"Error en {anio}-{mes:02d}: {e}")
                datos.append({
                    'Fecha': fecha,
                    'Precipitacion': np.nan,
                    'Latitud': lat,
                    'Longitud': lon
                })
    
    # Crear DataFrame
    df = pd.DataFrame(datos)
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df = df.set_index('Fecha')
    
    return df


def descargar_chirps_multiple(coordenadas, fecha_inicio, fecha_fin):
    """
    Descarga datos MENSUALES CHIRPS para múltiples coordenadas
    
    Parámetros:
        coordenadas: DataFrame con columnas 'lat', 'long' (y opcionalmente 'DPTO', 'LOC')
        fecha_inicio: String 'YYYYMMDD' (ej: '20140101')
        fecha_fin: String 'YYYYMMDD' (ej: '20241231')
    
    Retorna:
        DataFrame con datos de todos los puntos combinados incluyendo DPTO y LOC
    """
    import time
    
    # Verificar que sea un DataFrame
    if not isinstance(coordenadas, pd.DataFrame):
        raise ValueError("coordenadas debe ser un DataFrame con columnas 'lat' y 'long'")
    
    # Obtener coordenadas únicas con sus metadatos
    coords_info = coordenadas[['lat', 'long']].drop_duplicates()
    
    # Agregar DPTO y LOC si existen
    columnas_extra = []
    if 'DPTO' in coordenadas.columns:
        columnas_extra.append('DPTO')
    if 'LOC' in coordenadas.columns:
        columnas_extra.append('LOC')
    
    if columnas_extra:
        coords_info = coordenadas[['lat', 'long'] + columnas_extra].drop_duplicates(subset=['lat', 'long'])
    
    todos_datos = []
    total = len(coords_info)
    
    for idx, row in coords_info.iterrows():
        lat = row['lat']
        lon = row['long']
        print(f"Descargando punto {idx+1}/{total}: lat={lat}, lon={lon}", end='')
        
        if columnas_extra:
            info = ' - ' + ', '.join([f"{col}={row[col]}" for col in columnas_extra])
            print(info)
        else:
            print()
        
        try:
            df = descargar_chirps_mensual(lat, lon, fecha_inicio, fecha_fin)
            
            # Agregar columnas extra al DataFrame
            for col in columnas_extra:
                df[col] = row[col]
            
            todos_datos.append(df)
            # Pausa breve para no saturar el servidor
            time.sleep(1)
        except Exception as e:
            print(f"  Error en punto ({lat}, {lon}): {e}")
            continue
    
    # Combinar todos los datos
    if todos_datos:
        df_combinado = pd.concat(todos_datos, ignore_index=False)
        df_combinado = df_combinado.reset_index()
        return df_combinado
    else:
        return pd.DataFrame()


# ============================================================
# EJEMPLO DE USO
# ============================================================
if __name__ == "__main__":
    
    # Leer archivo de localidades (Hoja1)
    print("Leyendo localidades desde Hoja1...")
    localidades = pd.read_excel('localidades.xlsx', sheet_name='Hoja1')
    print(f"Total de localidades: {len(localidades)}")
    print(localidades.head())
    
    # Descargar datos mensuales CHIRPS para todas las localidades (2014-2024)
    print("\nDescargando datos mensuales CHIRPS 2014-2024 para todas las localidades...")
    print("Esto puede tardar bastante tiempo (descarga archivos GeoTIFF)...\n")
    df = descargar_chirps_multiple(
        coordenadas=localidades,
        fecha_inicio='20140101',
        fecha_fin='20241231'
    )
    
    print(f"\nDataFrame resultante: {df.shape}")
    print(df.head(20))
    
    # Guardar
    df.to_csv('datos_chirps_mensuales_todas_localidades.csv', index=False)
    print("\nDatos guardados en: datos_chirps_mensuales_todas_localidades.csv")
