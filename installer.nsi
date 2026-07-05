; NSIS Installer for Question Paper Generator
; This creates a professional Windows installer

!include "MUI2.nsh"
!include "x64.nsh"

; Basic Settings
Name "Question Paper Generator"
OutFile "QuestionPaperGenerator-Installer.exe"
InstallDir "$PROGRAMFILES\QuestionPaperGenerator"
InstallDirRegKey HKCU "Software\QuestionPaperGenerator" ""

; Request admin privileges
RequestExecutionLevel admin

; MUI Settings
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

; Version Info
VIProductVersion "1.0.0.0"
VIAddVersionKey "ProductName" "Question Paper Generator"
VIAddVersionKey "CompanyName" "OpenSource"
VIAddVersionKey "FileDescription" "Offline Question Paper Generator"
VIProductVersion "1.0.0.0"

Section "Install"
    SetOutPath "$INSTDIR"
    
    ; Copy application files
    File "dist\QuestionPaperGenerator\QuestionPaperGenerator.exe"
    File "README-OFFLINE.md"
    
    ; Create start menu shortcuts
    CreateDirectory "$SMPROGRAMS\QuestionPaperGenerator"
    CreateShortcut "$SMPROGRAMS\QuestionPaperGenerator\Question Paper Generator.lnk" "$INSTDIR\QuestionPaperGenerator.exe"
    CreateShortcut "$SMPROGRAMS\QuestionPaperGenerator\Uninstall.lnk" "$INSTDIR\uninstall.exe"
    
    ; Create desktop shortcut
    CreateShortcut "$DESKTOP\Question Paper Generator.lnk" "$INSTDIR\QuestionPaperGenerator.exe"
    
    ; Write registry for uninstall
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\QuestionPaperGenerator" "DisplayName" "Question Paper Generator"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\QuestionPaperGenerator" "UninstallString" "$INSTDIR\uninstall.exe"
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"
    
    ; Run the application
    MessageBox MB_YESNO "Installation complete!$\n$\nWould you like to launch Question Paper Generator now?" IDNO done
    Exec "$INSTDIR\QuestionPaperGenerator.exe"
    done:
SectionEnd

Section "Uninstall"
    ; Remove files
    Delete "$INSTDIR\QuestionPaperGenerator.exe"
    Delete "$INSTDIR\README-OFFLINE.md"
    Delete "$INSTDIR\uninstall.exe"
    RMDir "$INSTDIR"
    
    ; Remove shortcuts
    Delete "$SMPROGRAMS\QuestionPaperGenerator\Question Paper Generator.lnk"
    Delete "$SMPROGRAMS\QuestionPaperGenerator\Uninstall.lnk"
    RMDir "$SMPROGRAMS\QuestionPaperGenerator"
    
    Delete "$DESKTOP\Question Paper Generator.lnk"
    
    ; Remove registry
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\QuestionPaperGenerator"
    DeleteRegKey HKCU "Software\QuestionPaperGenerator"
SectionEnd
