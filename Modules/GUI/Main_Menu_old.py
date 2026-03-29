# main_gui.py
import re
import threading

from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QListWidget, QPlainTextEdit, QGroupBox, QAbstractItemView
from PySide6.QtCore import Qt, QObject, Signal

from Modules.API_and_WebScrapers.IPSW_IOS_Models import Apple
from Modules.API_and_WebScrapers.IPSW_API import Stable
from Modules.Stages.Stage_1_IPSW import IPSW_Control

def ident_key(ident: str):
    m = re.match(r"^iPhone(\d+),(\d+)$", ident)
    if not m:
        return (-1, -1)  # shove unknowns to the end
    return (int(m.group(1)), int(m.group(2)))

class ConsoleSignals(QObject):
    log = Signal(str)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.Selected_IOS = None
        self.Selected_IOS_Model = None
        self.setWindowTitle("DragonXmodz1569 IPSW Tools")
        self.setFixedSize(800, 600)

        container = QWidget()
        self.setCentralWidget(container)

        self.IOS_List = QListWidget()
        self.IOS_List.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.IOS_List.setContextMenuPolicy(Qt.CustomContextMenu)
        self.IOS_List.customContextMenuRequested.connect(self.unselect_item)
        self.IOS_List.itemClicked.connect(self.ios_selected)

        IOS_Models = QListWidget()

        # Top Right Side
        Download_Button = QPushButton("Download")
        Download_Button.setFixedSize(70, 30)
        Download_Button.clicked.connect(lambda: self.Download_IPSW(self.Selected_IOS, self.Selected_IOS_Model))

        IPSW_Extract_Button = QPushButton("Extract")
        IPSW_Extract_Button.setFixedSize(70, 30)
        IPSW_Extract_Button.clicked.connect(lambda: self.Extract_IPSW(self.Selected_IOS, self.Selected_IOS_Model))

        Refresh_Button = QPushButton("⟳")
        Refresh_Button.setFixedSize(40, 40)
        Refresh_Button.setStyleSheet("""QPushButton { border-radius: 20px; background-color: #2c2c2c; color: white; font-size: 18px;} QPushButton:hover {background-color: #3a3a3a;}""")
        Refresh_Button.clicked.connect(lambda: (IOS_Func.Main_Function()))


        GridLayout = QGridLayout(container)
        # make 4 “panels”

        #Top Left Panel - IOS and Model Selecting
        tl = QWidget();
        tl_layout = QHBoxLayout(tl)
        tl_layout.addWidget(IOS_Models)
        tl_layout.addWidget(self.IOS_List)
        IOS_Models.currentItemChanged.connect(self.Model_From_List)

        #Top Right Panel - Button Options
        tr = QWidget();
        button_row = QHBoxLayout()
        button_row.setSpacing(8)  # small gap
        button_row.addWidget(Download_Button)
        button_row.addWidget(IPSW_Extract_Button)

        tr_layout = QHBoxLayout(tr)
        tr_layout.setContentsMargins(5, 5, 5, 5)
        tr_layout.setAlignment(Qt.AlignTop)
        tr_layout.addLayout(button_row)
        tr_layout.addStretch()
        tr_layout.addWidget(Refresh_Button, alignment=Qt.AlignTop)

        # Bottom Left Panel - Console
        bl = QWidget();
        Console_title = QGroupBox("Console Output")
        bl_layout = QVBoxLayout(bl)
        # small console
        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        bl_layout.addWidget(Console_title)
        bl_layout.addWidget(self.console)
        self.signals = ConsoleSignals()
        self.signals.log.connect(self.console.appendPlainText)
        self.console.moveCursor(QTextCursor.End)

        #Bottom Right Panel
        br = QWidget();
        br.setLayout(QVBoxLayout())

        IOS_Func = Apple(self.console_print)
        iPhone_Models, self.iPhone_Versions = IOS_Func.Main_Function()

        sorted_devices = sorted(iPhone_Models, key=lambda d: ident_key(d["identifier"]), reverse=True)
        nameidentifier = [{"name": d["name"], "identifier": d["identifier"]} for d in sorted_devices]

        for item in nameidentifier:
            IOS_Models.addItem(f'{item["name"]} | {item["identifier"]}')
        IOS_Models.itemClicked.connect(self.ios_Model_selected)

        GridLayout.addWidget(tl, 0, 0)
        GridLayout.addWidget(tr, 0, 1)
        GridLayout.addWidget(bl, 1, 0)
        GridLayout.addWidget(br, 1, 1)

        GridLayout.setRowStretch(0, 1)  # top half
        GridLayout.setRowStretch(1, 1)  # bottom half
        GridLayout.setColumnStretch(0, 1)  # left half
        GridLayout.setColumnStretch(1, 1)  # right half

    def ios_selected(self, item):
        self.Selected_IOS = [i.text() for i in self.IOS_List.selectedItems()]

    def ios_Model_selected(self, item):
        _, model_ident = item.text().split(" | ")
        self.Selected_IOS_Model = model_ident

    def console_print(self, text):
        self.signals.log.emit(text)

    def Model_From_List(self, current):
        model = current.text()
        model_name, model_ident = model.split(" | ")
        self.IOS_List.clear()
        versions = []
        seen = set()
        for ios in self.iPhone_Versions:
            if ios.get("identifier", "") == model_ident:
                for firmware in ios.get("firmwares", []):
                    version = firmware.get("version", "")
                    if version and version not in seen:
                        seen.add(version)
                        versions.append(version)

                for version in reversed(versions):
                    self.IOS_List.addItem(version)

    def unselect_item(self, pos):
        item = self.IOS_List.itemAt(pos)
        if item:
            item.setSelected(False)

    def Download_IPSW(self, version, identifer):
        self.console_print(f'Starting download of {version} IPSW for {identifer}')
        stable = Stable(console_print=self.console_print)
        for x in range(len(version)):
            threading.Thread(target=stable.IPSW_Download, args=(identifer, version[x]), daemon=True).start()

    def Extract_IPSW(self, version, identifer):
        if QApplication.keyboardModifiers() == Qt.ShiftModifier:
            self.console_print(f'Starting Extraction of All Local IPSW for {identifer}')
            Extract = IPSW_Control(console_print=self.console_print)
            threading.Thread(target=Extract.Main, args=(identifer, None), daemon=True).start()
        else:
            self.console_print(f'Starting Extraction of {version} IPSW for {identifer}')
            Extract = IPSW_Control(console_print=self.console_print)
            if version is None:
                self.console_print(f'Error Please Select a IOS Version for {identifer}')
                return
            for x in range(len(version)):
                threading.Thread(target=Extract.Main, args=(identifer, version[x]), daemon=True).start()



app = QApplication()
window = MainWindow()
window.show()
app.exec_()