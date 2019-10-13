#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Classes that preform a set of IO operations for APT repositories using
a consistent interface with consistent exceptions
"""

import urllib.parse

from .exceptions import *
from .directorylisting import DirectoryListing
from .transport import Transport

from ..transports import File, UrlLib


def get_transport(uri: str) -> Transport:
    """
    Gets the best Transport based on a URI

    :param str uri:

    :return Transport:
    """

    url: urllib.parse.ParseResult = urllib.parse.urlparse(uri)

    if url.scheme == 'file':
        return File()

    if url.scheme == 's3':
        raise NotImplementedError()

    return UrlLib()
