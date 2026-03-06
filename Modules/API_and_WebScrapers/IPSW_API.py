import hashlib
import os
import pathlib
import requests

class Stable:
    def __init__(self, Directory='IPSW Files', console_print=None):
        self.URL = 'https://api.ipsw.me/v4'
        self.console_print = console_print or (lambda msg: None)
        self.IPSW_Directory = pathlib.Path(Directory)
        if not os.path.exists(self.IPSW_Directory):
            self.console_print("IPSW Directory does not exist")
            return

    def IPSW_Download(self, identifer=None, version=None):
        if identifer is None:
            self.console_print("Identifier not provided please select a model")
            return

        if version is None:
            self.console_print("Version not provided please select a version")
            return

        md5 = hashlib.md5()
        sha1 = hashlib.sha1()
        sha256 = hashlib.sha256()

        binary_mode = 'wb'
        IPSW_File = None
        MD5_Match = False
        SHA1_Match = False
        SHA256_Match = False

        All_IPSW_Files = requests.get(f'{self.URL}/device/{identifer}?type=ipsw').json()
        for fw in All_IPSW_Files['firmwares']:
            if fw['version'] == version:
                IPSW_File = fw['url']
                Target_md5 = fw['md5sum']
                Target_sha1 = fw['sha1sum']
                Target_sha256 = fw['sha256sum']
                Target_Size = fw['filesize']
                for name in IPSW_File.split("/"):
                    if name.endswith(".ipsw"):
                        IPSW_Name = name
        if IPSW_File is None:
            self.console_print("IPSW File not found please select a model and version again")
            return

        IPSW_Path = self.IPSW_Directory.joinpath(IPSW_Name)
        headers = {}
        if IPSW_Path.exists():
            current_size = os.path.getsize(IPSW_Path)
            if current_size >= Target_Size:
                self.console_print("IPSW already downloaded")
                return

            if current_size < Target_Size:
                self.console_print("Continuing the download")
                print("continuing of download")
                binary_mode = 'ab'
                headers["Range"] = f"bytes={current_size}-"

        IPSW_Data = requests.get(IPSW_File, headers=headers, stream=True)
        if "Range" in headers and IPSW_Data.status_code != 206:
            self.console_print("Server ignored resume request")
            return
        downloaded = 0
        last_print = 0

        with open(IPSW_Path, binary_mode) as f:
            for chunk in IPSW_Data.iter_content(16 * 1024 * 1024):
                if chunk:
                    f.write(chunk)
                    f.flush()

                    downloaded += len(chunk)
                    percent = int((downloaded / Target_Size) * 100)

                    if percent >= last_print + 5:
                        last_print = percent
                        self.console_print(f"{percent}% downloaded")

        if self.console_print:
            self.console_print(f"Downloaded IPSW firmware {IPSW_Name}")
            self.console_print(f"Verifying Hash of {IPSW_Name}")
        with (open(IPSW_Path, "rb")) as file:
            while chuck := file.read(1024 * 1024):
                md5.update(chuck)
                sha1.update(chuck)
                sha256.update(chuck)
        if md5.hexdigest() == Target_md5:
            MD5_Match = True
        if sha1.hexdigest() == Target_sha1:
            SHA1_Match = True
        if sha256.hexdigest() == Target_sha256:
            SHA256_Match = True

        if self.console_print:
            self.console_print(f"MD5 Match: {MD5_Match}")
            self.console_print(f"SHA1 Match: {SHA1_Match}")
            self.console_print(f"SHA256 Match: {SHA256_Match}")
        return