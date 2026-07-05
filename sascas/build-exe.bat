@echo off
REM Build Question Paper Generator to Windows EXE
REM This creates a standalone .exe that doesn't need Python

title Building Question Paper Generator...

echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║     Building Question Paper Generator to .EXE          ║
echo ╚════════════════════════════════════════════════════════╝
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ✗ Python not found
    echo Please install Python from https://www.python.org
    pause
    exit /b 1
)

echo ✓ Python found

REM Step 1: Install PyInstaller
echo.
echo Installing PyInstaller...
pip install -q pyinstaller

if %errorLevel% neq 0 (
    echo ✗ Failed to install PyInstaller
    echo Try: pip install pyinstaller
    pause
    exit /b 1
)

echo ✓ PyInstaller installed

REM Step 2: Build the EXE
echo.
echo Building EXE...
echo This may take 2-5 minutes...
echo.

pyinstaller QuestionPaperGenerator.spec

if %errorLevel% neq 0 (
    echo ✗ Failed to build EXE
    echo Check the errors above
    pause
    exit /b 1
)

echo.
echo ✓ EXE built successfully!

REM Step 3: Verify
echo.
echo Checking output...

if exist "dist\QuestionPaperGenerator\QuestionPaperGenerator.exe" (
    echo ✓ QuestionPaperGenerator.exe created
    echo ✓ Location: dist\QuestionPaperGenerator\QuestionPaperGenerator.exe
) else (
    echo ✗ EXE not found
    pause
    exit /b 1
)

echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║ ✓ Build Complete!                                      ║
echo ╚════════════════════════════════════════════════════════╝
echo.
echo Your standalone EXE is ready:
echo   Location: dist\QuestionPaperGenerator\QuestionPaperGenerator.exe
echo.
echo You can now:
echo   1. Share the EXE with others (no Python needed!)
echo   2. Commit to GitHub for auto-releases
echo   3. Create a Windows installer (need NSIS)
echo.
pause
