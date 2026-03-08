# Guide de Compilation - Chambre Froide

## Compilation avec PyInstaller

Ce guide explique comment compiler l'application Chambre Froide en exécutable Windows autonome.

### Prérequis

1. **Python 3.8+** installé
2. **Environnement virtuel** configuré avec toutes les dépendances
3. **PyInstaller** installé dans l'environnement virtuel

### Installation des dépendances

```powershell
# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
pip install pyinstaller
```

### Compilation

#### Méthode 1: Script PowerShell (Recommandé)

```powershell
# Depuis le répertoire racine du projet
.\build.ps1
```

#### Méthode 2: Script Batch (Windows CMD)

```cmd
# Depuis le répertoire racine du projet
build.bat  # prendra l'icône dans images\favicon.ico
```

#### Méthode 3: Compilation manuelle

```powershell
# Activer l'environnement virtuel
venv\Scripts\activate

# Compiler
pyinstaller --onefile --windowed --name ChambreFroide ^
    --add-data "images;images" ^
    --add-data "base_des_donnees;base_des_donnees" ^
    --hidden-import PySide6.QtCore ^
    --hidden-import PySide6.QtGui ^
    --hidden-import PySide6.QtWidgets ^
    --hidden-import pymysql ^
    --hidden-import bcrypt ^
    --hidden-import reportlab ^
    --hidden-import PIL ^
    --hidden-import win32print ^
    --hidden-import win32ui ^
    main.py
```

Les scripts automatiques vont automatiquement :
- Activer l'environnement virtuel
- Vérifier PyInstaller
- Nettoyer les anciens builds
- Créer le fichier spec approprié (pour PowerShell)
- Utiliser `images\favicon.ico` comme icône pour l'exécutable
- Compiler l'application
- Générer un exécutable autonome

### Résultat de la compilation

Après compilation, vous trouverez dans le dossier `dist/` :
- `ChambreFroide.exe` : L'exécutable principal
- Tous les fichiers nécessaires à l'application

### Distribution

Pour distribuer l'application :

1. **Copiez tout le contenu du dossier `dist/`**
2. **Assurez-vous que les conditions suivantes sont remplies sur la machine cible :**
   - Windows 10/11
   - Pilotes d'imprimante thermique installés (si utilisé)
   - Base de données MySQL/MariaDB accessible

### Dépannage

#### Erreur "ModuleNotFoundError"
- Vérifiez que toutes les dépendances sont installées
- Utilisez `pip list` pour vérifier

#### Erreur d'impression thermique
- L'impression thermique nécessite `pywin32` et `Pillow`
- Testez avec le script `test_thermal.py`

#### Application ne démarre pas
- Vérifiez les logs d'erreur
- Assurez-vous que la base de données est accessible
- Testez avec `python main.py` d'abord

### Assets inclus

Le script de compilation inclut automatiquement :
- `images/logo.png` : Logo de l'application
- `base_des_donnees/*.sql` : Scripts de base de données

### Optimisations

L'exécutable est optimisé avec :
- UPX compression
- Exclusion des modules inutiles
- Interface graphique (pas de console)

### Support

En cas de problème, vérifiez :
1. Les logs de compilation dans la console
2. Les dépendances dans `requirements.txt`
3. La configuration de la base de données