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

    def Stage_Updater(self, file, iPhone_Model):
        Extracted_path = file.replace('.ipsw', '').split('_')
        Extracted_Origins = os.path.join(self.Extract_Path, iPhone_Model, f'{Extracted_path[1]}_{Extracted_path[2]}')
        Extracted_Check_part_1 = os.path.exists(Extracted_Origins)
        Extracted_Check_End = None

        if Extracted_Check_part_1 == True:
            Extracted_Check_End = 'Part 1 unZip Done'
            current_folders = []
            for folder in os.listdir(Extracted_Origins):
                if os.path.isdir(os.path.join(Extracted_Origins, folder)):
                    current_folders.append(folder)
            if len(current_folders) == 1:
                Extracted_Check_End = False
                shutil.rmtree(Extracted_Origins)
            if len(current_folders) >= 2:
                for check in current_folders:
                    if os.path.isfile(check):
                        continue
                    if check == 'Extra':
                        for check2 in os.listdir(os.path.join(Extracted_Origins, check)):
                            if check2 == 'PEM':
                                Extracted_Check_End = 'Part 2 AEADecryption Done'

        if not Extracted_Check_part_1:
            return False, Extracted_Origins

        return Extracted_Check_End, Extracted_Origins

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

            Folder_Results, Folder_Path = self.Stage_Updater(file, iPhone_Model)

            self.Downloaded_IPSW_Files.append({
                'File Location': os.path.join(self.IPSW_Directory, Chosen_Model['identifier']),
                'File Name': file,
                'Size': os.path.getsize(os.path.join(self.IPSW_Directory,Chosen_Model['identifier'],file)),
                'Extracted Location': Folder_Path,
                'Extracted': Folder_Results
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

                Folder_Results, Folder_Path = self.Stage_Updater(file, iPhone_Model)

                iPhone_Version = []
                iPhone_Version .append({
                    'File Location': os.path.join(self.IPSW_Directory, iPhone_Model),
                    'File Name': file,
                    'Extracted Location': Folder_Path,
                    'Extracted': Folder_Results
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
        Folder_Exception = ['Part 1 unZip Done', 'Part 2 AEADecryption Done', True]
        for ipsw in extract_list:
            if ipsw['Extracted'] in Folder_Exception:
                continue
            os.makedirs(ipsw["Extracted Location"], exist_ok=True)
            unzip_command = subprocess.Popen(['unzip', f"{ipsw['File Location']}/{ipsw['File Name']}", '-d', ipsw['Extracted Location']], text=True)
            self.Processors.append(unzip_command)
            ipsw['Extracted'] = 'Part 1 unZip Done'

        failed = self.wait_process()
        if len(failed) > 0:
            print(f'Stage 1 have {len(failed)} failed')
        for update_stage_1 in extract_list:
            if update_stage_1['Extracted'] in Folder_Exception[1:]:
                continue
            self.console_print(f'[{iPhone_Model}][Stage 1] IPSW UnzipPart 1/10 Finished for {update_stage_1["Extracted Location"].split("/")[-1]}')
            self.console_print("----------------------------------------------------")
            self.console_print(f'[{iPhone_Model}][Stage 1] IPSW Initialising Stage 2')

        for ipsw in extract_list:
            self.console_print(f'[{iPhone_Model}][{ipsw["File Name"].split("_")[2]}] Grabbing PEM file')
            if ipsw['Extracted'] in Folder_Exception[2:]:
                continue
            if os.path.exists(os.path.join(ipsw['Extracted Location'], 'Extra', 'PEM')):
                continue
            os.makedirs(os.path.join(ipsw['Extracted Location'], 'Extra', 'PEM'), exist_ok=True)
            self.Processors.append(subprocess.Popen(['ipsw', 'extract', '--fcs-key', os.path.join(ipsw['File Location'], ipsw['File Name']), '-o', os.path.join(ipsw['Extracted Location'], 'Extra', 'PEM')], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True))


