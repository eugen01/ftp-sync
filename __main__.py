#!/usr/bin/env python3
"""
ftp-sync: Backup tool over FTP
"""

import argparse
import sys
from pathlib import Path

from ftpClient import FTPClient, DryFTPClient
from sync import Sync
import log


def main():
    """Main entry point for the ftp-sync CLI application."""
    parser = argparse.ArgumentParser(
        prog='ftp-sync',
        description='Backup tool over FTP',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --help                  Show this help message
  %(prog)s --version               Show version information
  %(prog)s SRC DEST --host [HOST] --user [USER] --password []


        """
    )

    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )

    parser.add_argument(
        'source',
        help='Source directory or file to backup'
    )

    parser.add_argument(
        'destination',
        help='Destination directory'
    )

    parser.add_argument(
        'host',
        help='FTP host address'
    )

    parser.add_argument(
        'user',
        help='FTP username'
    )

    parser.add_argument(
        'password',
        help='FTP password'
    )

    parser.add_argument(
        '--port',
        type=int,
        default=21,
        help='FTP port (default: 21)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be transferred without actually doing it'
    )

    parser.add_argument(
        '--delete',
        action='store_true',
        help='Delete extraneous from the remote server'
    )

    parser.add_argument(
        '--strict_match',
        action='store_true',
        help='Compares hashes of the entire file when matching [WARNING - unsuitable for medium or large files]'
    )

    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Do not compare files between source and destination. Overwrite existing files'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.source or not args.destination or not args.host or not args.user or not args.password:
        parser.print_help()
        parser.error("Source, destination, host, username and password are all required")
        return 0

    if args.verbose:
        print(f"Source: {args.source}")
        print(f"Destination: {args.destination}")
        print(f"FTP Host: {args.host}")
        print(f"Dry run: {args.dry_run}")
        print(f"Delete: {args.delete}")
        log.setVerboseLogging(True)

    if not args.destination.startswith('/'):
        print("WARNING - it is highly recommended to use an absolute path for the remote directory")

    ftpClient = None

    if args.dry_run:
        ftpClient = DryFTPClient(args.host, args.user, args.password, args.port)
    else:
        ftpClient = FTPClient(args.host, args.user, args.password, args.port)

    if False == ftpClient.connect():
        print(f"Failed to connect to {args.host}")
        return 0

    syncer = Sync(ftpClient, delete = args.delete, update = not args.overwrite, strictMatch = args.strict_match)

    success = False

    import os

    if os.path.isdir(args.source):
        counts = {'files': 0, 'dirs': 0}
        if syncer.syncCurrentFolder(args.source, args.destination, counts):
            print(f"Synced {counts['files']} files and {counts['dirs']} directories")
            success = True
    elif os.path.isfile(args.source):
         if syncer.syncCurrentFile(args.source, args.destination):
            print (f"1 File synced")
            success = True

    else:
        print(f"Invalid source")

    if not success:
        return 0

    return 1


if __name__ == '__main__':
    sys.exit(main())
