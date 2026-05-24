$ErrorActionPreference = "Stop"

$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectDir

$scriptName = "ndvi_modis_localidades.py"
$scriptPath = Join-Path $projectDir $scriptName

if (-not (Test-Path $scriptPath)) {
    Write-Host "No se encontro el archivo $scriptName en $projectDir" -ForegroundColor Red
    exit 1
}

$pythonCandidates = @(
    (Join-Path $projectDir ".venv\Scripts\python.exe"),
    "C:\Users\tereb\AppData\Local\Python\bin\python.exe"
)

$pythonExe = $null

foreach ($candidate in $pythonCandidates) {
    if (Test-Path $candidate) {
        $pythonExe = $candidate
        break
    }
}

if (-not $pythonExe) {
    try {
        & py -3 --version *> $null
        $pythonExe = "py -3"
    }
    catch {
        Write-Host "No se encontro un interprete Python utilizable." -ForegroundColor Red
        Write-Host "Instala Python o ajusta la ruta en run_ndvi_modis.ps1" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "Ejecutando $scriptName ..." -ForegroundColor Cyan

if ($pythonExe -eq "py -3") {
    & py -3 $scriptPath
}
else {
    & $pythonExe $scriptPath
}

$exitCode = $LASTEXITCODE
if ($null -eq $exitCode) { $exitCode = 0 }

if ($exitCode -eq 0) {
    Write-Host "Finalizo correctamente." -ForegroundColor Green
}
else {
    Write-Host "Finalizo con error. Codigo: $exitCode" -ForegroundColor Red
}

exit $exitCode
