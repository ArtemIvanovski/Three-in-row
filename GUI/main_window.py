from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout, QLabel, QVBoxLayout

from GUI.game_window import GameWindow
from GUI.rules_window import RulesWindow
from core.setting_deploy import get_resource_path
from logger import logger


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.join_game_window = None
        self.create_game_window = None
        self.rules_window = None
        self.init_ui()

    def init_ui(self):
        logger.info("Инициализация главного окна")
        self.setWindowTitle("Three in row")
        self.setGeometry(100, 100, 500, 880)
        self.setWindowIcon(QIcon(get_resource_path("assets/icon.png")))
        self.setFixedSize(500, 880)

        background = QLabel(self)
        background.setPixmap(QPixmap(get_resource_path("assets/start_background.png")).scaled(500, 880))
        background.setGeometry(0, 0, 500, 880)

        btn_create_game = QPushButton("Создать игру")
        btn_join_game = QPushButton("Присоединиться к игре")
        btn_rules = QPushButton("Правила игры")

        button_style = """
                    QPushButton {
                        background-color: rgba(255, 255, 255, 0.9);
                        color: black;
                        font-size: 24px;
                        font-weight: bold;
                        border-radius: 10px;
                        padding: 15px 30px;
                    }
                    QPushButton:hover {
                        background-color: rgba(255, 255, 255, 1);
                    }
                """

        btn_create_game.setStyleSheet(button_style)
        btn_create_game.clicked.connect(self.create_game)

        btn_join_game.setStyleSheet(button_style)
        btn_join_game.clicked.connect(self.join_game)

        btn_rules.setStyleSheet(button_style)
        btn_rules.clicked.connect(self.show_rules)

        button_layout = QHBoxLayout()
        button_layout.addWidget(btn_create_game)
        button_layout.addWidget(btn_join_game)
        button_layout.addWidget(btn_rules)
        button_layout.setSpacing(50)
        button_layout.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)

        main_layout = QVBoxLayout(self)
        main_layout.addStretch()
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def show_rules(self):
        logger.info("Открытие окна с правилами игры")
        self.rules_window = RulesWindow()
        self.rules_window.show()

    def create_game(self):
        logger.info("Создание новой игры")
        self.create_game_window = GameWindow()
        self.create_game_window.show()

    def join_game(self):
        logger.info("Присоединение к игре")
        self.join_game_window = JoinGameWindow(self)
        self.join_game_window.show()
