"""Utilitaires pour l'application"""

def format_currency(amount, currency="FC"):
    """
    Formate un montant d'argent avec séparateurs de milliers.
    
    Args:
        amount: Le montant à formater (int ou float)
        currency: La devise à afficher (défaut: "FC")
    
    Returns:
        Chaîne formatée avec séparateurs (ex: "1 234,50 FC")
    
    Exemples:
        >>> format_currency(1234.5)
        '1 234,50 FC'
        >>> format_currency(1000000.99)
        '1 000 000,99 FC'
        >>> format_currency(42.1)
        '42,10 FC'
    """
    try:
        # Formater avec 2 décimales
        formatted = f"{float(amount):,.2f}"
        
        # Remplacer la virgule et le point pour le format français
        # from "1,234.50" to "1 234,50"
        parts = formatted.split('.')
        integer_part = parts[0].replace(',', ' ')  # Remplacer virgules par espaces
        decimal_part = parts[1] if len(parts) > 1 else "00"
        
        return f"{integer_part},{decimal_part} {currency}"
    except (ValueError, TypeError):
        return f"0,00 {currency}"


def resource_path(relative_path: str) -> str:
    """
    Retourne le chemin absolu d'une ressource, compatible avec PyInstaller.

    Lorsque l'application est empaquetée avec PyInstaller, les fichiers de
    données sont extraits dans un répertoire temporaire accessible via
    ``sys._MEIPASS``. Cette fonction gère ce cas en renvoyant soit le
    chemin local (mode développement), soit le chemin dans le bundle.

    Args:
        relative_path: chemin relatif à la racine du projet (ex: "images/logo.png")

    Returns:
        Chemin absolu vers la ressource.
    """
    import sys
    import os

    base_path = getattr(sys, '_MEIPASS', os.path.abspath('.'))
    return os.path.join(base_path, relative_path)


def ask_print_options(parent=None, title="Options d'impression", message="Choisissez les options d'impression :"):
    """
    Demande à l'utilisateur les options d'impression (PDF et/ou thermique)
    
    Args:
        parent: Widget parent pour la boîte de dialogue
        title: Titre de la boîte de dialogue
        message: Message à afficher
    
    Returns:
        dict: {'print_pdf': bool, 'print_thermal': bool, 'thermal_width': str}
    """
    from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QCheckBox, QComboBox, QDialogButtonBox, QGroupBox, QHBoxLayout
    from PySide6.QtCore import Qt
    
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setModal(True)
    
    layout = QVBoxLayout(dialog)
    
    # Message
    message_label = QLabel(message)
    layout.addWidget(message_label)
    
    # Options d'impression
    options_group = QGroupBox("Options d'impression")
    options_layout = QVBoxLayout(options_group)
    
    # PDF
    pdf_checkbox = QCheckBox("Générer PDF")
    pdf_checkbox.setChecked(True)  # PDF activé par défaut
    options_layout.addWidget(pdf_checkbox)
    
    # Thermique
    thermal_checkbox = QCheckBox("Imprimer sur thermique")
    thermal_checkbox.setChecked(False)
    options_layout.addWidget(thermal_checkbox)
    
    # Largeur thermique (activé seulement si thermique coché)
    thermal_width_layout = QHBoxLayout()
    thermal_width_label = QLabel("Largeur thermique:")
    thermal_width_combo = QComboBox()
    thermal_width_combo.addItems(["56mm", "80mm"])
    thermal_width_combo.setCurrentText("80mm")
    thermal_width_combo.setEnabled(False)
    
    thermal_width_layout.addWidget(thermal_width_label)
    thermal_width_layout.addWidget(thermal_width_combo)
    thermal_width_layout.addStretch()
    options_layout.addLayout(thermal_width_layout)
    
    layout.addWidget(options_group)
    
    # Connecter les signaux
    def on_thermal_toggled(checked):
        thermal_width_combo.setEnabled(checked)
    
    thermal_checkbox.toggled.connect(on_thermal_toggled)
    
    # Boutons
    button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)
    layout.addWidget(button_box)
    
    # Exécuter la boîte de dialogue
    if dialog.exec() == QDialog.Accepted:
        return {
            'print_pdf': pdf_checkbox.isChecked(),
            'print_thermal': thermal_checkbox.isChecked(),
            'thermal_width': thermal_width_combo.currentText() if thermal_checkbox.isChecked() else None
        }
    else:
        return None
    """
    Formate un montant d'argent avec séparateurs de milliers.
    
    Args:
        amount: Le montant à formater (int ou float)
        currency: La devise à afficher (défaut: "FC")
    
    Returns:
        Chaîne formatée avec séparateurs (ex: "1 234,50 FC")
    
    Exemples:
        >>> format_currency(1234.5)
        '1 234,50 FC'
        >>> format_currency(1000000.99)
        '1 000 000,99 FC'
        >>> format_currency(42.1)
        '42,10 FC'
    """
    try:
        # Formater avec 2 décimales
        formatted = f"{float(amount):,.2f}"
        
        # Remplacer la virgule et le point pour le format français
        # from "1,234.50" to "1 234,50"
        parts = formatted.split('.')
        integer_part = parts[0].replace(',', ' ')  # Remplacer virgules par espaces
        decimal_part = parts[1] if len(parts) > 1 else "00"
        
        return f"{integer_part},{decimal_part} {currency}"
    except (ValueError, TypeError):
        return f"0,00 {currency}"
