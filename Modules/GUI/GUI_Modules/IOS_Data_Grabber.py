import json
import os
import queue
import threading
import requests

q = queue.Queue()

def Test_Wifi():
    try:
        requests.get("https://api.ipsw.me/v4/devices", timeout=(2, 5))
        q.put(True)
    except requests.exceptions.RequestException:
        q.put(False)

class iPhone:
    def __init__(self, console_print=None):
        self.console_print = console_print or (lambda msg: None)
        self.iPhone_IOS = []
        self.iPhone_Beta_IOS = []
        self.iPhone_Models = []
        self.iPad_Models = []
        self.Mac_Models = []

        self.Offline_IOS_Index = []
        self.Offline_Beta_IOS_Index = []
        self.Offline_iPhone_IOS = []
        self.Offline_Beta_iPhone_IOS = []
        self.Offline_iPhone_Models = []
        self.Offline_iPad_Models = []
        self.Offline_Mac_Models = []

        threading.Thread(target=Test_Wifi).start()
        self.Wifi_Status = q.get()

        self.Offline_iPhone_Models_Files = False
        self.Offline_iPad_Models_Files = False
        self.Offline_Mac_Models_Files = False
        self.Offline_iPhone_IOS_Files = False
        if os.path.exists("Modules/DataBases"):
            for file in os.listdir("Modules/DataBases"):
                if file == "iPhone_Models.json":
                    self.Offline_iPhone_Models_Files = True
                    with open("Modules/DataBases/iPhone_Models.json", 'r') as file:
                        offiPhone = json.load(file)
                    self.Offline_iPhone_Models.extend(offiPhone)
                if file == "iPad_Models.json":
                    self.Offline_iPad_Models_Files = True
                    with open("Modules/DataBases/iPad_Models.json", 'r') as file:
                        offiPad = json.load(file)
                    self.Offline_iPad_Models.extend(offiPad)
                if file == "Mac_Models.json":
                    self.Offline_Mac_Models_Files = True
                    with open("Modules/DataBases/Mac_Models.json", 'r') as file:
                        offMac = json.load(file)
                    self.Offline_Mac_Models.extend(offMac)

                if file == "iPhone_IOS.json":
                    self.Offline_iPhone_IOS_Files = True
                    with open("Modules/DataBases/iPhone_IOS.json", 'r') as file:
                        offios = json.load(file)
                    self.Offline_iPhone_IOS.extend(offios)
            if not self.Wifi_Status:
                self.console_print("[Warning] Error With Wifi Running in Offline Mode")
                self.console_print("-------------------------------------------------------")
                self.console_print(f"[Statuses] Offline iPhone Database: {self.Offline_iPhone_Models_Files}")
                self.console_print(f"[Statuses] Offline IOS Database: {self.Offline_iPhone_IOS_Files}")
                self.console_print("-------------------------------------------------------")
                self.console_print(f"[Statuses] Offline iPad Database: {self.Offline_iPad_Models_Files}")
                self.console_print("-------------------------------------------------------")
                self.console_print(f"[Statuses] Offline Mac Database: {self.Offline_Mac_Models_Files}")
                self.console_print("-------------------------------------------------------")


        self.IPSW_API = "https://api.ipsw.me/v4"
        self.IPSW_Beta_API = 'https://ipswbeta.dev/v1'

    def Grab_Apple_Models(self, Wifi_Check=True):
        if (self.Wifi_Status and Wifi_Check):
            self.console_print("[Apple Models] Initiating API Models Request")
            Apple_URL = self.IPSW_API + "/devices"
            ALL_Apple = requests.get(Apple_URL)
            for Product in ALL_Apple.json():
                if Product["identifier"].startswith("iPhone"):
                    self.iPhone_Models.append(Product)
                if Product["identifier"].startswith("iPad"):
                    self.iPad_Models.append(Product)
                if Product["identifier"].startswith("Mac"):
                    self.Mac_Models.append(Product)
            if len(self.iPhone_Models) > 0:
                self.console_print("-------------------------------------------------------")
                self.console_print("[Apple Models] Saving iPhone Models for Offline Mode")
                if os.path.exists("Modules/DataBases/iPhone_Models.json"):
                    self.console_print("[Apple Models] Error iPhone_Models.json already exists")
                    self.console_print("[Apple Models] Replacing File")
                    os.remove("Modules/DataBases/iPhone_Models.json")
                with open("Modules/DataBases/iPhone_Models.json", 'w') as file:
                    json.dump(self.iPhone_Models, file, indent=4)
                self.console_print("[Apple Models] Saved iPhone_Models.json Completed")

            if len(self.iPad_Models) > 0:
                self.console_print("-------------------------------------------------------")
                self.console_print("[Apple Models] Saving iPad Models for Offline Mode")
                if os.path.exists("Modules/DataBases/iPad_Models.json"):
                    self.console_print("[Apple Models] Error iPad_Models.json already exists")
                    self.console_print("[Apple Models] Replacing File")
                    os.remove("Modules/DataBases/iPad_Models.json")
                with open("Modules/DataBases/iPad_Models.json", 'w') as file:
                    json.dump(self.iPad_Models, file, indent=4)
                self.console_print("[Apple Models] Saved iPad_Models.json Completed")

            if len(self.Mac_Models) > 0:
                self.console_print("-------------------------------------------------------")
                self.console_print("[Apple Models] Saving Mac Models for Offline Mode")
                if os.path.exists("Modules/DataBases/Mac_Models.json"):
                    self.console_print("[Apple Models] Error Mac_Models.json already exists")
                    self.console_print("[Apple Models] Replacing File")
                    os.remove("Modules/DataBases/Mac_Models.json")
                with open("Modules/DataBases/Mac_Models.json", 'w') as file:
                    json.dump(self.Mac_Models, file, indent=4)
                self.console_print("[Apple Models] Saved Mac_Models.json Completed")
            self.console_print("-------------------------------------------------------")
        elif (not self.Wifi_Status or not Wifi_Check):
            return
        else:
            raise Exception("Error")

    def Stable_IOS(self, Wifi_Check=True, Grab_iPhone=True):
        if (self.Wifi_Status and Wifi_Check):
            if Grab_iPhone:
                self.IOS_Index = []
                self.iPhone_IOS_Index = []
                for i in range(len(self.iPhone_Models)):
                    IOS_URL = self.IPSW_API + "/device/" + self.iPhone_Models[i]["identifier"]
                    Model_Version = requests.get(IOS_URL).json()
                    temp_iPhone_IOS_Index = []
                    for fw in Model_Version.get('firmwares', []):
                        version = fw.get('version')
                        temp_iPhone_IOS_Index.append(version)
                    self.iPhone_IOS_Index.append({
                        "name": self.iPhone_Models[i]["name"],
                        "identifier": self.iPhone_Models[i]["identifier"],
                        "versions": temp_iPhone_IOS_Index
                    })
                for device in self.iPhone_IOS_Index:
                    for v in device["versions"]:
                        if v not in self.IOS_Index:
                            self.IOS_Index.append(v)
                self.IOS_Index.sort(key=lambda v: [int(x) for x in v.split(".")])
        elif (not self.Wifi_Status) or (not Wifi_Check):
            for device in self.Offline_iPhone_IOS:
                for v in device["versions"]:
                    if v not in self.Offline_IOS_Index:
                        self.Offline_IOS_Index.append(v)
            self.Offline_IOS_Index.sort(key=lambda v: [int(x) for x in v.split(".")])
        else:
            raise Exception("Error")

    def Beta_IOS(self, Wifi_Check=True, Grab_iPhone=True):
        if (self.Wifi_Status and Wifi_Check):
            if Grab_iPhone:
                self.Beta_IOS_Index = []
                self.iPhone_Beta_IOS_Index = []
                for i in range(len(self.iPhone_Models)):
                    IOS_URL = self.IPSW_API + "/firmware/" + self.iPhone_Models[i]["identifier"]
                    Model_Version = requests.get(IOS_URL).json()
                    temp_iPhone_IOS_Index = []
                    for fw in Model_Version.get('firmwares', []):
                        if fw['beta']:
                            version = fw.get('version')
                            temp_iPhone_IOS_Index.append(version)
                    self.iPhone_Beta_IOS_Index.append({
                        "name": self.iPhone_Models[i]["name"],
                        "identifier": self.iPhone_Models[i]["identifier"],
                        "versions": temp_iPhone_IOS_Index
                    })
                for device in self.iPhone_Beta_IOS_Index:
                    for v in device["versions"]:
                        if v not in self.Beta_IOS_Index:
                            self.Beta_IOS_Index.append(v)
                self.Beta_IOS_Index.sort(key=lambda v: [int(x) for x in v.split(".")])
        elif (not self.Wifi_Status) or (not Wifi_Check):
            for device in self.Offline_iPhone_IOS:
                for v in device["versions"]:
                    if v not in self.Offline_Beta_IOS_Index:
                        self.Offline_Beta_IOS_Index.append(v)
            self.Offline_Beta_IOS_Index.sort(key=lambda v: [int(x) for x in v.split(".")])
        else:
            raise Exception("Error")

    def Main_Function(self):
        self.Grab_Apple_Models()
        self.Stable_IOS()
        if len(self.iPhone_Models) > 0:
            return self.iPhone_Models, self.IOS_Index, self.iPhone_IOS_Index
        else:
            return self.Offline_iPhone_Models, self.Offline_IOS_Index, self.Offline_iPhone_IOS
