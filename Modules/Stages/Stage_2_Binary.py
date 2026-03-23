import json
import os
import subprocess


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

    def IPSW_Extra(self, IOS=None, Target='All', Target_Compare_IOS=None):
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
                print(os.path.join(self.Extract_Path, temp, 'Extra', 'IPSW_Changes.json'))
                with open(os.path.join(self.Extract_Path, temp, 'Extra', 'IPSW_Changes.json'), 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            Target_Dyld.append(json.loads(line)["path"])
            else:
                self.Console_Print('[Binary] Please choose one Target options [All, Change]')
                return

            for x in range(len(Target_Dyld)):
                self.Console_Print(f'[Binary] Running IPSW Macho Strings on {Target_Dyld[x]} on {x}/{len(Target_Dyld)}')
                with open(os.path.join(self.Extract_Path, Root_Folders, 'Extra', 'Dyld Cache',Target_Dyld[x].replace('.dylib', '_strings.txt')), 'w') as f:
                    image_path = '/' + Target_Dyld[x].lstrip('/')
                    subprocess.run([
                        'ipsw', 'dyld', 'macho',
                        os.path.join(Dyld_Cache, 'System', 'Library', 'Caches', 'com.apple.dyld', 'dyld_shared_cache_arm64e'),
                        image_path,
                        '--strings'
                    ], stdout=f, stderr=subprocess.DEVNULL, check=True)
            self.Console_Print(f'[Binary] Completed IPSW Strings {len(Target_Dyld)}/{len(Target_Dyld)}')
            self.Console_Print('-------------------------------------------------------')
            for x in range(len(Target_Dyld)):
                self.Console_Print(f'[Binary] Running IPSW Macho Symbols on {Target_Dyld[x]} on {x}/{len(Target_Dyld)}')
                with open(os.path.join(self.Extract_Path, Root_Folders, 'Extra', 'Dyld Cache',Target_Dyld[x].replace('.dylib', '_Symbols.txt')), 'w') as f:
                    image_path = '/' + Target_Dyld[x].lstrip('/')
                    subprocess.run([
                        'ipsw', 'dyld', 'macho',
                        os.path.join(Dyld_Cache, 'System', 'Library', 'Caches', 'com.apple.dyld', 'dyld_shared_cache_arm64e'),
                        image_path,
                        '--symbols'
                    ], stdout=f, stderr=subprocess.DEVNULL, check=True)
            self.Console_Print(f'[Binary] Completed IPSW Symbols {len(Target_Dyld)}/{len(Target_Dyld)}')
            self.Console_Print('-------------------------------------------------------')
            for x in range(len(Target_Dyld)):
                self.Console_Print(f'[Binary] Running IPSW Macho Symbols on {Target_Dyld[x]} on {x}/{len(Target_Dyld)}')
                with open(os.path.join(self.Extract_Path, Root_Folders, 'Extra', 'Dyld Cache',Target_Dyld[x].replace('.dylib', '_Starts.txt')), 'w') as f:
                    image_path = '/' + Target_Dyld[x].lstrip('/')
                    subprocess.run([
                        'ipsw', 'dyld', 'macho',
                        os.path.join(Dyld_Cache, 'System', 'Library', 'Caches', 'com.apple.dyld', 'dyld_shared_cache_arm64e'),
                        image_path,
                        '--starts'
                    ], stdout=f, stderr=subprocess.DEVNULL, check=True)
            self.Console_Print(f'[Binary] Completed IPSW Starts {len(Target_Dyld)}/{len(Target_Dyld)}')
            self.Console_Print('-------------------------------------------------------')
            for x in range(len(Target_Dyld)):
                self.Console_Print(f'[Binary] Running IPSW Imports on {Target_Dyld[x]} on {x}/{len(Target_Dyld)}')
                with open(os.path.join(self.Extract_Path, Root_Folders, 'Extra', 'Dyld Cache',Target_Dyld[x].replace('.dylib', '_imports.txt')), 'w') as f:
                    image_path = '/' + Target_Dyld[x].lstrip('/')
                    subprocess.run([
                        'ipsw', 'dyld', 'imports',
                        os.path.join(Dyld_Cache, 'System', 'Library', 'Caches', 'com.apple.dyld', 'dyld_shared_cache_arm64e'),
                        image_path
                    ], stdout=f, stderr=subprocess.DEVNULL, check=True)
            self.Console_Print(f'[Binary] Completed IPSW Imports {len(Target_Dyld)}/{len(Target_Dyld)}')