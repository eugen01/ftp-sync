
from ftpClient import FTPClient, RemoteFile
import os
from hash import hashFilePartial, hashFile

from io import BytesIO

class Sync:
    def __init__(self, ftpClient):
        
        self.ftpClient = ftpClient


    def syncCurrentFolder(self, local, remote):
        
        remoteEntries = self.ftpClient.getDirectoryContent(remote)

        localEntries = os.scandir(local)

        for localEntry in localEntries:

            if localEntry.is_dir():
                # local entry is a directory, recursively sync its contents
                if localEntry.name in remoteEntries:
                    if remoteEntries[localEntry.name]['type'] != 'dir':
                        # For some reason, a file with the same name as this directory 
                        self.ftpClient.removeFile(os.path.join(remote, localEntry.name))
                else:
                    self.ftpClient.createDirectory(os.path.join(remote, localEntry.name))

                self.syncCurrentFolder(localEntry.path, os.path.join(remote, localEntry.name))

                #TODO - mark directory as synced in the list of remote entries
            else:
                #local entry is a file, not a directory

                if localEntry.name in remoteEntries:
                    if remoteEntries[localEntry.name]['type'] == 'dir':
                        # A directory with this name already exists
                        self.ftpClient.removeDirectory(remoteEntries[localEntry.name])

                self.syncCurrentFile(localEntry.path, remote, remoteEntries)

                #TODO - mark the file, and its hash file as synced in the list of remote entries
        
        # remove all unsynced files and directories

    def syncCurrentFile(self, local, remotePath, folderContents):
        
        file = open(local, 'rb')
        hashValue = hashFilePartial(file)

        
        fileName = os.path.basename(local)
        hashName = "." + fileName

        if fileName in folderContents:
            if hashName in folderContents:
                remoteFile = self.ftpClient.readFile(os.path.join(remotePath, hashName))

                if remoteFile is None:
                    print(f"Failed to read hash file for {local}")
                elif remoteFile.content.decode("utf-8") == hashValue:
                    print(f"File {local} already synced")
                    file.close()
                    return
                
                # remove the Hash file. It will be rewritten
                self.ftpClient.removeFile(os.path.join(remotePath, hashName))

            # remove the file. It will be rewritten.
            self.ftpClient.removeFile(os.path.join(remotePath, fileName))

        file.seek(0)

        self.ftpClient.transferFile(file, os.path.join(remotePath, fileName))
        file.close()

        # now write the hash file
        hashFileBuffer = BytesIO(hashValue.encode("utf-8"))
        self.ftpClient.transferFile(hashFileBuffer, os.path.join(remotePath, hashName))
        
        hashFileBuffer.close()