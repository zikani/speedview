; SpeedView Inno Setup 6 Installer Script
; Builds dist\SpeedView-Installer-x64.exe installing extracted onedir bundle to Program Files\SpeedView

#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif

[Setup]
AppId={{7E19C4A1-8E65-4D1B-A2E7-5F9E0A44B210}
AppName=SpeedView - Network Speed Meter
AppVersion={#AppVersion}
AppVerName=SpeedView v{#AppVersion}
AppPublisher=SpeedView
AppPublisherURL=https://github.com/zikani/speedview
AppSupportURL=https://github.com/zikani/speedview/releases
AppUpdatesURL=https://github.com/zikani/speedview/releases
DefaultDirName={autopf}\SpeedView
DefaultGroupName=SpeedView
AllowNoIcons=yes
LicenseFile=..\..\LICENSE
OutputDir=..\..\dist
OutputBaseFilename=SpeedView-Installer-x64
SetupIconFile=..\..\speedview\ui\resources\speedview.ico
UninstallDisplayIcon={app}\speedview.ico
UninstallDisplayName=SpeedView - Network Speed Meter
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
#if VER >= EncodeVer(6,3,0)
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
#else
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
#endif
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "autostart"; Description: "Start SpeedView automatically on Windows startup"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\..\dist\SpeedView\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\..\speedview\ui\resources\speedview.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\SpeedView"; Filename: "{app}\SpeedView.exe"; WorkingDir: "{app}"; IconFilename: "{app}\speedview.ico"
Name: "{group}\Uninstall SpeedView"; Filename: "{uninstallexe}"; IconFilename: "{app}\speedview.ico"
Name: "{autodesktop}\SpeedView"; Filename: "{app}\SpeedView.exe"; WorkingDir: "{app}"; IconFilename: "{app}\speedview.ico"; Tasks: desktopicon

[Registry]
Root: HKA; Subkey: "Software\SpeedView"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\SpeedView"; ValueType: string; ValueName: "Version"; ValueData: "{#AppVersion}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "SpeedView"; ValueData: """{app}\SpeedView.exe"""; Tasks: autostart; Flags: uninsdeletevalue

[Run]
Filename: "{app}\SpeedView.exe"; Description: "{cm:LaunchProgram,SpeedView}"; Flags: nowait postinstall skipifsilent
