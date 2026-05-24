"""
Script simple: Descargar indices climaticos mensuales/estacionales (CPC NOAA + MEI v2)
y filtrarlos al periodo de trabajo.

Fuentes:
- CPC indices: https://www.cpc.ncep.noaa.gov/data/indices/
- MEI v2 (PSL): https://psl.noaa.gov/data/timeseries/month/MEIV2/
"""

from __future__ import annotations

import argparse
import re
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

DEFAULT_REFERENCES = [
    "datos_chirps_mensuales_todas_localidades.csv",
    "datos_gpcc_mensuales_todas_localidades.csv",
    "datos_nasa_mensuales_todas_localidades.csv",
    "datos_noaa_psl_mensuales_todas_localidades.csv",
    "datos_ndvi_modis_mensual_todas_localidades.csv",
]

SEASON_TO_MONTH = {
    "DJF": 1,
    "JFM": 2,
    "FMA": 3,
    "MAM": 4,
    "AMJ": 5,
    "MJJ": 6,
    "JJA": 7,
    "JAS": 8,
    "ASO": 9,
    "SON": 10,
    "OND": 11,
    "NDJ": 12,
}

CPC_SOURCES = [
    {
        "source": "CPC",
        "url": "https://www.cpc.ncep.noaa.gov/data/indices/zwnd200",
        "parser": "year12",
        "series": [{"name": "zwnd200", "position": 0}],
    },
    {
        "source": "CPC",
        "url": "https://www.cpc.ncep.noaa.gov/data/indices/wpac850",
        "parser": "year12",
        "series": [{"name": "wpac850", "position": 0}],
    },
    {
        "source": "CPC",
        "url": "https://www.cpc.ncep.noaa.gov/data/indices/cpac850",
        "parser": "year12",
        "series": [{"name": "cpac850", "position": 0}],
    },
    {
        "source": "CPC",
        "url": "https://www.cpc.ncep.noaa.gov/data/indices/epac850",
        "parser": "year12",
        "series": [{"name": "epac850", "position": 0}],
    },
    {
        "source": "CPC",
        "url": "https://www.cpc.ncep.noaa.gov/data/indices/qbo.u30.index",
        "parser": "year12",
        "series": [{"name": "qbo_u30", "position": 0}],
    },
    {
        "source": "CPC",
        "url": "https://www.cpc.ncep.noaa.gov/data/indices/qbo.u50.index",
        "parser": "year12",
        "series": [{"name": "qbo_u50", "position": 0}],
    },
    {
        "source": "CPC",
        "url": "https://www.cpc.ncep.noaa.gov/data/indices/darwin",
        "parser": "year12",
        "series": [{"name": "darwin_slp", "position": 0}],
    },
    {
        "source": "CPC",
        "url": "https://www.cpc.ncep.noaa.gov/data/indices/tahiti",
        "parser": "year12",
        "series": [{"name": "tahiti_slp", "position": 0}],
    },
    {
        "source": "CPC",
        "url": "https://www.cpc.ncep.noaa.gov/data/indices/soi",
        "parser": "year12",
        "series": [{"name": "soi", "position": 0}],
    },
    {
        "source": "CPC",
        "url": "https://www.cpc.ncep.noaa.gov/data/indices/olr",
        "parser": "year12",
        "series": [{"name": "olr_equatorial", "position": 0}],
    },
    {
        "source": "CPC",
        "url": "https://www.cpc.ncep.noaa.gov/data/indices/z500t",
        "parser": "year12",
        "series": [{"name": "z500t", "position": 0}],
    },
    {
        "source": "CPC",
        "url": "https://www.cpc.ncep.noaa.gov/data/indices/ersst5.nino.mth.91-20.ascii",
        "parser": "year_month",
        "series": [
            {"name": "nino12_sst", "position": 0},
            {"name": "nino12_anom", "position": 1},
            {"name": "nino3_sst", "position": 2},
            {"name": "nino3_anom", "position": 3},
            {"name": "nino4_sst", "position": 4},
            {"name": "nino4_anom", "position": 5},
            {"name": "nino34_sst", "position": 6},
            {"name": "nino34_anom", "position": 7},
        ],
    },
    {
        "source": "CPC",
        "url": "https://www.cpc.ncep.noaa.gov/data/indices/rel_mthsst9120.txt",
        "parser": "year_month",
        "series": [
            {"name": "rnino12", "position": 0},
            {"name": "rnino3", "position": 1},
            {"name": "rnino4", "position": 2},
            {"name": "rnino34", "position": 3},
        ],
    },
    {
        "source": "CPC",
        "url": "https://www.cpc.ncep.noaa.gov/data/indices/sstoi.indices",
        "parser": "year_month",
        "series": [
            {"name": "oisst_nino12_sst", "position": 0},
            {"name": "oisst_nino12_anom", "position": 1},
            {"name": "oisst_nino3_sst", "position": 2},
            {"name": "oisst_nino3_anom", "position": 3},
            {"name": "oisst_nino4_sst", "position": 4},
            {"name": "oisst_nino4_anom", "position": 5},
            {"name": "oisst_nino34_sst", "position": 6},
            {"name": "oisst_nino34_anom", "position": 7},
        ],
    },
    {
        "source": "CPC",
        "url": "https://www.cpc.ncep.noaa.gov/data/indices/sstoi.atl.indices",
        "parser": "year_month",
        "series": [
            {"name": "atl_natl_sst", "position": 0},
            {"name": "atl_natl_anom", "position": 1},
            {"name": "atl_satl_sst", "position": 2},
            {"name": "atl_satl_anom", "position": 3},
            {"name": "atl_trop_sst", "position": 4},
            {"name": "atl_trop_anom", "position": 5},
        ],
    },
    {
        "source": "CPC",
        "url": "https://www.cpc.ncep.noaa.gov/data/indices/cpolr.mth.91-20.ascii",
        "parser": "year_month",
        "series": [{"name": "cpolr", "position": 0}],
    },
    {
        "source": "CPC",
        "url": "https://www.cpc.ncep.noaa.gov/data/indices/Rnino34.ascii.txt",
        "parser": "year_month",
        "series": [{"name": "rnino34_anom", "position": 0}],
    },
    {
        "source": "CPC",
        "url": "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt",
        "parser": "seasonal",
        "series": [
            {"name": "oni_total", "position": 0},
            {"name": "oni_anom", "position": 1},
        ],
    },
    {
        "source": "CPC",
        "url": "https://www.cpc.ncep.noaa.gov/data/indices/3mth.nino34.91-20.ascii.txt",
        "parser": "seasonal",
        "series": [{"name": "nino34_3m_anom", "position": 0}],
    },
    {
        "source": "CPC",
        "url": "https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt",
        "parser": "seasonal",
        "series": [{"name": "roni_anom", "position": 0}],
    },
]

