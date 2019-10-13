#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FIXME: The data about a package
"""

from typing import Optional, List

from apt import tags, deb

from .abstractrepoobject import AbstractRepoObject


class Package(AbstractRepoObject, tags.TagBlock):
    """
    FIXME: The data about a package
    """
    _hashes: tags.FileHash
    _contents: Optional[List[str]] = None

    # noinspection PyUnresolvedReferences
    def __init__(
            self,
            repository: 'apt.repo.Repository',
            parent: 'apt.repo.Repository',
            data: tags.TagBlock
    ):
        AbstractRepoObject.__init__(self, repository, parent)
        tags.TagBlock.__init__(self)

        self.magic.append('Filename')
        self.magic.append('MD5Sum')
        self.magic.append('SHA1')
        self.magic.append('SHA256')
        self.magic.append('SHA512')

        self._hashes = tags.FileHash('')

        for key in data.dict:
            self[key] = data.dict[key]

        for key in data.magic:
            self[key] = data[key]

    def contents(self) -> List[str]:
        """
        Returns a list of all files provided by this package.

        :return:
        """
        if self._contents:
            return self._contents

        if not self._hashes.filename:
            # FIXME: Decide on a useful exception type here
            raise Exception("No package file to have contents")

        filename: List[str] = [self['Filename'] + '.contents']

        if self._file_exists(filename):
            with self._open_file(filename) as contents_file:
                self._contents = contents_file.readlines()
        else:
            with self._open_file(filename) as deb_file:
                self._contents = deb.extract_contents_list(deb_file)

        return self._contents

    def hashes(self) -> tags.FileHash:
        """
        Gets the FileHash object for this package

        :return:
        """
        return self._hashes

    def __setitem__(self, key: str, value: str) -> None:
        if key not in self.magic:
            tags.TagBlock.__setitem__(self, key, value)
        else:
            self._hashes.__setattr__(key, value)

    def __getitem__(self, key: str) -> Optional[str]:
        if key not in self.magic:
            return tags.TagBlock.__getitem__(self, key)

        return self._hashes[key]

    def __repr__(self):
        return "<apt.repo.Package {0[Package]}={0[Version]}>".format(self)
