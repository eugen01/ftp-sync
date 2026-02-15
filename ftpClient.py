
from ftplib import FTP, error_perm

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
    def disconnect(self):
        if self.ftp is not None:
            try:
                self.ftp.quit()
            except Exception as e:
                print(f"Failed to close the FTP connection{e}")
                self.ftp.close()

        self.connected = False
        self.ftp = None

    '''
        Checks if an error code returned by the server is a 'Transient Negative Completion' reply
        These errors indicate a temporary issue and the command can be retried.
    '''
    def isTransientError(self, error):
        try:
            errorMessage = str(error)[:3]
            return errorMessage.startswith("4")
        except Exception as e:
            # Error message is smaller than 3 characters or not a string.
            return False

    @_checkConnection
    def reconnect(self):
        self.disconnect()
        self.ftp = FTP()
        return self.connect()

    @_checkConnection
    def getDirectoryContent(self, path):

        print(f"Retrieving directory content {path}")

        retries = 3

        while retries > 0:
            try:
                files = self.ftp.mlsd(path)
                return dict(files)
            except Exception as e:
                print(f"Failed to retrieve directory content: {e}")
                if self.isTransientError(e):
                    self.reconnect()
                    retries -= 1
                else:
                    return None

    @_checkConnection
    def getDirectoryNames(self):

        print (f"Retrieving directory names {path}")

        retries = 3

        while retries > 0:
            try:
                names = self.ftp.nlst(path)
                return names
            except Exception as e:
                print(f"Failed to retrieve directory content: {e}")
                if self.isTransientError(e):
                    self.reconnect()
                    retries -= 1
                else:
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
    def createDirectory(self, path, makeParents = True):

        if path == "/" :
            print(f"Will not create root directory{path}")
            return False

        print (f"Creating directory {path}")
        
        retries = 3

        while retries > 0:
            try:
                self.ftp.mkd(path)
            except error_perm as permError:
                if str(permError).startswith("550") and True == makeParents:
                    import os
                    head, tail = os.path.split(path)
                    if not tail:
                        head = os.path.dirname(head)

                    if True == self.createDirectory(head, True):
                        return self.createDirectory(path, False)
                    else:
                        return False

                else:
                    print (f"Failed to create directory {path}: {e}")
                    return False

            except Exception as e:
                print (f"Failed to create directory {path}: {e}")
                if self.isTransientError(e):
                    self.reconnect()
                    retries -= 1
                else:
                    return False

        return True


    @_checkConnection
    def removeDirectory(self, path):

        print (f"Removing directory {path}")
        import os
        retries = 3

        while retries > 0:
            try:
                content = self.getDirectoryContent(path)

                for name, details in content.items():
                    if details["type"] == "dir":
                        self.removeDirectory(os.path.join(path, name))
                    elif details["type"] == "file":
                        self.removeFile(os.path.join(path, name))
                    else:
                        print (f"Skipping {os.path.join(path, name)}")

                self.ftp.rmd(path)
                return True

            except Exception as e:
                print (f"Failed to remove directory {path}: {e} ")
                if self.isTransientError(e):
                    self.reconnect()
                    retries -= 1
                else:
                    return False

        return True

    @_checkConnection
    def transferFile(self, fileObj, path):

        print (f"Transfering file {path}")
        retries = 3

        while retries > 0:
            try:
                self.ftp.storbinary(f"STOR {path}", fileObj)
                return True
            except Exception as e:
                print (f"Failed to transfer file {path}: {e}")
                if self.isTransientError(e):
                    self.reconnect()
                    retries -= 1
                else:
                    return False

        return True


    @_checkConnection
    def readFile(self, path):
        remoteFile = RemoteFile()

        retries = 3

        while retries > 0:
            try:
                self.ftp.retrbinary('RETR '+ path, remoteFile.write)
                return remoteFile
            except Exception as e:
                print (f"Failed to read file {path}: {e}")
                if self.isTransientError(e):
                    self.reconnect()
                    retries -= 1
                else:
                    return None

        return remoteFile

class DryFTPClient(FTPClient):

    def __init__(self, host, user, password, port=21):
        super(DryFTPClient, self).__init__(host, user, password, port)

    def transferFile(self, fileObj, path):
        print (f"[DRY] Transfering file {path}")
        return True

    def createDirectory(self, fileObj, path):
        print (f"[DRY] Creating directory {path}")
        return True

    def removeFile(self, path):
        print (f"[DRY] Removing {path} from FTP filesystem")
        return True

    def removeDirectory(self, path):
        print (f"[DRY] Removing directory {path}")
        return True

class RemoteFile:

    def __init__(self):
        self.content = b''

    def write(self, bytes):
        self.content += bytes