MEI_SOURCE = {
    "source": "PSL",
    "url": "https://psl.noaa.gov/data/correlation/meiv2.csv",
    "parser": "mei_csv",
    "series": [{"name": "MEI_v2", "position": 0}],
}


def _to_num(x: str) -> float | None:
    try:
        v = float(x)
    except Exception:
        return None
    if v <= -900:
        return None
    return v


def _parse_year12(text: str, series_cfg: list[dict]) -> list[dict]:
    registros = []
    for line in text.splitlines():
        toks = line.strip().split()
        if len(toks) < 13 or not re.fullmatch(r"\d{4}", toks[0]):
            continue

        year = int(toks[0])
        vals = [_to_num(v) for v in toks[1:13]]

        for m in range(1, 13):
            fecha = pd.Timestamp(year=year, month=m, day=1)
            for s in series_cfg:
                pos = s["position"]
                if pos == 0:
                    valor = vals[m - 1]
                    registros.append({"Fecha": fecha, "indice": s["name"], "valor": valor})
    return registros


def _parse_year_month(text: str, series_cfg: list[dict]) -> list[dict]:
    registros = []
    for line in text.splitlines():
        toks = line.strip().split()
        if len(toks) < 3:
            continue
        if not re.fullmatch(r"\d{4}", toks[0]):
            continue
        if not re.fullmatch(r"\d{1,2}", toks[1]):
            continue

        year = int(toks[0])
        month = int(toks[1])
        if month < 1 or month > 12:
            continue

        values = toks[2:]
        for s in series_cfg:
            pos = s["position"]
            if pos < len(values):
                valor = _to_num(values[pos])
                fecha = pd.Timestamp(year=year, month=month, day=1)
                registros.append({"Fecha": fecha, "indice": s["name"], "valor": valor})
    return registros


