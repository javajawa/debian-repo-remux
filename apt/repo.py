#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Class structure for containing the conceptual view of an APT Repository.

A complete repository is represented by the Repository class, with subsections
handled by classes that extend the abstract AbstractRepoObject class.

Each AbstractRepoObject is expects to belong to a Repository, from where
it inherits information like its URI for reading and writing data.
"""

import urllib.error
import urllib.parse
import urllib.request
import gzip
import hashlib

from typing import List, IO, Type, Optional, Callable, Dict
from gnupg import GPG

from apt import tags, transport


class UnattachedAptObjectException(Exception):
    """Exception indicating that an AbstractRepoObject is being used outside
    of an existing :class:Repository content"""
    pass


class NonExistentException(Exception):
    """The exception is raised where an :class:AbstractRepoObject is used
    but does not exist in the repo.

    Reliance on this exception is discouraged, and code should call
    .exists() on the object first."""
    pass


class AbstractRepoObject(object):
    """The AbstractRepoObject represents any part of an APT repository,
    and provides implementations the required logic for reading and writing
    files to that repository.
    """
    repo = ...  # type: Optional[Repository]
    parent = ...  # type: Optional[AbstractRepoObject]

    def __init__(self, parent: Optional['AbstractRepoObject'], repo: Optional['Repository']):
        self.parent = parent
        self.repo = repo

    def get_parent_of_type(self, object_type: Type['AbstractRepoObject']) -> Optional['AbstractRepoObject']:
        """Traverse up this object ancestry to find the nearest object of
        te type supplied

        :param Type[AbstractRepoObject] object_type: The type that is requested
        :return AbstractRepoObject:"""
        parent = self

        while parent:
            if isinstance(parent, object_type):
                return parent

            parent = self.parent

        return None

    def _open_file(self, relative_path: List[str]) -> IO:
        """Opens a repo in the file for read

        :param List[str] relative_path:

        :return IO:

        :raises UnattachedAptObjectException:
        :raises NotImplementedError:
        :raises URIMismatchError:
        :raises FileNotFoundError:
        """
        if not self.repo:
            raise UnattachedAptObjectException()

        path = urllib.request.urljoin(self.repo.base_uri, '/'.join(relative_path))

        return self.repo.transport.open_read(path)

    def _list_dir(self, relative_path: List[str]) -> 'transport.DirectoryListing':
        """Gets a Directory listing for a directory relative to the Repo

        :param List[str] relative_path:

        :return transport.DirectoryListing:

        :raises UnattachedAptObjectException:
        :raises NotImplementedError:
        :raises URIMismatchError:
        :raises FileNotFoundError:
        """
        if not self.repo:
            raise UnattachedAptObjectException()

        path = urllib.request.urljoin(self.repo.base_uri, '/'.join(relative_path))

        return self.repo.transport.list_directory(path)

    def _download_file(self, path: List[str], decoder: Callable, hashes: Dict[str, str]):
        if not self.repo:
            raise UnattachedAptObjectException()

        hash_func = ...  # type: hashlib
        output = b''
        size = 0

        for hash_value, hash_name in [('SHA256', 'sha256'), ('SHA512', 'sha512'), ('MD5Sum', 'md5')]:
            if hash_value in hashes:
                hash_value = hashes[hash_value]
                hash_func = hashlib.new(hash_name)  # type: hashlib

                break

        if 'size' not in hashes:
            raise ValueError("File size missing from hash")

        if not hash_func:
            raise ValueError("No valid hash supplied")

        with self._open_file(path) as stream:
            for block in iter(lambda: stream.read(4096), b""):
                hash_func.update(block)
                size += len(block)
                output += block

        output = decoder(output)
        valid = (hash_func.hexdigest() == hash_value) and (size == hashes['size'])

        return valid, output


class Repository(AbstractRepoObject):
    """Class that represents a complete APT repository

    An APT repository is a simple data store generally broken down into two
    distinct parts.

    The first is the "Pool": an unstructured blob store of all the
    .deb package files in the Repository which can be downloaded and
    installed onto a machine.

    The second is a series of distributions contained structured and signed
    metadata about the Packages in the pool, allowing tools to find relevant
    packages, do dependency resolution, and then download the packages.
    """
    base_uri = ...  # type: str

    distributions = {}  # type: Dict[str, Distribution]

    gpg = ...  # type: Optional[GPG]
    transport = ...  # type: transport.Transport

    def __init__(self, base_uri: str, gpg: Optional[GPG] = None):
        super(Repository, self).__init__(None, self)

        if base_uri[0] == '/':
            base_uri = 'file://' + base_uri

        if base_uri[-1] != '/':
            base_uri += '/'

        self.base_uri = base_uri

        self.gpg = gpg
        self.transport = transport.Transport.get_transport(self.base_uri)

        self.distributions = None

    def distribution(self, distribution: str) -> 'Distribution':
        """Gets a distribution object from this Repo by name.

        This method is just a convince method around the Distribution
        constructor.

        Note that the Distribution may not exist, you must check that with
        distribution.exists().

        :param dtr distribution:
        :return Distribution:
        """
        if distribution not in self.distributions:
            self.distributions[distribution] = Distribution(self, distribution)

        return self.distributions[distribution]


class Distribution(AbstractRepoObject):
    """A distribution contains the meta data for a major grouping of packages
    within a :class:Repository, such as all of those used for a major release.

    All of the packages in a repo are expected to be compatible with a system,
    although some may conflict directly with each other.

    A distribution is split into package lists by "component" (a judgement
    grouping, normally based on licensing requirements) and "architecture"
    (the CPU type that the package was built for).

    All combinations of these should have a valid PackageList of packages in
    the Repository's Pool
    """

    distribution = ...  # type: str
    _exists = ...  # type: bool
    release_data = None  # type: Optional[tags.ReleaseFile]

    def __init__(self, parent: 'Repository', name: str):
        super(Distribution, self).__init__(parent, parent)

        self.distribution = name

    def exists(self) -> bool:
        """Returns whether the distribution currently existing in the repo.

        Existing is, in this context, defined as having a parse-able
        release file.
        If the Repository was created with a GPG context, then the release file
        must also have a valid signature (either inline in the InRelease
        file, or as part of a Release/Release.gpg file pair)

        :return: Whether this distribution exists
        """
        if self._exists is not Ellipsis:
            return self._exists

        try:
            self._exists = bool(self._get_release_file())
        except FileNotFoundError:
            self._exists = False

        return self._exists

    def components(self) -> List[str]:
        """Returns the list of components that are in this Distribution

        :return List[str]:
        """
        if not self.exists():
            raise NonExistentException

        return self._get_release_file().components()

    def architectures(self) -> List[str]:
        """Gets the list of architectures that this Distribution supports

        :return List[str]: A list of architecture names
        """
        if not self.exists():
            raise NonExistentException

        return self._get_release_file().architectures()

    def package_list(self, component: str, architecture: str) -> None:
        """Gets the package list for a specific component and architecture
        in the current distribution.

        :param str component:
        :param str architecture:
        :return PackageList:
        """
        if not self.exists():
            raise NonExistentException

        files = self._get_release_file().files

        for extension, reader in [('.gz', gzip.decompress), ('', lambda data: data)]:  # type: (str, Callable)
            filename = '{}/binary-{}/Packages{}'.format(component, architecture, extension)

            if filename in files:
                file_data = files[filename]

                verified, contents = self._download_file(['dists', self.distribution, filename], reader, file_data)

                print('Packages file verification returned', str(verified))
                # print(contents.decode('utf-8'))

                break

    def _get_release_file(self) -> tags.ReleaseFile:
        """Download and parses the InRelease/Release files for this Repository.

        If the Repository has a GPG Context, the signature will also be verified.
        In that case, the file "InRelease" is downloaded first, followed by
        the "Release" and detached signature "Release.gpg" if the former was
        not available.

        Without a GPG context, only "Release" is downloaded.

        This function will return None if the listed files are not available,
        or if the GPG signatures were not verified.

        :return apt_tags.ReleaseFile:
        """
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

            # A Not Found here still allows us to fall back to the Release file
            except FileNotFoundError:
                pass

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
            self.release_data = next(tags.read_tag_file(release_data, tags.ReleaseFile))

            return self.release_data
