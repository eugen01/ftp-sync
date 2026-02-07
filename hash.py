import hashlib

'''
Hash the first 8192 bytes and the last 8192.
If the file is smaller than that, hash all of it.

This isn't perfect, but it should be enough to determine if the file has changed
without having to process a large file.

The caller is responsible for opening the file and closing it
'''
def hashFilePartial(fileObj):

    hasher = hashlib.sha256()

    # Get file size
    fileObj.seek(0, 2)  # Seek to end
    file_size = fileObj.tell()

    if file_size <= 16384:
        # If file is smaller than 16384 bytes, hash all of it
        fileObj.seek(0)
        data = fileObj.read()
        hasher.update(data)
    else:
        # Hash first 8192 bytes
        fileObj.seek(0)
        data = fileObj.read(8192)
        hasher.update(data)

        # Hash last 8192 bytes
        fileObj.seek(-8192, 2)
        data = fileObj.read(8192)
        hasher.update(data)

    return hasher.hexdigest()


'''
Hashes the entire file in chunks of 8192 bytes

The caller is responsible for opening the file and closing it
'''
def hashFile(fileObj):

    hasher = hashlib.sha256()

    while chunk:= fileObj.read(8192):
        hasher.update(chunk)

    return hasher.hexdigest()