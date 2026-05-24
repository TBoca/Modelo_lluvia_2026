"""
Script: Descargar rendimientos de cultivos desde MAGYP
=======================================================
Cultivos: Trigo total, Maíz, Girasol, Sorgo
Variable: Rendimiento (Kg/Ha)
Fuente: https://datosestimaciones.magyp.gob.ar/reportes.php?reporte=Estimaciones

Estrategia:
  - Usa el botón "Descargar dataset" (descarga el CSV completo de Argentina)
  - Filtra por los 4 cultivos y por los departamentos de localidades.xlsx
  - El CSV completo incluye todas las campañas, provincias y cultivos

Datos de localidades leídos desde: localidades.xlsx
(columnas requeridas: DPTO, LOC, lat, long)

Salida:
  - rendimientos_magyp_por_dpto.csv  → rendimiento por departamento, cultivo y campaña
  - rendimientos_magyp_por_loc.csv   → idem expandido a nivel localidad
"""

import io
import unicodedata

import pandas as pd
import requests

# ─── Configuración ────────────────────────────────────────────────────────────
URL_FORM = "https://datosestimaciones.magyp.gob.ar/reportes.php?reporte=Estimaciones"

# Nombres exactos de los cultivos en el dataset MAGYP
# (verificados desde el CSV completo)
CULTIVOS = ["Trigo total", "Maíz", "Girasol", "Sorgo"]

# Alias legibles para los nombres de archivo / columnas adicionales
ALIAS_CULTIVOS = {
    "Trigo total": "Trigo",
    "Maíz":        "Maiz",
    "Girasol":     "Girasol",
    "Sorgo":       "Sorgo",
}

ARCHIVO_LOCALIDADES = "localidades.xlsx"
SALIDA_DPTO         = "rendimientos_magyp_por_dpto.csv"
SALIDA_LOC          = "rendimientos_magyp_por_loc.csv"
# ──────────────────────────────────────────────────────────────────────────────


def normalizar_texto(s: str) -> str:
    """Convierte a mayúsculas y elimina tildes/diacríticos."""
    s = str(s).upper().strip()
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def descargar_dataset_completo() -> pd.DataFrame:
    """
    Descarga el dataset completo de estimaciones agrícolas de MAGYP.

    Usa el botón 'Descargar dataset' (sin filtros) que retorna un CSV con
    todas las campañas, cultivos, provincias y departamentos de Argentina.

    Columnas del CSV:
        ID Provincia | Provincia | ID Departamento | Departamento |
        Id Cultivo   | Cultivo   | ID Campaña      | Campana      |
        Sup. Sembrada (Ha) | Sup. Cosechada (Ha) |
        Producción (Tn)    | Rendimiento (Kg/Ha)

    Retorna DataFrame con esas columnas.
    """
    print("  Enviando solicitud de descarga...")
    resp = requests.post(URL_FORM, data={"Dataset": "Dataset"}, timeout=300)
    resp.raise_for_status()

    content_type = resp.headers.get("Content-Type", "")
    if "csv" not in content_type.lower():
        raise ValueError(
            f"Respuesta inesperada. Content-Type: {content_type}\n"
            f"Primeros 200 caracteres: {resp.text[:200]}"
        )

    print(f"  Descarga OK ({len(resp.content) / 1_048_576:.1f} MB). Parseando CSV...")

    # El CSV empieza con \n antes de las cabeceras; sep=; con quotechar="
    df = pd.read_csv(
        io.StringIO(resp.text.lstrip("\n")),
        sep=";",
        quotechar='"',
        encoding="utf-8",
        dtype=str,
    )
    df.columns = df.columns.str.strip().str.replace('"', "")
    return df


