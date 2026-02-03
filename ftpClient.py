
from ftplib import FTP

class FTPClient:
    def __init__(self, host, user, password, port=21):
        self.host = host
        self.port = port
        self.connected = False
        self.username = user
        self.password = password

        self.ftp = FTP()

    def __del__(self):
        self.disconnect()
 
    def _checkConnection(func):
        def wrapper(self, *args, **kwargs):
            if not self.connected:
                print("Error: Not connected to any FTP server.")
                return
            return func(self, *args, **kwargs)
        return wrapper

    def connect(self):
        print(f"Connecting to FTP server at {self.host}:{self.port}...")
        try:
            self.ftp.connect(self.host, self.port)
        except Exception as e:
            print(f"Failed to connect to FTP server: {e}")
            return False

        try:
            self.ftp.login(self.username, self.password)
        except Exception as e:
            print(f"Failed to login: {e}")
            return False

        self.connected = True
        print("Connected.")
        return True

    @_checkConnection
    def disconnect(self)
        if self.ftp is not None:
            try:
                self.ftp.quit()
            except Exception as e:
                print(f"Failed to close the FTP connection{e}")
                self.ftp.close()
        
        self.ftp = None


    @_checkConnection
    def disconnect(self):
        if self.connected:
            print("Disconnecting from FTP server...")
            self.ftp.quit()
            self.connected = False
            print("Disconnected.")
        else:
            print("Not connected to any FTP server.")

    @_checkConnection
    def getDirectoryContent(self, path):

        print("Retrieving directory content...")
        try:

            files = self.ftp.mlsd(path)
            return dict(files)
        except Exception as e:
            print(f"Failed to retrieve directory content: {e}")
            return None

    @_checkConnection
    def getDirectoryNames(self):

        print ("Retrieving directory content...")

        try:
            names = self.ftp.nlst()
            return names
        except Exception as e:
            print(f"Failed to retrieve directory content: {e}")
            return None

    @_checkConnection 
    def removeFile(self, path):

        print (f"Removing {path} from FTP filesystem")

        try:
            self.ftp.delete(path)
            return True
        except Exception as e:
            print (f"Failed to remove file {path}: {e}")

        return False

    @_checkConnection
    def createDirectory(self, path):
        
        try:
            self.ftp.mkd(path)
        except Exception as e:
            print (f"Failed to create directory {path}: {e}")
            return False

        return True


    @_checkConnection
    def removeDirectory(self, path):

        import os
        try:
            content = self.getDirectoryContent(path)

            for name, details in content.items():
                if details["type"] == "dir":
                    self.removeDirectory(os.path.join(path, name))
                elif details["type"] == "file":
                    self.removeFile(os.path.join(path, name))
                else:
                    print (f"Skipping {path}")

        except Exception as e:
            print (f"Failed to remove directory {path}: {e} ")
            return False

        return True
    
    @_checkConnection
    def transferFile(self, fileObj, path):

        print (f"Transfering file {path}")
        try:
            self.ftp.storbinary(f"STOR {path}", fileObj)
        except Exception as e:
            print (f"Failed to transfer file {path}: {e}")


    @_checkConnection
    def readFile(self, path):
        remoteFile = RemoteFile()

        try:
            self.ftp.retrbinary('RETR '+ path, remoteFile.write)
        except Exception as e:
            print (f"Failed to read file {path}: {e}")
            return None

        return remoteFile


class RemoteFile:

    def __init__(self):
        self.content = b''

    def write(self, bytes):
        self.content += bytes