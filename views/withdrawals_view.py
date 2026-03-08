from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
                             QLabel, QDateEdit, QPushButton, QMessageBox, QGroupBox, QCalendarWidget,
                             QComboBox, QSpinBox, QDialog)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QFont
from database import (get_pending_withdrawals, update_sale, get_all_users, is_manager)
from utils import format_currency
from datetime import datetime


class WithdrawalsView(QWidget):
    """Vue pour gérer les retraits programmés (ULTERIEUR) a posteriori"""

    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.is_manager = is_manager(current_user['id_ut'])
        self.setWindowTitle("Gestion des Retraits")
        self.setGeometry(100, 100, 1400, 700)
        self.setup_ui()
        self.load_pending_withdrawals()

    def setup_ui(self):
        """Configure l'interface utilisateur"""
        main_layout = QVBoxLayout()

        # Titre
        title_text = "Gestion des Retraits" if self.is_manager else "Mes Retraits en Attente"
        title = QLabel(title_text)
        title.setObjectName("title")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(title)

        # Filtres
        filters_layout = QHBoxLayout()
        filters_layout.addWidget(QLabel("Statut :"))

        self.status_filter = QComboBox()
        self.status_filter.addItem("En attente (ULTERIEUR)", "ULTERIEUR")
        self.status_filter.addItem("Tous les retraits", "ALL")
        self.status_filter.currentIndexChanged.connect(self.load_pending_withdrawals)
        filters_layout.addWidget(self.status_filter)

        filters_layout.addWidget(QLabel("Période à partir de :"))
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addMonths(-3))
        self.date_from.dateChanged.connect(self.load_pending_withdrawals)
        filters_layout.addWidget(self.date_from)

        # Filtre par vendeur (manager seulement)
        if self.is_manager:
            filters_layout.addWidget(QLabel("Vendeur :"))
            self.vendor_filter = QComboBox()
            self.vendor_filter.addItem("TOUS LES VENDEURS", "")
            users = get_all_users()
            for user in users:
                if user['statut'] == 'ACTIF':
                    full_name = f"{user['prenom_ut']} {user['nom_ut']}"
                    self.vendor_filter.addItem(full_name, user['id_ut'])
            self.vendor_filter.currentIndexChanged.connect(self.load_pending_withdrawals)
            filters_layout.addWidget(self.vendor_filter)

        btn_refresh = QPushButton("🔄 Actualiser")
        btn_refresh.clicked.connect(self.load_pending_withdrawals)
        filters_layout.addWidget(btn_refresh)

        filters_layout.addStretch()
        main_layout.addLayout(filters_layout)

        # Section statistiques
        stats_layout = QHBoxLayout()

        stats_group = QGroupBox("Statistiques")
        stats_inner = QHBoxLayout()

        self.label_pending_count = QLabel("0")
        self.label_pending_count.setStyleSheet("font-size: 16px; font-weight: bold; color: #e74c3c;")
        stats_inner.addWidget(QLabel("En attente :"))
        stats_inner.addWidget(self.label_pending_count)

        stats_inner.addSpacing(30)

        self.label_pending_amount = QLabel("0,00 FC")
        self.label_pending_amount.setStyleSheet("font-size: 16px; font-weight: bold; color: #f39c12;")
        stats_inner.addWidget(QLabel("Montant en attente :"))
        stats_inner.addWidget(self.label_pending_amount)

        stats_inner.addStretch()
        stats_group.setLayout(stats_inner)
        stats_layout.addWidget(stats_group)

        main_layout.addLayout(stats_layout)

        # Tableau des retraits
        self.table_withdrawals = QTableWidget()
        self.table_withdrawals.setColumnCount(8)
        self.table_withdrawals.setHorizontalHeaderLabels([
            "Date Vente", "Vendeur", "Client", "Montant", "Date Retrait Prévue",
            "Date Retrait Effectuée", "Statut", "Actions"
        ])
        self.table_withdrawals.setColumnWidth(0, 100)
        self.table_withdrawals.setColumnWidth(1, 150)
        self.table_withdrawals.setColumnWidth(2, 150)
        self.table_withdrawals.setColumnWidth(3, 100)
        self.table_withdrawals.setColumnWidth(4, 130)
        self.table_withdrawals.setColumnWidth(5, 150)
        self.table_withdrawals.setColumnWidth(6, 100)
        self.table_withdrawals.setColumnWidth(7, 200)

        main_layout.addWidget(self.table_withdrawals)

        self.setLayout(main_layout)

    def load_pending_withdrawals(self):
        """Charge les retraits en attente"""
        status_filter = self.status_filter.currentData()
        date_from = self.date_from.date().toString("yyyy-MM-dd")

        # Récupérer les retraits
        if self.is_manager:
            vendor_id = self.vendor_filter.currentData() if hasattr(self, 'vendor_filter') else None
            pending = get_pending_withdrawals(status_filter, date_from, vendor_id)
        else:
            pending = get_pending_withdrawals(status_filter, date_from, self.current_user['id_ut'])

        # Calculer les statistiques
        pending_count = len([w for w in pending if w.get('statut_retrait') == 'ULTERIEUR'])
        pending_amount = sum(float(w.get('montant_total', 0) or 0) for w in pending if w.get('statut_retrait') == 'ULTERIEUR')

        self.label_pending_count.setText(str(pending_count))
        self.label_pending_amount.setText(format_currency(pending_amount))

        # Remplir le tableau
        self.table_withdrawals.setRowCount(len(pending))

        for row, withdrawal in enumerate(pending):
            # Date vente
            self.table_withdrawals.setItem(row, 0, QTableWidgetItem(str(withdrawal.get('date_vente', ''))))

            # Vendeur
            vendor_name = withdrawal.get('vendeur', 'N/A')
            self.table_withdrawals.setItem(row, 1, QTableWidgetItem(vendor_name))

            # Client
            client_name = withdrawal.get('client', 'N/A')
            self.table_withdrawals.setItem(row, 2, QTableWidgetItem(client_name))

            # Montant
            amount = float(withdrawal.get('montant_total', 0) or 0)
            self.table_withdrawals.setItem(row, 3, QTableWidgetItem(format_currency(amount)))

            # Date retrait prévue (si ULTERIEUR, sinon N/A)
            planned_date = withdrawal.get('date_retrait_effective') or "IMMEDIAT"
            self.table_withdrawals.setItem(row, 4, QTableWidgetItem(str(planned_date)))

            # Date retrait effectuée (on va le mettre à jour)
            effective_date = withdrawal.get('date_retrait_effective') if withdrawal.get('statut_retrait') == 'ULTERIEUR' else "—"
            self.table_withdrawals.setItem(row, 5, QTableWidgetItem(str(effective_date)))

            # Statut
            status = withdrawal.get('statut_retrait', 'IMMEDIAT')
            status_item = QTableWidgetItem(status)
            # Styliser le statut
            font = QFont()
            font.setBold(True)
            status_item.setFont(font)
            if status == "ULTERIEUR":
                status_item.setForeground(QColor("#f39c12"))  # Orange
            else:
                status_item.setForeground(QColor("#27ae60"))  # Vert
            self.table_withdrawals.setItem(row, 6, status_item)

            # Actions
            action_widget = QWidget()
            action_layout = QHBoxLayout()

            if status == "ULTERIEUR":
                btn_mark = QPushButton("✓ Marquer comme retiré")
                btn_mark.clicked.connect(
                    lambda checked, sale_id=withdrawal.get('id_vente'), row_num=row:
                    self.mark_withdrawal_done(sale_id, row_num)
                )
                action_layout.addWidget(btn_mark)

            btn_edit = QPushButton("📝 Modifier")
            btn_edit.clicked.connect(
                lambda checked, sale_id=withdrawal.get('id_vente'):
                self.edit_withdrawal(sale_id)
            )
            action_layout.addWidget(btn_edit)

            action_layout.setContentsMargins(0, 0, 0, 0)
            action_widget.setLayout(action_layout)
            self.table_withdrawals.setCellWidget(row, 7, action_widget)

    def mark_withdrawal_done(self, sale_id, row_num):
        """Marque un retrait comme effectué"""
        try:
            # Mettre à jour le retrait à IMMEDIAT avec la date actuelle
            if update_sale(sale_id, statut_retrait="IMMEDIAT", date_retrait=QDate.currentDate().toString("yyyy-MM-dd")):
                QMessageBox.information(
                    self,
                    "Succès",
                    f"Retrait de la vente #{sale_id} marqué comme effectué le {QDate.currentDate().toString('dd/MM/yyyy')}"
                )
                self.load_pending_withdrawals()
            else:
                QMessageBox.critical(self, "Erreur", "Impossible de mettre à jour le retrait")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la mise à jour : {str(e)}")

    def edit_withdrawal(self, sale_id):
        """Ouvre un dialogue pour éditer les détails du retrait"""
        dialog = EditWithdrawalDialog(sale_id, self)
        if dialog.exec():
            self.load_pending_withdrawals()


