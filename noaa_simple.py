"""
Script simple: Descargar precipitación mensual NOAA PSL (real)
Extrae valores para coordenadas específicas y exporta CSV.

Fuente:
- NOAA PSL / CMAP Enhanced Monthly Precipitation
- URL OPeNDAP: https://psl.noaa.gov/thredds/dodsC/Datasets/cmap/enh/precip.mon.mean.nc
"""

import pandas as pd

try:
    import xarray as xr
except ImportError:
    print("Instalando xarray y netCDF4...")
    import subprocess
    subprocess.check_call(["pip", "install", "xarray", "netCDF4"])
    import xarray as xr


NOAA_PSL_CMAP_URL = "https://psl.noaa.gov/thredds/dodsC/Datasets/cmap/enh/precip.mon.mean.nc"


def _ajustar_longitud_para_dataset(lon_usuario, lon_dataset):
    """Ajusta longitud al sistema del dataset (0-360 o -180 a 180)."""
    if float(lon_dataset.max()) > 180 and lon_usuario < 0:
        return lon_usuario + 360
    return lon_usuario


def descargar_noaa_psl_mensual_multiple(coordenadas, fecha_inicio, fecha_fin, url=NOAA_PSL_CMAP_URL):
    """
    Descarga precipitación mensual real NOAA PSL para múltiples coordenadas.

    Parámetros:
        coordenadas: DataFrame con columnas 'lat', 'long' (y opcionalmente 'DPTO', 'LOC')
        fecha_inicio: String 'YYYYMMDD' (ej: '20130101')
        fecha_fin: String 'YYYYMMDD' (ej: '20241231')
        url: URL OPeNDAP del dataset mensual

    Retorna:
        DataFrame combinado con precipitación mensual en mm/mes
    """

    if not isinstance(coordenadas, pd.DataFrame):
        raise ValueError("coordenadas debe ser un DataFrame con columnas 'lat' y 'long'")

    columnas_requeridas = {"lat", "long"}
    if not columnas_requeridas.issubset(set(coordenadas.columns)):
        raise ValueError("El DataFrame debe incluir columnas: 'lat' y 'long'")

    print("Abriendo dataset mensual NOAA PSL (CMAP)...")
    ds = xr.open_dataset(url)

    if "precip" not in ds:
        raise ValueError("No se encontró la variable 'precip' en el dataset")

    fecha_ini = pd.to_datetime(fecha_inicio, format="%Y%m%d")
    fecha_fin = pd.to_datetime(fecha_fin, format="%Y%m%d")

    # Selección temporal primero para reducir procesamiento.
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
        df = serie.to_dataframe(name="precip_mm_dia").reset_index()

        # CMAP mensual suele estar en mm/día promedio mensual.
        # Convertimos a acumulado mensual (mm/mes).
        df["Precipitacion_mm_mes"] = df["precip_mm_dia"] * df["time"].dt.days_in_month

        df = df.rename(columns={"time": "Fecha"})
        df["Latitud_solicitada"] = lat
        df["Longitud_solicitada"] = lon

        # Guardar la coordenada real de grilla usada (útil para validación espacial).
        lat_grid = float(serie["lat"].values)
        lon_grid = float(serie["lon"].values)
        if float(ds["lon"].max()) > 180 and lon_grid > 180:
            lon_grid = lon_grid - 360

        df["Latitud_grilla"] = lat_grid
        df["Longitud_grilla"] = lon_grid
        df["Fuente"] = "NOAA PSL - CMAP Enhanced"

        for col in columnas_extra:
            df[col] = row[col]

        resultados.append(df)

    if not resultados:
        return pd.DataFrame()

    df_final = pd.concat(resultados, ignore_index=True)
    df_final = df_final[[
        "Fecha",
        "Precipitacion_mm_mes",
        "precip_mm_dia",
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
    localidades = pd.read_excel("localidades.xlsx", sheet_name="Hoja1")
    print(f"Total de localidades: {len(localidades)}")
    print(localidades.head())

    print("\nDescargando precipitación mensual NOAA PSL 2013-2024...")
    print("Esto puede tardar varios minutos...\n")

    df = descargar_noaa_psl_mensual_multiple(
        coordenadas=localidades,
        fecha_inicio="20130101",
        fecha_fin="20241231",
    )

    print(f"\nDataFrame resultante: {df.shape}")
    print(df.head(20))

    salida = "datos_noaa_psl_mensuales_todas_localidades.csv"
    df.to_csv(salida, index=False)
    print(f"\nDatos guardados en: {salida}")
