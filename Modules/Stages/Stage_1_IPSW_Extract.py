import json
import os
import plistlib
import shutil
import subprocess


class IPSW_Control:
    def __init__(self, IPSW_Directory='IPSW Files', Extract_Path='Extracted_Directory', console_print=None):
        self.Processors = []
        self.Downloaded_IPSW_Files = []

        self.IPSW_Directory = IPSW_Directory
        self.Root_Extract_Path = Extract_Path

        self.iPhone_Model_Map = []
        self.iPhone_Version_Map = []
        self.iPad_Model_Map = []
        self.Mac_Model_Map = []

        self.Stages = ['Stage 0',
                       'Stage 1 Unzipped', 'Stage 2 AEADecryption',
                       'Stage 3 APFS Extraction'
                       'Stage 4 Cache Extraction'
                       ]

        if console_print is None:
            self.Console_Print = print
        else:
            self.Console_Print = console_print

    def get_dir_size(self, path):
        total = 0
        for root, dirs, files in os.walk(path):
            for file in files:
                fp = os.path.join(root, file)
                try:
                    total += os.path.getsize(fp)
                except OSError:
                    pass
        return total

    def wait_processes(self):
        failed = []
        for process in self.Processors:
            output, _ = process.communicate()
            if process.returncode != 0:
                failed.append({
                    "returncode": process.returncode,
                    "output": output
                })
        self.Processors.clear()
        return failed

    def IPSW_Stage_Finder(self, iPhone_Model=None, IPSW_File=None):
        if iPhone_Model is None:
            self.Console_Print('Error with iPhone Model not provided')
            return
        if IPSW_File is None:
            self.Console_Print('Error with IPSW File not provided')
            return
        self.Console_Print(f'[Prep Stage] Grabbing {IPSW_File} Stage')
        Extracted_Folder_Name = IPSW_File.replace('.ipsw', '').split('_')
        Extracted_Folder_Path = os.path.join(self.Root_Extract_Path, iPhone_Model, f'{Extracted_Folder_Name[1]}_{Extracted_Folder_Name[2]}')
        Stage = 'Stage 0'
        if os.path.exists(Extracted_Folder_Path):
            if self.get_dir_size(Extracted_Folder_Path) <= os.path.getsize(os.path.join(self.IPSW_Directory, iPhone_Model,IPSW_File)):
                return 'Stage -1', Extracted_Folder_Path
            if os.path.exists(os.path.join(Extracted_Folder_Path, 'Extra')):
                if os.path.exists(os.path.join(Extracted_Folder_Path, 'Extra', '.DS_Store')):
                    os.remove(os.path.join(Extracted_Folder_Path, 'Extra', '.DS_Store'))
                if self.get_dir_size(os.path.join(Extracted_Folder_Path, 'Extra')) <= 100:
                    return 'Stage -2', Extracted_Folder_Path
                for Stage1_Check in os.listdir(os.path.join(Extracted_Folder_Path, 'Extra', 'Pem')):
                    if Stage1_Check.endswith('.pem'):
                        Stage = 'Stage 2 AEADecryption'
                        for Stage2_Check in os.listdir(os.path.join(Extracted_Folder_Path)):
                            if Stage2_Check.endswith('.dmg.aea'):
                                Stage = 'Stage 3 APFS Extraction'
                            else:
                                Pass = 0
                                for Stage3_Check_Root in os.listdir(os.path.join(Extracted_Folder_Path)):
                                    for Stage3_Check in os.listdir(os.path.join(Extracted_Folder_Path, "Extra")):
                                        if not Stage3_Check_Root.endswith('.dmg'):
                                            continue
                                        if Stage3_Check_Root.replace('.dmg', '') in Stage3_Check:
                                            Pass += 1
                                if Pass == 3:
                                    Stage = 'Stage 4 Cache Extraction'

        return Stage, Extracted_Folder_Path

    def Database_Loader(self, Get_Database=False): #Need to sort Get_Database function sorted so IOS_Data_Grabber needs updating
        Root_Dir = 'Modules/DataBases'
        if Get_Database:
            return

        if not Get_Database:
            if not os.path.exists(Root_Dir):
                return
            for file in os.listdir(f'{Root_Dir}'):
                if file == 'iPhone_IOS.json':
                    with open(f'{Root_Dir}/iPhone_IOS.json') as json_file:
                        self.iPhone_Version_Map.extend(json.load(json_file))
                if file == 'iPhone_Models.json':
                    with open(f'{Root_Dir}/iPhone_Models.json') as json_file:
                        self.iPhone_Model_Map.extend(json.load(json_file))
                if file == 'iPad_Models.json':
                    with open(f'{Root_Dir}/iPad_Models.json') as json_file:
                        self.iPad_Model_Map.extend(json.load(json_file))
                if file == 'Mac_Models.json':
                    with open(f'{Root_Dir}/Mac_Models.json') as json_file:
                        self.Mac_Model_Map.extend(json.load(json_file))
            return

    def IPSW_File_Locate(self, iPhone_Model=None, iPhone_Version=None):
        self.Console_Print("-------------------------------------------------------")
        if iPhone_Model is None:
            self.Console_Print(f'[Stage 1][ERROR] Model Selected is invalid {iPhone_Model}')
            return
        Chosen_Model = None
        Chosen_IOS_Version = None
        for Model_info in self.iPhone_Model_Map:
            if Model_info['identifier'] == iPhone_Model or Model_info['name'] == iPhone_Model:
                Chosen_Model = Model_info
                for version_map in self.iPhone_Version_Map:
                    if version_map['identifier'] == iPhone_Model or version_map['name'] == iPhone_Model:
                        if iPhone_Version is None:
                            Chosen_IOS_Version = version_map['versions']
                        if iPhone_Version is not None:
                            for ios in version_map['versions']:
                                if ios == iPhone_Version:
                                    Chosen_IOS_Version = ios
        if Chosen_IOS_Version is None:
            self.Console_Print('Error with Chosen IOS Version')
            return

        for ipsw_file in os.listdir(os.path.join(self.IPSW_Directory, Chosen_Model['identifier'])):
            if not ipsw_file.endswith('.ipsw'):
                continue
            if isinstance(Chosen_IOS_Version, str):
                ipsw_file_part = ipsw_file.replace('.ipsw', '').split('_')
                ipsw_file_version = ipsw_file_part[1]
                if ipsw_file_version != Chosen_IOS_Version:
                    continue
            Stage, Extract_Location = self.IPSW_Stage_Finder(Chosen_Model['identifier'], ipsw_file)
            self.Console_Print(f'[Prep Stage] {ipsw_file} is on {Stage}')

            self.Downloaded_IPSW_Files.append({
                'File Name': ipsw_file,
                'File Path': os.path.join(self.IPSW_Directory, Chosen_Model['identifier']),
                'File Size': os.path.getsize(os.path.join(self.IPSW_Directory, Chosen_Model['identifier'], ipsw_file)),
                'Extract Path': Extract_Location,
                'Current Stage': Stage,
            })
        return

    def Stage_1_Unzip_Decrypted_File(self):
        self.Console_Print("-------------------------------------------------------")

        if self.Downloaded_IPSW_Files is None:
            self.Console_Print('[Stage 1][ERROR] Please Run IPSW_File_Locate First')
        #Unzip Main IPSW File or retry
        for ipsw_list in self.Downloaded_IPSW_Files:
            if ipsw_list['Current Stage'] in self.Stages[2:] or ipsw_list['Current Stage'] == 'Stage -2':
                continue
            if ipsw_list['Current Stage'] == 'Stage -1':
                self.Console_Print(f'[Stage 1][Error] {ipsw_list["File Name"]} had issue Deleting and starting again')
                shutil.rmtree(os.path.join(ipsw_list['Extract Path']))
            if os.path.exists(ipsw_list['Extract Path']) == False:
                self.Console_Print(f'[Stage 1] Unzipping {ipsw_list["File Name"]}')
                Unzip_Command = subprocess.Popen(['unzip', os.path.join(ipsw_list['File Path'], ipsw_list['File Name']), '-d', ipsw_list['Extract Path']], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.Processors.append(Unzip_Command)
            ipsw_list['Current Stage'] = 'Stage 2 AEADecryption'

        self.wait_processes()

        # Decryption Part for AEA files
        self.Console_Print("-------------------------------------------------------")
        for ipsw_list in self.Downloaded_IPSW_Files:
            if ipsw_list['Current Stage'] in self.Stages[3:]:
                continue
            if ipsw_list['Current Stage'] == 'Stage -2':
                os.removedirs(os.path.join(ipsw_list['Extract Path'], 'Extra'))
                ipsw_list['Current Stage'] = 'Stage 2 AEADecryption'
            if os.path.exists(os.path.join(ipsw_list['Extract Path'], 'Extra', 'Pem')) == False:
                self.Console_Print(f'[Stage 2] Grabbing Pem File for {ipsw_list["File Name"]}')
                os.makedirs(os.path.join(ipsw_list['Extract Path'], 'Extra', 'Pem'))
                subprocess.run(['ipsw', 'extract', '--fcs-key', os.path.join(ipsw_list['File Path'], ipsw_list['File Name']), '-o', os.path.join(ipsw_list['Extract Path'], 'Extra', 'Pem')], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                for folder in os.listdir(os.path.join(ipsw_list['Extract Path'], 'Extra', 'Pem')):
                    for pem_file in os.listdir(os.path.join(ipsw_list['Extract Path'], 'Extra', 'Pem', folder)):
                        shutil.move(os.path.join(ipsw_list['Extract Path'], 'Extra', 'Pem', folder, pem_file), os.path.join(ipsw_list['Extract Path'], 'Extra', 'Pem'))
                        ipsw_list['Pem File'] = pem_file
                        os.removedirs(os.path.join(ipsw_list['Extract Path'], 'Extra', 'Pem', folder))
            else: #need updating for pem directory
                self.Console_Print(f'[Stage 2] Updated Pem Location Data For {ipsw_list["File Name"]}')
                for pem_file in os.listdir(os.path.join(ipsw_list['Extract Path'], 'Extra', 'Pem')):
                    if pem_file.startswith('.'):
                        continue
                    if os.path.isdir(os.path.join(ipsw_list['Extract Path'], 'Extra','Pem', pem_file)):
                        if self.get_dir_size(os.path.join(ipsw_list['Extract Path'], 'Extra', 'Pem', pem_file)) > 0:
                            for pem_sub_file in os.listdir(os.path.join(ipsw_list['Extract Path'], 'Extra', 'Pem', pem_file)):
                                if pem_sub_file.startswith('.'):
                                    continue
                                shutil.move(os.path.join(ipsw_list['Extract Path'], 'Extra', 'Pem', pem_file, pem_sub_file), os.path.join(ipsw_list['Extract Path'], 'Extra', 'Pem'))
                                ipsw_list['Pem File'] = pem_sub_file
                                os.removedirs(os.path.join(ipsw_list['Extract Path'], 'Extra', 'Pem', pem_file))
                        else:
                            try:
                                if not pem_file.split('__')[1] == ipsw_list['File Path'].split('/')[1]:
                                    continue
                                os.removedirs(os.path.join(ipsw_list['Extract Path'], 'Extra', 'Pem', pem_file))
                            except:
                                continue
                    ipsw_list['Pem File'] = pem_file

            ipsw_list['APFS Files'] = []
            for Encrypted_AEA_Files in os.listdir(ipsw_list['Extract Path']):
                if not Encrypted_AEA_Files.endswith('.dmg.aea'):
                    continue
                self.Console_Print(f'[Stage 2] Decrypting {Encrypted_AEA_Files} from {ipsw_list["File Name"]}')
                AEA_Decrypt_Command = subprocess.Popen([
                    'ipsw', 'fw', 'aea', '--pem',
                    os.path.join(ipsw_list['Extract Path'], 'Extra', 'Pem', ipsw_list['Pem File']), os.path.join(ipsw_list['Extract Path'], Encrypted_AEA_Files), '-o', ipsw_list['Extract Path']
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                ipsw_list['APFS Files'].append(Encrypted_AEA_Files.replace('.aea', ''))
                self.Processors.append(AEA_Decrypt_Command)

            if not len(ipsw_list['APFS Files']) >= 3:
                for files in os.listdir(ipsw_list['Extract Path']):
                    if files in ipsw_list['APFS Files']:
                        continue
                    if not files.endswith('.dmg'):
                        continue
                    file_result = subprocess.run(['file', os.path.join(ipsw_list['Extract Path'], files)], capture_output=True, text=True)
                    if str(file_result.stdout).split(':')[1].split(',')[0] == ' Apple File System (APFS)':
                        ipsw_list['APFS Files'].append(files)

            self.wait_processes()

            #Help Tidy Directory don't need the encrypted dmg files any more :)
            for encrypt_aea in os.listdir(ipsw_list['Extract Path']):
                if not encrypt_aea.endswith('.dmg.aea'):
                    continue
                os.remove(os.path.join(ipsw_list['Extract Path'], encrypt_aea))
            self.Console_Print(f'[Stage 2] Completed Stage for {ipsw_list["File Name"]}')
            ipsw_list['Current Stage'] = 'Stage 3 APFS Extraction'
        return

    def Stage_2_AFPS_Extraction(self):
        self.Console_Print("-------------------------------------------------------")
        for ipsw_list in self.Downloaded_IPSW_Files:
            if ipsw_list['Current Stage'] in self.Stages[3:]:
                continue

            ipsw_list['APFS Volumes'] = []

            for files in os.listdir(ipsw_list['Extract Path']):
                if not files.endswith('.dmg'):
                    continue
                if files not in ipsw_list['APFS Files']:
                    continue
                if os.path.exists(os.path.join(ipsw_list['Extract Path'], 'Extra', files.replace('.dmg', ''))):
                    continue
                self.Console_Print(f'[Stage 3] Attaching {files} to extract')
                Attach_File_Command = subprocess.run([
                    'hdiutil', 'attach', '-readonly', '-nobrowse', '-plist',
                    os.path.join(ipsw_list['Extract Path'], files)
                ], stdout=subprocess.PIPE, check=True)
                attach_info = plistlib.loads(Attach_File_Command.stdout)
                for tab in attach_info['system-entities']:
                    if 'mount-point' in tab:
                        Mount_Point = tab['mount-point']
                        ipsw_list['APFS Volumes'].append(Mount_Point)
                        Extract_Attached_Command = subprocess.Popen([
                            'rsync', '-a', Mount_Point, os.path.join(ipsw_list['Extract Path'], 'Extra', files.replace('.dmg', ''))
                        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        ipsw_list['Current Stage'] = 'Stage 4 Cache Extraction'
                        self.Processors.append(Extract_Attached_Command)
            self.wait_processes()
            for volumes in ipsw_list['APFS Volumes']:
                if not os.path.exists(volumes):
                    continue
                self.Console_Print(f'[Stage 3] Detaching {volumes}')
                subprocess.run([
                    'hdiutil', 'detach', volumes
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def Main(self, Model=None, IOS=None):
        if Model is None:
            self.Console_Print('[Stage 1] No Model Selected or found')
            return
        self.Database_Loader()
        if IOS is None:
            self.IPSW_File_Locate(Model)
            self.Stage_1_Unzip_Decrypted_File()
            self.Stage_2_AFPS_Extraction()
        if IOS is not None:
            self.IPSW_File_Locate(Model, IOS)
            self.Stage_1_Unzip_Decrypted_File()
            self.Stage_2_AFPS_Extraction()