# main_gui.py
import re

from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QLineEdit, QTextEdit, QSlider, QProgressBar, QComboBox, QListWidget, QRadioButton
from PySide6.QtCore import Qt
from Modules.GUI.GUI_Modules import IOS_Data_Grabber


def ios_ver_key(v: str):
    nums = [int(x) for x in re.findall(r"\d+", v)]
    while len(nums) < 3:
        nums.append(0)
    return tuple(nums[:3])

def ident_key(ident: str):
    m = re.match(r"^iPhone(\d+),(\d+)$", ident)
    if not m:
        return (-1, -1)  # shove unknowns to the end
    return (int(m.group(1)), int(m.group(2)))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.Selected_IOS = None
        self.Selected_IOS_Model = None

        IOS_Func = IOS_Data_Grabber.iPhone()
        Models, IOS, before_iPhone_IOS = IOS_Func.Main_Function()
        IOS.sort(
            key=lambda v: [int(x) for x in v.split(".")],
            reverse=True
        )
        sorted_devices = sorted(Models, key=lambda d: ident_key(d["identifier"]), reverse=True)
        nameidentifier = [{"name": d["name"], "identifier": d["identifier"]} for d in sorted_devices]

        self.setWindowTitle("DragonXmodz1569 IPSW Tools")
        self.setFixedSize(800, 600)

        container = QWidget()
        self.setCentralWidget(container)

        IOS_List = QListWidget()
        IOS_List.addItems(IOS)
        IOS_List.itemClicked.connect(self.ios_selected)

        IOS_Models = QListWidget()
        for item in nameidentifier:
            IOS_Models.addItem(f'{item["name"]} | {item["identifier"]}')
        IOS_Models.itemClicked.connect(self.ios_Model_selected)

        # Top Right Side
        Selected_Button = QPushButton("Select")
        Selected_Button.setFixedSize(70, 30)
        Selected_Button.clicked.connect(lambda: print(f'Selected IOS: {self.Selected_IOS} and Model: {self.Selected_IOS_Model}'))

        GridLayout = QGridLayout(container)
        # make 4 “panels”

        #Top Left Panel - IOS and Model Selecting
        tl = QWidget();
        tl_layout = QHBoxLayout(tl)
        tl_layout.addWidget(IOS_List)
        tl_layout.addWidget(IOS_Models)

        #Top Right Panel - Button Options
        tr = QWidget();
        tr_layout = QHBoxLayout(tr)
        tr_layout.setContentsMargins(5, 5, 5, 5)
        tr_layout.addWidget(Selected_Button, alignment=Qt.AlignTop | Qt.AlignLeft)

        # Bottom Left Panel - Console
        bl = QWidget();
        bl.setLayout(QVBoxLayout())

        #Bottom Right Panel
        br = QWidget();
        br.setLayout(QVBoxLayout())

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

app = QApplication()
window = MainWindow()
window.show()
app.exec_()