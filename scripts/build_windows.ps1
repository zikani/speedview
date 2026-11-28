$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
Push-Location $RootDir

try {
    if ($env:OS -ne "Windows_NT") {
        throw "scripts/build_windows.ps1 must be run on Windows to build a native SpeedView.exe binary."
    }

    $PythonExe = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } else { "py" }

    Write-Host "==> Checking Python & installing dependencies..." -ForegroundColor Cyan
    & $PythonExe -m pip install --upgrade pip
    & $PythonExe -m pip install -r requirements.txt

    Write-Host "==> Running bytecode check and unit tests..." -ForegroundColor Cyan
    & $PythonExe -m compileall -q main.py speedview tests
    & $PythonExe -m unittest discover -s tests -v

    Write-Host "==> Building dist\SpeedView.exe with PyInstaller..." -ForegroundColor Cyan
    & $PythonExe -m PyInstaller --noconfirm --clean speedview.spec

    $ExePath = Join-Path $RootDir "dist\SpeedView.exe"
    if (-not (Test-Path $ExePath)) {
        throw "Expected executable not found at $ExePath"
    }

    $ZipPath = Join-Path $RootDir "dist\SpeedView-windows-x64.zip"
    Compress-Archive -Path $ExePath -DestinationPath $ZipPath -Force

    $ExeHash = (Get-FileHash -Algorithm SHA256 $ExePath).Hash.ToLower()
    $ZipHash = (Get-FileHash -Algorithm SHA256 $ZipPath).Hash.ToLower()
    $ShaPath = Join-Path $RootDir "dist\SpeedView-windows-x64.sha256"
    @(
        "$ExeHash  SpeedView.exe"
        "$ZipHash  SpeedView-windows-x64.zip"
    ) | Out-File -Encoding ascii $ShaPath

    Write-Host "`nBuild succeeded:" -ForegroundColor Green
    Write-Host "  Executable : $ExePath"
    Write-Host "  Archive    : $ZipPath"
    Write-Host "  Checksums  : $ShaPath"
}
finally {
    Pop-Location
}
