#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Classes that preform a set of IO operations for APT repositories using
a consistent interface with consistent exceptions"""

import urllib.parse
import urllib.request
import urllib.error
import os.path

from typing import IO, List, Optional


class URIMismatchError(Exception):
    """Exception indicating that the supplied URI is not valid for the
    selected transport"""
    pass


class DirectoryListing:
    """Class showing files and folders in a directory"""
    files = ...  # type: List[str]
    directories = ...  # type: List[str]

    def __init__(self, files: Optional[List[str]] = None, directories: Optional[List[str]] = None):
        if files is None:
            files = []
        if directories is None:
            directories = []

        self.files = files
        self.directories = directories


class Transport:
    """Abstract class for retrieving information from repos

    The functions 'exists' and 'open_read' are required to be implemented."""

    @staticmethod
    def get_transport(uri: str) -> 'Transport':
        """Gets the best Transport based on a URI

        :param str uri:

        :return Transport:
        """

        url = urllib.parse.urlparse(uri)  # type: urllib.parse.ParseResult

        if url.scheme == 'file':
            return File()

        if url.scheme == 's3':
            raise NotImplementedError()

        return UrlLib()

    def exists(self, uri: str) -> bool:
        """Returns whether a given uri exists.

        :param str uri:

        :return bool:

        :raises NotImplementedError:
        :raises URIMismatchError:
        """
        pass

    def open_read(self, uri: str) -> IO:
        """Opens a file as an IO-like for reading

        :param string uri:

        :return IO:

        :raises URIMismatchError:
        :raises FileNotFoundError:
        """
        pass

    def open_write(self, uri: str) -> IO:
        """Opens a file as an IO-like for writing

        :param string uri:

        :return:

        :raises NotImplementedError:
        :raises URIMismatchError:
        """
        pass

    def list_directory(self, uri: str) -> DirectoryListing:
        """Returns a list of files and directories in a directory

        :param string uri:

        :return List[str]:

        :raises NotImplementedError:
        :raises URIMismatchError:
        :raises FileNotFoundError:
        """
        pass


class File(Transport):
    """APT transport for a local OS accessible filesystem"""

    def exists(self, uri: str) -> bool:
        """Returns whether a given uri exists.

        :param str uri:

        :return bool:

        :raises URIMismatchError:
        """
        url = urllib.parse.urlparse(uri)  # type: urllib.parse.ParseResult

        if url.scheme != 'file':
            raise URIMismatchError("Scheme must be file:")

        return os.path.exists(url.path)

    def open_read(self, uri: str) -> IO:
        """Opens a file as an IO-like for reading

        :param string uri:

        :return IO:

        :raises URIMismatchError:
        :raises FileNotFoundError:
        """
        url = urllib.parse.urlparse(uri)  # type: urllib.parse.ParseResult

        if url.scheme != 'file':
            raise URIMismatchError("Scheme must be file:")

        if not os.path.exists(url.path):
            raise FileNotFoundError(url.path + " does not exist")

        return open(url.path, 'rb')

    def open_write(self, uri: str) -> IO:
        """Opens a file as an IO-like for writing

        :param string uri:

        :return:

        :raises URIMismatchError:
        """
        url = urllib.parse.urlparse(uri)  # type: urllib.parse.ParseResult

        if url.scheme != 'file':
            raise URIMismatchError("Scheme must be file:")

        return open(url.path, 'rb')

    def list_directory(self, uri: str) -> DirectoryListing:
        """Returns a list of files and directories in a directory

        :param string uri:

        :return List[str]:

        :raises URIMismatchError:
        :raises FileNotFoundError:
        """
        url = urllib.parse.urlparse(uri)  # type: urllib.parse.ParseResult

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


class UrlLib(Transport):
    """Transport that attempts to access arbitrary protocols using urllib"""

    def exists(self, uri: str) -> bool:
        """Returns whether a given uri exists.

        :param str uri:

        :raises NotImplementedError:
        """
        raise NotImplementedError('URLLib has no generic "exists" logic')

    def open_read(self, uri: str) -> IO:
        """Opens a file as an IO-like for reading

        :param string uri:

        :return IO:

        :raises FileNotFoundError:
        """
        try:
            return urllib.request.urlopen(uri)
        except (urllib.error.HTTPError, urllib.error.URLError) as ex:
            raise FileNotFoundError(uri, "not found", ex)

    def open_write(self, uri: str) -> IO:
        """Opens a file as an IO-like for writing

        :param string uri:

        :raises NotImplementedError:
        """
        raise NotImplementedError('URLLib has no generic "exists" logic')

    def list_directory(self, uri: str) -> DirectoryListing:
        """Returns a list of files and directories in a directory

        :param string uri:

        :raises NotImplementedError:
        """
        raise NotImplementedError('URLLib has no generic "exists" logic')


class Apache(UrlLib):
    """Special sub-class of the generic URLLib that utilises Apache's AutoIndex
    functionality to list Directories"""

    def exists(self, uri: str) -> bool:
        """Returns whether a given uri exists.

        :param str uri:

        :raises NotImplementedError:
        """
        raise NotImplementedError('URLLib has no generic "exists" logic')

    def open_write(self, uri: str) -> IO:
        """Opens a file as an IO-like for writing

        :param string uri:

        :raises NotImplementedError:
        """
        raise NotImplementedError('URLLib has no generic "exists" logic')

    def list_directory(self, uri: str) -> DirectoryListing:
        """Returns a list of files and directories in a directory

        :param string uri:

        :return DirectoryListing:

        :raises NotImplementedError:
        :raises FileNotFoundError:
        """
        url = urllib.parse.urlparse(uri)  # type: urllib.parse.ParseResult

        if url.scheme != 'http' and url.scheme != 'https':
            raise URIMismatchError("Scheme must be file:")

        listing = DirectoryListing()

        if uri[-1] != '/':
            uri += '/'

        uri += '?F=0'

        try:
            http = urllib.request.urlopen(uri)
        except (urllib.error.HTTPError, urllib.error.URLError):
            raise FileNotFoundError(uri)

        if http.readline() != b'<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n':
            raise FileNotFoundError(uri)

        html = http.read()
        http.close()

        import xml.etree.ElementTree

        xml = xml.etree.ElementTree.fromstring(html)

        for element in xml.findall('./body/ul/li/a')[1:]:  # type: xml.etree.Element
            file = element.attrib['href']

            if file[-1] == '/':
                listing.directories.append(file[:-1])
            else:
                listing.files.append(file)

        return listing
