# ftp-sync - Backup tool over FTP

BACKGROUND
----------

Ftp-sync is a tool for backing up files and to a FTP server.

It was developed for a relatively specific use-case, incremental back-ups to a server that only supports FTP.

For other use-cases there are better tools out there and you should seek them out.
Unfortunately, filesystems mounted via FTP do not support a lot of the file system operations that these tools use.

Individual files are transferred in their entirety, if they are different from the version in the destination.\
In order to check for file changes, a 'hidden' hash file is created in the remote location for each file.\
The file stores a partial or complete hash of the file, and this is used to compare the two versions.\
The hash is generated from the first and last 8192 bytes in the file. If the file is smaller than
16384 bytes, it is hased entirely.\
Obviously, this isn't a perfect hashing method, and for some files it may result in false matches.\
That's where the 'strict_match' and 'overwrite' options come in.

USAGE
-----

    ftp-sync /local/dir/ /remote/dir/ <IP/URL> <USER> <PASSWORD>

ftp-sync supports the following options:

--dry-run:\
    Any operation that modifies the remote filesystem is replaced with a log.\
    An FTP connection is still established in order to check existing files on the server.

--verbose:\
    Enables verbose logging

--delete:\
    Removes any file or folder on the remote server that doesn't also exist in the local folder.

--strict_match:\
    The entire file is hashed before matching it with the remote version.\
    This should only be used for individual files if the partial match is unsuitable and the size is not large enough to cause issues.

--overwrite:\
    The file hashes are not generated and the files are not compared. Everything is transferred.\
    Hash files will not be stored on the server. If they are already there, and 'delete' isn't used, they may interfere with future syncs


INSTALLATION
-----------

ftp-sync can be installed by running:

    pyinstaller -n ftp-sync __main__.py

pyinstaller can be installed using pip or by running:

    apt install python3-pyinstaller

LIMITATIONS
-----------

1. There are possible issues when using different filesystems between local and remote.

For example, the tool uses os.path.join to create paths to be used on the remote filesystem.\
This is technically incorrect, since the 'os' module is only valid for the operating system where it's being used.\
The tool was only tested between two ext4 filesystems.

2. The backed up files have different attributes

The user id , group id, permissions, etc. will all depend on the FTP user and the settings on the FTP server.\
They will not be the same as the local files.\

3. Python's ftplib can open too many connections

I couldn't find out exactly what's happening, but when processing a large number of files the server would\
sometimes respond with "421 - Too many open files".\
I tried multiple methods to mitigate this but I couldn't find one that works other than restarting the connection.