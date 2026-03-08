from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox, QCheckBox
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Signal, Qt
from database import verify_user

class LoginView(QWidget):
    login_success = Signal(dict) # Signal pour envoyer les données de l'utilisateur après succès

    def __init__(self):
        super().__init__()
        from utils import resource_path
        # application icon (also appears on the login window)
        self.setWindowIcon(QIcon(resource_path("images/logo.png")))
        self.setWindowTitle("Connexion - Gestion Chambre Froide")
        self.setFixedSize(380, 450)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 20, 40, 20)
        layout.setSpacing(15)

        # logo image at the top
        logo_label = QLabel()
        from utils import resource_path
        pixmap = QPixmap(resource_path("images/logo.png"))
        if not pixmap.isNull():
            logo_label.setPixmap(pixmap.scaled(350, 350, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)

        title = QLabel("<b>CONNEXION</b>")
        title.setStyleSheet("font-size: 22px; color: #2f3640;")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)  # centre le titre
        
        self.phone_input = QLineEdit()
        self.phone_input.returnPressed.connect(self.process_login)
        self.phone_input.setPlaceholderText("Numéro de téléphone")
        self.phone_input.setFixedHeight(35)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Mot de passe")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.returnPressed.connect(self.process_login)
        self.password_input.setFixedHeight(35)
        
        # checkbox pour afficher/masquer le mot de passe
        toggle_pwd = QCheckBox("Afficher mot de passe")
        toggle_pwd.toggled.connect(lambda checked: self.password_input.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password))
        
        btn_login = QPushButton("SE CONNECTER")
        btn_login.setStyleSheet("background-color: #027df8; color: white; font-size: 16px; font-weight: bold; border-radius: 5px;")
        btn_login.setObjectName("loginButton")
        btn_login.setFixedHeight(45)
        btn_login.setFixedWidth(220)
        btn_login.clicked.connect(self.process_login)
        
        layout.addWidget(title)
        layout.addWidget(self.phone_input)
        layout.addWidget(self.password_input)
        layout.addWidget(toggle_pwd)
        layout.addWidget(btn_login, alignment=Qt.AlignCenter)
        self.setLayout(layout)

    def process_login(self):
        phone = self.phone_input.text()
        password = self.password_input.text()
        
        user = verify_user(phone, password)
        if user:
            self.login_success.emit(user)
            self.close()
        else:
            QMessageBox.warning(self, "Erreur", "Identifiants invalides")