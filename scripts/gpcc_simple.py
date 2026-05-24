"""
Script simple: Descargar precipitación mensual GPCC (real)
Extrae valores para coordenadas específicas y exporta CSV.

Fuente:
- NOAA PSL (catálogo GPCC combinado)
- URL OPeNDAP:
  https://psl.noaa.gov/thredds/dodsC/Datasets/gpcc/combined/precip.comb.v2020to2019-v2020monitorafter.total.nc
"""

import pandas as pd
from pathlib import Path

try:
    import xarray as xr
except ImportError:
    print("Instalando xarray y netCDF4...")
    import subprocess
    subprocess.check_call(["pip", "install", "xarray", "netCDF4"])
    import xarray as xr


GPCC_URL = (
    "https://psl.noaa.gov/thredds/dodsC/Datasets/gpcc/combined/"
    "precip.comb.v2020to2019-v2020monitorafter.total.nc"
)

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "datos"
ARCHIVO_LOCALIDADES = DATA_DIR / "localidades.xlsx"
SALIDA_GPCC = DATA_DIR / "datos_gpcc_mensuales_todas_localidades.csv"


def _ajustar_longitud_para_dataset(lon_usuario, lon_dataset):
    """Ajusta longitud al sistema del dataset (0-360 o -180 a 180)."""
    if float(lon_dataset.max()) > 180 and lon_usuario < 0:
        return lon_usuario + 360
    return lon_usuario


def descargar_gpcc_mensual_multiple(coordenadas, fecha_inicio, fecha_fin, url=GPCC_URL):
    """
    Descarga precipitación mensual real GPCC para múltiples coordenadas.

    Parámetros:
        coordenadas: DataFrame con columnas 'lat', 'long' (y opcionalmente 'DPTO', 'LOC')
        fecha_inicio: String 'YYYYMMDD' (ej: '20130101')
        fecha_fin: String 'YYYYMMDD' (ej: '20241231')
        url: URL OPeNDAP del dataset mensual GPCC

    Retorna:
        DataFrame combinado con precipitación mensual en mm/mes
    """

    if not isinstance(coordenadas, pd.DataFrame):
        raise ValueError("coordenadas debe ser un DataFrame con columnas 'lat' y 'long'")

    columnas_requeridas = {"lat", "long"}
    if not columnas_requeridas.issubset(set(coordenadas.columns)):
        raise ValueError("El DataFrame debe incluir columnas: 'lat' y 'long'")

    print("Abriendo dataset mensual GPCC (combinado)...")
    ds = xr.open_dataset(url)

    if "precip" not in ds:
        raise ValueError("No se encontró la variable 'precip' en el dataset")

    fecha_ini = pd.to_datetime(fecha_inicio, format="%Y%m%d")
    fecha_fin = pd.to_datetime(fecha_fin, format="%Y%m%d")

    # Selección temporal primero para reducir el volumen remoto.
    ds = ds.sel(time=slice(fecha_ini, fecha_fin))

    columnas_extra = []
    if "DPTO" in coordenadas.columns:
        columnas_extra.append("DPTO")
    if "LOC" in coordenadas.columns:
        columnas_extra.append("LOC")

    coords_info = coordenadas[["lat", "long"] + columnas_extra].drop_duplicates(subset=["lat", "long"])

    total = len(coords_info)
    resultados = []

    for i, (_, row) in enumerate(coords_info.iterrows(), start=1):
        lat = float(row["lat"])
        lon = float(row["long"])

        print(f"Descargando punto {i}/{total}: lat={lat}, lon={lon}")

        lon_dataset = _ajustar_longitud_para_dataset(lon, ds["lon"])

        serie = ds["precip"].sel(lat=lat, lon=lon_dataset, method="nearest")
        df = serie.to_dataframe(name="Precipitacion_mm_mes").reset_index()

        df = df.rename(columns={"time": "Fecha"})
        df["Latitud_solicitada"] = lat
        df["Longitud_solicitada"] = lon

        # Coordenada real de celda usada en la extracción.
        lat_grid = float(serie["lat"].values)
        lon_grid = float(serie["lon"].values)
        if float(ds["lon"].max()) > 180 and lon_grid > 180:
            lon_grid = lon_grid - 360

        df["Latitud_grilla"] = lat_grid
        df["Longitud_grilla"] = lon_grid
        df["Fuente"] = "GPCC combinado (NOAA PSL)"

        for col in columnas_extra:
            df[col] = row[col]

        resultados.append(df)

    if not resultados:
        return pd.DataFrame()

    df_final = pd.concat(resultados, ignore_index=True)
    df_final = df_final[[
        "Fecha",
        "Precipitacion_mm_mes",
        "Latitud_solicitada",
        "Longitud_solicitada",
        "Latitud_grilla",
        "Longitud_grilla",
        "Fuente",
    ] + columnas_extra]

    df_final = df_final.sort_values(["Latitud_solicitada", "Longitud_solicitada", "Fecha"])
    return df_final


# ============================================================
# EJEMPLO DE USO
# ============================================================
if __name__ == "__main__":

    print("Leyendo localidades desde Hoja1...")
    localidades = pd.read_excel(ARCHIVO_LOCALIDADES, sheet_name="Hoja1")
    print(f"Total de localidades: {len(localidades)}")
    print(localidades.head())

    print("\nDescargando precipitación mensual GPCC 2013-2024...")
    print("Esto puede tardar varios minutos...\n")

    df = descargar_gpcc_mensual_multiple(
        coordenadas=localidades,
        fecha_inicio="20130101",
        fecha_fin="20241231",
    )

    print(f"\nDataFrame resultante: {df.shape}")
    print(df.head(20))

    salida = SALIDA_GPCC
    df.to_csv(salida, index=False)
    print(f"\nDatos guardados en: {salida}")
