import json
import os.path
import re
import socket
import subprocess
import threading
import time
from concurrent.futures.thread import ThreadPoolExecutor

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QInputDialog, \
    QAbstractItemView, QListWidget, QMenu


#Used to inject shift clicking
class MyListWidget(QListWidget):
    def __init__(self, pc_page):
        super().__init__()
        self.pc_page = pc_page

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.modifiers() & Qt.ShiftModifier:
            item = self.itemAt(event.pos())
            if item:
                old_bg = item.background()
                old_fg = item.foreground()

                item.setBackground(QColor("black"))
                item.setForeground(QColor("white"))

                menu = QMenu(self)
                open_action = menu.addAction("Open")
                rename_action = menu.addAction("Rename")
                delete_action = menu.addAction("Delete")

                action = menu.exec(self.mapToGlobal(event.pos()))

                item.setBackground(old_bg)
                item.setForeground(old_fg)

                if action == open_action:
                    print("Open", item.text())
                elif action == rename_action:
                    print("Rename", item.text())
                elif action == delete_action:
                    self.pc_page.Delete_host(item)
                return

        super().mousePressEvent(event)

class PCPage(QWidget):
    First_Ran = False
    def __init__(self, console_print=None, Resources=None):
        super().__init__()
        self.Console_Print = console_print
        self.shared_data = Resources
        self.worker_thread = None
        self.stop_event = threading.Event()
        self.Selected_Host = None

        main_layout = QHBoxLayout(self)

        self.Backend_Computer_List = []
        self.Computer_list = MyListWidget(self)
        self.Computer_list.setFixedWidth(300)
        self.Computer_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.Computer_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.Computer_list.itemClicked.connect(self.Host_Select)
        self.Computer_list.customContextMenuRequested.connect(self.unselect_item)

        # Left area
        left = QWidget()
        left.setFixedWidth(350)
        left_Root_layout = QVBoxLayout(left)
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)

        top_layout.addWidget(QLabel("Remote Computer List"))
        Add_Button = QPushButton('+⃝')
        Add_Button.setFixedSize(30, 30)
        Add_Button.setStyleSheet(""" QPushButton { background-color: #3A3A3D; color: white;} QPushButton:pressed { background-color: #1E1E20; } """)
        Add_Button.clicked.connect(self.Add_New_Computer)
        top_layout.addWidget(Add_Button)

        left_Root_layout.addWidget(top_widget)
        left_Root_layout.addWidget(self.Computer_list)


        # Right area
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(5, 5, 5, 5)

        WOL_Button =  QPushButton('Wake-On-Lan')
        WOL_Button.setFixedSize(100, 40)
        WOL_Button.clicked.connect(lambda: self.Wake_On_Lan(self.Selected_Host))
        WOL_Button.setStyleSheet(""" QPushButton { background-color: black; color: white;} QPushButton:pressed { background-color: #1E1E20; } """)

        Shutdown_Button =  QPushButton('Shutdown')
        Shutdown_Button.setFixedSize(100, 40)
        Shutdown_Button.clicked.connect(lambda: self.Shutdown(self.Selected_Host))
        Shutdown_Button.setStyleSheet(""" QPushButton { background-color: black; color: white;} QPushButton:pressed { background-color: #1E1E20; } """)


        right_layout.addWidget(WOL_Button, alignment=Qt.AlignTop)


        left.setStyleSheet(""" background-color: #2F2F32; border: 1px solid #3A3A3D; border-radius: 10px; """)
        right.setStyleSheet(""" background-color: #2F2F32; border: 1px solid #3A3A3D; border-radius: 10px; """)

        main_layout.addWidget(left)
        main_layout.addWidget(right)

    #Button Functions below
    def Wake_On_Lan(self, Host_PC=None):
        if Host_PC is None:
            self.Console_Print(f'Please Select a Option as {Host_PC} not a option')
            return
        for Host_PC in Host_PC:
            for device_info in self.Backend_Computer_List:
                expected = f"{device_info['Host']} ({device_info['Username']}) | Active: {device_info['Active']}"
                if expected != str(Host_PC).replace("['", '').replace("']", ''):
                    continue
                self.Console_Print(f"Wake-On-Lan on {Host_PC}")

                mac_address = device_info['Mac Address'].replace(":", "").replace("-", "")
                if len(mac_address) != 12:
                    raise ValueError("Invalid MAC address")

                magic_packet = bytes.fromhex("FF" * 6 + mac_address * 16)

                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                    sock.sendto(magic_packet, ("255.255.255.255", 9))

    #Menu Functions below
    def Add_New_Computer(self):
        Host_Machine, ok = QInputDialog.getText(self, "IP/Domain Name", "Please enter your Computer Name or IP Address")
        if ok:
            with ThreadPoolExecutor() as executor:
                activity = executor.submit(self.is_Alive, Host_Machine)
                Mac = executor.submit(self.get_mac, Host_Machine)
                Username, ok = QInputDialog.getText(self, "Username", "Please enter your Computer Username")
                if ok:
                    Password, ok = QInputDialog.getText(self, "Password", "Please enter your Computer Password")
                    if ok:
                        Append_List = {
                                'Host': Host_Machine,
                                'Username': Username,
                                'Password': Password,
                                'Mac Address': Mac.result(),
                                'Active': activity.result()
                            }
                        exists = any(pc['Host'] == Host_Machine and pc['Username'] == Username for pc in self.Backend_Computer_List)
                        if exists:
                            self.Console_Print(f'[Remote PC] {Host_Machine} or {Host_Machine}/{Username} already exists')
                            return
                        if not exists:
                            self.Backend_Computer_List.append(Append_List)
                            self.Computer_list.addItem(f"{Host_Machine} ({Username}) | Active: {activity.result()}")
                            with open("Modules/DataBases/Machines.json", 'w') as file:
                                json.dump(self.Backend_Computer_List, file, indent=4)

    def Host_Select(self, item):
        self.Selected_Host = [i.text() for i in self.Computer_list.selectedItems()]

    def unselect_item(self, pos):
        item = self.Computer_list.itemAt(pos)
        if item:
            item.setSelected(False)

    def mousePressEvent(self, event):
        if (event.button() == Qt.LeftButton and event.modifiers() & Qt.ShiftModifier):
            item = self.itemAt(event.pos())
            if item:
                menu = QMenu(self)
                menu.addAction("Open")
                menu.addAction("Rename")
                menu.addAction("Delete")
                menu.exec(self.mapToGlobal(event.pos()))
                return  # stops normal selection if you want

        super().mousePressEvent(event)

    def is_Alive(self, target, timeout=1):
        try:
            with socket.create_connection((target, '22'), timeout):
                return True
        except:
            return False

    def get_mac(self, ip):
        result = subprocess.check_output(["arp", "-n", ip]).decode()
        match = re.search(r"([0-9a-f]{2}:){5}[0-9a-f]{2}", result.lower())
        return match.group(0) if match else None

    def Background_Thread(self, PC_Activity=True):
        def PC_Activity_Thread():
            if PC_Activity:
                if len(self.Backend_Computer_List) == 0:
                    return
                for check in self.Backend_Computer_List:
                    if self.stop_event.is_set():
                        break
                    alive = self.is_Alive(check['Host'])
                    if alive != check['Active']:
                        check['Active'] = alive
                        for x in range(self.Computer_list.count()):
                            item = self.Computer_list.item(x)
                            expected = f"{check['Host']} ({check['Username']}) | Active: {check['Active']}"
                            if item.text().startswith(f"{check['Host']} ({check['Username']})"):
                                item.setText(expected)
        def Shared_Thread():
            if self.Computer_list.count() == 0:
                print('Error in first bit')
                return
            if len(self.Backend_Computer_List) == 0:
                return
            append_list = []
            for x in range(len(self.Backend_Computer_List)):
                if self.Backend_Computer_List[x]['Active'] == True:
                    append_list.append(self.Backend_Computer_List[x])
            self.shared_data.copy_remote(append_list)

        while not self.stop_event.is_set():
            for x in range(len(self.Backend_Computer_List)):
                item = self.Backend_Computer_List[x]['Mac Address']
                if (item is None or item in ["", " "]):
                    self.Backend_Computer_List[x]['Mac Address'] = self.get_mac(self.Backend_Computer_List[x]['Host'])
                    with open("Modules/DataBases/Machines.json", 'w') as file:
                        json.dump(self.Backend_Computer_List, file, indent=4)

            if PC_Activity:
                threading.Thread(target=PC_Activity_Thread).start()

            if self.shared_data is not None:
                threading.Thread(target=Shared_Thread).start()

            time.sleep(1)

    def on_enter(self):
        self.stop_event.clear()
        if self.worker_thread and self.worker_thread.is_alive():
            self.Console_Print("Worker already running")
            return

        self.worker_thread = threading.Thread(target=self.Background_Thread, daemon=True)
        self.worker_thread.start()
        self.Console_Print("PC page worker started")

    def load_data(self):
        if os.path.exists("Modules/DataBases/Machines.json"):
            with open("Modules/DataBases/Machines.json", 'r') as file:
                self.Backend_Computer_List = json.load(file)
            with ThreadPoolExecutor() as executor:
                for i in range(len(self.Backend_Computer_List)):
                    Results = executor.submit(self.is_Alive, self.Backend_Computer_List[i]['Host'])
                    if not Results.result() == self.Backend_Computer_List[i]['Active']:
                        self.Backend_Computer_List[i]['Active'] = Results.result()
                    self.Computer_list.addItem(f"{self.Backend_Computer_List[i]['Host']} ({self.Backend_Computer_List[i]['Username']}) | Active: {self.Backend_Computer_List[i]['Active']}")

    def on_leave(self):
        self.stop_event.set()

    def Delete_host(self, item):
        text = item.text()

        for host in self.Backend_Computer_List[:]:
            if text == f"{host['Host']} ({host['Username']}) | Active: {host['Active']}":
                self.Backend_Computer_List.remove(host)
                with open("Modules/DataBases/Machines.json", 'w') as file:
                    json.dump(self.Backend_Computer_List, file, indent=4)

        row = self.Computer_list.row(item)
        self.Computer_list.takeItem(row)