import sys
from PySide6.QtWidgets import QApplication
from views.login_view import LoginView # Importez votre classe Login
from PySide6.QtGui import QIcon
from views.main_view import MainView

class AppController:
    def __init__(self):
        self.login_window = LoginView()
        self.login_window.login_success.connect(self.show_main_window)
        self.login_window.show()

    def show_main_window(self, user_data):
        self.main_app = MainView(user_data)
        self.main_app.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # global application icon (taskbar, window headers)
    from utils import resource_path
    app.setWindowIcon(QIcon(resource_path("images/logo.png")))
    controller = AppController()
    sys.exit(app.exec())