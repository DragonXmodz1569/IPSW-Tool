from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel


class iPadPage(QWidget):
    def __init__(self, console_print=None):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("This is the iPad page"))