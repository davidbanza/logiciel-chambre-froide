from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                             QTableWidget, QTableWidgetItem, QLabel, QPushButton,
                             QDateEdit, QComboBox, QMessageBox)
from PySide6.QtCore import Qt, QDate
from database import (get_total_sales_stats, get_sales_by_vendor, 
                      get_sales_by_payment_mode, get_debts_summary, 
                      get_all_sales_detailed, get_sales_by_date_range, is_manager,
                      get_all_payments_with_details)
from utils import format_currency
from invoice_generator import (get_invoice_storage_path, build_invoice_filename)


class ReportsView(QWidget):
    """Vue pour les rapports et bilans des ventes (Manager uniquement)"""
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        
        # Vérifier si l'utilisateur est manager
        if not is_manager(current_user['id_ut']):
            QMessageBox.warning(self, "Accès refusé", 
                              "Seuls les managers peuvent consulter les rapports")
            return
        
        self.setWindowTitle("Rapports & Bilans des Ventes")
        self.setGeometry(100, 100, 1200, 700)
        self.setup_ui()

    def setup_ui(self):
        """Configure l'interface utilisateur"""
        main_layout = QVBoxLayout()
        
        # Titre
        title = QLabel("Rapports & Bilans des Ventes")
        title.setObjectName("title")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(title)
        
        # Onglets pour différentes vues
        self.tabs = QTabWidget()
        
        # Onglet 1 : Statistiques générales
        self.tab_stats = QWidget()
        self.setup_general_stats_tab()
        self.tabs.addTab(self.tab_stats, "📊 Statistiques Générales")
        
        # Onglet 2 : Ventes par vendeur
        self.tab_by_vendor = QWidget()
        self.setup_by_vendor_tab()
        self.tabs.addTab(self.tab_by_vendor, "👥 Ventes par Vendeur")
        
        # Onglet 3 : Ventes par mode de paiement
        self.tab_by_payment = QWidget()
        self.setup_by_payment_tab()
        self.tabs.addTab(self.tab_by_payment, "💳 Ventes par Mode Paiement")
        
        # Onglet 4 : Gestion des dettes
        self.tab_debts = QWidget()
        self.setup_debts_tab()
        self.tabs.addTab(self.tab_debts, "💰 Résumé des Dettes")
        
        # Onglet 5 : Toutes les ventes
        self.tab_all_sales = QWidget()
        self.setup_all_sales_tab()
        self.tabs.addTab(self.tab_all_sales, "📋 Toutes les Ventes")
        
        # Onglet 6 : Historique des paiements
        self.tab_payments_history = QWidget()
        self.setup_payments_history_tab()
        self.tabs.addTab(self.tab_payments_history, "💰 Historique des Paiements")
        
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)
        
        # Charger les données
        self.refresh_all_data()

    def setup_general_stats_tab(self):
        """Onglet des statistiques générales"""
        layout = QVBoxLayout()
        
        # Filtres de date
        filters_layout = QHBoxLayout()
        filters_layout.addWidget(QLabel("Période :"))
        self.stats_date_start = QDateEdit()
        self.stats_date_start.setDate(QDate.currentDate().addMonths(-1))
        self.stats_date_start.dateChanged.connect(self.load_general_stats)
        filters_layout.addWidget(self.stats_date_start)
        
        filters_layout.addWidget(QLabel("à"))
        self.stats_date_end = QDateEdit()
        self.stats_date_end.setDate(QDate.currentDate())
        self.stats_date_end.dateChanged.connect(self.load_general_stats)
        filters_layout.addWidget(self.stats_date_end)
        
        btn_refresh_stats = QPushButton("🔄 Actualiser")
        btn_refresh_stats.clicked.connect(self.load_general_stats)
        filters_layout.addWidget(btn_refresh_stats)
        
        filters_layout.addStretch()
        layout.addLayout(filters_layout)
        
        # Conteneur pour les statistiques en cartes
        stats_layout = QHBoxLayout()
        
        self.label_total_sales = QLabel()
        self.label_total_clients = QLabel()
        self.label_total_vendors = QLabel()
        self.label_total_amount = QLabel()
        
        # Styliser les labels
        for label in [self.label_total_sales, self.label_total_clients, 
                      self.label_total_vendors, self.label_total_amount]:
            label.setStyleSheet("""
                QLabel {
                    background-color: #f0f0f0;
                    padding: 20px;
                    border-radius: 5px;
                    font-size: 14px;
                    font-weight: bold;
                    border: 1px solid #ddd;
                }
            """)
        
        stats_layout.addWidget(self.label_total_sales)
        stats_layout.addWidget(self.label_total_clients)
        stats_layout.addWidget(self.label_total_vendors)
        stats_layout.addWidget(self.label_total_amount)
        
        layout.addLayout(stats_layout)
        layout.addStretch()
        self.tab_stats.setLayout(layout)

    def setup_by_vendor_tab(self):
        """Onglet des ventes par vendeur"""
        layout = QVBoxLayout()
        
        # Filtres de date
        filters_layout = QHBoxLayout()
        filters_layout.addWidget(QLabel("Période :"))
        self.vendor_date_start = QDateEdit()
        self.vendor_date_start.setDate(QDate.currentDate().addMonths(-1))
        self.vendor_date_start.dateChanged.connect(self.load_by_vendor_data)
        filters_layout.addWidget(self.vendor_date_start)
        
        filters_layout.addWidget(QLabel("à"))
        self.vendor_date_end = QDateEdit()
        self.vendor_date_end.setDate(QDate.currentDate())
        self.vendor_date_end.dateChanged.connect(self.load_by_vendor_data)
        filters_layout.addWidget(self.vendor_date_end)
        
        btn_refresh_vendor = QPushButton("🔄 Actualiser")
        btn_refresh_vendor.clicked.connect(self.load_by_vendor_data)
        filters_layout.addWidget(btn_refresh_vendor)
        
        filters_layout.addStretch()
        layout.addLayout(filters_layout)
        
        self.table_by_vendor = QTableWidget()
        self.table_by_vendor.setColumnCount(4)
        self.table_by_vendor.setHorizontalHeaderLabels([
            "Vendeur", "Nombre de Ventes", "Montant Total", "Montant Moyen"
        ])
        self.table_by_vendor.setColumnWidth(0, 250)
        self.table_by_vendor.setColumnWidth(1, 150)
        self.table_by_vendor.setColumnWidth(2, 150)
        self.table_by_vendor.setColumnWidth(3, 150)
        
        layout.addWidget(self.table_by_vendor)
        
        self.tab_by_vendor.setLayout(layout)

    def setup_by_payment_tab(self):
        """Onglet des ventes par mode de paiement"""
        layout = QVBoxLayout()
        
        # Filtres de date
        filters_layout = QHBoxLayout()
        filters_layout.addWidget(QLabel("Période :"))
        self.payment_date_start = QDateEdit()
        self.payment_date_start.setDate(QDate.currentDate().addMonths(-1))
        self.payment_date_start.dateChanged.connect(self.load_by_payment_data)
        filters_layout.addWidget(self.payment_date_start)
        
        filters_layout.addWidget(QLabel("à"))
        self.payment_date_end = QDateEdit()
        self.payment_date_end.setDate(QDate.currentDate())
        self.payment_date_end.dateChanged.connect(self.load_by_payment_data)
        filters_layout.addWidget(self.payment_date_end)
        
        btn_refresh_payment = QPushButton("🔄 Actualiser")
        btn_refresh_payment.clicked.connect(self.load_by_payment_data)
        filters_layout.addWidget(btn_refresh_payment)
        
        filters_layout.addStretch()
        layout.addLayout(filters_layout)
        
        self.table_by_payment = QTableWidget()
        self.table_by_payment.setColumnCount(4)
        self.table_by_payment.setHorizontalHeaderLabels([
            "Mode de Paiement", "Nombre de Ventes", "Montant Total", "Montant Moyen"
        ])
        self.table_by_payment.setColumnWidth(0, 250)
        self.table_by_payment.setColumnWidth(1, 150)
        self.table_by_payment.setColumnWidth(2, 150)
        self.table_by_payment.setColumnWidth(3, 150)
        
        layout.addWidget(self.table_by_payment)
        
        self.tab_by_payment.setLayout(layout)

    def setup_debts_tab(self):
        """Onglet de gestion des dettes"""
        layout = QVBoxLayout()
        
        # Filtres de date
        filters_layout = QHBoxLayout()
        filters_layout.addWidget(QLabel("Période :"))
        self.debts_date_start = QDateEdit()
        self.debts_date_start.setDate(QDate.currentDate().addMonths(-1))
        self.debts_date_start.dateChanged.connect(self.load_debts_data)
        filters_layout.addWidget(self.debts_date_start)
        
        filters_layout.addWidget(QLabel("à"))
        self.debts_date_end = QDateEdit()
        self.debts_date_end.setDate(QDate.currentDate())
        self.debts_date_end.dateChanged.connect(self.load_debts_data)
        filters_layout.addWidget(self.debts_date_end)
        
        btn_refresh_debts = QPushButton("🔄 Actualiser")
        btn_refresh_debts.clicked.connect(self.load_debts_data)
        filters_layout.addWidget(btn_refresh_debts)
        
        filters_layout.addStretch()
        layout.addLayout(filters_layout)
        
        self.table_debts = QTableWidget()
        self.table_debts.setColumnCount(4)
        self.table_debts.setHorizontalHeaderLabels([
            "Statut", "Type de Dette", "Nombre de Dettes", "Montant Total"
        ])
        self.table_debts.setColumnWidth(0, 150)
        self.table_debts.setColumnWidth(1, 150)
        self.table_debts.setColumnWidth(2, 200)
        self.table_debts.setColumnWidth(3, 150)
        
        layout.addWidget(self.table_debts)
        
        self.tab_debts.setLayout(layout)

    def setup_all_sales_tab(self):
        """Onglet de toutes les ventes"""
        layout = QVBoxLayout()
        
        # Filtres de date
        filters_layout = QHBoxLayout()
        filters_layout.addWidget(QLabel("Période :"))
        self.date_start = QDateEdit()
        self.date_start.setDate(QDate.currentDate().addMonths(-1))
        self.date_start.dateChanged.connect(self.load_all_sales_data)
        filters_layout.addWidget(self.date_start)
        
        filters_layout.addWidget(QLabel("à"))
        self.date_end = QDateEdit()
        self.date_end.setDate(QDate.currentDate())
        self.date_end.dateChanged.connect(self.load_all_sales_data)
        filters_layout.addWidget(self.date_end)
        
        btn_filter = QPushButton("🔄 Actualiser")
        btn_filter.clicked.connect(self.load_all_sales_data)
        filters_layout.addWidget(btn_filter)
        
        # Bouton d'impression de l'historique des ventes
        btn_print_sales_history = QPushButton("🖨️ Imprimer Historique Ventes (PDF)")
        btn_print_sales_history.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold; padding: 8px;")
        btn_print_sales_history.clicked.connect(self.print_sales_history_pdf)
        filters_layout.addWidget(btn_print_sales_history)
        
        filters_layout.addStretch()
        layout.addLayout(filters_layout)
        
        # Tableau
        self.table_all_sales = QTableWidget()
        self.table_all_sales.setColumnCount(7)
        self.table_all_sales.setHorizontalHeaderLabels([
            "ID Vente", "Date", "Vendeur", "Client", "Mode Paiement", "Montant", "Articles"
        ])
        self.table_all_sales.setColumnWidth(0, 80)
        self.table_all_sales.setColumnWidth(1, 100)
        self.table_all_sales.setColumnWidth(2, 150)
        self.table_all_sales.setColumnWidth(3, 150)
        self.table_all_sales.setColumnWidth(4, 120)
        self.table_all_sales.setColumnWidth(5, 100)
        self.table_all_sales.setColumnWidth(6, 80)
        
        layout.addWidget(self.table_all_sales)
        
        self.tab_all_sales.setLayout(layout)

    def load_general_stats(self):
        """Charge les statistiques générales"""
        start_date = self.stats_date_start.date().toString("yyyy-MM-dd")
        end_date = self.stats_date_end.date().toString("yyyy-MM-dd")
        
        stats = get_total_sales_stats(start_date, end_date)
        if stats:
            self.label_total_sales.setText(
                f"Total Ventes\n{stats['total_ventes'] or 0}"
            )
            self.label_total_clients.setText(
                f"Total Clients\n{stats['total_clients'] or 0}"
            )
            self.label_total_vendors.setText(
                f"Total Vendeurs\n{stats['total_vendeurs'] or 0}"
            )
            montant = stats['montant_total'] or 0
            self.label_total_amount.setText(
                f"Montant Total\n{format_currency(montant)}"
            )

    def load_by_vendor_data(self):
        """Charge les ventes par vendeur"""
        start_date = self.vendor_date_start.date().toString("yyyy-MM-dd")
        end_date = self.vendor_date_end.date().toString("yyyy-MM-dd")
        
        data = get_sales_by_vendor(start_date, end_date)
        self.table_by_vendor.setRowCount(len(data))
        
        for row, item in enumerate(data):
            # Vendeur
            self.table_by_vendor.setItem(row, 0, QTableWidgetItem(item['vendeur'] or "N/A"))
            # Nombre de ventes
            nombre = item['nombre_ventes'] or 0
            self.table_by_vendor.setItem(row, 1, QTableWidgetItem(str(nombre)))
            # Montant total
            montant = item['montant_total'] or 0
            self.table_by_vendor.setItem(row, 2, QTableWidgetItem(format_currency(montant)))
            # Montant moyen
            moyenne = (montant / nombre) if nombre > 0 else 0
            self.table_by_vendor.setItem(row, 3, QTableWidgetItem(format_currency(moyenne)))

    def load_by_payment_data(self):
        """Charge les ventes par mode de paiement"""
        start_date = self.payment_date_start.date().toString("yyyy-MM-dd")
        end_date = self.payment_date_end.date().toString("yyyy-MM-dd")
        
        data = get_sales_by_payment_mode(start_date, end_date)
        self.table_by_payment.setRowCount(len(data))
        
        for row, item in enumerate(data):
            # Mode de paiement
            self.table_by_payment.setItem(row, 0, QTableWidgetItem(item['mode_paiement'] or "N/A"))
            # Nombre de ventes
            nombre = item['nombre_ventes'] or 0
            self.table_by_payment.setItem(row, 1, QTableWidgetItem(str(nombre)))
            # Montant total
            montant = item['montant_total'] or 0
            self.table_by_payment.setItem(row, 2, QTableWidgetItem(format_currency(montant)))
            # Montant moyen
            moyenne = (montant / nombre) if nombre > 0 else 0
            self.table_by_payment.setItem(row, 3, QTableWidgetItem(format_currency(moyenne)))

    def load_debts_data(self):
        """Charge le résumé des dettes"""
        start_date = self.debts_date_start.date().toString("yyyy-MM-dd")
        end_date = self.debts_date_end.date().toString("yyyy-MM-dd")
        
        data = get_debts_summary(start_date, end_date)
        self.table_debts.setRowCount(len(data))
        
        for row, item in enumerate(data):
            # Statut
            self.table_debts.setItem(row, 0, QTableWidgetItem(item['statut'] or "N/A"))
            # Type de dette
            self.table_debts.setItem(row, 1, QTableWidgetItem(item['type_dette'] or "N/A"))
            # Nombre de dettes
            nombre = item['nombre_dettes'] or 0
            self.table_debts.setItem(row, 2, QTableWidgetItem(str(nombre)))
            # Montant total
            montant = item['montant_total'] or 0
            self.table_debts.setItem(row, 3, QTableWidgetItem(format_currency(montant)))

    def load_all_sales_data(self):
        """Charge toutes les ventes"""
        start_date = self.date_start.date().toString("yyyy-MM-dd")
        end_date = self.date_end.date().toString("yyyy-MM-dd")
        
        # on récupère les ventes détaillées puis on filtre par date
        raw = get_all_sales_detailed()
        # filter in Python to avoid changing DB query structure
        data = [item for item in raw
                if start_date <= str(item.get('date_vente', '')) <= end_date]
        self.table_all_sales.setRowCount(len(data))
        
        for row, item in enumerate(data):
            # sécuriser l'accès aux clés
            self.table_all_sales.setItem(row, 0, QTableWidgetItem(str(item.get('id_vente', ''))))
            self.table_all_sales.setItem(row, 1, QTableWidgetItem(str(item.get('date_vente', ''))))
            self.table_all_sales.setItem(row, 2, QTableWidgetItem(item.get('vendeur', 'N/A') or "N/A"))
            self.table_all_sales.setItem(row, 3, QTableWidgetItem(item.get('client', 'N/A') or "N/A"))
            self.table_all_sales.setItem(row, 4, QTableWidgetItem(item.get('mode_paiement', 'N/A') or "N/A"))
            montant = item.get('montant_total', 0) or 0
            self.table_all_sales.setItem(row, 5, QTableWidgetItem(format_currency(montant)))
            self.table_all_sales.setItem(row, 6, QTableWidgetItem(str(item.get('nombre_articles', 0) or 0)))

    def refresh_all_data(self):
        """Actualise toutes les données"""
        self.load_general_stats()
        self.load_by_vendor_data()
        self.load_by_payment_data()
        self.load_debts_data()
        self.load_all_sales_data()
        self.load_payments_history_data()

    def print_sales_history_pdf(self):
        """Imprime l'historique des ventes en PDF"""
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.lib.utils import ImageReader
        import datetime
        import os

        # Récupérer les données filtrées
        start_date = self.date_start.date().toString("yyyy-MM-dd")
        end_date = self.date_end.date().toString("yyyy-MM-dd")

        raw = get_all_sales_detailed()
        sales_data = [item for item in raw
                     if start_date <= str(item.get('date_vente', '')) <= end_date]

        # Créer le PDF
        storage_path = get_invoice_storage_path(self)
        base_filename = f"historique_ventes_{start_date}_au_{end_date}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filename = build_invoice_filename(storage_path, base_filename)

        doc = SimpleDocTemplate(filename, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        # Ajouter le logo en haut au centre
        from invoice_generator import get_logo_path
        logo_path = get_logo_path()
        if logo_path:
            try:
                from reportlab.platypus import Image as RLImage
                logo = RLImage(logo_path, width=1.5*inch, height=1.5*inch)
                logo_table = Table([[logo]], colWidths=[6*inch])
                logo_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ]))
                elements.append(logo_table)
                elements.append(Spacer(1, 0.1*inch))
            except Exception as e:
                print(f"Erreur lors de l'ajout du logo: {e}")

        # Informations de l'entreprise
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.blue,
            spaceAfter=10,
            alignment=1
        )

        elements.append(Paragraph("SOCIETE CAMELEON GABRIELLA", title_style))
        elements.append(Paragraph("SOCAGA en sigle", title_style))
        company_info = [
            "N. RCCM: CD/KND/RCCM/21-B-788",
            "ID. NAT: N. 14-F4300-N04828N",
            "N. IMPOT: A2202409T",
            "Adresse: N.03, Av. Potopoto, Q/Kasuku, C/Kasuku, Ville de Kindu",
            "Province du Maniema, RDC",
            "0815100000, 0993200000, 0997800000, 0978100000, 0976111111, 0813155555",
            "Email: mussagabriel85@gmail.com, mussagabriel82@gmail.com"
        ]
        for info in company_info:
            elements.append(Paragraph(info, styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))

        # Titre du rapport
        elements.append(Paragraph("HISTORIQUE DES VENTES", title_style))
        elements.append(Spacer(1, 0.1*inch))

        # Informations sur la période
        period_info = f"Période: du {self.date_start.date().toString('dd/MM/yyyy')} au {self.date_end.date().toString('dd/MM/yyyy')}"
        elements.append(Paragraph(period_info, styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))

        # Préparer les données du tableau
        table_data = [["N.", "ID Vente", "Date", "Vendeur", "Client", "Mode Paiement", "Montant", "Articles"]]

        total_montant = 0
        total_articles = 0

        for idx, sale in enumerate(sales_data, 1):
            montant = sale.get('montant_total', 0) or 0
            articles = sale.get('nombre_articles', 0) or 0

            table_data.append([
                str(idx),
                str(sale.get('id_vente', '')),
                str(sale.get('date_vente', '')),
                sale.get('vendeur', 'N/A') or "N/A",
                sale.get('client', 'N/A') or "N/A",
                sale.get('mode_paiement', 'N/A') or "N/A",
                format_currency(montant),
                str(articles),
            ])

            total_montant += montant
            total_articles += articles

        # Ajouter la ligne de total
        table_data.append([
            "", "TOTAL GÉNÉRAL", "", "", "", "",
            format_currency(total_montant), str(total_articles)
        ])

        # Créer le tableau
        table = Table(table_data, colWidths=[0.4*inch, 0.8*inch, 1.2*inch, 1.5*inch, 1.5*inch, 1.3*inch, 1.2*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('WORDWRAP', (0, 0), (-1, -1), 'ON'),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 0.2*inch))

        # Pied de page
        footer_style = ParagraphStyle(
            'CustomFooter',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.black,
            alignment=1
        )
        elements.append(Paragraph(f"Rapport généré le {datetime.datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}", footer_style))
        elements.append(Paragraph(f"Nombre total de ventes: {len(sales_data)}", footer_style))

        try:
            doc.build(elements)
            QMessageBox.information(self, "Historique Ventes PDF", f"PDF généré avec succès :\n{filename}\nVoulez-vous l'ouvrir ?")
            from invoice_generator import open_invoice
            open_invoice(filename)
        except Exception as e:
            QMessageBox.critical(self, "Erreur PDF", f"Erreur lors de la génération du PDF : {str(e)}")

    def setup_payments_history_tab(self):
        """Onglet de l'historique des paiements"""
        layout = QVBoxLayout()

        # Filtres de date
        filters_layout = QHBoxLayout()
        filters_layout.addWidget(QLabel("Période :"))
        self.payments_date_start = QDateEdit()
        self.payments_date_start.setDate(QDate.currentDate().addMonths(-1))
        self.payments_date_start.dateChanged.connect(self.load_payments_history_data)
        filters_layout.addWidget(self.payments_date_start)

        filters_layout.addWidget(QLabel("à"))
        self.payments_date_end = QDateEdit()
        self.payments_date_end.setDate(QDate.currentDate())
        self.payments_date_end.dateChanged.connect(self.load_payments_history_data)
        filters_layout.addWidget(self.payments_date_end)

        btn_refresh_payments = QPushButton("🔄 Actualiser")
        btn_refresh_payments.clicked.connect(self.load_payments_history_data)
        filters_layout.addWidget(btn_refresh_payments)

        # Bouton d'impression de l'historique des paiements
        btn_print_payments_history = QPushButton("🖨️ Imprimer Historique Paiements (PDF)")
        btn_print_payments_history.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 8px;")
        btn_print_payments_history.clicked.connect(self.print_payments_history_pdf)
        filters_layout.addWidget(btn_print_payments_history)

        filters_layout.addStretch()
        layout.addLayout(filters_layout)

        # Tableau
        self.table_payments_history = QTableWidget()
        self.table_payments_history.setColumnCount(5)
        self.table_payments_history.setHorizontalHeaderLabels([
            "ID Paiement", "Date", "Vendeur", "Client", "Montant"
        ])
        self.table_payments_history.setColumnWidth(0, 100)
        self.table_payments_history.setColumnWidth(1, 120)
        self.table_payments_history.setColumnWidth(2, 150)
        self.table_payments_history.setColumnWidth(3, 150)
        self.table_payments_history.setColumnWidth(4, 120)

        layout.addWidget(self.table_payments_history)

        self.tab_payments_history.setLayout(layout)

    def load_payments_history_data(self):
        """Charge l'historique des paiements"""
        start_date = self.payments_date_start.date().toString("yyyy-MM-dd")
        end_date = self.payments_date_end.date().toString("yyyy-MM-dd")

        # Récupérer tous les paiements (ventes + paiements de dettes)
        payments_data = get_all_payments_with_details(start_date, end_date)

        self.table_payments_history.setRowCount(len(payments_data))

        for row, payment in enumerate(payments_data):
            self.table_payments_history.setItem(row, 0, QTableWidgetItem(str(payment.get('id_paiement', ''))))
            self.table_payments_history.setItem(row, 1, QTableWidgetItem(str(payment.get('date_paiement', ''))))
            self.table_payments_history.setItem(row, 2, QTableWidgetItem(payment.get('vendeur', 'N/A') or "N/A"))
            self.table_payments_history.setItem(row, 3, QTableWidgetItem(payment.get('client', 'N/A') or "N/A"))
            montant = payment.get('montant_paiement', 0) or 0
            self.table_payments_history.setItem(row, 4, QTableWidgetItem(format_currency(montant)))

    def print_payments_history_pdf(self):
        """Imprime l'historique des paiements en PDF"""
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.lib.utils import ImageReader
        import datetime
        import os

        # Récupérer les données filtrées
        start_date = self.payments_date_start.date().toString("yyyy-MM-dd")
        end_date = self.payments_date_end.date().toString("yyyy-MM-dd")

        payments_data = get_all_payments_with_details(start_date, end_date)

        # Créer le PDF
        storage_path = get_invoice_storage_path(self)
        base_filename = f"historique_paiements_{start_date}_au_{end_date}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filename = build_invoice_filename(storage_path, base_filename)

        doc = SimpleDocTemplate(filename, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        # Ajouter le logo en haut au centre
        from invoice_generator import get_logo_path
        logo_path = get_logo_path()
        if logo_path:
            try:
                from reportlab.platypus import Image as RLImage
                logo = RLImage(logo_path, width=1.5*inch, height=1.5*inch)
                logo_table = Table([[logo]], colWidths=[6*inch])
                logo_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ]))
                elements.append(logo_table)
                elements.append(Spacer(1, 0.1*inch))
            except Exception as e:
                print(f"Erreur lors de l'ajout du logo: {e}")

        # Informations de l'entreprise
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.blue,
            spaceAfter=10,
            alignment=1
        )

        elements.append(Paragraph("SOCIETE CAMELEON GABRIELLA", title_style))
        elements.append(Paragraph("SOCAGA en sigle", title_style))
        company_info = [
            "N. RCCM: CD/KND/RCCM/21-B-788",
            "ID. NAT: N. 14-F4300-N04828N",
            "N. IMPOT: A2202409T",
            "Adresse: N.03, Av. Potopoto, Q/Kasuku, C/Kasuku, Ville de Kindu",
            "Province du Maniema, RDC",
            "0815100000, 0993200000, 0997800000, 0978100000, 0976111111, 0813155555",
            "Email: mussagabriel85@gmail.com, mussagabriel82@gmail.com"
        ]
        for info in company_info:
            elements.append(Paragraph(info, styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))

        # Titre du rapport
        elements.append(Paragraph("HISTORIQUE DES PAIEMENTS", title_style))
        elements.append(Spacer(1, 0.1*inch))

        # Informations sur la période
        period_info = f"Période: du {self.payments_date_start.date().toString('dd/MM/yyyy')} au {self.payments_date_end.date().toString('dd/MM/yyyy')}"
        elements.append(Paragraph(period_info, styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))

        # Préparer les données du tableau
        table_data = [["N.", "ID Paiement", "Date", "Vendeur", "Client", "Montant"]]

        total_montant = 0

        for idx, payment in enumerate(payments_data, 1):
            montant = payment.get('montant_paiement', 0) or 0

            table_data.append([
                str(idx),
                str(payment.get('id_paiement', '')),
                str(payment.get('date_paiement', '')),
                payment.get('vendeur', 'N/A') or "N/A",
                payment.get('client', 'N/A') or "N/A",
                format_currency(montant),
            ])

            total_montant += montant

        # Ajouter la ligne de total
        table_data.append([
            "", "TOTAL GÉNÉRAL", "", "", "",
            format_currency(total_montant)
        ])

        # Créer le tableau
        table = Table(table_data, colWidths=[0.4*inch, 1*inch, 1.2*inch, 1.5*inch, 1.5*inch, 1.4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('WORDWRAP', (0, 0), (-1, -1), 'ON'),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 0.2*inch))

        # Pied de page
        footer_style = ParagraphStyle(
            'CustomFooter',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.black,
            alignment=1
        )
        elements.append(Paragraph(f"Rapport généré le {datetime.datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}", footer_style))
        elements.append(Paragraph(f"Nombre total de paiements: {len(payments_data)}", footer_style))

        try:
            doc.build(elements)
            QMessageBox.information(self, "Historique Paiements PDF", f"PDF généré avec succès :\n{filename}\nVoulez-vous l'ouvrir ?")
            from invoice_generator import open_invoice
            open_invoice(filename)
        except Exception as e:
            QMessageBox.critical(self, "Erreur PDF", f"Erreur lors de la génération du PDF : {str(e)}")