def _parse_seasonal(text: str, series_cfg: list[dict]) -> list[dict]:
    registros = []
    for line in text.splitlines():
        toks = line.strip().split()
        if len(toks) < 3:
            continue
        season = toks[0].upper()
        if season not in SEASON_TO_MONTH:
            continue
        if not re.fullmatch(r"\d{4}", toks[1]):
            continue

        year = int(toks[1])
        month = SEASON_TO_MONTH[season]
        values = toks[2:]

        for s in series_cfg:
            pos = s["position"]
            if pos < len(values):
                valor = _to_num(values[pos])
                fecha = pd.Timestamp(year=year, month=month, day=1)
                registros.append({"Fecha": fecha, "indice": s["name"], "valor": valor})
    return registros


def _parse_mei_csv(text: str, series_cfg: list[dict]) -> list[dict]:
    del series_cfg
    df = pd.read_csv(StringIO(text), skipinitialspace=True)
    if df.shape[1] < 2:
        return []

    df = df.iloc[:, :2].copy()
    df.columns = ["Fecha", "valor"]
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    df.loc[df["valor"] <= -900, "valor"] = pd.NA
    df = df.dropna(subset=["Fecha"]).reset_index(drop=True)
    df["indice"] = "MEI_v2"

    return df[["Fecha", "indice", "valor"]].to_dict("records")


def descargar_indice(cfg: dict) -> pd.DataFrame:
    url = cfg["url"]
    parser = cfg["parser"]
    source = cfg["source"]

    response = requests.get(url, timeout=60)
    response.raise_for_status()
    text = response.text

    if parser == "year12":
        registros = _parse_year12(text, cfg["series"])
    elif parser == "year_month":
        registros = _parse_year_month(text, cfg["series"])
    elif parser == "seasonal":
        registros = _parse_seasonal(text, cfg["series"])
    elif parser == "mei_csv":
        registros = _parse_mei_csv(text, cfg["series"])
    else:
        raise ValueError(f"Parser no soportado: {parser}")

    if not registros:
        return pd.DataFrame(columns=["Fecha", "indice", "valor", "fuente", "url"])

    df = pd.DataFrame(registros)
    df["fuente"] = source
    df["url"] = url
    return df


def _leer_fechas_desde_csv(path_csv: Path) -> pd.Series:
    if not path_csv.exists():
        return pd.Series(dtype="datetime64[ns]")

    def _parse_fechas_robusto(s: pd.Series) -> pd.Series:
        formatos = ["%Y-%m-%d", "%d/%m/%Y", "%Y%m%d", "%Y%m"]
        candidatos = []

        for fmt in formatos:
            f = pd.to_datetime(s, format=fmt, errors="coerce")
            if f.notna().any():
                candidatos.append(f)

        candidatos.append(pd.to_datetime(s, errors="coerce", dayfirst=True))
        candidatos.append(pd.to_datetime(s, errors="coerce", dayfirst=False))

        mejor = max(candidatos, key=lambda x: int(x.notna().sum()))
        return mejor.dropna()

    for sep in [",", ";", "\t"]:
        try:
            df = pd.read_csv(path_csv, sep=sep, usecols=["Fecha"], low_memory=False)
            fechas = _parse_fechas_robusto(df["Fecha"])
            if not fechas.empty:
                return fechas
        except Exception:
            continue

    return pd.Series(dtype="datetime64[ns]")


def detectar_rango_fechas(archivos_referencia: list[Path]) -> tuple[pd.Timestamp, pd.Timestamp]:
    fechas_validas = []

    for archivo in archivos_referencia:
        fechas = _leer_fechas_desde_csv(archivo)
        if not fechas.empty:
            fechas_validas.append((archivo.name, fechas.min(), fechas.max(), len(fechas)))

    if not fechas_validas:
        raise ValueError(
            "No se pudo detectar un rango temporal. Usa --fecha-inicio y --fecha-fin."
        )

    fecha_min = min(item[1] for item in fechas_validas)
    fecha_max = max(item[2] for item in fechas_validas)

    print("Rango detectado desde archivos de referencia:")
    for nombre, fmin, fmax, n in fechas_validas:
        print(f"  - {nombre}: {fmin.date()} a {fmax.date()} ({n} filas con Fecha)")

    return fecha_min, fecha_max


