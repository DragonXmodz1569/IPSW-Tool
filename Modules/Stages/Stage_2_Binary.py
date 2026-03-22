import json
import os


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

        IPSW_Mapping.sort(key=lambda x: x['IPSW Name'])
        Old = IPSW_Mapping[0]['Data']
        New = IPSW_Mapping[1]['Data']
        old_map = {}
        new_map = {}

        get_dylibs(Old, old_map)
        get_dylibs(New, new_map)

        for path in new_map:
            if path not in old_map:
                self.Console_Print("NEW:", path)
                with open(os.path.join(self.Extract_Path, IPSW_Mapping[1]['IPSW Name'].strip('_Dyld_Mapping.json'), 'Extra', 'IPSW_New.json'), 'a+') as f:
                    json.dump(("NEW:", path), f, indent=4)

            elif new_map[path] != old_map[path]:
                self.Console_Print("CHANGED:", path, old_map[path], "->", new_map[path])
                with open(os.path.join(self.Extract_Path, IPSW_Mapping[1]['IPSW Name'].strip('_Dyld_Mapping.json'), 'Extra', 'IPSW_Changes.json'), 'a+') as f:
                    json.dump(("CHANGED:", path, old_map[path], "->", new_map[path]), f, indent=4)

        for path in old_map:
            if path not in new_map:
                self.Console_Print("REMOVED:", path)
                with open(os.path.join(self.Extract_Path, IPSW_Mapping[1]['IPSW Name'].strip('_Dyld_Mapping.json'), 'Extra', 'IPSW_Removed.json'), 'a+') as f:
                    json.dump(("REMOVED:", path), f, indent=4)





