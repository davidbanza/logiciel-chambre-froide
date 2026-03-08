from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QStackedWidget, QFrame, QLabel)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
from views.sales_view import SalesView
from views.users_view import UsersView
from views.reports_view import ReportsView
from views.debts_view import DebtsView
from views.stock_view import StockView
from views.sales_history_view import SalesHistoryView
from views.withdrawals_view import WithdrawalsView
from database import is_manager

class MainView(QMainWindow):
    def __init__(self, user):
        super().__init__()
        self.user = user
        # set the same icon for the main window (in case app icon isn't inherited)
        from utils import resource_path
        self.setWindowIcon(QIcon(resource_path("images/logo.png")))
        # [cite_start]Utilisation du nom et statut récupérés de la DB [cite: 14, 16]
        self.setWindowTitle(f"Chambre Froide - {user['prenom_ut']} ({user['statut']})")
        self.resize(1200, 800)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.layout_principal = QVBoxLayout(main_widget)

        # 1. MENU SUPÉRIEUR
        self.top_menu = QHBoxLayout()
        self.btn_task_ventes = QPushButton("🛒 GESTION VENTES")
        self.btn_task_stock = QPushButton("📦 GESTION STOCK")
        self.btn_task_dettes = QPushButton("💳 SUIVI DETTES")
        self.btn_task_admin = QPushButton("👤 UTILISATEURS")
        # mark these for styling and track in a list
        for b in (self.btn_task_ventes, self.btn_task_stock, self.btn_task_dettes, self.btn_task_admin):
            b.setProperty("class", "topMenu")
        self.top_buttons = [self.btn_task_ventes, self.btn_task_stock, self.btn_task_dettes, self.btn_task_admin]

        # [cite_start]Restriction : Seul le manager accède à la gestion des utilisateurs [cite: 39, 40]
        if not is_manager(user['id_ut']): 
            self.btn_task_admin.setVisible(False)

        self.top_menu.addWidget(self.btn_task_ventes)
        self.top_menu.addWidget(self.btn_task_stock)
        self.top_menu.addWidget(self.btn_task_dettes)
        self.top_menu.addWidget(self.btn_task_admin)
        self.layout_principal.addLayout(self.top_menu)

        # 2. ZONE INFÉRIEURE
        self.bottom_layout = QHBoxLayout()
        self.side_menu_frame = QFrame()
        self.side_menu_frame.setFixedWidth(220)
        self.side_menu_frame.setStyleSheet("background-color: #f0f0f0; border-right: 1px solid #ccc;")
        self.side_menu = QVBoxLayout(self.side_menu_frame)
        self.side_menu.setAlignment(Qt.AlignTop)
        
        self.content_stack = QStackedWidget()
        
        self.bottom_layout.addWidget(self.side_menu_frame)
        self.bottom_layout.addWidget(self.content_stack)
        self.layout_principal.addLayout(self.bottom_layout)

        # Connexions des tâches principales
        self.btn_task_ventes.clicked.connect(lambda: self.load_sales_menu(self.btn_task_ventes))
        self.btn_task_stock.clicked.connect(lambda: self.load_stock_menu(self.btn_task_stock))
        self.btn_task_dettes.clicked.connect(lambda: self.load_debts_menu(self.btn_task_dettes))
        self.btn_task_admin.clicked.connect(lambda: self.load_admin_menu(self.btn_task_admin))

        # [cite_start]Chargement par défaut [cite: 57, 63]
        self.load_sales_menu(self.btn_task_ventes)

    def clear_side_menu(self):
        while self.side_menu.count():
            child = self.side_menu.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def _highlight_top_button(self, btn):
        # clear previous
        for b in self.top_buttons:
            b.setProperty('active', False)
            b.setStyleSheet("")
        # set new
        btn.setProperty('active', True)
        btn.setStyleSheet("background-color:#3498db; color:white;")

    def _activate_first_side_item(self):
        # find first clickable widget in side_menu
        if self.side_menu.count() > 1:  # first is label
            item = self.side_menu.itemAt(1)
            if item and item.widget():
                item.widget().click()

    def _highlight_side_button(self, btn):
        # clear previous highlights in the side menu
        for i in range(self.side_menu.count()):
            w = self.side_menu.itemAt(i).widget()
            if isinstance(w, QPushButton):
                w.setProperty('active', False)
                w.setStyleSheet("")
        btn.setProperty('active', True)
        btn.setStyleSheet("background-color:#3498db; color:white;")

    # --- MENUS LATÉRAUX ---

    def load_sales_menu(self, source_button=None):
        self.clear_side_menu()
        if source_button:
            self._highlight_top_button(source_button)
        self.side_menu.addWidget(QLabel("<b>OPTIONS VENTES</b>"))
        btn_nv = QPushButton("Nouvelle Vente")
        btn_nv.setProperty('class', 'sideMenu')
        btn_nv.clicked.connect(lambda checked=False, b=btn_nv: (self._highlight_side_button(b), self.show_sales_view()))
        btn_hist = QPushButton("Historique Ventes")
        btn_hist.setProperty('class', 'sideMenu')
        btn_hist.clicked.connect(lambda checked=False, b=btn_hist: (self._highlight_side_button(b), self.show_sales_history()))
        btn_my_sales = QPushButton("Mes Ventes")
        btn_my_sales.setProperty('class', 'sideMenu')
        btn_my_sales.clicked.connect(lambda checked=False, b=btn_my_sales: (self._highlight_side_button(b), self.show_my_sales_history()))
        btn_withdrawals = QPushButton("Gestion des Retraits")
        btn_withdrawals.setProperty('class', 'sideMenu')
        btn_withdrawals.clicked.connect(lambda checked=False, b=btn_withdrawals: (self._highlight_side_button(b), self.show_withdrawals_view()))
        
        self.side_menu.addWidget(btn_nv)
        self.side_menu.addWidget(btn_hist)
        self.side_menu.addWidget(btn_my_sales)
        self.side_menu.addWidget(btn_withdrawals)
        self.side_menu.addStretch()
        # auto-trigger first option
        self._activate_first_side_item()

    def load_stock_menu(self, source_button=None):
        self.clear_side_menu()
        if source_button:
            self._highlight_top_button(source_button)
        self.side_menu.addWidget(QLabel("<b>OPTIONS STOCK</b>"))
        btn_liste = QPushButton("État du Stock") # [cite: 102]
        btn_liste.setProperty('class', 'sideMenu')
        btn_liste.clicked.connect(lambda checked=False, b=btn_liste: (self._highlight_side_button(b), self.show_stock_view()))
        self.side_menu.addWidget(btn_liste)
        
        if is_manager(self.user['id_ut']): # Manager uniquement [cite: 42, 43]
            btn_add = QPushButton("Ajouter Produit")
            btn_add.setProperty('class', 'sideMenu')
            btn_add.clicked.connect(lambda checked=False, b=btn_add: (self._highlight_side_button(b), self.show_stock_view(open_add=True)))
            self.side_menu.addWidget(btn_add)
        self.side_menu.addStretch()
        self._activate_first_side_item()

    def load_debts_menu(self, source_button=None):
        self.clear_side_menu()
        if source_button:
            self._highlight_top_button(source_button)
        self.side_menu.addWidget(QLabel("<b>OPTIONS DETTES</b>"))
        btn_list_dettes = QPushButton("Clients Débiteurs") # [cite: 28, 98]
        btn_list_dettes.setProperty('class', 'sideMenu')
        btn_list_dettes.clicked.connect(lambda checked=False, b=btn_list_dettes: (self._highlight_side_button(b), self.show_debts_view()))
        self.side_menu.addWidget(btn_list_dettes)
        self.side_menu.addStretch()
        self._activate_first_side_item()

    def load_admin_menu(self, source_button=None):
        self.clear_side_menu()
        if source_button:
            self._highlight_top_button(source_button)
        self.side_menu.addWidget(QLabel("<b>ADMINISTRATION</b>"))
        btn_users = QPushButton("Gérer Vendeurs") # [cite: 40]
        btn_users.setProperty('class', 'sideMenu')
        btn_users.clicked.connect(lambda checked=False, b=btn_users: (self._highlight_side_button(b), self.show_users_management()))
        btn_rapports = QPushButton("Rapports & Bilans") # [cite: 45, 68]
        btn_rapports.setProperty('class', 'sideMenu')
        btn_rapports.clicked.connect(lambda checked=False, b=btn_rapports: (self._highlight_side_button(b), self.show_reports()))
        self.side_menu.addWidget(btn_users)
        self.side_menu.addWidget(btn_rapports)
        self.side_menu.addStretch()
        self._activate_first_side_item()

    # --- GESTION DES VUES (QStackedWidget) ---

    def show_new_sale_form(self):
        """Affiche le formulaire de saisie de vente dans la zone centrale."""
        self.sales_page = SalesView(self.user) 
        self.content_stack.addWidget(self.sales_page)
        self.content_stack.setCurrentWidget(self.sales_page)

    def show_sales_view(self, default_tab=0):
        """Affiche la vue complète des ventes

        :param default_tab: index d'onglet à afficher (0: nouvelle vente,
                            1: ventes du jour, 2: modifier vente)
        """
        self.sales_page = SalesView(self.user)
        self.content_stack.addWidget(self.sales_page)
        self.content_stack.setCurrentWidget(self.sales_page)
        # définir l'onglet initial si possible
        try:
            self.sales_page.tabs.setCurrentIndex(default_tab)
        except Exception:
            pass

    def show_sales_history(self):
        """Ouvre la vue des ventes et affiche l'onglet de l'historique."""
        self.show_sales_view(default_tab=1)

    def show_my_sales_history(self):
        """Affiche l'historique des ventes du vendeur connecté avec KPIs."""
        self.my_sales_page = SalesHistoryView(self.user)
        self.content_stack.addWidget(self.my_sales_page)
        self.content_stack.setCurrentWidget(self.my_sales_page)

    def show_withdrawals_view(self):
        """Affiche la vue de gestion des retraits programmés."""
        self.withdrawals_page = WithdrawalsView(self.user)
        self.content_stack.addWidget(self.withdrawals_page)
        self.content_stack.setCurrentWidget(self.withdrawals_page)

    def show_debts_view(self):
        """Affiche la vue de gestion des dettes"""
        self.debts_page = DebtsView(self.user)
        self.content_stack.addWidget(self.debts_page)
        self.content_stack.setCurrentWidget(self.debts_page)

    def show_stock_view(self, open_add=False):
        """Affiche la vue de gestion du stock

        :param open_add: si True, ouvre automatiquement l'interface d'ajout de produit
        """
        self.stock_page = StockView(self.user)
        self.content_stack.addWidget(self.stock_page)
        self.content_stack.setCurrentWidget(self.stock_page)
        if open_add:
            # appeler la méthode du StockView pour afficher le dialog d'ajout
            try:
                self.stock_page.open_add_product_dialog()
            except Exception:
                pass

    def show_users_management(self):
        """Affiche l'interface de gestion des utilisateurs"""
        self.users_page = UsersView(self.user)
        self.content_stack.addWidget(self.users_page)
        self.content_stack.setCurrentWidget(self.users_page)

    def show_reports(self):
        """Affiche l'interface des rapports et bilans"""
        self.reports_page = ReportsView(self.user)
        self.content_stack.addWidget(self.reports_page)
        self.content_stack.setCurrentWidget(self.reports_page)