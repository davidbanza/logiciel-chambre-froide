from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QFormLayout,
                             QLineEdit, QComboBox, QPushButton, QLabel, QMessageBox,
                             QTableWidget, QTableWidgetItem, QSpinBox, QDateEdit, QDialog,
                             QRadioButton, QButtonGroup, QGroupBox, QTextEdit)
from PySide6.QtCore import QDate, Qt
from datetime import datetime
from database import (get_all_products, get_all_payment_modes, create_sale, get_sales_by_vendor_id, get_sale_by_id, 
                      is_manager, create_debt, is_credit_payment,
                      get_clients_by_phone, create_client_direct, update_sale, get_all_users, get_all_sales_detailed)
from invoice_generator import generate_invoice, open_invoice, print_thermal_receipt, generate_and_print_receipt
from utils import format_currency, ask_print_options


class ClientSelectionDialog(QDialog):
    def __init__(self, existing_clients, new_client_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Choix du Client")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Ce numéro de téléphone est déjà pris. Veuillez choisir :"))
        
        self.radio_group = QButtonGroup(self)
        self.radio_buttons = []
        
        for client in existing_clients:
            nom_complet = f"{client['nom_client'] or ''} {client['prenom_client'] or ''} {client['postnom_client'] or ''}".strip()
            rb = QRadioButton(f"EXISTANT : ID {client['id_client']} - {nom_complet}")
            self.radio_group.addButton(rb)
            self.radio_buttons.append((rb, client['id_client']))
            layout.addWidget(rb)
            
        if self.radio_buttons:
            self.radio_buttons[0][0].setChecked(True)
            
        new_nom_complet = f"{new_client_data['nom']} {new_client_data['prenom']} {new_client_data['postnom']}".strip()
        self.radio_new = QRadioButton(f"CRÉER NOUVEAU : {new_nom_complet}")
        self.radio_group.addButton(self.radio_new)
        layout.addWidget(self.radio_new)
        
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Valider")
        btn_cancel = QPushButton("Annuler")
        
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        
    def get_selection(self):
        if self.radio_new.isChecked():
            return "NEW", None
        for rb, c_id in self.radio_buttons:
            if rb.isChecked():
                return "EXISTING", c_id
        return None, None