def generar_indices_periodo(
    fecha_inicio: str | None = None,
    fecha_fin: str | None = None,
    salida_long: str = "datos_indices_climaticos_mensuales_long.csv",
    salida_wide: str = "datos_indices_climaticos_mensuales.csv",
    incluir_mei: bool = True,
    carpeta_base: Path | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    base = carpeta_base or Path.cwd()

    if fecha_inicio is None or fecha_fin is None:
        refs = [base / nombre for nombre in DEFAULT_REFERENCES]
        fmin, fmax = detectar_rango_fechas(refs)
        if fecha_inicio is None:
            fecha_inicio = fmin.strftime("%Y-%m-%d")
        if fecha_fin is None:
            fecha_fin = fmax.strftime("%Y-%m-%d")

    ini = pd.to_datetime(fecha_inicio)
    fin = pd.to_datetime(fecha_fin)

    if pd.isna(ini) or pd.isna(fin):
        raise ValueError("fecha_inicio o fecha_fin no tienen formato valido.")
    if ini > fin:
        raise ValueError("fecha_inicio no puede ser mayor que fecha_fin.")

    fuentes = CPC_SOURCES.copy()
    if incluir_mei:
        fuentes.append(MEI_SOURCE)

    frames = []
    for cfg in fuentes:
        nombre = cfg["url"].split("/")[-1]
        print(f"Descargando: {nombre}")
        try:
            df_i = descargar_indice(cfg)
            frames.append(df_i)
            print(f"  OK: {len(df_i)} filas")
        except Exception as e:
            print(f"  ERROR en {nombre}: {e}")

    if not frames:
        raise ValueError("No se pudieron descargar indices.")

    df_long = pd.concat(frames, ignore_index=True)
    df_long["Fecha"] = pd.to_datetime(df_long["Fecha"], errors="coerce")
    df_long["valor"] = pd.to_numeric(df_long["valor"], errors="coerce")
    df_long = df_long.dropna(subset=["Fecha"])

    df_long = df_long.loc[(df_long["Fecha"] >= ini) & (df_long["Fecha"] <= fin)].copy()
    df_long = df_long.sort_values(["Fecha", "indice"]).reset_index(drop=True)

    # Si un indice trae duplicados para la misma Fecha, promediamos.
    df_wide = (
        df_long.groupby(["Fecha", "indice"], as_index=False)["valor"]
        .mean()
        .pivot(index="Fecha", columns="indice", values="valor")
        .reset_index()
        .sort_values("Fecha")
    )

    out_long = base / salida_long
    out_wide = base / salida_wide
    df_long.to_csv(out_long, index=False)
    df_wide.to_csv(out_wide, index=False)

    print(f"\nPeriodo final: {ini.date()} a {fin.date()}")
    print(f"Filas long: {len(df_long)}")
    print(f"Filas wide: {len(df_wide)}")
    print(f"Long guardado en: {out_long}")
    print(f"Wide guardado en: {out_wide}")

    return df_long, df_wide


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Descarga indices climaticos de CPC (+ MEI v2 opcional), "
            "los filtra por fechas y exporta CSV long/wide."
        )
    )
    parser.add_argument("--fecha-inicio", type=str, default=None, help="Fecha inicio YYYY-MM-DD")
    parser.add_argument("--fecha-fin", type=str, default=None, help="Fecha fin YYYY-MM-DD")
    parser.add_argument(
        "--salida-long",
        type=str,
        default="datos_indices_climaticos_mensuales_long.csv",
        help="CSV de salida en formato largo",
    )
    parser.add_argument(
        "--salida-wide",
        type=str,
        default="datos_indices_climaticos_mensuales.csv",
        help="CSV de salida en formato ancho",
    )
    parser.add_argument(
        "--sin-mei",
        action="store_true",
        help="No incluir el indice MEI v2 de PSL",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    generar_indices_periodo(
        fecha_inicio=args.fecha_inicio,
        fecha_fin=args.fecha_fin,
        salida_long=args.salida_long,
        salida_wide=args.salida_wide,
        incluir_mei=not args.sin_mei,
    )
