from Modules.GUI.Main_Menu import MainWindows
from PySide6.QtWidgets import QApplication
import sys
app = QApplication(sys.argv)

window = MainWindows()
window.show()

sys.exit(app.exec())