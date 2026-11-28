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

    $MsiPath = Join-Path $RootDir "dist\SpeedView-windows-x64.msi"
    if (Get-Command wix -ErrorAction SilentlyContinue) {
        Write-Host "==> Building WiX GUI MSI dist\SpeedView-windows-x64.msi..." -ForegroundColor Cyan
        $AppVersion = (& $PythonExe -c "from speedview.config.config import APP_VERSION; print(APP_VERSION)").Trim()
        $AppFilesWxs = Join-Path $RootDir "installer\windows\AppFiles.wxs"
        & $PythonExe installer\windows\generate_files_wxs.py --dist-dir $OnedirPath --output $AppFilesWxs
        wix extension add -g WixToolset.UI.wixext 2>$null | Out-Null
        wix build installer\windows\SpeedView.wxs $AppFilesWxs -ext WixToolset.UI.wixext -d "AppVersion=$AppVersion" -arch x64 -o $MsiPath
    } else {
        Write-Host "NOTE: WiX Toolset ('wix') not found on PATH; skipping .msi build (GUI .exe Setup + .zip still built)." -ForegroundColor Yellow
    }

    $HashLines = @(
        "$((Get-FileHash -Algorithm SHA256 $ExePath).Hash.ToLower())  SpeedView.exe"
        "$((Get-FileHash -Algorithm SHA256 $ZipPath).Hash.ToLower())  SpeedView-windows-x64.zip"
    )
    if (Test-Path $SetupExePath) {
        $HashLines += "$((Get-FileHash -Algorithm SHA256 $SetupExePath).Hash.ToLower())  SpeedView-Setup.exe"
    }
    if (Test-Path $MsiPath) {
        $HashLines += "$((Get-FileHash -Algorithm SHA256 $MsiPath).Hash.ToLower())  SpeedView-windows-x64.msi"
    }

    $ShaPath = Join-Path $RootDir "dist\SpeedView-windows-x64.sha256"
    $HashLines | Out-File -Encoding ascii $ShaPath

    Write-Host "`nBuild succeeded:" -ForegroundColor Green
    Write-Host "  Onedir App : $OnedirPath"
    Write-Host "  GUI Setup  : $SetupExePath"
    Write-Host "  Archive    : $ZipPath"
    if (Test-Path $MsiPath) {
        Write-Host "  MSI Package: $MsiPath"
    }
    Write-Host "  Checksums  : $ShaPath"
}
finally {
    Pop-Location
}
