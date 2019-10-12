#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FIXME: The data about a package
"""

from typing import Optional

from apt import tags

from .abstractrepoobject import AbstractRepoObject


class Package(AbstractRepoObject, tags.TagBlock):
    """
    FIXME: The data about a package
    """
    hashes: tags.FileHash

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

        self.hashes = tags.FileHash('')

        for key in data.dict:
            self[key] = data.dict[key]

        for key in data.magic:
            self[key] = data[key]

    def __setitem__(self, key: str, value: str) -> None:
        if key not in self.magic:
            tags.TagBlock.__setitem__(self, key, value)
        else:
            self.hashes.__setattr__(key, value)

    def __getitem__(self, key: str) -> Optional[str]:
        if key not in self.magic:
            return tags.TagBlock.__getitem__(self, key)

        return self.hashes[key]

    def __repr__(self):
        return "<apt.repo.Package {0['Package']}={0['Version']}>".format(self)