def main() -> None:
    print("=" * 60)
    print("DESCARGA DE RENDIMIENTOS AGRÍCOLAS – MAGYP")
    print("=" * 60)

    # ── 1. Cargar localidades ────────────────────────────────────────────────
    print(f"\n[1] Cargando '{ARCHIVO_LOCALIDADES}'...")
    localidades = pd.read_excel(ARCHIVO_LOCALIDADES)
    dptos_excel = localidades["DPTO"].unique().tolist()
    print(f"    {len(localidades)} localidades, {len(dptos_excel)} departamentos únicos:")
    for d in dptos_excel:
        print(f"      {d}")

    # ── 2. Descargar dataset completo ────────────────────────────────────────
    print("\n[2] Descargando dataset completo de MAGYP...")
    df = descargar_dataset_completo()
    print(f"    Columnas: {df.columns.tolist()}")
    print(f"    Total filas: {len(df):,}")
    print(f"    Cultivos disponibles: {sorted(df['Cultivo'].unique())}")

    # ── 3. Filtrar por cultivos de interés ───────────────────────────────────
    print(f"\n[3] Filtrando cultivos: {CULTIVOS}")

    # Buscar nombres exactos o con variaciones menores
    cultivos_disponibles_norm = {
        normalizar_texto(c): c for c in df["Cultivo"].unique()
    }
    cultivos_a_usar = {}
    for cultivo in CULTIVOS:
        norm = normalizar_texto(cultivo)
        if norm in cultivos_disponibles_norm:
            cultivos_a_usar[cultivo] = cultivos_disponibles_norm[norm]
        else:
            print(f"    AVISO: '{cultivo}' no encontrado en el dataset. "
                  f"Cultivos similares: {[c for c in df['Cultivo'].unique() if 'trig' in c.lower() or 'maiz' in c.lower() or 'maíz' in c.lower() or 'girasol' in c.lower() or 'sorgo' in c.lower()]}")

    if not cultivos_a_usar:
        print("No se encontraron cultivos. Verificar nombres.")
        return

    df_cult = df[df["Cultivo"].isin(cultivos_a_usar.values())].copy()
    print(f"    Filas después del filtro de cultivos: {len(df_cult):,}")

    # ── 4. Filtrar por departamentos de localidades ──────────────────────────
    print(f"\n[4] Filtrando por {len(dptos_excel)} departamentos de localidades...")

    # Normalizar columna Departamento del dataset
    df_cult["_dept_norm"] = df_cult["Departamento"].apply(normalizar_texto)

    # Normalizar dptos del Excel
    dptos_norm = {normalizar_texto(d): d for d in dptos_excel}

    # Filtrar filas que coincidan
    df_filt = df_cult[df_cult["_dept_norm"].isin(dptos_norm.keys())].copy()
    print(f"    Filas después del filtro de departamentos: {len(df_filt):,}")

    # Agregar columna con nombre original del DPTO del Excel
    df_filt["DPTO_LOC"] = df_filt["_dept_norm"].map(dptos_norm)
    df_filt = df_filt.drop(columns=["_dept_norm"])

    if len(df_filt) == 0:
        # Diagnóstico: comparar nombres
        depts_csv_norm = set(df_cult["Departamento"].apply(normalizar_texto).unique())
        print("\n    DIAGNÓSTICO: Ningún departamento coincidió.")
        print("    Departamentos en localidades (normalizados):", list(dptos_norm.keys()))
        print("    Algunos departamentos en CSV (normalizados):",
              sorted(depts_csv_norm)[:30])
        return

    # ── 5. Seleccionar columnas y convertir tipos ────────────────────────────
    print("\n[5] Procesando datos...")

    # Renombrar columnas para mayor claridad
    df_filt = df_filt.rename(columns={
        "ID Provincia":        "id_provincia",
        "Provincia":           "provincia",
        "ID Departamento":     "id_departamento",
        "Departamento":        "departamento",
        "Id Cultivo":          "id_cultivo",
        "Cultivo":             "cultivo",
        "ID Campaña":          "id_campana",
        "Campana":             "campana",
        "Sup. Sembrada (Ha)":  "sup_sembrada_ha",
        "Sup. Cosechada (Ha)": "sup_cosechada_ha",
        "Producción (Tn)":     "produccion_tn",
        "Rendimiento (Kg/Ha)": "rendimiento_kg_ha",
    })

    # Conversión numérica
    for col in ["sup_sembrada_ha", "sup_cosechada_ha", "produccion_tn", "rendimiento_kg_ha"]:
        if col in df_filt.columns:
            df_filt[col] = (
                df_filt[col]
                .str.replace(".", "", regex=False)  # separador de miles
                .str.replace(",", ".", regex=False)  # separador decimal
                .pipe(pd.to_numeric, errors="coerce")
            )

    # Ordenar
    df_filt = df_filt.sort_values(
        ["cultivo", "provincia", "departamento", "campana"]
    ).reset_index(drop=True)

    # ── 6. Guardar por departamento ──────────────────────────────────────────
    df_filt.to_csv(SALIDA_DPTO, index=False, encoding="utf-8-sig")
    print(f"\n[6] Guardado: '{SALIDA_DPTO}'  ({len(df_filt):,} filas)")

    # ── 7. Expandir a nivel localidad ────────────────────────────────────────
    # Cada localidad hereda los rendimientos de su departamento
    df_loc = localidades.merge(
        df_filt,
        left_on="DPTO",
        right_on="DPTO_LOC",
        how="left",
    )
    df_loc.to_csv(SALIDA_LOC, index=False, encoding="utf-8-sig")
    print(f"[7] Guardado: '{SALIDA_LOC}'  ({len(df_loc):,} filas)")

    # ── 8. Resumen ───────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    resumen = (
        df_filt.groupby(["cultivo", "provincia"])["rendimiento_kg_ha"]
        .agg(registros="count", rend_promedio="mean", rend_max="max")
        .round(0)
    )
    print(resumen.to_string())
    print("\nCampañas disponibles:", sorted(df_filt["campana"].unique()))
    print("\n¡Descarga completada!")


if __name__ == "__main__":
    main()

