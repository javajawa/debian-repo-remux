#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
APT transport for a local OS accessible filesystem
"""

import os.path
import urllib.parse
from typing import IO

from apt.transport import Transport
from apt.transport.exceptions import URIMismatchError
from apt.transport.directorylisting import DirectoryListing


class File(Transport):
    """
    APT transport for a local OS accessible filesystem
    """

    def exists(self, uri: str) -> bool:
        """
        Returns whether a given uri exists.

        :param str uri:

        :return bool:

        :raises URIMismatchError:
        """
        url: urllib.parse.ParseResult = urllib.parse.urlparse(uri)

        if url.scheme != 'file':
            raise URIMismatchError("Scheme must be file:")

        return os.path.exists(url.path)

    def open_read(self, uri: str) -> IO:
        """
        Opens a file as an IO-like for reading

        :param string uri:

        :return IO:

        :raises URIMismatchError:
        :raises FileNotFoundError:
        """
        url: urllib.parse.ParseResult = urllib.parse.urlparse(uri)

        if url.scheme != 'file':
            raise URIMismatchError("Scheme must be file:")

        if not os.path.exists(url.path):
            raise FileNotFoundError(url.path + " does not exist")

        return open(url.path, 'rb')

    def open_write(self, uri: str) -> IO:
        """
        Opens a file as an IO-like for writing

        :param string uri:

        :return:

        :raises URIMismatchError:
        """
        url: urllib.parse.ParseResult = urllib.parse.urlparse(uri)

        if url.scheme != 'file':
            raise URIMismatchError("Scheme must be file:")

        os.makedirs(os.path.dirname(url.path), exist_ok=True)

        return open(url.path, 'wb')

    def list_directory(self, uri: str) -> DirectoryListing:
        """
        Returns a list of files and directories in a directory

        :param string uri:

        :return List[str]:

        :raises URIMismatchError:
        :raises FileNotFoundError:
        """
        url: urllib.parse.ParseResult = urllib.parse.urlparse(uri)

        if url.scheme != 'file':
            raise URIMismatchError("Scheme must be file:")

        if not os.path.exists(url.path):
            raise FileNotFoundError(url.path + " does not exist")

        listing = DirectoryListing()

        with os.scandir(url.path) as iterator:
            for entry in iterator:
                if entry.is_dir():
                    listing.directories.append(entry.name)
                if entry.is_file():
                    listing.files.append(entry.name)

        return listing
