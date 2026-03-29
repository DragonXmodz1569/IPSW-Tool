import hashlib
from datetime import datetime
import json
import os
import re
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed


class Binary_Compare:
    def __init__(self, iPhone_Model=None, Extract_Path='Extracted_Directory', console_print=None):
        self.Exclude = ['.DS_Store']
        self.json_mappings = []
        if console_print is None:
            self.Console_Print = print
        else:
            self.Console_Print = console_print
        if iPhone_Model is None:
            self.Console_Print('Error with iPhone Model not provided')
            exit()
        self.Extract_Path = os.path.join(Extract_Path, iPhone_Model)

    def Map_IPSW(self):
        self.Console_Print('[Binary] Mapping IPSW Extracted Directory')
        for folder in os.listdir(self.Extract_Path):
            if folder in self.Exclude:
                continue
            self.Console_Print('-------------------------------------------------------')

            Dyld_Cache = os.path.join(self.Extract_Path, folder, 'Extra', 'Dyld Cache')
            if not os.path.exists(Dyld_Cache):
                continue

            self.Console_Print(f'[Binary] Mapping IPSW Directory {folder}')
            output_path = os.path.join(self.Extract_Path, folder, 'Extra', f"{folder}_Dyld_Mapping.json")
            if not os.path.exists(output_path):
                Mapping_Dyld_Data = self.Map_Directory(Dyld_Cache)
                with open(output_path, "w") as f:
                    json.dump(Mapping_Dyld_Data, f, indent=4)
                self.Console_Print(f"[Binary] Saved: {folder}_Dyld_Mapping.json")
                self.json_mappings.append(output_path)
            if os.path.exists(output_path):
                self.json_mappings.append(output_path)
                self.Console_Print(f'[Binary] IPSW Directory {folder} Already Mapped')

    def Map_Directory(self, Path=None):
        directory_map = []
        try:
            items = os.listdir(Path)
        except Exception:
            return []

        for item in items:
            if item in self.Exclude:
                continue
            full_path = os.path.join(Path, item)
            item_info = {
                "Name": item,
                "Path": full_path,
                "Type": "Dir" if os.path.isdir(full_path) else "File"
            }
            if item_info["Type"] == 'File':
                item_info['Size'] = os.path.getsize(full_path)

            if os.path.isdir(full_path):
                item_info["Children"] = self.Map_Directory(full_path)

            directory_map.append(item_info)
        return directory_map

    def Binary_Compare(self, Old_IOS=None, New_IOS=None):
        IPSW_Mapping = []
        if len(self.json_mappings) <= 1:
            self.Map_IPSW()
        self.Console_Print('-------------------------------------------------------')
        for x in range(len(self.json_mappings)):
            if self.json_mappings[x].split('/')[-1].split('_')[0] not in [Old_IOS, New_IOS]:
                continue
            self.Console_Print(f'[Binary] Loading up IPSW Mapping {self.json_mappings[x].split('/')[-1]}')
            with open(self.json_mappings[x], 'r') as f:
                content = json.load(f)

            IPSW_Mapping.append({
                'IPSW Name': self.json_mappings[x].split('/')[-1],
                'Data': content
            })

        def get_dylibs(data, result):
            for item in data:
                if item["Type"] == "File" and item["Name"].endswith(".dylib"):
                    clean_path = item["Path"].split("Dyld Cache/")[-1]
                    result[clean_path] = item["Size"]

                if item["Type"] == "Dir":
                    get_dylibs(item.get("Children", []), result)
        self.Console_Print('-------------------------------------------------------')
        IPSW_Mapping.sort(key=lambda x: x['IPSW Name'])
        Old = IPSW_Mapping[0]['Data']
        New = IPSW_Mapping[1]['Data']
        old_map = {}
        new_map = {}

        get_dylibs(Old, old_map)
        get_dylibs(New, new_map)
        if os.path.exists(
                os.path.join(self.Extract_Path, IPSW_Mapping[1]['IPSW Name'].strip('_Dyld_Mapping.json'), 'Extra',
                             'IPSW_Changes.json')):
            os.remove(os.path.join(self.Extract_Path, IPSW_Mapping[1]['IPSW Name'].strip('_Dyld_Mapping.json'), 'Extra',
                                   'IPSW_Changes.json'))

        for path in new_map:
            if path not in old_map:
                self.Console_Print("NEW:", path)
                with open(os.path.join(self.Extract_Path, IPSW_Mapping[1]['IPSW Name'].strip('_Dyld_Mapping.json'), 'Extra', 'IPSW_New.json'), 'a+') as f:
                    json.dump(("NEW:", path), f, indent=4)

            elif new_map[path] != old_map[path]:
                self.Console_Print("CHANGED:", path, old_map[path], "->", new_map[path])
                with open(os.path.join(self.Extract_Path, IPSW_Mapping[1]['IPSW Name'].strip('_Dyld_Mapping.json'), 'Extra', 'IPSW_Changes.json'), 'a') as f:
                    new_change = {
                        "type": "CHANGED",
                        "path": path,
                        "old_size": old_map[path],
                        "new_size": new_map[path]
                    }
                    json.dump(new_change, f)
                    f.write('\n')

        for path in old_map:
            if path not in new_map:
                self.Console_Print("REMOVED:", path)
                with open(os.path.join(self.Extract_Path, IPSW_Mapping[1]['IPSW Name'].strip('_Dyld_Mapping.json'), 'Extra', 'IPSW_Removed.json'), 'a+') as f:
                    json.dump(("REMOVED:", path), f, indent=4)

    def Dyld_Extract_Extra(self, IOS=None, Target='All', Target_Compare_IOS=None):
        IOS_Targets = []
        Target_Dyld = []
        if IOS is not None:
            for root_folders in os.listdir(self.Extract_Path):
                if root_folders.split("_")[0] == IOS:
                    IOS_Targets.append(root_folders)
            if len(IOS_Targets) == 0:
                self.Console_Print('[Binary] No IOS Targets Found Extracted')
                return
        if IOS is None:
            self.Console_Print('[Binary] No IOS was Given Running on all')
            for x in range(len(self.json_mappings)):
                IOS_Targets.append(self.json_mappings[x].split('/')[-1].strip('_Dyld_Mapping.json'))
        self.Console_Print('-------------------------------------------------------')

        def extract_file_paths(data):
            paths = []
            for item in data:
                if item.get("Type") == "File":
                    paths.append(item.get("Path"))
                if "Children" in item:
                    paths.extend(extract_file_paths(item["Children"]))
            return paths

        Dyld_Cache = None
        for Main_Root in IOS_Targets:
            for Root_Folders in os.listdir(os.path.join(self.Extract_Path, Main_Root)):
                if Root_Folders.endswith('.dmg'):
                    if not os.path.exists(os.path.join(self.Extract_Path, Main_Root, 'Extra', Root_Folders.replace('.dmg', ''))):
                        continue
                    for sub_root in os.listdir(os.path.join(self.Extract_Path, Main_Root, 'Extra', Root_Folders.replace('.dmg', ''))):
                        if not os.path.exists(os.path.join(self.Extract_Path, Main_Root, 'Extra', Root_Folders.replace('.dmg', ''), sub_root, 'System', 'Library', 'Caches', 'com.apple.dyld')):
                            continue
                        Dyld_Cache = os.path.join(os.path.join(self.Extract_Path, Main_Root, 'Extra', Root_Folders.replace('.dmg', ''), sub_root))

        for Root_Folders in IOS_Targets:
            if Target.lower() == 'all':
                for dyld_map in os.listdir(os.path.join(self.Extract_Path, Root_Folders, 'Extra')):
                    if dyld_map.endswith("_Dyld_Mapping.json"):
                        with open(os.path.join(self.Extract_Path, Root_Folders, 'Extra', dyld_map), 'r') as f:
                            data = json.load(f)
                            Target_Dyld.extend(extract_file_paths(data))
            elif Target.lower() == 'change':
                if Target_Compare_IOS is not None:
                    for new_root_folder in os.listdir(self.Extract_Path):
                        if new_root_folder.split("_")[0] == Target_Compare_IOS:
                            temp = new_root_folder
                else:
                    temp = Root_Folders
                with open(os.path.join(self.Extract_Path, temp, 'Extra', 'IPSW_Changes.json'), 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            Target_Dyld.append(json.loads(line)["path"])
            else:
                self.Console_Print('[Binary] Please choose one Target options [All, Change]')
                return

            for x in range(len(Target_Dyld)):
                if os.path.exists(os.path.join(Target_Dyld[x].replace('.dylib', '_strings.txt'))):
                    self.Console_Print(f'[Binary] {Target_Dyld[x]} Already Ran Before Skipping {x}/{len(Target_Dyld)}')
                    continue
                target = Target_Dyld[x]
                if '/usr/' in target:
                    image_path = target[target.index('/usr/'):]
                elif 'usr/' in target:
                    image_path = '/' + target[target.index('usr/'):]
                elif '/System/' in target:
                    image_path = target[target.index('/System/'):]
                elif 'System/' in target:
                    image_path = '/' + target[target.index('System/'):]
                else:
                    self.Console_Print(f'[Binary] Skipping invalid dyld image path: {target}')
                    continue
                self.Console_Print(f'[Binary] Running IPSW Macho Strings on {Target_Dyld[x]} on {x}/{len(Target_Dyld)}')
                with open(os.path.join(Target_Dyld[x].replace('.dylib', '_strings.txt')), 'w') as f:
                    subprocess.run([
                        'ipsw', 'dyld', 'macho',
                        os.path.join(Dyld_Cache,
                                     'System',
                                     'Library',
                                     'Caches',
                                     'com.apple.dyld',
                                     'dyld_shared_cache_arm64e'),
                        image_path,
                        '--strings'
                    ], stdout=f, stderr=subprocess.DEVNULL, check=True)
            self.Console_Print(f'[Binary] Completed IPSW Strings {len(Target_Dyld)}/{len(Target_Dyld)}')
            self.Console_Print('-------------------------------------------------------')
            for x in range(len(Target_Dyld)):
                if os.path.exists(os.path.join(Target_Dyld[x].replace('.dylib', '_Symbols.txt'))):
                    self.Console_Print(f'[Binary] {Target_Dyld[x]} Already Ran Before Skipping {x}/{len(Target_Dyld)}')
                    continue
                target = Target_Dyld[x]
                if '/usr/' in target:
                    image_path = target[target.index('/usr/'):]
                elif 'usr/' in target:
                    image_path = '/' + target[target.index('usr/'):]
                elif '/System/' in target:
                    image_path = target[target.index('/System/'):]
                elif 'System/' in target:
                    image_path = '/' + target[target.index('System/'):]
                else:
                    self.Console_Print(f'[Binary] Skipping invalid dyld image path: {target}')
                    continue
                self.Console_Print(f'[Binary] Running IPSW Macho Symbols on {Target_Dyld[x]} on {x}/{len(Target_Dyld)}')
                with open(os.path.join(Target_Dyld[x].replace('.dylib', '_Symbols.txt')), 'w') as f:
                    subprocess.run([
                        'ipsw', 'dyld', 'macho',
                        os.path.join(Dyld_Cache, 'System', 'Library', 'Caches', 'com.apple.dyld', 'dyld_shared_cache_arm64e'),
                        image_path,
                        '--symbols'
                    ], stdout=f, stderr=subprocess.DEVNULL, check=True)
            self.Console_Print(f'[Binary] Completed IPSW Symbols {len(Target_Dyld)}/{len(Target_Dyld)}')
            self.Console_Print('-------------------------------------------------------')
            for x in range(len(Target_Dyld)):
                if os.path.exists(os.path.join(Target_Dyld[x].replace('.dylib', '_Starts.txt'))):
                    self.Console_Print(f'[Binary] {Target_Dyld[x]} Already Ran Before Skipping {x}/{len(Target_Dyld)}')
                    continue
                target = Target_Dyld[x]
                if '/usr/' in target:
                    image_path = target[target.index('/usr/'):]
                elif 'usr/' in target:
                    image_path = '/' + target[target.index('usr/'):]
                elif '/System/' in target:
                    image_path = target[target.index('/System/'):]
                elif 'System/' in target:
                    image_path = '/' + target[target.index('System/'):]
                else:
                    self.Console_Print(f'[Binary] Skipping invalid dyld image path: {target}')
                    continue
                self.Console_Print(f'[Binary] Running IPSW Macho Start on {Target_Dyld[x]} on {x}/{len(Target_Dyld)}')
                with open(os.path.join(Target_Dyld[x].replace('.dylib', '_Starts.txt')), 'w') as f:
                    subprocess.run([
                        'ipsw', 'dyld', 'macho',
                        os.path.join(Dyld_Cache, 'System', 'Library', 'Caches', 'com.apple.dyld', 'dyld_shared_cache_arm64e'),
                        image_path,
                        '--starts'
                    ], stdout=f, stderr=subprocess.PIPE, check=True)
            self.Console_Print(f'[Binary] Completed IPSW Starts {len(Target_Dyld)}/{len(Target_Dyld)}')
            self.Console_Print('-------------------------------------------------------')
            for x in range(len(Target_Dyld)):
                if os.path.exists(os.path.join(Target_Dyld[x].replace('.dylib', '_imports.txt'))):
                    self.Console_Print(f'[Binary] {Target_Dyld[x]} Already Ran Before Skipping {x}/{len(Target_Dyld)}')
                    continue
                target = Target_Dyld[x]
                if '/usr/' in target:
                    image_path = target[target.index('/usr/'):]
                elif 'usr/' in target:
                    image_path = '/' + target[target.index('usr/'):]
                elif '/System/' in target:
                    image_path = target[target.index('/System/'):]
                elif 'System/' in target:
                    image_path = '/' + target[target.index('System/'):]
                else:
                    self.Console_Print(f'[Binary] Skipping invalid dyld image path: {target}')
                    continue
                self.Console_Print(f'[Binary] Running IPSW Imports on {Target_Dyld[x]} on {x}/{len(Target_Dyld)}')
                with open(os.path.join(Target_Dyld[x].replace('.dylib', '_imports.txt')), 'w') as f:
                    subprocess.run([
                        'ipsw', 'dyld', 'imports',
                        os.path.join(Dyld_Cache, 'System', 'Library', 'Caches', 'com.apple.dyld', 'dyld_shared_cache_arm64e'),
                        image_path
                    ], stdout=f, stderr=subprocess.DEVNULL, check=True)
            self.Console_Print(f'[Binary] Completed IPSW Imports {len(Target_Dyld)}/{len(Target_Dyld)}')

    def Binary_Decompile(self, Old_IOS=None, New_IOS=None, Target='All', Binary=None):
        To_Compare = []
        To_Compare.append(Old_IOS)
        To_Compare.append(New_IOS)
        if Target.lower() == 'all':
            self.Console_Print('[Binary] All Function work in progress')
            return
        if Target.lower() == 'change':
            Root_Directory = []
            Change = []
            Old = []
            New = []
            for x in range(len(To_Compare)):
                for Root_Dir in os.listdir(self.Extract_Path):
                    if Root_Dir.split('_')[0] == To_Compare[x]:
                        Root_Directory.append(os.path.join(self.Extract_Path, Root_Dir))
            for Root_Dir in Root_Directory:
                if not Root_Dir.split('/')[-1].split('_')[0] == New_IOS:
                    continue
                with open(os.path.join(Root_Dir, 'Extra', 'IPSW_Changes.json'), 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            Change.append(json.loads(line))
            for x in range(len(Root_Directory)):
                To_Compare.clear()
                #Grab Both Old vs New Dylib
                for item in Change:
                    path = item['path']
                    if os.path.exists(os.path.join(Root_Directory[x], 'Extra', 'Dyld Cache', path)):
                        Dyld_file = os.path.join(Root_Directory[x], 'Extra', 'Dyld Cache', path)
                    if os.path.exists(os.path.join(Root_Directory[x], 'Extra', 'Dyld Cache', path.replace('.dylib', '_imports.txt'))):
                        Dyld_Imports = os.path.join(Root_Directory[x], 'Extra', 'Dyld Cache', path.replace('.dylib', '_imports.txt'))
                    if os.path.exists(os.path.join(Root_Directory[x], 'Extra', 'Dyld Cache', path.replace('.dylib', '_Starts.txt'))):
                        Dyld_starts = os.path.join(Root_Directory[x], 'Extra', 'Dyld Cache', path.replace('.dylib', '_Starts.txt'))
                    if os.path.exists(os.path.join(Root_Directory[x], 'Extra', 'Dyld Cache', path.replace('.dylib', '_strings.txt'))):
                        Dyld_strings = os.path.join(Root_Directory[x], 'Extra', 'Dyld Cache', path.replace('.dylib', '_strings.txt'))
                    if os.path.exists(os.path.join(Root_Directory[x], 'Extra', 'Dyld Cache', path.replace('.dylib', '_Symbols.txt'))):
                        Dyld_Symbols = os.path.join(Root_Directory[x], 'Extra', 'Dyld Cache', path.replace('.dylib', '_Symbols.txt'))

                    if Root_Directory[x].split('/')[-1].split('_')[0] == Old_IOS:
                        Old.append({
                        'Binary': Dyld_file,
                        'Imports': Dyld_Imports,
                        'Starts': Dyld_starts,
                        'Strings': Dyld_strings,
                        'Symbols': Dyld_Symbols
                    })
                    if Root_Directory[x].split('/')[-1].split('_')[0] == New_IOS:
                        New.append({
                        'Binary': Dyld_file,
                        'Imports': Dyld_Imports,
                        'Starts': Dyld_starts,
                        'Strings': Dyld_strings,
                        'Symbols': Dyld_Symbols
                    })
            self.Console_Print('-------------------------------------------------------')
            self.Console_Print('[Binary] Mapped Each Function Now Grabbing Information')
            for Main_Map in [Old, New]:
                for x in range(len(Main_Map)):
                    with open(Main_Map[x]['Starts'], 'r') as f:
                        Starts = []
                        for line in f:
                            line = line.strip()
                            if line.startswith('0x'):
                                Starts.append(int(line, 16))
                    Main_Map[x]['Starts_Data'] = sorted(Starts)
                    with open(Main_Map[x]['Symbols'], 'r') as f:
                        Symbols = {}
                        for line in f:
                            line = line.strip()
                            # remove terminal color codes
                            line = re.sub(r'\x1b\[[0-9;]*m', '', line)

                            # match: 0xADDRESS: ... SYMBOLNAME
                            match = re.search(r'(0x[0-9A-Fa-f]+):.*?([_A-Za-z][_A-Za-z0-9$]*)\s*$', line)
                            if match:
                                addr = int(match.group(1), 16)
                                name = match.group(2)
                                Symbols[addr] = name

                    Main_Map[x]['Symbols_Data'] = Symbols

                    Functions = []
                    for i in range(len(Main_Map[x]['Starts_Data']) - 1):
                        start = Main_Map[x]['Starts_Data'][i]
                        end = Main_Map[x]['Starts_Data'][i+1]
                        name = Main_Map[x]['Symbols_Data'].get(start, f'sub_{hex(start)}')

                        Functions.append({
                            'Name': name,
                            'Start': start,
                            'End': end
                        })
                    Main_Map[x]['Functions_Data'] = Functions

            for Root in Root_Directory:
                Cache = None
                for dmg in os.listdir(Root):
                    dmgs = []
                    if not dmg.endswith('.dmg'):
                        continue
                    dmgs.append(dmg.replace('.dmg', ''))
                    if dmg.replace('.dmg', '') in os.listdir(os.path.join(Root, 'Extra')):
                        for sub_dmg_folder in os.listdir(os.path.join(Root, 'Extra', dmg.replace('.dmg', ''))):
                            if os.path.exists(
                                os.path.join(Root, 'Extra', dmg.replace('.dmg', ''),sub_dmg_folder, 'System', 'Library', 'Caches', 'com.apple.dyld')):
                                Cache = os.path.join(Root, 'Extra', dmg.replace('.dmg', ''), sub_dmg_folder, 'System', 'Library', 'Caches', 'com.apple.dyld', 'dyld_shared_cache_arm64e')
                if Cache is None:
                    self.Console_Print('[Decompile] Error on Cache Grabbing')
                    return

            def get_function_code(disasm_lines, start, end): #ChatGPT Helped make parts Will remake below part with get_function_code mainly for testing
                func_lines = []
                inside = False
                start_hex = hex(start)
                end_hex = hex(end)
                for line in disasm_lines:
                    line = line.strip()
                    # start capturing
                    if start_hex in line:
                        inside = True
                    if inside:
                        func_lines.append(line)
                    # stop when we hit end
                    if end_hex in line and inside:
                        break

                return func_lines

            Old_Map = {}
            for item in Old:
                for func in item['Functions_Data']:
                    if not func['Name'].startswith('sub_0x'):
                        Old_Map[func['Name']] = {
                            'Function': func,
                            'Item': item
                        }

            New_Map = {}
            for item in New:
                for func in item['Functions_Data']:
                    if not func['Name'].startswith('sub_0x'):
                        New_Map[func['Name']] = {
                            'Function': func,
                            'Item': item
                        }

            def Process_Dylib_Disasm(dylib_file):
                disasm_path = dylib_file['Binary'].replace('.dylib', '_Disasm.txt')
                if os.path.exists(disasm_path):
                    if os.path.getsize(disasm_path) == 0:
                        os.remove(disasm_path)
                    if os.path.getsize(disasm_path) > 0:
                        return {
                            'ok': 'Skipped',
                            'file': dylib_file['Binary'],
                        }
                job_id = hashlib.md5(dylib_file['Binary'].encode()).hexdigest()[:8]
                project_dir = os.path.join('Extracted_Directory', 'ghidra_tmp')
                project_name = f'ghidra_proj_{job_id}'

                os.makedirs(project_dir, exist_ok=True)
                print(f'Working on {dylib_file["Binary"]} ({os.path.getsize(dylib_file["Binary"]) / (1024*1024)} MB) at {datetime.now()}')
                cmd = [
                    'analyzeHeadless',
                    project_dir,
                    project_name,
                    '-import', dylib_file['Binary'],
                    '-max-cpu', '4',
                    '-analysisTimeoutPerFile', '2100',
                    '-scriptPath', 'Modules/GhidraHeadless',
                    '-postScript', 'ExportDisasm.py', disasm_path,
                    '-deleteProject',
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode != 0:
                    return {
                        'ok': False,
                        'file': dylib_file['Binary'],
                        'code': result.returncode,
                        'stdout': result.stdout,
                        'stderr': result.stderr,
                    }

                if not os.path.exists(disasm_path):
                    return {
                        'ok': False,
                        'file': dylib_file['Binary'],
                        'code': 0,
                        'stdout': result.stdout,
                        'stderr': result.stderr + f'\nOutput file not created: {disasm_path}',
                    }

                dylib_file['Disasm'] = disasm_path
                return {
                    'ok': True,
                    'file': dylib_file['Binary'],
                }

            failed_heap = []
            timed_out = []
            failed_other = []
            if os.path.exists('Extracted_Directory/ghidra_tmp'):
                shutil.rmtree('Extracted_Directory/ghidra_tmp')
            def Run_Disasm_Queue(items, max_workers=4):
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = [executor.submit(Process_Dylib_Disasm, dylib) for dylib in items]

                    for future in as_completed(futures):
                        result = future.result()
                        if result['ok'] == True:
                            print(f"Done: {result['file']}")
                        elif result['ok'] == 'Skipped':
                            print(f"Skipped: {result['file']} Already Exists")
                        else:
                            print(f"Failed: {result['file']}")
                            print(f"Return code: {result['code']}")

                            if 'Java heap space' in result.get('stdout', ''):
                                failed_heap.append(result['file'])
                            elif "ANALYSIS TIMED OUT" in result.get('stout', ''):
                                print(f'Timed Out: {result["file"]}')
                                timed_out.append(result['file'])
                            else:
                                failed_other.append(result['file'])

                            print("STDOUT:")
                            print(result['stdout'])
                            print("STDERR:")
                            print(result['stderr'])

            Run_Disasm_Queue(Old, max_workers= 1)
            print('----------(new)----------')
            Run_Disasm_Queue(New, max_workers= 1)
            exit()

            for item in New:
                disasm_path = item['Binary'].replace('.dylib', '_Disasm.txt')
                with open(disasm_path, 'r') as f:
                    item['Disasm_Read'] = f.readlines()

            for name in Old_Map:
                if name in New_Map:
                    old_function = Old_Map[name]['Function']
                    new_function = New_Map[name]['Function']

                    old_item = Old_Map[name]['Item']
                    new_item = New_Map[name]['Item']

                    old_code = get_function_code(old_item['Disasm_Read'], old_function['Start'], old_function['End'])
                    new_code = get_function_code(new_item['Disasm_Read'], new_function['Start'], new_function['End'])

                    if old_code != new_code:
                        print('CHANGED:', name)

        else:
            self.Console_Print('[Binary] Error has raised please choose [All | Change]')
