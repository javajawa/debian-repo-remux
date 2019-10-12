#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Special sub-class of the generic URLLib that utilises Apache's AutoIndex
functionality to list Directories
"""

import urllib.error
import urllib.parse
import urllib.request
import xml

from apt.transport.base import URIMismatchError, DirectoryListing
from apt.transports.urllib import UrlLib


class Apache(UrlLib):
    """
    Special sub-class of the generic URLLib that utilises Apache's AutoIndex
    functionality to list Directories
    """

    def list_directory(self, uri: str) -> DirectoryListing:
        """
        Returns a list of files and directories in a directory

        :param string uri:

        :return DirectoryListing:

        :raises NotImplementedError:
        :raises FileNotFoundError:
        """
        url: urllib.parse.ParseResult = urllib.parse.urlparse(uri)

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

        xml_obj = xml.etree.ElementTree.fromstring(html)

        # Ignore the first element (which is always the '..' directory)
        for element in xml_obj.findall('./body/ul/li/a')[1:]:  # type: xml.etree.Element
            file = element.attrib['href']

            if file[-1] == '/':
                listing.directories.append(file[:-1])
            else:
                listing.files.append(file)

        return listing
