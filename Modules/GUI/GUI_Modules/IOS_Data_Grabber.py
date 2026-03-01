import json
import os
import requests

class iPhone:
    def __init__(self):
        self.iPhone_Models = []
        self.iPad_Models = []
        self.IOS = []
        self.Have_Models = False
        self.Have_IOS = False
        self.ipsw_api = "https://api.ipsw.me/v4"
        if os.path.exists('Modules/Databases'):
            for files in os.listdir('Modules/Databases'):
                if files == 'iPhone_Models.json':
                    self.Have_Models = 'Modules/Databases/iPhone_Models.json'
                if files == 'iPhone_IOS.json':
                    self.Have_IOS = 'Modules/Databases/iPhone_IOS.json'

    def Model_Information(self):
        if self.Have_Models:
            return
        url = self.ipsw_api + '/devices'
        ALL_Apple = requests.get(url)
        #Seperating the Models up iPhone/iPad
        for product in ALL_Apple.json():
            if product['identifier'].startswith('iPhone'):
                self.iPhone_Models.append(product)
            if product['identifier'].startswith('iPad'):
                self.iPad_Models.append(product)
        if len(self.iPhone_Models) > 0:
            if os.path.exists('Modules/DataBases/iPhone_Models.json'):
                os.remove('Modules/DataBases/iPhone_Models.json')
            with open('Modules/DataBases/iPhone_Models.json', 'w') as outfile:
                json.dump(self.iPhone_Models, outfile, indent=4)

    def IOS_Stable(self):
        if self.Have_IOS:
            return
        for i in range(len(self.iPhone_Models)):
            url = self.ipsw_api + '/device/' + self.iPhone_Models[i]['identifier']
            IOSes = requests.get(url).json()
            list = []
            for fw in IOSes.get('firmwares', []):
                ver = fw.get('version')
                list.append(ver)
            self.IOS.append({
                "name": self.iPhone_Models[i]["name"],
                "identifier": self.iPhone_Models[i]["identifier"],
                "versions": list
            })
        with open('Modules/DataBases/iPhone_IOS.json', 'w') as outfile:
            json.dump(self.IOS, outfile, indent=4)

    def Main_Function(self):
        if not self.Have_Models:
            self.Model_Information()
        if not self.Have_IOS:
            self.IOS_Stable()

        return self.iPhone_Models, self.IOS

