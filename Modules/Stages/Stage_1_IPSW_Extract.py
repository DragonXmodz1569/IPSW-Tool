import json
import os
import subprocess
import shutil



class IPSW_Control:
    def __init__(self, IPSW_Directory='IPSW Files', Extract_Path='Extracted_Directory', console_print=None):
        self.console_print = console_print or (lambda msg: None)
        if not os.path.exists(IPSW_Directory):
            self.console_print('IPSW Directory does not exist please Double Check')
            return
        self.IPSW_Directory = IPSW_Directory
        with open('Modules/DataBases/iPhone_Models.json', 'r') as iPhone_Models:
            self.iPhone_Model_map = json.load(iPhone_Models)
        with open('Modules/DataBases/iPhone_IOS.json', 'r') as iPhone_Versions:
            self.iPhone_Version_map = json.load(iPhone_Versions)
        self.Extract_Path = Extract_Path
        os.makedirs(self.Extract_Path, exist_ok=True)
        self.Downloaded_IPSW_Files = []
        self.Processors = []

    def wait_process(self):
        failed = []
        for Process in self.Processors:
            ouput = Process.communicate()[0]
            if Process.returncode != 0:
                failed.append((Process.returncode, ouput))
        self.Processors.clear()
        return failed

    def IPSW_Files_Locate(self, iPhone_Model=None, iPhone_Version=None):
        if iPhone_Model is None:
            self.console_print('[Stage 1] No iPhone Model provided Must be provided')
            return
        Chosen_Version = None
        for Model_info in self.iPhone_Model_map:
            if Model_info['identifier'] == iPhone_Model or Model_info['name'] == iPhone_Model:
                Chosen_Model = Model_info
                for version_map in self.iPhone_Version_map:
                    if version_map['name'] == Chosen_Model['name'] or version_map['identifier'] == Chosen_Model['identifier']:
                        if iPhone_Version is None:
                            Chosen_Version = version_map['versions']
                        if iPhone_Version is not None:
                            for ios in version_map['versions']:
                                if ios == iPhone_Version:
                                    Chosen_Version = ios

        for file in os.listdir(os.path.join(self.IPSW_Directory, Chosen_Model['identifier'])):
            if not file.endswith('.ipsw'):
                continue
            if Chosen_Version:
                if isinstance(Chosen_Version, str):
                    file_part = file.replace('.ipsw', '').split('_')
                    file_version = file_part[1]
                    if Chosen_Version and file_version != Chosen_Version:
                        continue
            Extracted_path = file.replace('.ipsw', '').split('_')
            Extracted_Check = os.path.exists(os.path.join(self.Extract_Path,Chosen_Model['identifier'],f'{Extracted_path[1]}_{Extracted_path[2]}'))
            self.Downloaded_IPSW_Files.append({
                'File Location': os.path.join(self.IPSW_Directory, Chosen_Model['identifier']),
                'File Name': file,
                'Size': os.path.getsize(os.path.join(self.IPSW_Directory,Chosen_Model['identifier'],file)),
                'Extracted Location': os.path.join(self.Extract_Path, Chosen_Model['identifier'],f'{Extracted_path[1]}_{Extracted_path[2]}'),
                'Extracted': Extracted_Check
            })

    def Unzip_Decrypt_Files(self, iPhone_Model=None, iPhone_Version=None):
        if iPhone_Model is None:
            self.console_print('[Stage 1] No iPhone Model provided Must be provided')
            return
        if iPhone_Version:
            match = False
            for file in os.listdir(os.path.join(self.IPSW_Directory, iPhone_Model)):
                if not file.endswith('.ipsw'):
                    continue
                file_part = file.replace('.ipsw', '').split('_')
                file_version = file_part[1]
                if iPhone_Version and file_version != iPhone_Version:
                    continue
                Extracted_path = file.replace('.ipsw', '').split('_')
                Extracted_Check = os.path.exists(os.path.join(self.Extract_Path, iPhone_Model, f'{Extracted_path[1]}_{Extracted_path[2]}'))
                iPhone_Version = []
                iPhone_Version .append({
                    'File Location': os.path.join(self.IPSW_Directory, iPhone_Model),
                    'File Name': file,
                    'Extracted Location': os.path.join(self.Extract_Path, iPhone_Model,f'{Extracted_path[1]}_{Extracted_path[2]}'),
                    'Extracted': Extracted_Check
                })
                match = True
            if not match:
                self.console_print('[Stage 1] IPSW Files Dont Exist Please Download File')
                return
        if iPhone_Version is None:
            if len(self.Downloaded_IPSW_Files) == 0:
                print('[Stage 1] No iPhone Version provided or Provided by IPSW_Files_Locate')
                self.console_print('[Stage 1] No iPhone Version provided or Provided by IPSW_Files_Locate')
                return
            if len(self.Downloaded_IPSW_Files) >= 1:
                iPhone_Version = [self.Downloaded_IPSW_Files]

        extract_list = []
        for item in iPhone_Version:
            if isinstance(item, list):
                extract_list.extend(item)
            else:
                extract_list.append(item)
        for ipsw in extract_list:
            if ipsw['Extracted']:
                continue
            os.makedirs(ipsw["Extracted Location"], exist_ok=True)
            unzip_command = subprocess.Popen(['unzip', f"{ipsw['File Location']}/{ipsw['File Name']}", '-d', ipsw['Extracted Location']], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
            self.Processors.append(unzip_command)

        failed = self.wait_process()
        if len(failed) > 0:
            print(f'Stage 1 have {len(failed)} failed')
        self.console_print(f'[{iPhone_Model}][Stage 1] IPSW UnzipPart 1/10 Finished for {iPhone_Version}')

