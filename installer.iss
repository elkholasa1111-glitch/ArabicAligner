; Inno Setup script -> ArabicAligner_Setup.exe
; Requires: Inno Setup 6 (iscc). Run: iscc installer.iss
#define MyAppName "ArabicAligner"
#define MyAppVersion "1.2.0-beta.1"
#define MyAppPublisher "Elkholasa"
#define SrcDir "dist\ArabicAligner"
#define OutDir "release"

[Setup]
AppId={code:GetInstallationId}
UsePreviousLanguage=no
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
LicenseFile=LICENSE
DefaultDirName={localappdata}\Programs\ArabicAligner Preview
DefaultGroupName={#MyAppName}
OutputDir={#OutDir}
OutputBaseFilename=ArabicAligner_1.2.0-beta.1_Windows_x64_Setup
Compression=lzma2/max
SolidCompression=yes
ArchitecturesAllowed=x64os
ArchitecturesInstallIn64BitMode=x64os
MinVersion=10.0.17763
WizardStyle=modern
PrivilegesRequired=lowest
UninstallDisplayName={#MyAppName} {#MyAppVersion}
; ~2GB bundle support
DiskSpanning=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "arabic"; MessagesFile: "compiler:Languages\Arabic.isl"

[Files]
Source: "{#SrcDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[InstallDelete]
; Remove only the two retired model directories when upgrading an older edition.
Type: filesandordirs; Name: "{app}\_internal\offline_assets\models\models--Systran--faster-whisper-base"
Type: filesandordirs; Name: "{app}\_internal\offline_assets\models\models--Systran--faster-whisper-medium"
Type: filesandordirs; Name: "{app}\offline_assets\models\models--Systran--faster-whisper-base"
Type: filesandordirs; Name: "{app}\offline_assets\models\models--Systran--faster-whisper-medium"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\ArabicAligner.exe"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\ArabicAligner.exe"; Tasks: desktopicon

[Tasks]
Name: desktopicon; Description: "Create a &desktop icon"; Flags: unchecked

[Run]
Filename: "{app}\ArabicAligner.exe"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Code]
function GetInstallationId(Param: String): String;
begin
  { Isolate acceptance installs from the user's installed application. }
  if ExpandConstant('{param:VERIFICATION|0}') = '1' then
    Result := 'ArabicAligner-Offline-Acceptance-Test'
  else
    { Preview installs separately from existing 1.1.1. }
    Result := 'ArabicAligner-Public-Preview';
end;
