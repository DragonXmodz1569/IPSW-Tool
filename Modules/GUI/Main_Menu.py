# main_gui.py
import re
import time
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QListWidget, QPlainTextEdit, QGroupBox
from PySide6.QtCore import Qt, QObject, Signal
from Modules.GUI.GUI_Modules import IOS_Data_Grabber

def ident_key(ident: str):
    m = re.match(r"^iPhone(\d+),(\d+)$", ident)
    if not m:
        return (-1, -1)  # shove unknowns to the end
    return (int(m.group(1)), int(m.group(2)))

class Worker(QObject):
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
        self.IOS_List.itemClicked.connect(self.ios_selected)

        IOS_Models = QListWidget()

        # Top Right Side
        Selected_Button = QPushButton("Select")
        Selected_Button.setFixedSize(70, 30)
        Selected_Button.clicked.connect(lambda: print(f'Selected IOS: {self.Selected_IOS} and Model: {self.Selected_IOS_Model}'))

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
        tr_layout = QHBoxLayout(tr)
        tr_layout.setContentsMargins(5, 5, 5, 5)
        tr_layout.addWidget(Selected_Button, alignment=Qt.AlignTop | Qt.AlignLeft)
        tr_layout.addWidget(Refresh_Button, alignment=Qt.AlignTop | Qt.AlignRight)

        # Bottom Left Panel - Console
        bl = QWidget();
        Console_title = QGroupBox("Console Output")
        bl_layout = QVBoxLayout(bl)
        # small console
        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        bl_layout.addWidget(Console_title)
        bl_layout.addWidget(self.console)

        #Bottom Right Panel
        br = QWidget();
        br.setLayout(QVBoxLayout())

        IOS_Func = IOS_Data_Grabber.iPhone(self.console_print)
        Models, IOS, self.before_iPhone_IOS = IOS_Func.Main_Function()
        IOS.sort(key=lambda v: [int(x) for x in v.split(".")],reverse=True)

        sorted_devices = sorted(Models, key=lambda d: ident_key(d["identifier"]), reverse=True)
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
        self.Selected_IOS = item.text()

    def ios_Model_selected(self, item):
        self.Selected_IOS_Model = item.text()

    def console_print(self, text):
        self.console.appendPlainText(text)

    def Model_From_List(self, current):
        model = current.text()
        model_name, model_ident = model.split(" | ")
        for ios in self.before_iPhone_IOS:
            if ios.get("identifier", "") == model_ident:
                self.IOS_List.clear()
                seen = []
                for items in ios.get('versions'):
                    if items not in seen:
                        seen.append(items)
                        self.IOS_List.addItem(items)
app = QApplication()
window = MainWindow()
window.show()
app.exec_()