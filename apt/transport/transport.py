#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Abstract Transport
"""

import typing
import abc

from .base import DirectoryListing


class Transport:
    """
    Abstract class for retrieving information from repos

    The functions 'exists' and 'open_read' are required to be implemented.

    """
    @abc.abstractmethod
    def exists(self, uri: str) -> bool:
        """
        Returns whether a given uri exists.

        :param str uri:

        :return bool:

        :raises URIMismatchError:
        """

    @abc.abstractmethod
    def open_read(self, uri: str) -> typing.IO:
        """
        Opens a file as an IO-like for reading

        :param string uri:

        :return IO:

        :raises URIMismatchError:
        :raises FileNotFoundError:
        """

    @abc.abstractmethod
    def open_write(self, uri: str) -> typing.IO:
        """
        Opens a file as an IO-like for writing

        This function is required to handle the operation of creating directories
        if the underlying data store has such a concept.

        :param string uri:

        :return:

        :raises NotImplementedError:
        :raises URIMismatchError:
        """

    @abc.abstractmethod
    def list_directory(self, uri: str) -> DirectoryListing:
        """
        Returns a list of files and directories in a directory

        :param string uri:

        :return List[str]:

        :raises NotImplementedError:
        :raises URIMismatchError:
        :raises FileNotFoundError:
        """
