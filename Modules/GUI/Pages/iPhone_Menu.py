import re
import threading

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QPushButton, QGridLayout, QListWidget, \
    QAbstractItemView, QHBoxLayout

from Modules.API_and_WebScrapers.IPSW_IOS_Models import Apple
from Modules.API_and_WebScrapers.IPSW_API import Stable


class iPhonePage(QWidget):
    First_Ran = False
    def __init__(self, console_print=None, Resources=None):
        super().__init__()
        self.Console_Print = console_print
        self.shared_data = Resources
        self.Selected_Iphone_Model = None
        self.Selected_Iphone_Version = None
        self.worker_thread = None
        self.stop_event = threading.Event()


        self.iPhone_Models = QListWidget()
        self.iPhone_Models.itemClicked.connect(self.iPhone_Model_Select)

        self.iPhone_Versions = QListWidget()
        self.iPhone_Versions.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.iPhone_Versions.setContextMenuPolicy(Qt.CustomContextMenu)
        self.iPhone_Versions.customContextMenuRequested.connect(self.unselect_item)
        self.iPhone_Versions.itemClicked.connect(self.iPhone_Version_Select)

        main_layout = QVBoxLayout(self)

        grid = QGridLayout()
        main_layout.addLayout(grid)

        # Section 1 - Top Left
        section1 = QGroupBox("iPhone List")
        s1_layout = QHBoxLayout()
        s1_layout.addWidget(self.iPhone_Models)
        s1_layout.addWidget(self.iPhone_Versions)
        self.iPhone_Models.currentItemChanged.connect(self.Model_From_List)
        section1.setLayout(s1_layout)

        Download_IPSW= QPushButton("Download IPSW")
        Download_IPSW.clicked.connect(lambda: self.Download_IPSW(self.Selected_Iphone_Version, self.Selected_Iphone_Model))
        Download_IPSW.setFixedSize(100, 40)

        Stage_1_Extract = QPushButton("Extract IPSW")
        Stage_1_Extract.clicked.connect(lambda: print(self.Selected_Iphone_Version, self.Selected_Iphone_Model))
        Stage_1_Extract.setFixedSize(90, 40)

        # Section 2 - Top Right
        section2 = QGroupBox("IPSW Functions")
        s2_layout = QHBoxLayout()
        s2_layout.setAlignment(Qt.AlignTop)

        s2_button = QHBoxLayout()
        button_row = QHBoxLayout()
        button_row.setSpacing(8)

        s2_layout.addLayout(s2_button)
        s2_button.addWidget(Download_IPSW)
        s2_button.addWidget(Stage_1_Extract)

        section2.setLayout(s2_layout)

        # Section 3
        section3 = QGroupBox("Bottom Left")
        s3_layout = QVBoxLayout()
        section3.setLayout(s3_layout)

        # Section 4
        section4 = QGroupBox("Bottom Right")
        s4_layout = QVBoxLayout()
        section4.setLayout(s4_layout)

        # Add to grid
        grid.addWidget(section1, 0, 0)
        grid.addWidget(section2, 0, 1)
        grid.addWidget(section3, 1, 0)
        grid.addWidget(section4, 1, 1)

        # Make them stretch evenly
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

    def unselect_item(self, pos):
        item = self.iPhone_Versions.itemAt(pos)
        if item:
            item.setSelected(False)

    def iPhone_Version_Select(self, item):
        self.Selected_Iphone_Version = [i.text() for i in self.iPhone_Versions.selectedItems()]

    def iPhone_Model_Select(self, item):
        _, model_ident = item.text().split(" | ")
        self.Selected_Iphone_Model = model_ident

    def Model_From_List(self, current):
        if not current:
            return
        model = current.text()
        model_name, model_ident = model.split(" | ")
        self.iPhone_Versions.clear()
        versions = []
        seen = set()
        for ios in self.iPhone_Versions_List:
            if ios.get("identifier", "") == model_ident:
                for firmware in ios.get("firmwares", []):
                    version = firmware.get("version", "")
                    if version and version not in seen:
                        seen.add(version)
                        versions.append(version)

        for version in reversed(versions):
            self.iPhone_Versions.addItem(version)

    def Download_IPSW(self, version, identifer):
        self.Console_Print(f'Starting download of {version} IPSW for {identifer}')
        stable = Stable(console_print=self.Console_Print)
        for x in range(len(version)):
            threading.Thread(target=stable.IPSW_Download, args=(identifer, version[x]), daemon=True).start()

    def Background_Activity(self):
        Apple_Info = Apple(self.Console_Print)
        New_iPhone_Model_list, New_iPhone_Versions_List = Apple_Info.Reload_DataBase()

        models_changed = New_iPhone_Model_list != self.iPhone_Model_list
        versions_changed = New_iPhone_Versions_List != self.iPhone_Versions_List

        if models_changed:
            self.Console_Print('[Database] Found new iPhone Model updating Database')
            self.iPhone_Model_list = New_iPhone_Model_list

        if versions_changed:
            self.Console_Print('[Database] Found new iPhone Version updating Database')
            self.iPhone_Versions_List = New_iPhone_Versions_List

        if models_changed or versions_changed:
            QTimer.singleShot(0, lambda: (
                self.iPhone_Models.clear(),
                [self.iPhone_Models.addItem(f'{item["name"]} | {item["identifier"]}') for item in sorted(
                    self.iPhone_Model_list,
                    key=lambda d: tuple(map(int, re.findall(r"\d+", d["identifier"]))),
                    reverse=True
                )]
            ))

    def load_data(self):
        if iPhonePage.First_Ran == False:
            iPhonePage.First_Ran = True
            Apple_Info = Apple(self.Console_Print)
            self.iPhone_Model_list, self.iPhone_Versions_List = Apple_Info.Main_Function()

            for item in sorted(self.iPhone_Model_list,key=lambda d: tuple(map(int, re.findall(r"\d+", d["identifier"]))), reverse=True):
                self.iPhone_Models.addItem(f'{item["name"]} | {item["identifier"]}')

    def on_leave(self):
        self.stop_event.set()

    def on_enter(self):
        self.stop_event.clear()
        if self.worker_thread and self.worker_thread.is_alive():
            self.Console_Print("Worker already running")
            return

        self.worker_thread = threading.Thread(target=self.Background_Activity, daemon=True)
        self.worker_thread.start()