#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Transport that attempts to access arbitrary protocols using urllib
"""

import urllib.error
import urllib.request
from typing import Optional, IO, Dict

from apt.transport import Transport


class UrlLib(Transport):
    """
    Transport that attempts to access arbitrary protocols using urllib
    """

    _last_uri: str
    _last_req: Optional[IO] = None
    _exists: Dict[str, bool] = {}

    def exists(self, uri: str) -> bool:
        """
        Returns whether a given uri exists.

        :param str uri:

        :return bool:
        """
        if self._last_req:
            self._last_req.close()
            self._last_req = None
            self._last_uri = None

        if uri in self._exists:
            return self._exists[uri]

        try:
            self._last_req = urllib.request.urlopen(uri)
            self._last_uri = uri
            self._exists[uri] = True

            return True

        except (urllib.error.HTTPError, urllib.error.URLError):
            self._exists[uri] = False

            return False

    def open_read(self, uri: str) -> IO:
        """
        Opens a file as an IO-like for reading

        :param string uri:

        :return IO:

        :raises FileNotFoundError:
        """
        if self._last_req:
            if self._last_uri == uri:
                return self._last_req

            self._last_req.close()
            self._last_req = None
            self._last_uri = None

        try:
            return urllib.request.urlopen(uri)
        except (urllib.error.HTTPError, urllib.error.URLError) as ex:
            raise FileNotFoundError(uri, "not found", ex)

    def open_write(self, uri: str):
        """
        Opens a file as an IO-like for writing

        :param string uri:

        :raises NotImplementedError:
        """
        if self._last_req:
            self._last_req.close()
            self._last_req = None
            self._last_uri = None

        raise NotImplementedError('URLLib has no generic "write" logic')

    def list_directory(self, uri: str):
        """
        Returns a list of files and directories in a directory

        :param string uri:

        :raises NotImplementedError:
        """
        if self._last_req:
            self._last_req.close()
            self._last_req = None
            self._last_uri = None

        raise NotImplementedError('URLLib has no generic "exists" logic')
