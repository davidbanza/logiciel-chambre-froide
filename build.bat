@echo off
REM Script batch pour compiler l'application Chambre Froide avec PyInstaller
REM Utilisation: build.bat

echo === Compilation de l'application Chambre Froide ===
echo.

REM Variables de configuration
set PROJECT_ROOT=%~dp0
set DIST_DIR=%PROJECT_ROOT%dist
set BUILD_DIR=%PROJECT_ROOT%build
set MAIN_SCRIPT=%PROJECT_ROOT%main.py
set EXE_NAME=ChambreFroide.exe
set ICON_PATH=%PROJECT_ROOT%images\favicon.ico

REM Activer l'environnement virtuel
echo 1. Activation de l'environnement virtuel...
if exist "%PROJECT_ROOT%venv\Scripts\activate.bat" (
    call "%PROJECT_ROOT%venv\Scripts\activate.bat"
    echo ✓ Environnement virtuel activé
) else (
    echo ❌ Environnement virtuel non trouvé à %PROJECT_ROOT%venv\Scripts\activate.bat
    echo Veuillez créer l'environnement virtuel avec: python -m venv venv
    pause
    exit /b 1
)

REM Vérifier que PyInstaller est installé
echo.
echo 2. Vérification de PyInstaller...
python -c "import PyInstaller; print('PyInstaller version:', PyInstaller.__version__)" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    for /f "tokens=*" %%i in ('python -c "import PyInstaller; print(PyInstaller.__version__)"') do set PYINSTALLER_VERSION=%%i
    echo ✓ PyInstaller %PYINSTALLER_VERSION% trouvé
) else (
    echo ❌ PyInstaller non trouvé. Installation...
    pip install pyinstaller
    if %ERRORLEVEL% NEQ 0 (
        echo ❌ Échec de l'installation de PyInstaller
        pause
        exit /b 1
    )
    echo ✓ PyInstaller installé
)

REM Nettoyer les anciens builds
echo.
echo 3. Nettoyage des anciens builds...
if exist "%DIST_DIR%" (
    rmdir /s /q "%DIST_DIR%"
    echo ✓ Dossier dist supprimé
)
if exist "%BUILD_DIR%" (
    rmdir /s /q "%BUILD_DIR%"
    echo ✓ Dossier build supprimé
)

REM Compiler avec PyInstaller
echo.
echo 4. Compilation avec PyInstaller...
echo Cette opération peut prendre plusieurs minutes...
pyinstaller --onefile --windowed --name %EXE_NAME% --icon "%ICON_PATH%" ^
    --add-data "images;images" ^
    --add-data "base_des_donnees;base_des_donnees" ^
    --hidden-import PySide6.QtCore ^
    --hidden-import PySide6.QtGui ^
    --hidden-import PySide6.QtWidgets ^
    --hidden-import pymysql ^
    --hidden-import bcrypt ^
    --hidden-import reportlab ^
    --hidden-import reportlab.lib ^
    --hidden-import reportlab.lib.pagesizes ^
    --hidden-import reportlab.lib.colors ^
    --hidden-import reportlab.lib.units ^
    --hidden-import reportlab.platypus ^
    --hidden-import reportlab.lib.styles ^
    --hidden-import PIL ^
    --hidden-import PIL.Image ^
    --hidden-import PIL.ImageDraw ^
    --hidden-import PIL.ImageFont ^
    --hidden-import win32print ^
    --hidden-import win32ui ^
    --hidden-import PIL.ImageWin ^
    --hidden-import datetime ^
    --hidden-import os ^
    --hidden-import sys ^
    --hidden-import decimal ^
    --hidden-import hashlib ^
    "%MAIN_SCRIPT%"

if %ERRORLEVEL% EQU 0 (
    echo ✓ Compilation réussie!
) else (
    echo ❌ Erreur lors de la compilation
    pause
    exit /b 1
)

REM Vérifier que l'exécutable a été créé
if exist "%DIST_DIR%\%EXE_NAME%" (
    for %%A in ("%DIST_DIR%\%EXE_NAME%") do set FILE_SIZE=%%~zA
    set /a FILE_SIZE_MB=%FILE_SIZE%/1048576
    echo.
    echo === COMPILATION TERMINÉE ===
    echo ✓ Exécutable créé: %DIST_DIR%\%EXE_NAME%
    echo ✓ Taille: %FILE_SIZE_MB% MB
    echo.
    echo Pour distribuer l'application:
    echo 1. Copiez tout le contenu du dossier '%DIST_DIR%'
    echo 2. Assurez-vous que les imprimantes thermiques sont configurées
    echo 3. Testez l'application sur une machine différente
    echo.
    echo Note: L'application nécessite une base de données MySQL/MariaDB
    echo       Les scripts SQL sont inclus dans base_des_donnees/
) else (
    echo ❌ L'exécutable n'a pas été trouvé à l'emplacement attendu
    pause
    exit /b 1
)

echo.
echo 🎉 Compilation terminée avec succès!
pause