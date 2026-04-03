import threading
import time

from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QListWidget, QStackedWidget

from Modules.GUI.Pages.Dashboard_Menu import DashboardPage
from Modules.GUI.Pages.iPhone_Menu import iPhonePage
from Modules.GUI.Pages.iPad_Menu import iPadPage
from Modules.GUI.Pages.Mac_Menu import MacPage
from Modules.GUI.Pages.Console_Menu import ConsolePage
from Modules.GUI.Pages.Settings_Menu import SettingsPage
from Modules.GUI.Pages.PC_Helpers_Menu import PCPage


class Shared_Resources:
    def __init__(self):
        self.List = {
            'Active Remote PC List': []
        }
        threading.Thread(target=self.Background_Task, daemon=True).start()

    def Background_Task(self):
        while True:
                remote_list = self.load_data('Remote PC List')
                active_list = self.load_data('Active Remote PC List')

                active_hosts = {device['Host'] for device in active_list}
                for device in remote_list:
                    if device['Active'] is True:
                        if device['Host'] in active_hosts:
                            continue
                        self.add_resource('Active Remote PC List', device)

                    if device['Active'] is False:
                        for al in active_list:
                            if device['Host'] == al['Host']:
                                self.remove_resource('Active Remote PC List', al)
                time.sleep(1)

    def add_resource(self, List_Name, Data):
        if isinstance(Data, dict):
            devices = [Data]
        elif isinstance(Data, list):
            devices = Data
        else:
            print("❌ Invalid type passed to add_remote:", type(Data), Data)
            return
        if List_Name not in self.List:
            self.List[List_Name] = []
        for d in devices:
            self.List[List_Name].append(d)

    def remove_resource(self, List_Name, Data):
        if List_Name in self.List:
            if Data in self.List[List_Name]:
                self.List[List_Name].remove(Data)

            if not self.List[List_Name]:
                del self.List[List_Name]

    def change_resources(self, List_Name, Data, change):
        if List_Name in self.List:
            if Data in self.List[List_Name]:
                change = change.split(', ')
                if self.List[List_Name][change[0]] != change[1]:
                    self.List[List_Name][change[0]] = change[1]

    def load_data(self, List_Name):
        return self.List.get(List_Name, [])


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
            "Mac Stager", "Console", "Remote PC's","Settings"
        ])

        self.stack = QStackedWidget()

        # create shared pages ONCE
        self.console_page = ConsolePage()
        self.Shared_Resources = Shared_Resources()

        self.iphone_page = iPhonePage(console_print=self.console_page.get_logger("iPhone Menu"), Resources=self.Shared_Resources)
        self.ipad_page = iPadPage(console_print=self.console_page.get_logger("iPad Menu"), Resources=self.Shared_Resources)
        self.mac_page = MacPage(console_print=self.console_page.get_logger("Mac Menu"), Resources=self.Shared_Resources)
        self.dashboard_page = DashboardPage(console_print=self.console_page.get_logger("Dashboard"))
        self.settings_page = SettingsPage(console_print=self.console_page.get_logger("Settings"))
        self.PC_Helper_Page = PCPage(console_print=self.console_page.get_logger("Remote PCs"), Resources=self.Shared_Resources)

        # add the SAME instances to the stack
        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.iphone_page)
        self.stack.addWidget(self.ipad_page)
        self.stack.addWidget(self.mac_page)
        self.stack.addWidget(self.console_page)
        self.stack.addWidget(self.PC_Helper_Page)
        self.stack.addWidget(self.settings_page)

        self.menu.currentRowChanged.connect(self.change_page)
        self.menu.setFixedWidth(120)
        self.menu.setCurrentRow(0)

        layout.addWidget(self.menu, 1)
        layout.addWidget(self.stack, 4)

    def change_page(self, index):
        old_page = self.stack.currentWidget()
        if old_page and hasattr(old_page, "on_leave"):
            old_page.on_leave()

        self.stack.setCurrentIndex(index)
        new_page = self.stack.currentWidget()

        if hasattr(new_page, "load_data") and not getattr(new_page, "_loaded", False):
            new_page._loaded = True
            new_page.load_data()

        if hasattr(new_page, "on_enter"):
            new_page.on_enter()