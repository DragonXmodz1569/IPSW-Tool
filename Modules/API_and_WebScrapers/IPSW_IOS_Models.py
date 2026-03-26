import json
import os.path

import requests

class Apple:
    def __init__(self,console_print=None):
        if console_print is None:
            self.Console_Print = print
        else:
            self.Console_Print = console_print
        self.IPSW_API = "https://api.ipsw.me/v4"

        self.Internet_Activity = self.Internet_Check()
        if self.Internet_Activity == False:
            self.Console_Print('No Internet Activity Detected Running Offline')

        self.iPhone_IOS = []
        self.iPhone_Models = []
        self.iPad_Models = []
        self.Mac_Models = []

        if os.path.exists('Modules/DataBases'):
            for file in os.listdir('Modules/DataBases'):
                if file == 'iPhone_IOS.json':
                    with open('Modules/DataBases/iPhone_IOS.json') as json_file:
                        self.iPhone_IOS.extend(json.load(json_file))
                if file == 'iPhone_Models.json':
                    with open('Modules/DataBases/iPhone_Models.json') as json_file:
                        self.iPhone_Models.extend(json.load(json_file))
                if file == 'iPad_Models.json':
                    with open('Modules/DataBases/iPad_Models.json') as json_file:
                        self.iPad_Models.extend(json.load(json_file))
                if file == 'Mac_Models.json':
                    with open('Modules/DataBases/Mac_Models.json') as json_file:
                        self.Mac_Models.extend(json.load(json_file))
        else:
            os.mkdir('Modules/DataBases')

    def Internet_Check(self, Timeout=2):
        urls = [
            'https://api.ipsw.me/v4',
            'https://1.1.1.1',
        ]
        Passed = 0
        for url in urls:
            try:
                requests.get(url, timeout=Timeout)
                return True
            except requests.RequestException:
                continue
        return False

    def Apple_Models(self):
        if self.Internet_Activity == False:
            self.Console_Print("[Apple Models] Skipping Due to no Detected Wifi Connection")
            return
        self.Console_Print("-------------------------------------------------------")
        self.Console_Print("[Apple Models] Initiating API Models Request")
        Models_Url = self.IPSW_API + '/devices'
        All_Apple_Models = requests.get(Models_Url)
        Before_iPhone = len(self.iPhone_Models)
        Before_iPad = len(self.iPad_Models)
        Before_Mac = len(self.Mac_Models)
        for Model in All_Apple_Models.json():
            if Model["identifier"].startswith("iPhone"):
                identifier = Model.get("identifier", "")
                if any(x.get('identifier') == identifier for x in self.iPhone_Models):
                    continue
                self.iPhone_Models.append(Model)
            if Model["identifier"].startswith("iPad"):
                identifier = Model.get("identifier", "")
                if any(x.get('identifier') == identifier for x in self.iPad_Models):
                    continue
                self.iPad_Models.append(Model)
            if Model["identifier"].startswith("Mac"):
                identifier = Model.get("identifier", "")
                if any(x.get('identifier') == identifier for x in self.Mac_Models):
                    continue
                self.Mac_Models.append(Model)
        After_iPhone = len(self.iPhone_Models)
        After_iPad = len(self.iPad_Models)
        After_Mac = len(self.Mac_Models)
        self.Console_Print('[Apple Models] Updating Offline DataBase')
        if Before_iPhone != After_iPhone:
            self.Console_Print('[Apple Models] Updating iPhone Models')
            with open('Modules/DataBases/iPhone_Models.json', 'w') as outfile:
                json.dump(self.iPhone_Models, outfile, indent=4)
        if Before_iPad != After_iPad:
            self.Console_Print('[Apple Models] Updating iPad Models')
            with open('Modules/DataBases/iPad_Models.json', 'w') as outfile:
                json.dump(self.iPad_Models, outfile, indent=4)
        if Before_Mac != After_Mac:
            self.Console_Print('[Apple Models] Updating Mac Models')
            with open('Modules/DataBases/Mac_Models.json', 'w') as outfile:
                json.dump(self.Mac_Models, outfile, indent=4)

    def Stable_Apple_Versions(self, Grab_iPhone=True):
        if Grab_iPhone:
            iPhone_Index = []
            for i in range(len(self.iPhone_Models)):
                IOS_Url = self.IPSW_API + '/device/' + self.iPhone_Models[i]['identifier']
                Model_Versions = requests.get(IOS_Url).json()
                if 'firmwares' in Model_Versions:
                    Model_Versions['firmwares'] = sorted(
                        Model_Versions['firmwares'],
                        key=lambda x: tuple(map(int, x['version'].split('.')))
                    )
                iPhone_Index.append(Model_Versions)
            iPhone_Index = sorted(iPhone_Index, key=lambda x: x['identifier'])
            with open('Modules/DataBases/iPhone_IOS.json', 'w') as outfile:
                json.dump(iPhone_Index, outfile, indent=4)


    def Main_Function(self):
        if self.Internet_Activity:
            self.Apple_Models()
            self.Stable_Apple_Versions()
        return self.iPhone_Models, self.iPhone_IOS