class SaleDetailsDialog(QDialog):
    """Boîte de dialogue pour afficher les détails d'une vente"""
    
    def __init__(self, sale_id, parent=None):
        super().__init__(parent)
        self.sale_id = sale_id
        self.sale_data = get_sale_by_id(sale_id)
        
        if not self.sale_data:
            QMessageBox.warning(parent, "Erreur", "Vente non trouvée")
            return
        
        self.setWindowTitle(f"Détails de la Vente #{sale_id}")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        self.setup_ui()
    
    def setup_ui(self):
        """Configure l'interface de la boîte de dialogue"""
        layout = QVBoxLayout()
        
        # En-tête avec informations principales
        header_group = QGroupBox("Informations de la Vente")
        header_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3498db;
                border-radius: 5px;
                margin-top: 1ex;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }
        """)
        header_layout = QFormLayout()
        
        # Informations de base avec couleurs
        id_label = QLabel(f"#{self.sale_data['id_vente']}")
        id_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
        header_layout.addRow("ID Vente :", id_label)
        
        header_layout.addRow("Date :", QLabel(str(self.sale_data['date_vente'])))
        header_layout.addRow("Client :", QLabel(self.sale_data['client'] or "N/A"))
        header_layout.addRow("Vendeur :", QLabel(self.sale_data['vendeur'] or "N/A"))
        
        # Mode de paiement avec couleur selon le type
        payment_mode = self.sale_data['mode_paiement'] or "N/A"
        payment_label = QLabel(payment_mode)
        if payment_mode.upper() == "DETTE":
            payment_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        else:
            payment_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        header_layout.addRow("Mode de Paiement :", payment_label)
        
        # Statut retrait avec couleur
        retrait_status = self.sale_data['statut_retrait'] or "N/A"
        retrait_label = QLabel(retrait_status)
        if retrait_status == "IMMEDIAT":
            retrait_label.setStyleSheet("color: #27ae60;")
        elif retrait_status == "ULTERIEUR":
            retrait_label.setStyleSheet("color: #f39c12;")
        retrait_label.setStyleSheet("font-weight: bold;")
        header_layout.addRow("Statut Retrait :", retrait_label)
        
        if self.sale_data['date_retrait_effective']:
            retrait_date_label = QLabel(str(self.sale_data['date_retrait_effective']))
            retrait_date_label.setStyleSheet("color: #3498db;")
            header_layout.addRow("Date Retrait Effective :", retrait_date_label)
        
        header_group.setLayout(header_layout)
        layout.addWidget(header_group)
        
        # Tableau des articles
        articles_group = QGroupBox("Articles Vendus")
        articles_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #27ae60;
                border-radius: 5px;
                margin-top: 1ex;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }
        """)
        articles_layout = QVBoxLayout()
        
        self.articles_table = QTableWidget()
        self.articles_table.setColumnCount(4)
        self.articles_table.setHorizontalHeaderLabels(["Produit", "Prix Unitaire", "Quantité", "Sous-total"])
        self.articles_table.setColumnWidth(0, 300)
        self.articles_table.setColumnWidth(1, 120)
        self.articles_table.setColumnWidth(2, 100)
        self.articles_table.setColumnWidth(3, 120)
        
        # Style du tableau
        self.articles_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #ddd;
                selection-background-color: #e3f2fd;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 8px;
                border: 1px solid #ddd;
                font-weight: bold;
            }
        """)
        
        # Désactiver l'édition du tableau
        self.articles_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # Remplir le tableau
        articles = self.sale_data.get('articles', [])
        self.articles_table.setRowCount(len(articles))
        
        total = 0
        for row, article in enumerate(articles):
            prix = article['prix_vente']
            quantite = article['quantite']
            subtotal = prix * quantite
            total += subtotal
            
            # Produit
            product_item = QTableWidgetItem(article['nom_pr'])
            product_item.setToolTip(article['nom_pr'])  # Tooltip pour les noms longs
            self.articles_table.setItem(row, 0, product_item)
            
            # Prix unitaire
            price_item = QTableWidgetItem(format_currency(prix))
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.articles_table.setItem(row, 1, price_item)
            
            # Quantité
            qty_item = QTableWidgetItem(str(quantite))
            qty_item.setTextAlignment(Qt.AlignCenter)
            self.articles_table.setItem(row, 2, qty_item)
            
            # Sous-total
            subtotal_item = QTableWidgetItem(format_currency(subtotal))
            subtotal_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.articles_table.setItem(row, 3, subtotal_item)
        
        articles_layout.addWidget(self.articles_table)
        
        # Résumé des articles
        summary_layout = QHBoxLayout()
        total_articles = sum(article['quantite'] for article in articles)
        summary_label = QLabel(f"Total articles : {total_articles} | Nombre de produits différents : {len(articles)}")
        summary_label.setStyleSheet("font-style: italic; color: #666;")
        summary_layout.addWidget(summary_label)
        summary_layout.addStretch()
        articles_layout.addLayout(summary_layout)
        
        articles_group.setLayout(articles_layout)
        layout.addWidget(articles_group)
        
        # Total avec cadre
        total_group = QGroupBox()
        total_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #27ae60;
                border-radius: 5px;
                background-color: #f8fff9;
            }
        """)
        total_layout = QHBoxLayout()
        total_layout.addStretch()
        
        total_title = QLabel("TOTAL : ")
        total_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        total_layout.addWidget(total_title)
        
        total_label = QLabel(format_currency(total))
        total_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #27ae60;")
        total_layout.addWidget(total_label)
        
        total_layout.addStretch()
        total_group.setLayout(total_layout)
        layout.addWidget(total_group)
        
        # Boutons d'action
        buttons_layout = QHBoxLayout()
        
        btn_print = QPushButton("🖨️ Imprimer Facture")
        btn_print.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        btn_print.clicked.connect(self.print_invoice)
        buttons_layout.addWidget(btn_print)
        
        buttons_layout.addStretch()
        
        btn_close = QPushButton("Fermer")
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
            QPushButton:pressed {
                background-color: #6c7b7d;
            }
        """)
        btn_close.clicked.connect(self.accept)
        buttons_layout.addWidget(btn_close)
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)
    
    def print_invoice(self):
        """Imprime la facture de la vente"""
        try:
            import os
            from datetime import datetime
            
            # Demander les options d'impression
            print_options = ask_print_options(self, "Impression de facture", "Choisissez les options d'impression pour cette vente :")
            if print_options is None:  # Annulé
                return
            
            success_messages = []
            error_messages = []
            
            # Générer PDF si demandé
            pdf_filename = None
            if print_options['print_pdf']:
                pdf_filename = f"factures/facture_{self.sale_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                os.makedirs("factures", exist_ok=True)
                
                if generate_invoice(self.sale_data, pdf_filename):
                    success_messages.append(f"✓ PDF généré: {pdf_filename}")
                else:
                    error_messages.append("❌ Erreur lors de la génération du PDF")
            
            # Imprimer sur thermique si demandé
            if print_options['print_thermal']:
                thermal_width = print_options.get('thermal_width', '80mm')
                if print_thermal_receipt(self.sale_data, thermal_width):
                    success_messages.append(f"✓ Reçu thermique imprimé ({thermal_width})")
                else:
                    error_messages.append("❌ Erreur lors de l'impression thermique")
            
            # Afficher les résultats
            if success_messages:
                message = "Impression terminée :\n\n" + "\n".join(success_messages)
                if error_messages:
                    message += "\n\nErreurs :\n" + "\n".join(error_messages)
                
                reply = QMessageBox.question(
                    self, 
                    "Impression terminée", 
                    message + "\n\nVoulez-vous ouvrir le PDF ?",
                    QMessageBox.Yes | QMessageBox.No
                ) if pdf_filename else QMessageBox.information(self, "Impression terminée", message)
                
                if pdf_filename and reply == QMessageBox.Yes:
                    open_invoice(pdf_filename)
            else:
                QMessageBox.warning(self, "Erreur", "Aucune impression n'a réussi :\n" + "\n".join(error_messages))
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'impression : {str(e)}")


class SalesView(QWidget):
    """Vue complète pour la gestion des ventes"""
    
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.cart_items = []  # Panier en mémoire
        
        self.setWindowTitle("Gestion des Ventes")
        self.setGeometry(100, 100, 1200, 700)
        self.setup_ui()

    def setup_ui(self):
        """Configure l'interface utilisateur"""
        main_layout = QVBoxLayout()
        
        # Titre
        title = QLabel(f"Gestion des Ventes - {self.user['prenom_ut']} {self.user['nom_ut']}")
        title.setObjectName("title")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(title)
        
        # Onglets
        self.tabs = QTabWidget()
        
        # Onglet 1 : Nouvelle vente
        self.tab_new_sale = QWidget()
        self.setup_new_sale_tab()
        self.tabs.addTab(self.tab_new_sale, "🛒 Nouvelle Vente")
        
        # Onglet 2 : Ventes du jour
        self.tab_daily_sales = QWidget()
        self.setup_daily_sales_tab()
        self.tabs.addTab(self.tab_daily_sales, "📊 Ventes du Jour")
        
        # Onglet 3 : Historique ventes (si manager)
        if is_manager(self.user['id_ut']):
            # Toutes les ventes (manager)
            self.tab_all_sales = QWidget()
            self.setup_all_sales_tab()
            self.tabs.addTab(self.tab_all_sales, "📈 Toutes les Ventes")
            
            # Modifier une vente (manager)
            self.tab_modify_sales = QWidget()
            self.setup_modify_sales_tab()
            self.tabs.addTab(self.tab_modify_sales, "✏️ Modifier Une Vente")
        
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)
        
        # Charger les données
        self.refresh_daily_sales()
        if is_manager(self.user['id_ut']):
            self.refresh_all_sales()

    def setup_new_sale_tab(self):
        """Onglet pour créer une nouvelle vente"""
        layout = QVBoxLayout()
        
        # Section client
        client_section = QHBoxLayout()
        client_section.addWidget(QLabel("CLIENT"))
        client_layout = QFormLayout()
        
        self.client_nom = QLineEdit()
        self.client_prenom = QLineEdit()
        self.client_postnom = QLineEdit()
        self.client_phone = QLineEdit()
        
        client_layout.addRow("Nom :", self.client_nom)
        client_layout.addRow("Prénom :", self.client_prenom)
        client_layout.addRow("Post-nom :", self.client_postnom)
        client_layout.addRow("Téléphone :", self.client_phone)
        
        client_section.addLayout(client_layout)
        client_section.addStretch()
        layout.addLayout(client_section)
        
        # Section produits (panier)
        layout.addWidget(QLabel("PANIER"))
        
        # Ajouter produit
        add_product_layout = QHBoxLayout()
        
        self.product_combo = QComboBox()
        self.refresh_product_combo()
        add_product_layout.addWidget(QLabel("Produit :"))
        add_product_layout.addWidget(self.product_combo)
        
        self.quantity_spinbox = QSpinBox()
        self.quantity_spinbox.setMinimum(1)
        self.quantity_spinbox.setValue(1)
        add_product_layout.addWidget(QLabel("Quantité :"))
        add_product_layout.addWidget(self.quantity_spinbox)
        
        btn_add_product = QPushButton("Ajouter au Panier")
        btn_add_product.clicked.connect(self.add_to_cart)
        add_product_layout.addWidget(btn_add_product)
        add_product_layout.addStretch()
        
        layout.addLayout(add_product_layout)
        
        # Tableau du panier
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(5)
        self.cart_table.setHorizontalHeaderLabels(["Produit", "Prix", "Quantité", "Total", "Supprimer"])
        self.cart_table.setColumnWidth(0, 300)
        self.cart_table.setColumnWidth(1, 100)
        self.cart_table.setColumnWidth(2, 100)
        self.cart_table.setColumnWidth(3, 100)
        self.cart_table.setColumnWidth(4, 100)
        layout.addWidget(self.cart_table)
        
        # Total
        total_layout = QHBoxLayout()
        total_layout.addStretch()
        self.label_total = QLabel("TOTAL : 0,00 FC")
        self.label_total.setStyleSheet("font-size: 14px; font-weight: bold; color: green;")
        total_layout.addWidget(self.label_total)
        layout.addLayout(total_layout)
        
        # Section paiement
        payment_layout = QFormLayout()
        
        self.payment_mode = QComboBox()
        self.refresh_payment_modes()
        self.payment_mode.currentIndexChanged.connect(self.on_payment_mode_changed)
        payment_layout.addRow("Mode de paiement :", self.payment_mode)
        
        self.retrait_mode = QComboBox()
        self.retrait_mode.addItems(["IMMEDIAT", "ULTERIEUR"])
        payment_layout.addRow("Retrait :", self.retrait_mode)
        
        self.date_retrait = QDateEdit()
        self.date_retrait.setDate(QDate.currentDate())
        self.date_retrait.setEnabled(False)
        self.retrait_mode.currentTextChanged.connect(self.on_retrait_mode_changed)
        payment_layout.addRow("Date retrait :", self.date_retrait)
        
        # Section dette (si crédit seulement)
        self.label_debt_section = QLabel("--- Si DETTE/Crédit ---")
        self.label_debt_section.setStyleSheet("font-weight: bold; color: #e74c3c;")
        payment_layout.addRow(self.label_debt_section)
        
        self.date_echeance = QDateEdit()
        self.date_echeance.setDate(QDate.currentDate().addDays(7))
        self.date_echeance.setEnabled(False)
        payment_layout.addRow("Date échéance (crédit) :", self.date_echeance)
        
        self.debt_type_label = QLabel("Type de dette : ARGENT")
        self.debt_type_label.setEnabled(False)
        payment_layout.addRow(self.debt_type_label)
        
        layout.addLayout(payment_layout)
        
        # Boutons
        button_layout = QHBoxLayout()
        
        btn_clear = QPushButton("Effacer le panier")
        btn_clear.clicked.connect(self.clear_cart)
        button_layout.addWidget(btn_clear)
        
        btn_save = QPushButton("Enregistrer et Imprimer Facture")
        btn_save.setStyleSheet("background-color: green; color: white; font-weight: bold;")
        btn_save.clicked.connect(self.save_sale)
        button_layout.addWidget(btn_save)
        
        layout.addLayout(button_layout)
        
        self.tab_new_sale.setLayout(layout)

    def setup_daily_sales_tab(self):
        """Onglet des ventes du jour"""
        layout = QVBoxLayout()
        
        self.table_daily_sales = QTableWidget()
        self.table_daily_sales.setColumnCount(6)
        self.table_daily_sales.setHorizontalHeaderLabels([
            "ID Vente", "Client", "Mode Paiement", "Montant", "Retrait", "Détails"
        ])
        self.table_daily_sales.setColumnWidth(0, 80)
        self.table_daily_sales.setColumnWidth(1, 250)
        self.table_daily_sales.setColumnWidth(2, 150)
        self.table_daily_sales.setColumnWidth(3, 120)
        self.table_daily_sales.setColumnWidth(4, 120)
        self.table_daily_sales.setColumnWidth(5, 150)
        
        layout.addWidget(self.table_daily_sales)
        
        btn_refresh = QPushButton("Actualiser")
        btn_refresh.clicked.connect(self.refresh_daily_sales)
        layout.addWidget(btn_refresh)
        
        self.tab_daily_sales.setLayout(layout)

    def setup_all_sales_tab(self):
        """Onglet pour afficher toutes les ventes avec filtres (manager)"""
        layout = QVBoxLayout()
        
        # Titre
        title = QLabel("Toutes les Ventes")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)
        
        # Filtres
        filters_layout = QHBoxLayout()
        
        # Filtre vendeur/utilisateur
        filters_layout.addWidget(QLabel("Vendeur :"))
        self.filter_vendor = QComboBox()
        self.filter_vendor.addItem("TOUS", None)
        self.refresh_vendor_combo()
        self.filter_vendor.currentIndexChanged.connect(self.refresh_all_sales)
        filters_layout.addWidget(self.filter_vendor)
        
        # Filtre date début
        filters_layout.addWidget(QLabel("Du :"))
        self.filter_start_date = QDateEdit()
        self.filter_start_date.setDate(QDate.currentDate().addDays(-30))
        self.filter_start_date.dateChanged.connect(self.refresh_all_sales)
        filters_layout.addWidget(self.filter_start_date)
        
        # Filtre date fin
        filters_layout.addWidget(QLabel("Au :"))
        self.filter_end_date = QDateEdit()
        self.filter_end_date.setDate(QDate.currentDate())
        self.filter_end_date.dateChanged.connect(self.refresh_all_sales)
        filters_layout.addWidget(self.filter_end_date)
        
        # Bouton actualiser
        btn_refresh = QPushButton("🔄 Actualiser")
        btn_refresh.clicked.connect(self.refresh_all_sales)
        filters_layout.addWidget(btn_refresh)
        
        filters_layout.addStretch()
        layout.addLayout(filters_layout)
        layout.addSpacing(10)
        
        # Tableau des ventes
        self.table_all_sales = QTableWidget()
        self.table_all_sales.setColumnCount(8)
        self.table_all_sales.setHorizontalHeaderLabels([
            "ID Vente", "Date", "Vendeur", "Client", "Mode Paiement", "Montant", "Détails", "Modifier"
        ])
        self.table_all_sales.setColumnWidth(0, 80)
        self.table_all_sales.setColumnWidth(1, 120)
        self.table_all_sales.setColumnWidth(2, 150)
        self.table_all_sales.setColumnWidth(3, 200)
        self.table_all_sales.setColumnWidth(4, 120)
        self.table_all_sales.setColumnWidth(5, 120)
        self.table_all_sales.setColumnWidth(6, 120)
        self.table_all_sales.setColumnWidth(7, 120)
        
        layout.addWidget(self.table_all_sales)
        
        self.tab_all_sales.setLayout(layout)
    
    def refresh_vendor_combo(self):
        """Remplit le combo vendeur avec tous les utilisateurs"""
        users = get_all_users()
        for user in users:
            nom_complet = f"{user['prenom_ut']} {user['nom_ut']}"
            self.filter_vendor.addItem(nom_complet, user['id_ut'])
    
    def refresh_all_sales(self):
        """Actualise le tableau de toutes les ventes avec filtres"""
        all_sales = get_all_sales_detailed()
        
        # Appliquer les filtres
        vendor_id = self.filter_vendor.currentData()
        start_date = self.filter_start_date.date()
        end_date = self.filter_end_date.date()
        
        filtered_sales = []
        for sale in all_sales:
            # Filtre vendeur
            if vendor_id is not None and sale.get('id_ut') != vendor_id:
                continue
            
            # Filtre date
            sale_date = QDate.fromString(str(sale['date_vente']), "yyyy-MM-dd")
            if not (start_date <= sale_date <= end_date):
                continue
            
            filtered_sales.append(sale)
        
        # Remplir le tableau
        self.table_all_sales.setRowCount(len(filtered_sales))
        
        for row, sale in enumerate(filtered_sales):
            self.table_all_sales.setItem(row, 0, QTableWidgetItem(str(sale['id_vente'])))
            self.table_all_sales.setItem(row, 1, QTableWidgetItem(str(sale['date_vente'])))
            self.table_all_sales.setItem(row, 2, QTableWidgetItem(sale.get('vendeur', 'N/A')))
            self.table_all_sales.setItem(row, 3, QTableWidgetItem(sale.get('client', 'N/A')))
            self.table_all_sales.setItem(row, 4, QTableWidgetItem(sale.get('mode_paiement', 'N/A')))
            
            montant = sale['montant_total'] or 0
            self.table_all_sales.setItem(row, 5, QTableWidgetItem(format_currency(montant)))
            
            # Bouttons d'action
            # Bouton voir les détails
            btn_details = QPushButton("👁️ Voir")
            btn_details.setStyleSheet("background-color: #9b59b6; color: white;")
            btn_details.clicked.connect(lambda checked, sid=sale['id_vente']: self.show_sale_details(sid))
            self.table_all_sales.setCellWidget(row, 6, btn_details)
            
            # Bouton modifier
            btn_modify = QPushButton("✏️ Modifier")
            btn_modify.setStyleSheet("background-color: #3498db; color: white;")
            btn_modify.clicked.connect(lambda checked, sid=sale['id_vente']: self.load_sale_to_edit_from_all_sales(sid))
            self.table_all_sales.setCellWidget(row, 7, btn_modify)

    def load_sale_to_edit_from_all_sales(self, sale_id):
        """Charge une vente depuis l'onglet toutes les ventes et navigue vers l'onglet modification"""
        # Remplir le champ ID dans l'onglet modification
        self.sale_id_input.setText(str(sale_id))
        
        # Charger la vente
        self.load_sale_for_edit()
        
        # Changer vers l'onglet modification
        self.tabs.setCurrentWidget(self.tab_modify_sales)

    def setup_modify_sales_tab(self):
        """Onglet pour modifier une vente (manager)"""
        layout = QVBoxLayout()
        
        # Titre
        title = QLabel("Modifier une Vente (Manager)")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)
        
        # Recherche de vente
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("ID Vente :"))
        self.sale_id_input = QLineEdit()
        search_layout.addWidget(self.sale_id_input)
        
        btn_search = QPushButton("Charger")
        btn_search.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn_search.clicked.connect(self.load_sale_for_edit)
        search_layout.addWidget(btn_search)
        search_layout.addStretch()
        
        layout.addLayout(search_layout)
        layout.addSpacing(15)
        
        # Affichage de la vente avec deux sections : infos et modification
        self.sale_edit_container = QVBoxLayout()
        
        # Section infos (non-éditable)
        self.info_group = QGroupBox("Informations de la Vente")
        self.info_group.setStyleSheet("""QGroupBox {
            font-weight: bold;
            border: 2px solid #95a5a6;
            border-radius: 5px;
            margin-top: 1ex;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 10px 0 10px;
        }""")
        self.info_layout = QFormLayout()
        self.info_group.setLayout(self.info_layout)
        self.sale_edit_container.addWidget(self.info_group)
        
        # Section modification
        self.edit_group = QGroupBox("Éditer la Vente")
        self.edit_group.setStyleSheet("""QGroupBox {
            font-weight: bold;
            border: 2px solid #3498db;
            border-radius: 5px;
            margin-top: 1ex;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 10px 0 10px;
        }""")
        self.edit_form_layout = QFormLayout()
        self.edit_group.setLayout(self.edit_form_layout)
        self.sale_edit_container.addWidget(self.edit_group)
        
        layout.addLayout(self.sale_edit_container)
        layout.addSpacing(10)
        
        # Boutons d'action
        buttons_layout = QHBoxLayout()
        
        self.btn_save = QPushButton("✓ Enregistrer les modifications")
        self.btn_save.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 10px;")
        self.btn_save.clicked.connect(self.save_sale_modifications)
        buttons_layout.addWidget(self.btn_save)
        
        self.btn_cancel = QPushButton("✗ Annuler")
        self.btn_cancel.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold; padding: 10px;")
        self.btn_cancel.clicked.connect(self.clear_sale_edit)
        buttons_layout.addWidget(self.btn_cancel)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        layout.addStretch()
        self.tab_modify_sales.setLayout(layout)
        
        # Masquer les boutons et groupes au départ
        self.info_group.hide()
        self.edit_group.hide()
        self.btn_save.hide()
        self.btn_cancel.hide()

    def refresh_product_combo(self):
        """Met à jour la liste des produits"""
        products = get_all_products()
        self.product_combo.clear()
        
        for product in products:
            stock_info = f" (Stock: {product['en_stock']})"
            text = f"{product['nom_pr']} - {product['prix_carton']} FC{stock_info}"
            self.product_combo.addItem(text, product['id_pr'])

    def refresh_payment_modes(self):
        """Met à jour les modes de paiement"""
        modes = get_all_payment_modes()
        self.payment_mode.clear()
        
        for mode in modes:
            self.payment_mode.addItem(mode['libelle_mode'], mode['id_mode'])

    def add_to_cart(self):
        """Ajoute un produit au panier"""
        if self.product_combo.count() == 0:
            QMessageBox.warning(self, "Erreur", "Aucun produit disponible")
            return
        
        product_id = self.product_combo.currentData()
        quantity = self.quantity_spinbox.value()
        
        # Récupérer les infos du produit
        product = None
        products = get_all_products()
        for p in products:
            if p['id_pr'] == product_id:
                product = p
                break
        
        if not product:
            QMessageBox.warning(self, "Erreur", "Produit non trouvé")
            return
        
        if product['en_stock'] < quantity:
            QMessageBox.warning(self, "Stock insuffisant", 
                              f"Seulement {product['en_stock']} articles disponibles")
            return
        
        # Ajouter au panier
        # Chercher si le produit existe déjà dans le panier
        found = False
        for item in self.cart_items:
            if item['product_id'] == product_id:
                # Augmenter la quantité
                item['quantity'] += quantity
                found = True
                break
        if not found:
            self.cart_items.append({
                'product_id': product_id,
                'nom': product['nom_pr'],
                'price': product['prix_carton'],
                'quantity': quantity
            })
        
        self.update_cart_display()
        self.quantity_spinbox.setValue(1)

    def update_cart_display(self):
        """Actualise l'affichage du panier"""
        self.cart_table.setRowCount(len(self.cart_items))
        
        total = 0
        for row, item in enumerate(self.cart_items):
            item_total = item['price'] * item['quantity']
            total += item_total
            
            self.cart_table.setItem(row, 0, QTableWidgetItem(item['nom']))
            self.cart_table.setItem(row, 1, QTableWidgetItem(format_currency(item['price'])))
            self.cart_table.setItem(row, 2, QTableWidgetItem(str(item['quantity'])))
            self.cart_table.setItem(row, 3, QTableWidgetItem(format_currency(item_total)))
            
            btn_remove = QPushButton("❌")
            btn_remove.clicked.connect(lambda checked, r=row: self.remove_from_cart(r))
            self.cart_table.setCellWidget(row, 4, btn_remove)
        
        self.label_total.setText(f"TOTAL : {format_currency(total)}")

    def remove_from_cart(self, row):
        """Supprime un article du panier"""
        self.cart_items.pop(row)
        self.update_cart_display()

    def clear_cart(self):
        """Vide le panier"""
        self.cart_items.clear()
        self.update_cart_display()

    def on_retrait_mode_changed(self):
        """Active/désactive le champ date de retrait"""
        self.date_retrait.setEnabled(self.retrait_mode.currentText() == "ULTERIEUR")

    def on_payment_mode_changed(self):
        """Active/désactive les champs de dette selon le mode de paiement"""
        payment_mode_id = self.payment_mode.currentData()
        is_credit = is_credit_payment(payment_mode_id)
        
        self.date_echeance.setEnabled(is_credit)
        self.debt_type_label.setEnabled(is_credit)
        
        if is_credit:
            self.label_debt_section.setText("--- DETTE/CRÉDIT : Remplir la date d'échéance ---")
            self.label_debt_section.setStyleSheet("font-weight: bold; color: #e74c3c;")
        else:
            self.label_debt_section.setText("--- Pas de dette pour ce mode de paiement ---")
            self.label_debt_section.setStyleSheet("font-weight: bold; color: #27ae60;")

    def save_sale(self):
        """Enregistre la vente"""
        # Validation
        if not self.client_nom.text().strip():
            QMessageBox.warning(self, "Erreur", "Veuillez entrer le nom du client")
            return
        
        if not self.cart_items:
            QMessageBox.warning(self, "Erreur", "Le panier est vide")
            return
        
        # Gérer la création/sélection du client
        phone = self.client_phone.text().strip()
        nom = self.client_nom.text().strip()
        prenom = self.client_prenom.text().strip()
        postnom = self.client_postnom.text().strip()

        client_id = None
        if phone:
            existing_clients = get_clients_by_phone(phone)
            if existing_clients:
                # Vérifier si les informations sont exactement les mêmes pour au moins un
                exact_match = None
                for c in existing_clients:
                    c_nom = c['nom_client'] or ""
                    c_prenom = c['prenom_client'] or ""
                    if c_nom.lower() == nom.lower() and c_prenom.lower() == prenom.lower():
                        exact_match = c['id_client']
                        break
                
                if exact_match and len(existing_clients) == 1:
                    # Un seul client correspond exactement, on le réutilise silencieusement
                    client_id = exact_match
                else:
                    # Demander au vendeur de choisir
                    dialog = ClientSelectionDialog(
                        existing_clients=existing_clients,
                        new_client_data={'nom': nom, 'prenom': prenom, 'postnom': postnom},
                        parent=self
                    )
                    if dialog.exec() == QDialog.Accepted:
                        action, selected_id = dialog.get_selection()
                        if action == "NEW":
                            client_id = create_client_direct(nom, prenom, postnom, phone)
                        elif action == "EXISTING":
                            client_id = selected_id
                    else:
                        return # Annulé par l'utilisateur
            else:
                client_id = create_client_direct(nom, prenom, postnom, phone)
        else:
            client_id = create_client_direct(nom, prenom, postnom, "")
        
        if not client_id:
            QMessageBox.critical(self, "Erreur", "Erreur lors de la création/sélection du client")
            return
        
        # Créer la vente
        sale_id = create_sale(
            client_id,
            self.user['id_ut'],
            self.payment_mode.currentData(),
            self.cart_items,
            self.retrait_mode.currentText(),
            self.date_retrait.date().toString("yyyy-MM-dd") if self.retrait_mode.currentText() == "ULTERIEUR" else None
        )
        
        if not sale_id:
            QMessageBox.critical(self, "Erreur", "Erreur lors de l'enregistrement de la vente")
            return
        
        # Si crédit (mode DETTE), créer une dette
        payment_mode_id = self.payment_mode.currentData()
        if is_credit_payment(payment_mode_id):
            total = sum(item['price'] * item['quantity'] for item in self.cart_items)
            debt_id = create_debt(sale_id, total, "ARGENT", self.date_echeance.date().toString("yyyy-MM-dd"))
            if debt_id:
                QMessageBox.information(self, "Crédit", f"Vente #{sale_id} enregistrée en crédit (Dette #{debt_id})")
            else:
                QMessageBox.warning(self, "Avertissement", f"Vente #{sale_id} créée mais la dette n'a pas pu être enregistrée !")
        
        # Générer la facture avec options d'impression
        sale_data = get_sale_by_id(sale_id)
        if sale_data:
            # Ajouter info paiement si crédit
            if is_credit_payment(payment_mode_id):
                total = sum(item['price'] * item['quantity'] for item in self.cart_items)
                sale_data['montant_paye'] = 0
                sale_data['montant_restant'] = total
            
            # Demander les options d'impression
            print_options = ask_print_options(self, "Impression de facture", "Vente enregistrée avec succès !\n\nChoisissez les options d'impression :")
            
            if print_options is not None:  # Pas annulé
                success_messages = []
                error_messages = []
                
                # Générer PDF si demandé
                pdf_filename = None
                if print_options['print_pdf']:
                    pdf_filename = f"factures/facture_{sale_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    import os
                    os.makedirs("factures", exist_ok=True)
                    
                    if generate_invoice(sale_data, pdf_filename):
                        success_messages.append(f"✓ PDF généré: {pdf_filename}")
                    else:
                        error_messages.append("❌ Erreur lors de la génération du PDF")
                
                # Imprimer sur thermique si demandé
                if print_options['print_thermal']:
                    thermal_width = print_options.get('thermal_width', '80mm')
                    if print_thermal_receipt(sale_data, thermal_width):
                        success_messages.append(f"✓ Reçu thermique imprimé ({thermal_width})")
                    else:
                        error_messages.append("❌ Erreur lors de l'impression thermique")
                
                # Afficher les résultats
                if success_messages:
                    message = "Impression terminée :\n\n" + "\n".join(success_messages)
                    if error_messages:
                        message += "\n\nErreurs :\n" + "\n".join(error_messages)
                    
                    reply = QMessageBox.question(
                        self, 
                        "Impression terminée", 
                        message + "\n\nVoulez-vous ouvrir le PDF ?",
                        QMessageBox.Yes | QMessageBox.No
                    ) if pdf_filename else QMessageBox.information(self, "Impression terminée", message)
                    
                    if pdf_filename and reply == QMessageBox.Yes:
                        open_invoice(pdf_filename)
                elif error_messages:
                    QMessageBox.warning(self, "Erreur d'impression", "Erreurs lors de l'impression :\n" + "\n".join(error_messages))
        
        # Message de confirmation finalisé
        if is_credit_payment(payment_mode_id):
            final_msg = f"✓ Vente #{sale_id} enregistrée\n✓ Crédit créé (à récupérer avant {self.date_echeance.date().toString('dd/MM/yyyy')})"
        else:
            final_msg = f"✓ Vente #{sale_id} enregistrée avec succès !"
        
        QMessageBox.information(self, "Succès", final_msg)
        
        # Réinitialiser le formulaire
        self.client_nom.clear()
        self.client_prenom.clear()
        self.client_postnom.clear()
        self.client_phone.clear()
        self.clear_cart()
        
        # Actualiser les ventes du jour
        self.refresh_daily_sales()

    def refresh_daily_sales(self):
        """Actualise les ventes du jour"""
        today = QDate.currentDate().toString("yyyy-MM-dd")
        sales = get_sales_by_vendor_id(self.user['id_ut'], today, today)
        
        self.table_daily_sales.setRowCount(len(sales))
        
        for row, sale in enumerate(sales):
            self.table_daily_sales.setItem(row, 0, QTableWidgetItem(str(sale['id_vente'])))
            self.table_daily_sales.setItem(row, 1, QTableWidgetItem(sale['client'] or "N/A"))
            self.table_daily_sales.setItem(row, 2, QTableWidgetItem(sale['mode_paiement'] or "N/A"))
            
            montant = sale['montant_total'] or 0
            self.table_daily_sales.setItem(row, 3, QTableWidgetItem(format_currency(montant)))
            
            btn_details = QPushButton("Voir")
            btn_details.clicked.connect(lambda checked, sid=sale['id_vente']: self.show_sale_details(sid))
            self.table_daily_sales.setCellWidget(row, 5, btn_details)

    def show_sale_details(self, sale_id):
        """Affiche les détails d'une vente dans une boîte de dialogue améliorée"""
        dialog = SaleDetailsDialog(sale_id, self)
        dialog.exec()

    def load_sale_for_edit(self):
        """Charge une vente pour édition (manager)"""
        sale_id_text = self.sale_id_input.text().strip()
        if not sale_id_text:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer un ID de vente")
            return
        
        try:
            sale_id = int(sale_id_text)
        except ValueError:
            QMessageBox.warning(self, "Erreur", "L'ID de vente doit être un nombre")
            return
        
        sale = get_sale_by_id(sale_id)
        if not sale:
            QMessageBox.warning(self, "Erreur", f"Vente #{sale_id} non trouvée")
            return
        
        # Stocker la vente actuelle
        self.current_sale_edit = sale
        
        # Nettoyer les layouts précédents
        while self.info_layout.count():
            widget = self.info_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()
        
        while self.edit_form_layout.count():
            widget = self.edit_form_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()
        
        # Remplir la section informations
        id_label = QLabel(f"#{sale['id_vente']}")
        id_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
        self.info_layout.addRow("ID Vente :", id_label)
        
        self.info_layout.addRow("Date :", QLabel(str(sale['date_vente'])))
        self.info_layout.addRow("Client :", QLabel(sale['client'] or "N/A"))
        self.info_layout.addRow("Vendeur :", QLabel(sale['vendeur'] or "N/A"))
        
        # Montant total
        total = sum(a['prix_vente'] * a['quantite'] for a in sale['articles'])
        montant_label = QLabel(format_currency(total))
        montant_label.setStyleSheet("font-weight: bold; color: #27ae60;")
        self.info_layout.addRow("Montant Total :", montant_label)
        
        # Nombre d'articles
        nb_articles = len(sale['articles'])
        self.info_layout.addRow("Nombre d'articles :", QLabel(str(nb_articles)))
        
        # Section édition
        # Mode de paiement
        self.edit_payment_mode = QComboBox()
        self.refresh_payment_modes()  # Remplir les modes
        # Sélectionner le mode actuel
        for i in range(self.edit_payment_mode.count()):
            if self.edit_payment_mode.itemData(i) == sale['id_mode']:
                self.edit_payment_mode.setCurrentIndex(i)
                break
        self.edit_form_layout.addRow("Mode de Paiement :", self.edit_payment_mode)
        
        # Statut retrait
        self.edit_retrait_status = QComboBox()
        self.edit_retrait_status.addItems(["IMMEDIAT", "ULTERIEUR"])
        self.edit_retrait_status.setCurrentText(sale['statut_retrait'] or "IMMEDIAT")
        self.edit_retrait_status.currentTextChanged.connect(self.on_edit_retrait_changed)
        self.edit_form_layout.addRow("Statut Retrait :", self.edit_retrait_status)
        
        # Date de retrait
        self.edit_date_retrait = QDateEdit()
        if sale['date_retrait_effective']:
            self.edit_date_retrait.setDate(QDate.fromString(str(sale['date_retrait_effective']), "yyyy-MM-dd"))
        else:
            self.edit_date_retrait.setDate(QDate.currentDate())
        
        # Activer la date si retrait ultérieur
        self.edit_date_retrait.setEnabled(sale['statut_retrait'] == "ULTERIEUR")
        self.edit_form_layout.addRow("Date Retrait :", self.edit_date_retrait)
        
        # Afficher les groupes et boutons
        self.info_group.show()
        self.edit_group.show()
        self.btn_save.show()
        self.btn_cancel.show()
        
        QMessageBox.information(self, "Succès", f"Vente #{sale_id} chargée. Vous pouvez maintenant la modifier.")
    
    def on_edit_retrait_changed(self):
        """Active/désactive la date de retrait selon le statut"""
        self.edit_date_retrait.setEnabled(self.edit_retrait_status.currentText() == "ULTERIEUR")
    
    def save_sale_modifications(self):
        """Sauvegarde les modifications de la vente"""
        if not hasattr(self, 'current_sale_edit'):
            QMessageBox.warning(self, "Erreur", "Aucune vente chargée")
            return
        
        sale_id = self.current_sale_edit['id_vente']
        payment_mode_id = self.edit_payment_mode.currentData()
        retrait_status = self.edit_retrait_status.currentText()
        date_retrait = None
        
        if retrait_status == "ULTERIEUR":
            date_retrait = self.edit_date_retrait.date().toString("yyyy-MM-dd")
        
        # Appeler la fonction update_sale de la base de données
        if update_sale(
            sale_id,
            payment_mode_id=payment_mode_id,
            statut_retrait=retrait_status,
            date_retrait=date_retrait
        ):
            QMessageBox.information(
                self,
                "Succès",
                f"Vente #{sale_id} modifiée avec succès !\n\n"
                f"Mode de paiement : {self.edit_payment_mode.currentText()}\n"
                f"Statut retrait : {retrait_status}\n"
                f"Date retrait : {date_retrait or 'N/A'}"
            )
            self.clear_sale_edit()
        else:
            QMessageBox.critical(self, "Erreur", "Erreur lors de la mise à jour de la vente")
    
    def clear_sale_edit(self):
        """Réinitialise le formulaire d'édition"""
        self.sale_id_input.clear()
        self.info_group.hide()
        self.edit_group.hide()
        self.btn_save.hide()
        self.btn_cancel.hide()
        
        # Nettoyer les layouts
        while self.info_layout.count():
            widget = self.info_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()
        
        while self.edit_form_layout.count():
            widget = self.edit_form_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()
