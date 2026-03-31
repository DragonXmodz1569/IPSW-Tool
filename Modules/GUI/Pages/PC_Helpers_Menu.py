import json
import os.path
import socket
import threading
from concurrent.futures.thread import ThreadPoolExecutor

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QListWidget, QPushButton, QInputDialog


class PCPage(QWidget):
    First_Ran = False
    def __init__(self, console_print=None):
        super().__init__()
        self.Console_Print = console_print

        main_layout = QHBoxLayout(self)

        self.Backend_Computer_List = []
        self.Computer_list = QListWidget()
        self.Computer_list.setFixedWidth(300)

        # Left area
        left = QWidget()
        left.setFixedWidth(350)
        left_Root_layout = QVBoxLayout(left)
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)

        top_layout.addWidget(QLabel("Remote Computer List"))
        Add_Button = QPushButton('+⃝')
        Add_Button.setFixedSize(30, 30)
        Add_Button.setStyleSheet("""
    QPushButton { background-color: #3A3A3D; color: white;}
    QPushButton:pressed { background-color: #1E1E20; } """)
        Add_Button.clicked.connect(self.Add_New_Computer)
        top_layout.addWidget(Add_Button)

        left_Root_layout.addWidget(top_widget)
        left_Root_layout.addWidget(self.Computer_list)


        # Right area
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.addWidget(QLabel("Right Area"))

        left.setStyleSheet(""" background-color: #2F2F32; border: 1px solid #3A3A3D; border-radius: 10px; """)
        right.setStyleSheet(""" background-color: #2F2F32; border: 1px solid #3A3A3D; border-radius: 10px; """)

        main_layout.addWidget(left)
        main_layout.addWidget(right)

    def Add_New_Computer(self):
        Host_Machine, ok = QInputDialog.getText(self, "IP/Domain Name", "Please enter your Computer Name or IP Address")
        if ok:
            with ThreadPoolExecutor() as executor:
                activity = executor.submit(self.is_Alive, Host_Machine)
                Username, ok = QInputDialog.getText(self, "Username", "Please enter your Computer Username")
                if ok:
                    Password, ok = QInputDialog.getText(self, "Password", "Please enter your Computer Password")
                    if ok:
                        Append_List = {
                                'Host': Host_Machine,
                                'Username': Username,
                                'Password': Password,
                                'Active': activity.result()
                            }
                        exists = any(pc['Host'] == Host_Machine and pc['Username'] == Username for pc in self.Backend_Computer_List)
                        if exists:
                            self.Console_Print(f'[Remote PC] {Host_Machine} or {Host_Machine}/{Username} already exists')
                            return
                        if not exists:
                            self.Backend_Computer_List.append(Append_List)
                            self.Computer_list.addItem(f"{Host_Machine} ({Username}), | Active: {activity.result()}")
                            with open("Modules/DataBases/Machines.json", 'w') as file:
                                json.dump(self.Backend_Computer_List, file, indent=4)

    def is_Alive(self, target, timeout=1):
        try:
            with socket.create_connection((target, '22'), timeout):
                return True
        except:
            return False

    def load_data(self):
        if PCPage.First_Ran == False:
            with open("Modules/DataBases/Machines.json", 'r') as file:
                self.Backend_Computer_List = json.load(file)
            with ThreadPoolExecutor() as executor:
                for i in range(len(self.Backend_Computer_List)):
                    Results = executor.submit(self.is_Alive, self.Backend_Computer_List[i]['Host'])
                    if not Results.result() == self.Backend_Computer_List[i]['Active']:
                        self.Backend_Computer_List[i]['Active'] = Results.result()
                    self.Computer_list.addItem(f"{self.Backend_Computer_List[i]['Host']} ({self.Backend_Computer_List[i]['Username']}) | Active: {self.Backend_Computer_List[i]['Active']}")
