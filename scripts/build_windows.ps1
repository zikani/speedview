$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
Push-Location $RootDir

try {
    if ($env:OS -ne "Windows_NT") {
        throw "scripts/build_windows.ps1 must be run on Windows to build native SpeedView Windows binaries."
    }

    $PythonExe = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } else { "py" }

    Write-Host "==> Checking Python & installing dependencies..." -ForegroundColor Cyan
    & $PythonExe -m pip install --upgrade pip
    & $PythonExe -m pip install -r requirements.txt

    Write-Host "==> Running bytecode check and unit tests..." -ForegroundColor Cyan
    & $PythonExe -m compileall -q main.py installer.py speedview tests
    & $PythonExe -m unittest discover -s tests -v

    Write-Host "==> Building onedir dist\SpeedView\SpeedView.exe with PyInstaller..." -ForegroundColor Cyan
    & $PythonExe -m PyInstaller --noconfirm --clean speedview.spec

    $OnedirPath = Join-Path $RootDir "dist\SpeedView"
    $ExePath = Join-Path $OnedirPath "SpeedView.exe"
    if (-not (Test-Path $ExePath)) {
        throw "Expected executable not found at $ExePath"
    }

    Write-Host "==> Building GUI Installer / Uninstaller dist\SpeedView-Setup.exe..." -ForegroundColor Cyan
    & $PythonExe -m PyInstaller --noconfirm --clean speedview_installer.spec

    $SetupExePath = Join-Path $RootDir "dist\SpeedView-Setup.exe"
    $ZipPath = Join-Path $RootDir "dist\SpeedView-windows-x64.zip"
    Compress-Archive -Path "$OnedirPath\*" -DestinationPath $ZipPath -Force

    $InnoPath = Join-Path $RootDir "dist\SpeedView-Installer-x64.exe"
    $Iscc = Get-Command ISCC.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
    if (-not $Iscc) {
        $IsccCandidates = @(
            "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
            "C:\Program Files\Inno Setup 6\ISCC.exe",
            "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
        )
        $Iscc = $IsccCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    }

    if ($Iscc) {
        Write-Host "==> Building Inno Setup installer dist\SpeedView-Installer-x64.exe..." -ForegroundColor Cyan
        $AppVersion = (& $PythonExe -c "from speedview.config.config import APP_VERSION; print(APP_VERSION)").Trim()
        & $Iscc "/DAppVersion=$AppVersion" installer\windows\speedview.iss
        if ($LASTEXITCODE -ne 0) {
            throw "Inno Setup compiler failed with exit code $LASTEXITCODE"
        }
    } else {
        Write-Host "NOTE: Inno Setup 6 (ISCC.exe) not found; skipping SpeedView-Installer-x64.exe (GUI SpeedView-Setup.exe + .zip still built)." -ForegroundColor Yellow
    }

    $HashLines = @(
        "$((Get-FileHash -Algorithm SHA256 $ExePath).Hash.ToLower())  SpeedView.exe"
        "$((Get-FileHash -Algorithm SHA256 $ZipPath).Hash.ToLower())  SpeedView-windows-x64.zip"
    )
    if (Test-Path $SetupExePath) {
        $HashLines += "$((Get-FileHash -Algorithm SHA256 $SetupExePath).Hash.ToLower())  SpeedView-Setup.exe"
    }
    if (Test-Path $InnoPath) {
        $HashLines += "$((Get-FileHash -Algorithm SHA256 $InnoPath).Hash.ToLower())  SpeedView-Installer-x64.exe"
    }

    $ShaPath = Join-Path $RootDir "dist\SpeedView-windows-x64.sha256"
    $HashLines | Out-File -Encoding ascii $ShaPath

    Write-Host "`nBuild succeeded:" -ForegroundColor Green
    Write-Host "  Onedir App      : $OnedirPath"
    Write-Host "  GUI Setup       : $SetupExePath"
    Write-Host "  Archive         : $ZipPath"
    if (Test-Path $InnoPath) {
        Write-Host "  Inno Installer  : $InnoPath"
    }
    Write-Host "  Checksums       : $ShaPath"
}
finally {
    Pop-Location
}
