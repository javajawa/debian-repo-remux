#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Represents an arbitrary list of packages in a repository
"""

from typing import Set, Iterator, Union, IO

from .abstractrepoobject import AbstractRepoObject
from .package import Package


class PackageList(AbstractRepoObject):
    """
    Represents an arbitrary list of packages in a repository
    """

    _hashes: Set[str] = set()
    _index: int

    _iter: Iterator[str]

    def __iter__(self):
        return self._hashes.__iter__()

    def __next__(self) -> Package:
        package = self._iter.__next__()

        return self.repo.package_by_hash(package)

    def __len__(self):
        return len(self._hashes)

    def add(self, package: Union[Package, IO]):
        """
        Adds a package to this PackageList, potentially causing the repo
        to adopt it.
        """
        package = self.repo.adopt(package)

        self._hashes.add(package['SHA256'])
