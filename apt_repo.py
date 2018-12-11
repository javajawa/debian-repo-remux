#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Class the represents a Debian repo somewhere
"""

import urllib.error
import urllib.parse
import urllib.request
import os

from typing import List, IO, Type, Optional
from gnupg import GPG

import apt_tags


class UnattachedAptObjectException(Exception):
    """Exception indicating that an AptReopObject is being used outside
    of an existing :class:Repo content"""
    pass


class NonExistentException(Exception):
    """The excpetion is raised where an :class:AptRepoObject is used
    but does not exist in the repo.

    Reliance on this exception is discouraged, and code should call
    .exists() on the object first."""
    pass


class AptRepoObject(object):
    repo = ...  # type: Optional[Repo]
    parent = ...  # type: Optional[AptRepoObject]

    def __init__(self, parent: Optional['AptRepoObject'], repo: Optional['Repo']):
        self.parent = parent
        self.repo = repo

    def get_parent_of_type(self, object_type: Type['AptRepoObject']) -> Optional['AptRepoObject']:
        parent = self

        while parent:
            if isinstance(parent, object_type):
                return parent

            parent = self.parent

        return None

    def _resolve_path(self, relative_path: List[str]) -> str:
        if not self.repo:
            raise UnattachedAptObjectException()

        path = self.repo.base_uri

        for segment in relative_path:
            path = path + '/' + segment

        return path

    def _open_file(self, relative_path: List[str]) -> IO:
        if not self.repo:
            raise UnattachedAptObjectException()

        path = self._resolve_path(relative_path)

        if self.repo.protocol in ['s3']:
            raise Exception("s3 not yet implemented")

        else:
            return urllib.request.urlopen(path)

    def _list_dir(self, relative_path: List[str]) -> IO:
        if not self.repo:
            raise UnattachedAptObjectException()

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
    protocol = ...  # type: str
    base_uri = ...  # type: str

    distributions = None  # type: Optional[List[Distribution]]

    gpg = ...  # type: Optional[GPG]

    def __init__(self, base_uri: str, gpg: Optional[GPG] = None):
        super(Repo, self).__init__(None, self)

        if base_uri[0] == '/':
            base_uri = 'file://' + base_uri

        self.protocol = urllib.parse.urlparse(base_uri).scheme
        self.base_uri = base_uri

        self.gpg = gpg

        self.distributions = None

    def distribution(self, distribution: str) -> 'Distribution':
        return Distribution(self, distribution)


class Distribution(AptRepoObject):
    """A distribution contains the meta data for a major grouping of packages
    within a :class:Repo, such as all of those used for a major release.


    """

    distribution = ...  # type: str
    _exists = ...  # type: bool
    release_data = None  # type: Optional[apt_tags.ReleaseFile]

    def __init__(self, parent: 'Repo', name: str):
        super(Distribution, self).__init__(parent, parent)

        self.distribution = name
        self.release_data = None

    def exists(self) -> bool:
        """Returns whether the distribution currently existing in the repo.

        Existing is, in this context, defined as having a parseable
        release file.
        If the Repo was created with a GPG context, then the release file
        must also have a valid signature (either inline in the InRelease
        file, or as part of a Release/Release.gpg file pair)

        :return: Whether this distribution exists
        """
        if self._exists is not None:
            return self._exists

        try:
            self._exists = bool(self._get_release_file())
        except:
            self._exists = False

        return self._exists

    def components(self) -> List[str]:
        if not self.exists():
            raise NonExistentException

        return self._get_release_file().components()

    def architectures(self) -> List[str]:
        if not self.exists():
            raise NonExistentException

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
