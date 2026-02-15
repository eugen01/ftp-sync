
from ftpClient import FTPClient, RemoteFile
import os
from hash import hashFilePartial, hashFile

from io import BytesIO
from log import logV, logA

class Sync:
    def __init__(self, ftpClient, delete = False, update = True, strictMatch = False):
        self.ftpClient = ftpClient
        self.delete = delete
        self.update = update
        self.strictMatch = strictMatch

    '''
        Syncs the content of a local folder to a folder on the FTP server
    '''
    def syncCurrentFolder(self, local, remote, counts = {'files': 0, 'dirs': 0}):

        success = True

        remoteEntries = self.ftpClient.getDirectoryContent(remote)

        if remoteEntries is None:
            self.ftpClient.createDirectory(remote)
            remoteEntries = {}

        localEntries = os.scandir(local)

        for localEntry in localEntries:

            if localEntry.is_dir():
                # local entry is a directory, recursively sync its contents
                if localEntry.name in remoteEntries:
                    if remoteEntries[localEntry.name]['type'] != 'dir':
                        # For some reason, there is a file with the same name as this directory
                        if False == self.ftpClient.removeFile(os.path.join(remote, localEntry.name)):
                            logA(f"Remote directory {localEntry.name} could not be deleted")
                            success = False
                            continue
                else:
                    if False == self.ftpClient.createDirectory(os.path.join(remote, localEntry.name)):
                        logA(f"Remote directory {localEntry.name} could not be created")
                        success = False
                        continue

                    # Create a record in 'remoteEntries' for consistency
                    remoteEntries[localEntry.name] = {'type' : 'dir', 'sizd': '', 'modify': '', 'unix.mode': ''}

                success = (success and self.syncCurrentFolder(localEntry.path, os.path.join(remote, localEntry.name), counts))

                # For safety, mark the remote folder as "DO NOT DELETE" even if the sync failed
                if self.delete:
                    remoteEntries[localEntry.name]['Synced'] = True

            else:
                #local entry is a file, not a directory

                if localEntry.name in remoteEntries:
                    if remoteEntries[localEntry.name]['type'] == 'dir':
                        # A directory with this name already exists
                        self.ftpClient.removeDirectory(remoteEntries[localEntry.name])

                if self.syncCurrentFile(localEntry.path, remote, remoteEntries):
                    counts['files'] += 1
                else:
                    success = False

        counts['dirs'] += 1

        if not self.delete:
            return success

        # remove all unsynced files and directories
        for remoteName, details in remoteEntries.items():
            if not details.get('Synced'):
                if details['type'] == 'dir':
                    self.ftpClient.removeDirectory(os.path.join(remote, remoteName))
                elif details['type'] == 'file':
                    self.ftpClient.removeFile(os.path.join(remote, remoteName))

        return success


    '''
        Syncs a local file to a remote directory
        Can be called with an existing listing of the remote directory
        or independently to sync just one file.
        Returns true if the file was synced successfully, false otherwise
    '''
    def syncCurrentFile(self, local, remotePath, folderContents = {}):

        success = True

        if not folderContents:
            folderContents = self.ftpClient.getDirectoryContent(remotePath)

        if folderContents is None:
            return False

        try:
            file = open(local, 'rb')
        except Exception as e:
            logA(f"Could not open {local} for reading: {e}")
            return False

        hashValue = ''
        if self.update:
            hashValue = hashFilePartial(file) if self.strictMatch else hashFile(file)

        fileName = os.path.basename(local)
        hashName = "." + fileName + ".hash"

        fileAlreadyExists = True if fileName in folderContents else False
        hashAlreadyExists = True if self.update and hashName in folderContents else False

        if fileAlreadyExists:
            if hashAlreadyExists:
                remoteFile = self.ftpClient.readFile(os.path.join(remotePath, hashName))

                if remoteFile is None:
                    logA(f"Failed to read hash file for {local}")
                elif remoteFile.content.decode("utf-8") == hashValue:
                    logV(f"File {local} already synced")
                    folderContents[fileName]['Synced'] = True
                    folderContents[hashName]['Synced'] = True
                    file.close()
                    return True

                # remove the Hash file. It will be rewritten
                success = self.ftpClient.removeFile(os.path.join(remotePath, hashName))

            # remove the file. It will be rewritten.
            success = (success and self.ftpClient.removeFile(os.path.join(remotePath, fileName)))

        file.seek(0)

        if not self.ftpClient.transferFile(file, os.path.join(remotePath, fileName)):
            success = False
        elif not fileAlreadyExists:
            # File was uploaded, update 'folderContents' with a dummy entry
            folderContents[fileName] = {'Synced': True, 'type': 'file', 'size': '', 'modify': '',\
                                         'unix.mode': '', 'unix.uid': '', 'unix.gid': '', 'unique': ''}
        else:
            folderContents[fileName]['Synced'] = True


        file.close()

        if self.update:
            # now write the hash file.
            hashFileBuffer = BytesIO(hashValue.encode("utf-8"))
            if not self.ftpClient.transferFile(hashFileBuffer, os.path.join(remotePath, hashName)):
                logA(f"File {local} synced, but hash file could not be created")
                success = False
            elif not hashAlreadyExists:
                folderContents[hashName] = {'Synced': True, 'type': 'file', 'size': '', 'modify': '',\
                                         'unix.mode': '', 'unix.uid': '', 'unix.gid': '', 'unique': ''}
            else:
                folderContents[hashName]['Synced'] = True

            hashFileBuffer.close()

        return success