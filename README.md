# Modelo lluvia 2026

Repositorio de trabajo para construir una base integrada de variables climaticas, satelitales y productivas orientada a analisis y modelado de precipitacion/rendimiento.

## Estructura del repositorio

- `scripts/`: scripts de descarga, procesamiento y utilidades.
- `datos/`: insumos y salidas tabulares del pipeline.
- `informes/`: documentos Quarto/R Markdown y bitacora del proceso.

## Datos incorporados

- CHIRPS mensual.
- NOAA PSL / CMAP mensual.
- GPCC mensual.
- NASA POWER mensual.
- NDVI MODIS mensual por localidad.
- Rendimientos MAGYP por localidad.
- Indices climaticos globales CPC + MEI v2.

## Scripts principales

- `scripts/chirps_simple.py`: descarga CHIRPS mensual.
- `scripts/noaa_simple.py`: descarga NOAA PSL / CMAP mensual.
- `scripts/gpcc_simple.py`: descarga GPCC mensual.
- `scripts/nasa_simple.py`: descarga NASA POWER mensual.
- `scripts/ndvi_modis_localidades.py`: descarga NDVI MODIS y genera salida mensual.
- `scripts/rendimientos_magyp.py`: descarga y filtra rendimientos MAGYP.
- `scripts/mei_simple.py`: descarga indices CPC + MEI.
- `informes/precipitacion_global.qmd`: integra todas las fuentes en una sola base.
- `informes/bitacora_replicacion.qmd`: bitacora metodologica y registro de fuentes.

## Como correr el pipeline

### 1. Preparar insumos

Ubicar en `datos/` el archivo `localidades.xlsx` con columnas al menos:

- `lat`
- `long`

Opcionalmente:

- `DPTO`
- `LOC`

### 2. Generar datasets por fuente

Ejecutar, segun necesidad:

```powershell
py scripts/chirps_simple.py
py scripts/noaa_simple.py
py scripts/gpcc_simple.py
py scripts/nasa_simple.py
py scripts/ndvi_modis_localidades.py
py scripts/rendimientos_magyp.py
py scripts/mei_simple.py
```

Cada script guarda sus salidas en `datos/`.

### 3. Integrar la base final

Renderizar:

- `informes/precipitacion_global.qmd`

Ese documento unifica:

- precipitacion de 4 fuentes,
- variables NASA,
- NDVI mensual,
- indices climaticos globales,
- rendimientos por cultivo y agregados anuales.

### 4. Documentacion y seguimiento

La bitacora del proceso se mantiene en:

- `informes/bitacora_replicacion.qmd`

## Archivos importantes

- `datos/datos_indices_climaticos_mensuales.csv`: indices climaticos en formato ancho.
- `datos/rendimientos_magyp_por_loc.csv`: rendimientos por localidad.
- `datos/datos_ndvi_modis_mensual_todas_localidades.csv`: NDVI mensual.
- `informes/tablero_precipitacion_flexdashboard.Rmd`: tablero interactivo.

## Notas

- El archivo `datos/datos_ndvi_modis_16dias_todas_localidades.csv` no se versiona.
- Los HTML renderizados y carpetas auxiliares de Quarto tampoco se versionan.
- Las fuentes web y el detalle metodologico estan documentados en `informes/bitacora_replicacion.qmd`.