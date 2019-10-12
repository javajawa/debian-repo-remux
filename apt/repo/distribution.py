#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A distribution contains the meta data for a major grouping of packages
within a :class:Repository, such as all of those used for a major release.

All of the packages in a repo are expected to be compatible with a system,
although some may conflict directly with each other.

A distribution is split into package lists by "component" (a judgement
grouping, normally based on licensing requirements) and "architecture"
(the CPU type that the package was built for).

All combinations of these should have a valid PackageList of packages in
the Repository's Pool.
"""

import zlib

from typing import Optional, List, Dict

from apt import tags

from .exceptions import NonExistentException
from .abstractrepoobject import AbstractRepoObject
from .packagelist import PackageList


_G_ZIPPER = zlib.decompressobj(16 + zlib.MAX_WBITS)


class Distribution(AbstractRepoObject):
    """
    A distribution contains the meta data for a major grouping of packages
    within a :class:Repository, such as all of those used for a major release.

    All of the packages in a repo are expected to be compatible with a system,
    although some may conflict directly with each other.

    A distribution is split into package lists by "component" (a judgement
    grouping, normally based on licensing requirements) and "architecture"
    (the CPU type that the package was built for).

    All combinations of these should have a valid PackageList of packages in
    the Repository's Pool.
    """

    distribution: str
    _exists: Optional[bool] = None
    release_data: Optional[tags.ReleaseFile] = None
    _packages: Optional[PackageList] = None

    def __init__(self, parent: 'apt.repo.Repository', name: str):
        AbstractRepoObject.__init__(self, parent, parent)

        self.distribution = name

    def exists(self) -> bool:
        """
        Returns whether the distribution currently existing in the repo.

        Existing is, in this context, defined as having a parse-able
        release file.
        If the Repository was created with a GPG context, then the release file
        must also have a valid signature (either inline in the InRelease
        file, or as part of a Release/Release.gpg file pair)

        :return: Whether this distribution exists
        """
        if self._exists is not None:
            return self._exists

        try:
            self._exists = bool(self._get_release_file())
        except FileNotFoundError:
            self._exists = False

        return self._exists

    def components(self) -> List[str]:
        """
        Returns the list of components that are in this Distribution

        :return List[str]:
        """
        if not self.exists():
            raise NonExistentException

        return self._get_release_file().components()

    def architectures(self) -> List[str]:
        """
        Gets the list of architectures that this Distribution supports

        :return List[str]: A list of architecture names
        """
        if not self.exists():
            raise NonExistentException

        return self._get_release_file().architectures()

    def package_list(self, component: str, architecture: str) -> PackageList:
        """
        Gets the package list for a specific component and architecture
        in the current distribution.

        Information about the packages that are found will also be populated
        in the Repository this distribution is from.

        :param str component:
        :param str architecture:
        :return PackageList:
        """
        if self._packages is not None:
            return self._packages

        self._packages = PackageList(self.repo, self)

        if not self.exists():
            return self._packages

        files: Dict[str, tags.FileHash] = self._get_release_file().files
        file_data: tags.FileHash

        for extension, reader in [('.gz', _G_ZIPPER.decompress), ('', Ellipsis)]:
            filename = '{}/binary-{}/Packages{}'.format(component, architecture, extension)

            if filename in files:
                file_data = files[filename]
                break

        if not file_data:
            raise FileNotFoundError()

        contents = self._download_file(
            ['dists', self.distribution, filename],
            file_data, reader
        )

        for package in tags.read_tag_file(contents):
            # pylint: disable=W0212
            imported_package = self.repo._add_package(package, package['Filename'])
            self._packages.add(imported_package)

        return self._packages

    def _get_release_file(self) -> tags.ReleaseFile:
        """
        Download and parses the InRelease/Release files for this Repository.

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

    def __repr__(self):
        return '<apt.repo.Distribution \'{0.distribution}\' of {0.repo.base_uri}>'.format(self)
