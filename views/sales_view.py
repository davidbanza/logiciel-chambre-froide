from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QFormLayout,
                             QLineEdit, QComboBox, QPushButton, QLabel, QMessageBox,
                             QTableWidget, QTableWidgetItem, QSpinBox, QDateEdit, QDialog,
                             QRadioButton, QButtonGroup)
from PySide6.QtCore import Qt, QDate
from datetime import datetime, timedelta
from database import (get_all_products, get_all_payment_modes, create_or_get_client,
                      create_sale, get_sales_by_vendor_id, get_sale_by_id, 
                      update_sale, is_manager, get_all_debts, update_debt_status, create_debt, is_credit_payment,
                      get_clients_by_phone, create_client_direct)
from invoice_generator import generate_invoice, open_invoice


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
            self.tab_modify_sales = QWidget()
            self.setup_modify_sales_tab()
            self.tabs.addTab(self.tab_modify_sales, "✏️ Modifier Une Vente")
        
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)
        
        # Charger les données
        self.refresh_daily_sales()

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
        self.label_total = QLabel("TOTAL : 0.00 FC")
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

    def setup_modify_sales_tab(self):
        """Onglet pour modifier une vente (manager)"""
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Modifier une vente (Manager uniquement)"))
        
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("ID Vente :"))
        self.sale_id_input = QLineEdit()
        search_layout.addWidget(self.sale_id_input)
        
        btn_search = QPushButton("Charger")
        btn_search.clicked.connect(self.load_sale_for_edit)
        search_layout.addWidget(btn_search)
        
        layout.addLayout(search_layout)
        
        # Affichage de la vente
        self.modify_layout = QFormLayout()
        layout.addLayout(self.modify_layout)
        
        self.tab_modify_sales.setLayout(layout)

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
            self.cart_table.setItem(row, 1, QTableWidgetItem(f"{item['price']:.2f}"))
            self.cart_table.setItem(row, 2, QTableWidgetItem(str(item['quantity'])))
            self.cart_table.setItem(row, 3, QTableWidgetItem(f"{item_total:.2f}"))
            
            btn_remove = QPushButton("❌")
            btn_remove.clicked.connect(lambda checked, r=row: self.remove_from_cart(r))
            self.cart_table.setCellWidget(row, 4, btn_remove)
        
        self.label_total.setText(f"TOTAL : {total:.2f} FC")

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
        
        # Générer la facture
        sale_data = get_sale_by_id(sale_id)
        if sale_data:
            # Ajouter info paiement si crédit
            if is_credit_payment(payment_mode_id):
                total = sum(item['price'] * item['quantity'] for item in self.cart_items)
                sale_data['montant_paye'] = 0
                sale_data['montant_restant'] = total
            
            # Préparer les données pour la facture
            invoice_filename = f"factures/facture_{sale_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            # Créer le dossier si nécessaire
            import os
            os.makedirs("factures", exist_ok=True)
            
            if generate_invoice(sale_data, invoice_filename):
                reply = QMessageBox.question(
                    self, 
                    "Facture générée", 
                    "Facture générée avec succès !\n\nVoulez-vous l'ouvrir ?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    open_invoice(invoice_filename)
        
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
            self.table_daily_sales.setItem(row, 3, QTableWidgetItem(f"{montant:.2f}"))
            
            btn_details = QPushButton("Voir")
            btn_details.clicked.connect(lambda checked, sid=sale['id_vente']: self.show_sale_details(sid))
            self.table_daily_sales.setCellWidget(row, 5, btn_details)

    def show_sale_details(self, sale_id):
        """Affiche les détails d'une vente"""
        sale = get_sale_by_id(sale_id)
        if not sale:
            QMessageBox.warning(self, "Erreur", "Vente non trouvée")
            return
        
        msg = f"""
ID Vente: {sale['id_vente']}
Date: {sale['date_vente']}
Client: {sale['client']}
Vendeur: {sale['vendeur']}
Mode Paiement: {sale['mode_paiement']}
Retrait: {sale['statut_retrait']}

Articles:
"""
        total = 0
        for article in sale['articles']:
            subtotal = article['prix_vente'] * article['quantite']
            total += subtotal
            msg += f"\n- {article['nom_pr']}: {article['quantite']} x {article['prix_vente']:.2f} = {subtotal:.2f}"
        
        msg += f"\n\nTOTAL: {total:.2f} FC"
        
        QMessageBox.information(self, "Détails de la Vente", msg)

    def load_sale_for_edit(self):
        """Charge une vente pour édition (manager)"""
        sale_id = self.sale_id_input.text()
        if not sale_id:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer un ID de vente")
            return
        
        sale = get_sale_by_id(int(sale_id))
        if not sale:
            QMessageBox.warning(self, "Erreur", "Vente non trouvée")
            return
        
        # Afficher les détails en formulaire
        # (À améliorer avec possibilité de modification)
        msg = f"ID Vente: {sale['id_vente']}\nClient: {sale['client']}\nMontant: {sum(a['prix_vente'] * a['quantite'] for a in sale['articles']):.2f}"
        QMessageBox.information(self, "Vente chargée", msg)
