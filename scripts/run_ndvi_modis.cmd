@echo off
setlocal
powershell -ExecutionPolicy Bypass -File "%~dp0run_ndvi_modis.ps1"
set EXIT_CODE=%ERRORLEVEL%
if %EXIT_CODE% neq 0 (
  echo.
  echo El script termino con error. Codigo: %EXIT_CODE%
)
exit /b %EXIT_CODE%
