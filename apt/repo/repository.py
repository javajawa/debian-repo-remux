#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Class that represents a complete APT repository

An APT repository is a simple data store generally broken down into two
distinct parts.

The first is the "Pool": an unstructured blob store of all the
.deb package files in the Repository which can be downloaded and
installed onto a machine.

The second is a series of distributions contained structured and signed
metadata about the Packages in the pool, allowing tools to find relevant
packages, do dependency resolution, and then download the packages.
"""

import hashlib

from typing import Dict, Optional, KeysView, Union, IO
from gnupg import GPG

from apt import deb, tags, transport

from .distribution import Distribution
from .package import Package
from .abstractrepoobject import AbstractRepoObject
from .exceptions import MissingControlFieldException


SHA256 = str
NameStr = str
Version = str


class Repository(AbstractRepoObject):
    """
    Class that represents a complete APT repository

    An APT repository is a simple data store generally broken down into two
    distinct parts.

    The first is the "Pool": an unstructured blob store of all the
    .deb package files in the Repository which can be downloaded and
    installed onto a machine.

    The second is a series of distributions contained structured and signed
    metadata about the Packages in the pool, allowing tools to find relevant
    packages, do dependency resolution, and then download the packages.
    """
    base_uri: str

    _distributions: Dict[NameStr, Distribution] = {}
    _pool: Dict[SHA256, Package] = {}

    """
    A list of all packages with a sub-list of all versions of that package,
    pointing to the package's hash
    """
    _pool_by_package: Dict[NameStr, Dict[Version, SHA256]] = {}

    gpg: Optional[GPG]
    transport: transport.Transport

    def __init__(self, base_uri: str, gpg: Optional[GPG] = None):
        AbstractRepoObject.__init__(self, self, None)

        if base_uri[0] == '/':
            base_uri = 'file://' + base_uri

        if base_uri[-1] != '/':
            base_uri += '/'

        self.base_uri = base_uri

        self.gpg = gpg
        self.transport = transport.get_transport(self.base_uri)

    def distribution(self, distribution: str) -> Distribution:
        """
        Gets a distribution object from this Repo by name.

        This method is just a convince method around the Distribution
        constructor.

        Note that the Distribution may not exist, you must check that with
        distribution.exists().

        :param str distribution:
        :return Distribution:
        """
        if distribution not in self._distributions:
            self._distributions[distribution] = Distribution(self, distribution)

        return self._distributions[distribution]

    def distributions(self) -> KeysView[str]:
        """
        Returns the list of distributions that are currently known of in
        this repo. These distributions may or may not exists, and will also
        include any distribution you have attempted to access.

        This list will be initially blank, and can be populated with calls
        to .scan_distributions() or .distribution().

        :return KeysView[str]:
        """
        return self._distributions.keys()

    def scan_distributions(self) -> bool:
        """
        Attempt to scan the repository for a list of distributions in a
        repository.

        This functionality requires the ability to list directories and check
        for existence of files on the remote.

        This function returns a boolean of whether the scan was successful;
        you can get the list of distribution keys with the .distributions()
        method, which may include distributions you have manually added.

        If the folder scan of /dists/ causes a not found error, then this
        method assumes the repo is blank, and returns true.

        :return bool:

        :raises URIMismatchError:
        :raises FileNotFoundError:
        """
        try:
            listing = self._list_dir(['dists'])
        except NotImplementedError:
            return False
        except FileNotFoundError:
            return True

        for directory in listing.directories:
            if directory not in self._distributions:
                self.distribution(directory)

        return True

    def package_by_hash(self, package_hash: SHA256) -> Optional[Package]:
        """
        Gets a package via it's SHA-256 hash.

        :param package_hash:
        :return:
        """
        return self._pool[package_hash]

    def adopt(self, package: Union[Package, IO]) -> Package:
        """
        Add a package to this repo's pool.

        The package can be one of:
         - An existing package object, which exists
         - An IO-like (implements "read") object the contains a .deb file
        """

        # If we have been supplied a package object, we need to copy it from
        # the existing repo to this one
        if isinstance(package, Package):
            # If the package is from this repo, short-circuit out
            if package.repo == self.repo:
                return package

            # If we have a package with a matching SHA256, use that
            if package['SHA256'] in self._pool:
                return self._pool[package['SHA256']]

            # Download the package from the remote repo, and verify it
            # pylint: disable=W0212
            deb_data = package._download_file([package['Filename']], package.hashes())

            contents_data = package.repo.contents()

            source_file = package['Filename']

        # Otherwise, if we have an IO-like read interface, we see if we can
        # parse the input as a .deb archive.
        elif hasattr(package, 'read'):
            # Load the data into memory
            deb_data = package.read()

            sha256 = hashlib.sha256(deb_data).hexdigest()

            # If we have a package with a matching SHA256, use that
            if sha256 in self._pool:
                return self._pool[sha256]

            package = deb.extract_control_file(deb_data)
            package['SHA256'] = sha256

            contents_data = deb.extract_contents_list(deb_data)

            source_file = 'buffer ' + str(package)

        else:
            raise ValueError("Invalid Type")

        filename = ['pool']

        # noinspection SpellCheckingInspection
        if package['Section'] in ['libs', 'oldlibs']:
            filename.append('lib' + package['Package'][0])
        else:
            filename.append(package['Package'][0])

        filename.append(package['Package'])

        basename = "{0[Package]}_{0[Version]}_{0[Architecture]}.deb".format(package)
        filename.append(basename)

        with self._write_file(filename) as output:
            output.write(deb_data)

        package = Package(self, self, package)
        package['Filename'] = '/'.join(filename)

        if contents_data and len(contents_data) > 0:
            # pylint: disable=W0212
            package._contents = contents_data

        filename[-1] = basename + '.dat'
        with self._write_file(filename) as output:
            output.write(str(package).encode())

        filename[-1] = basename + '.contents'
        with self._write_file(filename) as output:
            output.write('\n'.join(package.contents()).encode())

        self._add_package(package, source_file)

        return package

    def _add_package(self, package: tags.TagBlock, filename: str) -> Package:
        if not package['SHA256']:
            raise MissingControlFieldException(filename, 'SHA256')

        if not package['Filename']:
            raise MissingControlFieldException(filename, 'Filename')

        if not package['Package']:
            raise MissingControlFieldException(filename, 'Package')

        if not package['Version']:
            raise MissingControlFieldException(filename, 'Version')

        if package['SHA256'] in self._pool:
            return self._pool[package['SHA256']]

        package = Package(self, self, package)

        self._pool[package['SHA256']] = package

        if package['Package'] not in self._pool_by_package:
            self._pool_by_package[package['Package']] = {}
        self._pool_by_package[package['Package']][package['Version']] = package['SHA256']

        return package

    def __repr__(self) -> str:
        return \
            '<apt.repo.Repo {0.base_uri} (distributions: [{1}]; {2} packages)>'.format(
                self, ', '.join(self._distributions.keys()), len(self._pool)
            )
