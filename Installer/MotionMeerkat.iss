; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!
                        
[Setup]           
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{5C784574-7162-4518-849C-B2C13F88B122}
AppName=MotionMeerkat
AppVersion=2.0.2        
AppPublisher=Ben Weinstein                                   
AppPublisherURL=benweinstein.weebly.com
AppSupportURL=benweinstein.weebly.com
AppUpdatesURL=benweinstein.weebly.com                  
DefaultDirName={pf}\MotionMeerkat
DefaultGroupName=MotionMeerkat
LicenseFile=C:\Users\Ben\Documents\OpenCV_HummingbirdsMotion\License.txt           
OutputBaseFilename=MotionMeerkatSetup
Compression=lzma
SolidCompression=yes
                                                   
[Languages]                                                                           
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
         
[Files]
Source: "C:\Users\Ben\Documents\OpenCV_HummingbirdsMotion\MotionMeerkat\dist\main\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "C:\FFmpeg\bin\ffmpeg.exe";DestDir: "{app}\FFmpeg"; Flags: ignoreversion

; NOTE: Don't use "Flags: ignoreversion" on any shared system files
                                                                
[Icons]
Name: "{group}\MotionMeerkat"; Filename: "{app}\main.exe"; IconFileName: "{app}\thumbnail.ico"
Name: "{commondesktop}\MotionMeerkat"; IconFileName: "{app}\thumbnail.ico"; Filename: "{app}\main.exe"; Tasks: desktopicon

[Registry]
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}\FFmpeg";

[Run]
Filename: "{app}\main.exe"; Description: "{cm:LaunchProgram,MotionMeerkat}"; Flags: nowait postinstall skipifsilent
Filename: "https://github.com/bw4sz/OpenCV_HummingbirdsMotion/wiki"; Flags: shellexec runasoriginaluser postinstall; Description: "Open the Wiki."
             
