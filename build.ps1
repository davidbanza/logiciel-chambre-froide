# Script PowerShell pour compiler l'application Chambre Froide avec PyInstaller
# Utilisation: .\build.ps1

Write-Host "=== Compilation de l'application Chambre Froide ===" -ForegroundColor Cyan
Write-Host ""

# Variables de configuration
$PROJECT_ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
$DIST_DIR = Join-Path $PROJECT_ROOT "dist"
$BUILD_DIR = Join-Path $PROJECT_ROOT "build"
$MAIN_SCRIPT = Join-Path $PROJECT_ROOT "main.py"
$EXE_NAME = "ChambreFroide.exe"
$ICON_PATH = Join-Path $PROJECT_ROOT "images\favicon.ico"

# Activer l'environnement virtuel
Write-Host "1. Activation de l'environnement virtuel..." -ForegroundColor Yellow
$venvPath = Join-Path $PROJECT_ROOT "venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    & $venvPath
    Write-Host "Environnement virtuel active" -ForegroundColor Green
} else {
    Write-Host "Environnement virtuel non trouve a $venvPath" -ForegroundColor Red
    Write-Host "Veuillez creer l'environnement virtuel avec: python -m venv venv" -ForegroundColor Yellow
    exit 1
}

# Vérifier que PyInstaller est installé
Write-Host ""
Write-Host "2. Verification de PyInstaller..." -ForegroundColor Yellow
try {
    $pyinstallerVersion = & python -c "import PyInstaller; print(PyInstaller.__version__)" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "PyInstaller version $pyinstallerVersion trouve" -ForegroundColor Green
    } else {
        throw "PyInstaller non trouve"
    }
} catch {
    Write-Host "PyInstaller non trouve. Installation..." -ForegroundColor Red
    & pip install pyinstaller
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Echec de l'installation de PyInstaller" -ForegroundColor Red
        exit 1
    }
    Write-Host "PyInstaller installe" -ForegroundColor Green
}

# Nettoyer les anciens builds
Write-Host ""
Write-Host "3. Nettoyage des anciens builds..." -ForegroundColor Yellow
if (Test-Path $DIST_DIR) {
    Remove-Item -Recurse -Force $DIST_DIR
    Write-Host "Dossier dist supprime" -ForegroundColor Green
}
if (Test-Path $BUILD_DIR) {
    Remove-Item -Recurse -Force $BUILD_DIR
    Write-Host "Dossier build supprime" -ForegroundColor Green
}

# Créer le fichier spec personnalisé pour gérer les assets
Write-Host ""
Write-Host "4. Creation du fichier spec PyInstaller..." -ForegroundColor Yellow

# lorsque l'on insère le chemin de l'icône dans le spec python, les
# backslashes doivent être doublés pour éviter les escape sequences
$iconLiteral = $ICON_PATH -replace '\\','\\\\'

$specContent = @"
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['$MAIN_SCRIPT'],
    pathex=['$PROJECT_ROOT'],
    binaries=[],
    datas=[
        ('images', 'images'),                    # Logo et assets graphiques
        ('base_des_donnees', 'base_des_donnees'), # Scripts SQL
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'pymysql',
        'bcrypt',
        'reportlab',
        'reportlab.lib',
        'reportlab.lib.pagesizes',
        'reportlab.lib.colors',
        'reportlab.lib.units',
        'reportlab.platypus',
        'reportlab.lib.styles',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'win32print',
        'win32ui',
        'PIL.ImageWin',
        'datetime',
        'os',
        'sys',
        'decimal',
        'hashlib',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='$EXE_NAME',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Pas de console pour l'application GUI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=r'$iconLiteral',  # icône fournie par la variable PowerShell, en raw string
)
"@

$specFile = Join-Path $PROJECT_ROOT "ChambreFroide.spec"
$specContent | Out-File -FilePath $specFile -Encoding UTF8
Write-Host "Fichier spec cree: ChambreFroide.spec" -ForegroundColor Green

# Compiler avec PyInstaller
Write-Host ""
Write-Host "5. Compilation avec PyInstaller..." -ForegroundColor Yellow
Write-Host "Cette operation peut prendre plusieurs minutes..." -ForegroundColor Yellow

try {
    & pyinstaller --clean ChambreFroide.spec
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Compilation reussie!" -ForegroundColor Green
    } else {
        throw "Erreur lors de la compilation"
    }
} catch {
    Write-Host "Erreur lors de la compilation: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Verifier que l'executable a ete cree
$exePath = Join-Path $DIST_DIR $EXE_NAME
if (Test-Path $exePath) {
    $exeSize = (Get-Item $exePath).Length / 1MB
    Write-Host ""
    Write-Host "=== COMPILATION TERMINEE ===" -ForegroundColor Green
    Write-Host "Executable cree: $exePath" -ForegroundColor Green
    Write-Host "Taille: $([math]::Round($exeSize, 2)) MB" -ForegroundColor Green
    Write-Host ""
    Write-Host "Pour distribuer l'application:" -ForegroundColor Cyan
    Write-Host "1. Copiez tout le contenu du dossier '$DIST_DIR'" -ForegroundColor White
    Write-Host "2. Assurez-vous que les imprimantes thermiques sont configurees" -ForegroundColor White
    Write-Host "3. Testez l'application sur une machine differente" -ForegroundColor White
    Write-Host ""
    Write-Host "Note: L'application necessite une base de donnees MySQL/MariaDB" -ForegroundColor Yellow
    Write-Host "      Les scripts SQL sont inclus dans base_des_donnees/" -ForegroundColor Yellow
} else {
    Write-Host "L'executable n'a pas ete trouve a l'emplacement attendu" -ForegroundColor Red
    exit 1
}

# Nettoyer le fichier spec
Write-Host ""
Write-Host "6. Nettoyage..." -ForegroundColor Yellow
if (Test-Path $specFile) {
    Remove-Item $specFile
    Write-Host "Fichier spec nettoye" -ForegroundColor Green
}

Write-Host ""
Write-Host "Compilation terminee avec succes!" -ForegroundColor Green