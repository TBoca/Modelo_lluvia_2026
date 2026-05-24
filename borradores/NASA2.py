import requests
import pandas as pd
from datetime import datetime
import json

class NASAPowerDownloader:
    """Descarga datos climáticos de NASA POWER API"""

    def __init__(self):
        self.base_url = "https://power.larc.nasa.gov/api/temporal/daily/point"

    def descargar_datos_punto(self, lat, lon, fecha_inicio, fecha_fin, parametros=None):
        if parametros is None:
            # Parámetros climáticos comunes para agroclimatología
            parametros = ["PRECTOTCORR", "T2M", "T2M_MAX", "T2M_MIN", "RH2M"]

        # Formatear fechas a YYYYMMDD (aceptar string o datetime)
        if isinstance(fecha_inicio, datetime):
            fecha_inicio_str = fecha_inicio.strftime("%Y%m%d")
        else:
            fecha_inicio_str = str(fecha_inicio)
            
        if isinstance(fecha_fin, datetime):
            fecha_fin_str = fecha_fin.strftime("%Y%m%d")
        else:
            fecha_fin_str = str(fecha_fin)

        # Construir la URL y parámetros de la solicitud
        params = {
            "parameters": ",".join(parametros),
            "start": fecha_inicio_str,  # ✅ Corregido: 'start' en vez de 'startDate'
            "end": fecha_fin_str,        # ✅ Corregido: 'end' en vez de 'endDate'
            "community": "AG",           # Agroclimatology
            "latitude": lat,
            "longitude": lon,
            "format": "JSON"
        }

        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()  # Lanza una excepción para errores HTTP (4xx o 5xx)
            data = response.json()

            # Extraer los datos de 'properties.parameter'
            if 'properties' in data and 'parameter' in data['properties']:
                raw_data = data['properties']['parameter']

                # Convertir a DataFrame de pandas
                df = pd.DataFrame(raw_data)
                df.index = pd.to_datetime(df.index, format='%Y%m%d')
                df.index.name = 'Fecha'

                # Reemplazar valores -999 con NaN (valores nulos de NASA POWER)
                df = df.replace(-999.0, pd.NA)

                return df
            else:
                print("No se encontraron datos en la respuesta de la API.")
                return pd.DataFrame()

        except requests.exceptions.RequestException as e:
            print(f"Error en la solicitud HTTP: {e}")
            return pd.DataFrame()
        except json.JSONDecodeError as e:
            print(f"Error al decodificar JSON: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"Ocurrió un error inesperado: {e}")
            return pd.DataFrame()

# ============================================================
# EJEMPLO DE USO
# ============================================================
if __name__ == "__main__":
    
    print("="*70)
    print("EJEMPLO DE DESCARGA - NASA POWER")
    print("="*70)
    
    # Crear instancia del descargador
    downloader = NASAPowerDownloader()
    
    # Coordenadas de un punto en la regi�n pampeana
    latitud = -34.0
    longitud = -61.0
    
    # Per�odo de an�lisis (puedes usar strings o datetime)
    fecha_inicio = "20230101"  # 1 enero 2023
    fecha_fin = "20230131"     # 31 enero 2023
    
    print(f"\n?? Descargando datos para:")
    print(f"   Latitud: {latitud}�")
    print(f"   Longitud: {longitud}�")
    print(f"   Per�odo: {fecha_inicio} a {fecha_fin}")
    print()
    
    # Descargar datos
    df = downloader.descargar_datos_punto(
        lat=latitud,
        lon=longitud,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )
    
    # Mostrar resultados
    if not df.empty:
        print("? Datos descargados exitosamente!")
        print(f"\n?? Total de registros: {len(df)} d�as")
        print(f"\n?? Columnas disponibles: {list(df.columns)}")
        
        print("\n" + "="*70)
        print("PRIMEROS 10 D�AS:")
        print("="*70)
        print(df.head(10))
        
        print("\n" + "="*70)
        print("ESTAD�STICAS:")
        print("="*70)
        print(df.describe())
        
        # Guardar a CSV
        nombre_archivo = f"nasa_datos_{latitud}_{longitud}_{fecha_inicio}_{fecha_fin}.csv"
        df.to_csv(nombre_archivo)
        print(f"\n? Datos guardados en: {nombre_archivo}")
        
    else:
        print("? No se pudieron descargar datos")
