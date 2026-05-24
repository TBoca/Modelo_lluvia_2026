"""
Script: Descargar NDVI MODIS para localidades de localidades.xlsx
================================================================
Fuente: ORNL DAAC MODIS REST API (producto MOD13Q1)

Entradas:
  - localidades.xlsx (columnas requeridas: lat, long; opcionales: DPTO, LOC)

Salidas:
  - datos_ndvi_modis_16dias_todas_localidades.csv
  - datos_ndvi_modis_mensual_todas_localidades.csv

Notas técnicas:
  - MOD13Q1 es un producto de 16 días (250 m).
  - La API limita cada consulta de subset a un máximo de 10 fechas, por eso
    se descarga en lotes.
  - NDVI viene con escala 0.0001 (valor_real = valor_crudo * 0.0001).
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

import pandas as pd
import requests


# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
URL_BASE = "https://modis.ornl.gov/rst/api/v1"
PRODUCTO = "MOD13Q1"
BANDA_NDVI = "250m_16_days_NDVI"

ARCHIVO_LOCALIDADES = "localidades.xlsx"
SALIDA_16D = "datos_ndvi_modis_16dias_todas_localidades.csv"
SALIDA_MENSUAL = "datos_ndvi_modis_mensual_todas_localidades.csv"

FECHA_INICIO = "2014-01-01"
FECHA_FIN = datetime.now().strftime("%Y-%m-%d")

TIMEOUT = 120
PAUSA_ENTRE_PUNTOS_S = 0.4


def dividir_en_lotes(items: List[Dict], tam_lote: int) -> List[List[Dict]]:
    """Divide una lista en sublistas de tam_lote elementos."""
    return [items[i:i + tam_lote] for i in range(0, len(items), tam_lote)]


def obtener_fechas_disponibles(lat: float, lon: float) -> List[Dict]:
    """Obtiene fechas MODIS disponibles para una coordenada."""
    url = f"{URL_BASE}/{PRODUCTO}/dates"
    params = {"latitude": lat, "longitude": lon}
    resp = requests.get(url, params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    return data.get("dates", [])


def filtrar_fechas_rango(fechas: List[Dict], inicio: str, fin: str) -> List[Dict]:
    """Filtra fechas por rango [inicio, fin] en formato YYYY-MM-DD."""
    inicio_dt = pd.to_datetime(inicio)
    fin_dt = pd.to_datetime(fin)

    out = []
    for f in fechas:
        cal = pd.to_datetime(f["calendar_date"])
        if inicio_dt <= cal <= fin_dt:
            out.append(f)
    return out


def descargar_ndvi_lote(lat: float, lon: float, start_modis: str, end_modis: str) -> Dict:
    """Descarga NDVI para una coordenada en un lote de fechas MODIS."""
    url = f"{URL_BASE}/{PRODUCTO}/subset"
    params = {
        "latitude": lat,
        "longitude": lon,
        "band": BANDA_NDVI,
        "startDate": start_modis,
        "endDate": end_modis,
        "kmAboveBelow": 0,
        "kmLeftRight": 0,
    }
    resp = requests.get(url, params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def extraer_registros_subset(subset_json: Dict, metadatos: Dict) -> List[Dict]:
    """Transforma la respuesta de subset en filas tabulares."""
    escala = float(subset_json.get("scale", 1))
    filas = []

    for item in subset_json.get("subset", []):
        valor_crudo = item.get("data", [None])[0]
        if valor_crudo is None or valor_crudo == -3000:
            ndvi = pd.NA
        else:
            ndvi = valor_crudo * escala

        fila = {
            "Fecha": item.get("calendar_date"),
            "modis_date": item.get("modis_date"),
            "NDVI": ndvi,
            "NDVI_crudo": valor_crudo,
            "tile": item.get("tile"),
            "producto": PRODUCTO,
            "banda": BANDA_NDVI,
            "lat": metadatos["lat"],
            "long": metadatos["long"],
        }

        if "DPTO" in metadatos:
            fila["DPTO"] = metadatos["DPTO"]
        if "LOC" in metadatos:
            fila["LOC"] = metadatos["LOC"]

        filas.append(fila)

    return filas


def descargar_ndvi_para_coordenada(row: pd.Series) -> List[Dict]:
    """Descarga toda la serie NDVI para una coordenada en lotes de 10 fechas."""
    import time

    lat = float(row["lat"])
    lon = float(row["long"])

    meta = {"lat": lat, "long": lon}
    if "DPTO" in row.index:
        meta["DPTO"] = row["DPTO"]
    if "LOC" in row.index:
        meta["LOC"] = row["LOC"]

    fechas = obtener_fechas_disponibles(lat, lon)
    fechas = filtrar_fechas_rango(fechas, FECHA_INICIO, FECHA_FIN)

    if not fechas:
        return []

    lotes = dividir_en_lotes(fechas, 10)
    filas = []

    for lote in lotes:
        start_modis = lote[0]["modis_date"]
        end_modis = lote[-1]["modis_date"]
        subset_json = descargar_ndvi_lote(lat, lon, start_modis, end_modis)
        filas.extend(extraer_registros_subset(subset_json, meta))

    # Pausa corta para no saturar el servicio.
    time.sleep(PAUSA_ENTRE_PUNTOS_S)
    return filas


def construir_mensual(df_16d: pd.DataFrame) -> pd.DataFrame:
    """Agrega NDVI 16 días a frecuencia mensual por localidad."""
    if df_16d.empty:
        return pd.DataFrame()

    df = df_16d.copy()
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    df = df.dropna(subset=["Fecha"])
    df["anio"] = df["Fecha"].dt.year
    df["mes"] = df["Fecha"].dt.month

    group_cols = ["lat", "long", "anio", "mes"]
    if "DPTO" in df.columns:
        group_cols.append("DPTO")
    if "LOC" in df.columns:
        group_cols.append("LOC")

    mensual = (
        df.groupby(group_cols, dropna=False)["NDVI"]
        .mean()
        .reset_index()
        .rename(columns={"NDVI": "NDVI_mensual"})
    )

    mensual["Fecha"] = pd.to_datetime(
        mensual["anio"].astype(str) + "-" + mensual["mes"].astype(str).str.zfill(2) + "-01"
    )

    cols = ["Fecha", "anio", "mes", "lat", "long"]
    if "DPTO" in mensual.columns:
        cols.append("DPTO")
    if "LOC" in mensual.columns:
        cols.append("LOC")
    cols.append("NDVI_mensual")

    mensual = mensual[cols].sort_values(["lat", "long", "Fecha"]).reset_index(drop=True)
    return mensual


def main() -> None:
    print("=" * 62)
    print("DESCARGA NDVI MODIS (MOD13Q1) POR LOCALIDAD")
    print("=" * 62)

    print(f"\n[1] Leyendo {ARCHIVO_LOCALIDADES}...")
    localidades = pd.read_excel(ARCHIVO_LOCALIDADES)

    requeridas = {"lat", "long"}
    faltantes = requeridas - set(localidades.columns)
    if faltantes:
        raise ValueError(f"Faltan columnas requeridas en el Excel: {faltantes}")

    cols = ["lat", "long"]
    if "DPTO" in localidades.columns:
        cols.append("DPTO")
    if "LOC" in localidades.columns:
        cols.append("LOC")

    coords = localidades[cols].drop_duplicates(subset=["lat", "long"]).reset_index(drop=True)
    print(f"    Localidades: {len(localidades)}")
    print(f"    Coordenadas únicas: {len(coords)}")
    print(f"    Periodo: {FECHA_INICIO} a {FECHA_FIN}")

    print("\n[2] Descargando NDVI por coordenada...")
    todas_filas = []

    for i, row in coords.iterrows():
        etiqueta = f"Punto {i + 1}/{len(coords)}"
        if "LOC" in row.index:
            etiqueta += f" - {row['LOC']}"
        print(f"    {etiqueta} (lat={row['lat']}, long={row['long']})")

        try:
            filas = descargar_ndvi_para_coordenada(row)
            print(f"      -> {len(filas)} registros")
            todas_filas.extend(filas)
        except Exception as e:
            print(f"      -> Error: {e}")

    if not todas_filas:
        print("\nNo se pudieron descargar datos NDVI.")
        return

    print("\n[3] Armando DataFrame 16 días...")
    df_16d = pd.DataFrame(todas_filas)
    df_16d["Fecha"] = pd.to_datetime(df_16d["Fecha"], errors="coerce")
    df_16d = df_16d.sort_values(["lat", "long", "Fecha"]).reset_index(drop=True)

    print(f"    Filas 16 días: {len(df_16d):,}")
    print(f"    NDVI min/max: {df_16d['NDVI'].min()} / {df_16d['NDVI'].max()}")

    print(f"\n[4] Guardando {SALIDA_16D}...")
    df_16d.to_csv(SALIDA_16D, index=False, encoding="utf-8-sig")

    print("\n[5] Calculando serie mensual...")
    df_mensual = construir_mensual(df_16d)
    print(f"    Filas mensuales: {len(df_mensual):,}")

    print(f"\n[6] Guardando {SALIDA_MENSUAL}...")
    df_mensual.to_csv(SALIDA_MENSUAL, index=False, encoding="utf-8-sig")

    print("\n" + "=" * 62)
    print("RESUMEN")
    print("=" * 62)
    print(f"Archivo 16 días: {SALIDA_16D}")
    print(f"Archivo mensual: {SALIDA_MENSUAL}")
    print(f"Coordenadas procesadas: {len(coords)}")
    print("\nListo.")


if __name__ == "__main__":
    main()
