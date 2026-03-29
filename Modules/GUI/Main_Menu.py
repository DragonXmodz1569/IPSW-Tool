from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QListWidget, QStackedWidget

from Modules.GUI.Pages.Dashboard_Menu import DashboardPage
from Modules.GUI.Pages.iPhone_Menu import iPhonePage
from Modules.GUI.Pages.iPad_Menu import iPadPage
from Modules.GUI.Pages.Mac_Menu import MacPage
from Modules.GUI.Pages.Console_Menu import ConsolePage
from Modules.GUI.Pages.Settings_Menu import SettingsPage


class MainWindows(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DragonsXmodz Apple Tool")
        self.setFixedSize(1000, 600)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        self.menu = QListWidget()
        self.menu.addItems([
            "Dashboard", "iPhone Stager", "iPad Stager",
            "Mac Stager", "Console", "Settings"
        ])

        self.stack = QStackedWidget()

        # create shared pages ONCE
        self.console_page = ConsolePage()
        self.iphone_page = iPhonePage(console_print=self.console_page.get_logger("iPhone Menu"))
        self.dashboard_page = DashboardPage()
        self.ipad_page = iPadPage()
        self.mac_page = MacPage()
        self.settings_page = SettingsPage()

        # add the SAME instances to the stack
        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.iphone_page)
        self.stack.addWidget(self.ipad_page)
        self.stack.addWidget(self.mac_page)
        self.stack.addWidget(self.console_page)
        self.stack.addWidget(self.settings_page)

        self.menu.currentRowChanged.connect(self.change_page)
        self.menu.setFixedWidth(120)
        self.menu.setCurrentRow(0)

        layout.addWidget(self.menu, 1)
        layout.addWidget(self.stack, 4)

    def change_page(self, index):
        self.stack.setCurrentIndex(index)
        page = self.stack.widget(index)
        if hasattr(page, "load_data"):
            if not hasattr(page, "_loaded"):
                page._loaded = True
                page.load_data()