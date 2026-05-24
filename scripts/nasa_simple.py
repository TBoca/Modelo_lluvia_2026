"""
Script simple: Descargar datos NASA POWER mensuales
Solo descarga y crea DataFrame - Sin análisis
"""

import requests
import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "datos"
ARCHIVO_LOCALIDADES = DATA_DIR / "localidades.xlsx"
SALIDA_NASA = DATA_DIR / "datos_nasa_mensuales_todas_localidades.csv"


def descargar_nasa_power_mensual(lat, lon, fecha_inicio, fecha_fin):

    
    # URL de la API para datos MENSUALES
    url = "https://power.larc.nasa.gov/api/temporal/monthly/point"
    
    # Extraer año de las fechas
    anio_inicio = fecha_inicio[:4]
    anio_fin = fecha_fin[:4]
    
    # Parámetros de la solicitud
    params = {
        "parameters": "PRECTOTCORR,T2M,T2M_MAX,T2M_MIN,RH2M",
        "start": anio_inicio,
        "end": anio_fin,
        "community": "AG",
        "latitude": lat,
        "longitude": lon,
        "format": "JSON"
    }
    
    # Hacer la solicitud
    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()
    
    # Obtener datos
    data = response.json()
    
    # Crear DataFrame - la estructura es diferente para datos mensuales
    parametros = data['properties']['parameter']
    
    # Reorganizar datos: cada variable tiene sus propios valores por mes
    datos_reorganizados = {}
    for variable, valores in parametros.items():
        for fecha, valor in valores.items():
            # Filtrar mes 13 (es el promedio anual que NASA incluye)
            if fecha.endswith('13'):
                continue
            if fecha not in datos_reorganizados:
                datos_reorganizados[fecha] = {}
            datos_reorganizados[fecha][variable] = valor
    
    # Crear DataFrame
    df = pd.DataFrame.from_dict(datos_reorganizados, orient='index')
    df.index = pd.to_datetime(df.index, format='%Y%m')
    df.index.name = 'Fecha'
    df = df.sort_index()
    
    # Reemplazar -999 con NaN
    df = df.replace(-999.0, pd.NA)
    
    # Agregar coordenadas al DataFrame
    df['Latitud'] = lat
    df['Longitud'] = lon
    
    return df


def descargar_nasa_power_multiple(coordenadas, fecha_inicio, fecha_fin):
    """
    Descarga datos MENSUALES de NASA POWER para múltiples coordenadas
    
    Parámetros:
        coordenadas: DataFrame con columnas 'lat', 'long' (y opcionalmente 'DPTO', 'LOC')
        fecha_inicio: String 'YYYYMMDD' (ej: '20130101')
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
        # Obtener DPTO y LOC para cada coordenada única
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
            df = descargar_nasa_power_mensual(lat, lon, fecha_inicio, fecha_fin)
            
            # Agregar columnas extra al DataFrame
            for col in columnas_extra:
                df[col] = row[col]
            
            todos_datos.append(df)
            # Pausa breve para no saturar la API
            time.sleep(0.5)
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
    localidades = pd.read_excel(ARCHIVO_LOCALIDADES, sheet_name='Hoja1')
    print(f"Total de localidades: {len(localidades)}")
    print(localidades.head())
    
    # Descargar datos mensuales para todas las localidades (2013-2024)
    print("\nDescargando datos mensuales 2013-2024 para todas las localidades...")
    print("Esto puede tardar varios minutos...\n")
    df = descargar_nasa_power_multiple(
        coordenadas=localidades,
        fecha_inicio='20130101',
        fecha_fin='20241231'
    )
    
    print(f"\nDataFrame resultante: {df.shape}")
    print(df.head(20))
    
    # Guardar
    df.to_csv(SALIDA_NASA, index=False)
    print(f"\nDatos guardados en: {SALIDA_NASA}")
