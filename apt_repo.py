#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Class the represents a Debian repo somewhere
"""

import urllib.error
import urllib.parse
import urllib.request
import os

from typing import List, Union, IO, Type
from gnupg import GPG

import apt_tags


class NotInRepoException(Exception):
    pass


class AptRepoObject(object):
    def __init__(self, parent: Union['AptRepoObject', None], repo: Union['Repo', None]):
        self.parent = parent
        self.repo = repo

    def get_parent_of_type(self, type: Type['AptRepoObject']) -> Union['AptRepoObject', None]:
        parent = self

        while parent:
            if isinstance(parent, type):
                return parent

            parent = self.parent

        return None

    def _resolve_path(self, relative_path: List[str]) -> str:
        if not self.repo:
            raise NotInRepoException()

        path = self.repo.base_uri

        for segment in relative_path:
            path = path + '/' + segment

        return path

    def _open_file(self, relative_path: List[str]) -> IO:
        if not self.repo:
            raise NotInRepoException()

        path = self._resolve_path(relative_path)

        if self.repo.protocol in ['s3']:
            raise Exception("s3 not yet implemented")

        else:
            return urllib.request.urlopen(path)

    def _list_dir(self, relative_path: List[str]) -> IO:
        if not self.repo:
            raise NotInRepoException()

        path = self._resolve_path(relative_path)

        for segment in relative_path:
            path = os.path.join(path, segment)
            print(path)

        if self.repo.protocol in ['s3']:
            raise Exception("s3 not yet implemented")

        else:
            return urllib.request.urlopen(path)


class Repo(AptRepoObject):
    """
    Class that represents a Debian repo somewhere
    """
    def __init__(self, base_uri: str, gpg: Union[GPG, None] = None):
        super(Repo, self).__init__(None, self)

        if base_uri[0] == '/':
            base_uri = 'file://' + base_uri

        self.protocol = urllib.parse.urlparse(base_uri).scheme
        self.base_uri = base_uri

        self.gpg = gpg

        self.distributions = None

    def distribution(self, distribution: str) -> 'Distribution':
        pass


class Distribution(AptRepoObject):
    release_data = None  # type: Union[apt_tags.ReleaseFile, None]

    def __init__(self, parent: 'Repo', name: str):
        super(Distribution, self).__init__(parent, parent)

        self.distribution = name
        self.release_data = None

    def components(self) -> List[str]:
        return self._get_release_file().components()

    def architectures(self) -> List[str]:
        return self._get_release_file().architectures()

    def _get_release_file(self):
        if self.release_data:
            return self.release_data

        if self.repo and self.repo.gpg:
            gpg = self.repo.gpg
        else:
            gpg = None

        release_data = None

        # If we have a GPG context, attempt to download the InRelease
        # inline-signed file and verify that
        if gpg:
            try:
                release_stream = self._open_file(['dists', self.distribution, 'InRelease'])

                # Attempt to verify the release file
                release_gpg_data = gpg.verify_file(release_stream)
                release_stream.close()

                if release_gpg_data.valid:
                    release_data = release_gpg_data.data

            # Treat all non-404 errors as fatal
            # A 404 here still allows us to fall back to the Release file
            except urllib.error.HTTPError as ex:
                if ex.code != 404:
                    raise ex

        # If we have no data, either InRelease was wrong, or we have no GPG
        if not release_data:
            release_stream = self._open_file(['dists', self.distribution, 'Release'])

            # If we have GPG context, check the detached signature
            # otherwise, just read the data
            if gpg:
                signature_stream = self._open_file(['dists', self.distribution, 'Release.gpg'])
                signature_data = release_stream.read()
                signature_stream.close()

                gpg.verify_file(release_stream, signature_data)
            else:
                release_data = release_stream.read()

            # Make sure the stream gets closed
            release_stream.close()

            # Parse the data
            self.release_data = next(apt_tags.read_tag_file(release_data, apt_tags.ReleaseFile))

            return self.release_data
