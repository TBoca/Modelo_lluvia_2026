"""
consolidar_base_xlsx.py
Genera una base integrada (2014-2025) con todas las variables en una sola hoja Excel.
Fuentes: CHIRPS, GPCC, NOAA PSL, NASA POWER, NDVI MODIS, indices climaticos.
"""

import pandas as pd
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DATOS = RAIZ / "datos"
SALIDA = DATOS / "base_integrada_2014_2025.xlsx"

ANIO_INI = 2014
ANIO_FIN = 2025

# --------------------------------------------------------------------------- #
# Funciones auxiliares
# --------------------------------------------------------------------------- #

def leer_fecha(df, col="Fecha"):
    df[col] = pd.to_datetime(df[col], dayfirst=False, errors="coerce")
    return df

def filtrar_anios(df, col="Fecha"):
    return df[(df[col].dt.year >= ANIO_INI) & (df[col].dt.year <= ANIO_FIN)]

# --------------------------------------------------------------------------- #
# 1. CHIRPS  ->  precip_chirps
# --------------------------------------------------------------------------- #
chirps = pd.read_csv(DATOS / "datos_chirps_mensuales_todas_localidades.csv")
chirps = leer_fecha(chirps)
chirps = filtrar_anios(chirps)
chirps = chirps.rename(columns={"Precipitacion": "precip_chirps",
                                 "Latitud": "Latitud",
                                 "Longitud": "Longitud"})
chirps = chirps[["Fecha", "DPTO", "LOC", "Latitud", "Longitud", "precip_chirps"]]

# --------------------------------------------------------------------------- #
# 2. GPCC  ->  precip_gpcc
# --------------------------------------------------------------------------- #
gpcc = pd.read_csv(DATOS / "datos_gpcc_mensuales_todas_localidades.csv")
gpcc = leer_fecha(gpcc)
gpcc = filtrar_anios(gpcc)
gpcc = gpcc.rename(columns={"Precipitacion_mm_mes": "precip_gpcc",
                              "Latitud_solicitada": "Latitud",
                              "Longitud_solicitada": "Longitud"})
gpcc = gpcc[["Fecha", "DPTO", "LOC", "precip_gpcc"]]

# --------------------------------------------------------------------------- #
# 3. NOAA PSL  ->  precip_noaa
# --------------------------------------------------------------------------- #
noaa = pd.read_csv(DATOS / "datos_noaa_psl_mensuales_todas_localidades.csv")
noaa = leer_fecha(noaa)
noaa = filtrar_anios(noaa)
noaa = noaa.rename(columns={"Precipitacion_mm_mes": "precip_noaa",
                              "Latitud_solicitada": "Latitud",
                              "Longitud_solicitada": "Longitud"})
noaa = noaa[["Fecha", "DPTO", "LOC", "precip_noaa"]]

# --------------------------------------------------------------------------- #
# 4. NASA POWER  ->  precip_nasa, RH2M, T2M, T2M_MAX, T2M_MIN
# --------------------------------------------------------------------------- #
nasa = pd.read_csv(DATOS / "datos_nasa_mensuales_todas_localidades.csv", sep=";",
                   decimal=".", encoding="utf-8", on_bad_lines="skip")
nasa.columns = nasa.columns.str.strip()
nasa = leer_fecha(nasa)
nasa = filtrar_anios(nasa)
nasa = nasa.rename(columns={"PRECTOTCORR": "precip_nasa"})
cols_nasa = [c for c in ["Fecha", "DPTO", "LOC", "precip_nasa",
                          "RH2M", "T2M", "T2M_MAX", "T2M_MIN"] if c in nasa.columns]
nasa = nasa[cols_nasa]

# --------------------------------------------------------------------------- #
# 5. NDVI MODIS  ->  NDVI_mensual
# --------------------------------------------------------------------------- #
ndvi = pd.read_csv(DATOS / "datos_ndvi_modis_mensual_todas_localidades.csv")
ndvi = leer_fecha(ndvi)
ndvi = filtrar_anios(ndvi)
ndvi = ndvi[["Fecha", "DPTO", "LOC", "NDVI_mensual"]]

# --------------------------------------------------------------------------- #
# 6. Indices climaticos (formato largo -> ancho)
#    MEI_v2, PDO, AMO, etc.
# --------------------------------------------------------------------------- #
idx = pd.read_csv(DATOS / "datos_indices_climaticos_mensuales_long.csv")
idx = leer_fecha(idx)
idx = filtrar_anios(idx)
idx_wide = idx.pivot_table(index="Fecha", columns="indice", values="valor",
                            aggfunc="first").reset_index()
idx_wide.columns.name = None

# --------------------------------------------------------------------------- #
# 7. Merge progresivo por Fecha + DPTO + LOC
# --------------------------------------------------------------------------- #
base = chirps.copy()

for df_right, key in [
    (gpcc,  ["Fecha", "DPTO", "LOC"]),
    (noaa,  ["Fecha", "DPTO", "LOC"]),
    (nasa,  ["Fecha", "DPTO", "LOC"]),
    (ndvi,  ["Fecha", "DPTO", "LOC"]),
]:
    base = base.merge(df_right, on=key, how="left")

# Indices climaticos solo por Fecha (son globales)
base = base.merge(idx_wide, on="Fecha", how="left")

# --------------------------------------------------------------------------- #
# 8. Columnas de año y mes para facilidad de filtrado
# --------------------------------------------------------------------------- #
base.insert(1, "anio", base["Fecha"].dt.year)
base.insert(2, "mes",  base["Fecha"].dt.month)
base = base.sort_values(["Fecha", "DPTO", "LOC"]).reset_index(drop=True)

# --------------------------------------------------------------------------- #
# 9. Exportar a Excel
# --------------------------------------------------------------------------- #
with pd.ExcelWriter(SALIDA, engine="openpyxl", date_format="YYYY-MM-DD",
                    datetime_format="YYYY-MM-DD") as writer:
    base.to_excel(writer, sheet_name="base_integrada", index=False)

print(f"Archivo generado: {SALIDA}")
print(f"Filas: {len(base):,}  |  Columnas: {base.shape[1]}")
print(f"Columnas: {list(base.columns)}")