class EditWithdrawalDialog(QDialog):
    """Dialogue pour éditer les détails d'un retrait"""

    def __init__(self, sale_id, parent=None):
        super().__init__(parent)
        from database import get_sale_by_id
        self.sale = get_sale_by_id(sale_id)
        
        if not self.sale:
            QMessageBox.warning(self, "Erreur", f"Vente #{sale_id} non trouvée")
            self.close()
            return

        self.setWindowTitle(f"Éditer Retrait - Vente #{sale_id}")
        self.setMinimumWidth(500)

        layout = QVBoxLayout()

        # Infos vente
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel(f"Vente #{sale_id}"))
        info_layout.addWidget(QLabel(f"Client: {self.sale['client']}"))
        info_layout.addWidget(QLabel(f"Date: {self.sale['date_vente']}"))
        info_layout.addWidget(QLabel(f"Montant: {format_currency(sum(a['prix_vente'] * a['quantite'] for a in self.sale['articles']))}"))
        info_layout.addStretch()
        layout.addLayout(info_layout)

        # Statut retrait
        form_layout = QVBoxLayout()
        form_layout.addWidget(QLabel("Statut Retrait :"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["IMMEDIAT", "ULTERIEUR"])
        self.status_combo.setCurrentText(self.sale['statut_retrait'] or "IMMEDIAT")
        self.status_combo.currentTextChanged.connect(self.on_status_changed)
        form_layout.addWidget(self.status_combo)

        # Date retrait
        form_layout.addWidget(QLabel("Date Retrait :"))
        self.date_retrait = QDateEdit()
        if self.sale['date_retrait_effective']:
            self.date_retrait.setDate(QDate.fromString(str(self.sale['date_retrait_effective']), "yyyy-MM-dd"))
        else:
            self.date_retrait.setDate(QDate.currentDate())
        self.date_retrait.setEnabled(self.sale['statut_retrait'] == "ULTERIEUR")
        form_layout.addWidget(self.date_retrait)

        layout.addLayout(form_layout)

        # Calendrier pour sélection visuelle
        layout.addWidget(QLabel("Sélectionner une date sur le calendrier :"))
        self.calendar = QCalendarWidget()
        self.calendar.setSelectedDate(self.date_retrait.date())
        self.calendar.clicked.connect(self.on_calendar_clicked)
        layout.addWidget(self.calendar)

        # Boutons
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Enregistrer")
        btn_cancel = QPushButton("Annuler")

        btn_save.clicked.connect(self.save_withdrawal)
        btn_cancel.clicked.connect(self.close)

        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def on_status_changed(self):
        """Active/désactive la date selon le statut"""
        self.date_retrait.setEnabled(self.status_combo.currentText() == "ULTERIEUR")
        self.calendar.setEnabled(self.status_combo.currentText() == "ULTERIEUR")

    def on_calendar_clicked(self, date):
        """Met à jour la date quand on clique sur le calendrier"""
        self.date_retrait.setDate(date)

    def save_withdrawal(self):
        """Sauvegarde les modifications"""
        try:
            from database import update_sale
            
            status = self.status_combo.currentText()
            date_retrait = None if status == "IMMEDIAT" else self.date_retrait.date().toString("yyyy-MM-dd")

            if update_sale(self.sale['id_vente'], statut_retrait=status, date_retrait=date_retrait):
                QMessageBox.information(
                    self,
                    "Succès",
                    f"Retrait de la vente #{self.sale['id_vente']} mis à jour avec succès!"
                )
                self.accept()
            else:
                QMessageBox.critical(self, "Erreur", "Impossible de mettre à jour le retrait")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde : {str(e)}")
