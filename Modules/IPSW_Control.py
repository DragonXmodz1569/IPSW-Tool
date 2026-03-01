import os
import re
import json
import plistlib
import shutil
import subprocess

Processors = []

def wait_process():
    failed = []
    for Process in Processors:
        ouput = Process.communicate()[0]
        if Process.returncode != 0:
            failed.append((Process.returncode, ouput))
    Processors.clear()
    return failed

class IPSW:
    def __init__(self, IPSW_Files_Directory=None):
        self.IPSW_Files = []
        if not IPSW_Files_Directory:
            self.IPSW_Files_Directory = 'IPSW Files'
        with open('Modules/DataBases/iPhone_Models.json', 'r') as models:
            self.Device_map = json.load(models)
        self.Extract_Path = 'Work_Directory'
        os.makedirs(self.Extract_Path, exist_ok=True)

    def IPSW_Files_Locate(self):
        for file in os.listdir(self.IPSW_Files_Directory):
            if file.startswith('._'):
                continue
            if not file.endswith('.ipsw'):
                continue

            Models = []
            identifier = str(file.split('_')[0])
            LineUp = re.findall(r"iPhone\d+,\d+", identifier)
            for m in sorted(set(LineUp)):
                Models.append(self.Device_map.get(m, 'unknown'))
            if not len(Models) == 2:
                Models = str(Models).replace("['", '').replace("']", '')
            else:
                Models = str(Models)
            Version = str(file.split('_')[1])
            BuildID = str(file.split('_')[2])

            self.IPSW_Files.append({
                'IPSW File': file,
                'Version': Version,
                'BuildID': BuildID,
                'iPhone Identifer': identifier,
                'iPhone Model': Models,
                'IPSW File Location': f'{self.IPSW_Files_Directory}/{file}'
            })

    def IPSW_Files_Extract(self, File=None, Replace=False):
        interalmode = False

        if File is None:
            File = self.IPSW_Files
            interalmode = True

        if interalmode:
            for ipsw in File:
                if not ipsw['IPSW File'].endswith('.ipsw'):
                    continue

                unzip_output = f'{ipsw["Version"]}_{ipsw["BuildID"]}_{ipsw["iPhone Model"].replace(" ", ".").replace(",.", ",")}'

                if not os.path.exists(f"{self.Extract_Path}/{unzip_output}"):
                    command =subprocess.Popen([
                        "unzip", f"{self.IPSW_Files_Directory}/{ipsw['IPSW File']}",
                        "-d", f"{self.Extract_Path}/{unzip_output}",
                    ],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
                    ipsw['IPSW Extracted'] = f'{self.Extract_Path}/{unzip_output}'
                    Processors.append(command)
                else:
                    ipsw['IPSW Extracted'] = f'{self.Extract_Path}/{unzip_output}'

            failed = wait_process()
            if len(failed) > 0:
                print(f'Stage 1 have {len(failed)} failed')

            #Used Grab Pem Key to
            for ipsw in File:
                if os.path.exists(f"{ipsw['IPSW Extracted']}/PEM"):
                    continue
                else:
                    os.makedirs(f"{ipsw['IPSW Extracted']}/PEM")
                    PEM_Extract = subprocess.Popen([
                        'ipsw', 'extract', '--fcs-key',
                        ipsw['IPSW File Location'], '-o',
                        f'{ipsw["IPSW Extracted"]}/PEM',
                    ],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
                    Processors.append(PEM_Extract)

            failed = wait_process()
            if len(failed) > 0:
                print(f'Stage 2 have {len(failed)} failed')

            for ipsw in File:
                if not os.path.exists(f"{ipsw['IPSW Extracted']}/PEM"):
                    exit()
                for Pem in os.listdir(f'{ipsw["IPSW Extracted"]}/PEM/{ipsw["BuildID"]}__{ipsw["iPhone Identifer"]}'):
                    ipsw['Pem File Location'] = f'{ipsw["IPSW Extracted"]}/PEM/{ipsw["BuildID"]}__{ipsw["iPhone Identifer"]}'
                    ipsw['Pem File'] = Pem

                    if os.path.isfile(f"{ipsw["IPSW Extracted"]}/{ipsw['Pem File'].replace('.aea.pem', '')}"):
                        continue

                    if Pem.replace('.pem', '') in os.listdir(ipsw["IPSW Extracted"]):
                        Target_DMG = Pem.replace('.pem', '')
                    Decrypt_File = subprocess.Popen([
                        'ipsw', 'fw', 'aea',
                        '--pem', f'{ipsw['Pem File Location']}/{ipsw['Pem File']}', f'{ipsw['IPSW Extracted']}/{Target_DMG}',
                        '-o' ,f"{ipsw["IPSW Extracted"]}"
                    ])
                    Processors.append(Decrypt_File)

            failed = wait_process()
            if len(failed) > 0:
                print(f'Stage 3 have {len(failed)} failed')

            for ipsw in File:
                for file in os.listdir(ipsw["IPSW Extracted"]):
                    if file == ipsw["Pem File"].replace('.aea.pem', ''):
                        ipsw['Pem Decrypted File'] = f'{ipsw["IPSW Extracted"]}/{file}'
                    else:
                        continue

                if ipsw['Pem Decrypted File'] is None:
                    continue

                if (not os.path.exists(f"{ipsw['IPSW Extracted']}/PEM/Caches") or Replace == True):
                    Decrypt_File = subprocess.run([
                            'hdiutil', 'attach', '-readonly', '-nobrowse', '-plist', ipsw['Pem Decrypted File']],
                            stdout=subprocess.PIPE,
                            check=True
                        )

                    info = plistlib.loads(Decrypt_File.stdout)

                    for e in info["system-entities"]:
                        if "mount-point" in e:
                            mount = e["mount-point"]
                        if "dev-entry" in e:
                            device = e["dev-entry"]

                    print("Mounted at:", mount)
                    print("Device:", device)

                    for R in os.listdir(mount):
                        if R == 'System':
                            for RS in os.listdir(f'{mount}/{R}'):
                                if RS == 'Library':
                                    for RSS in os.listdir(f'{mount}/{R}/{RS}'):
                                        if RSS == 'Caches':
                                            shutil.copytree(f'{mount}/{R}/{RS}/{RSS}/com.apple.dyld', f"{ipsw['IPSW Extracted']}/PEM/Caches", dirs_exist_ok=Replace)

                    subprocess.run(["hdiutil", "detach", device], check=True)
                    print("\nDetached.")


                if file == None:
                    print("file already found")
                    continue



        else:
            return