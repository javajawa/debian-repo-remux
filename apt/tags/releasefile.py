#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Release File wrapper.

The ReleaseFile is the overall meta data file of a :class:apt.repo.Distribution
"""

from typing import Dict, Optional, List

from .tagblock import TagBlock
from .filehash import FileHash


class ReleaseFile(TagBlock):
    """
    Release File wrapper.

    The ReleaseFile is the overall meta data file of a :class:apt.repo.Distribution
    """
    files: Dict[str, FileHash]

    def __init__(self):
        super(ReleaseFile, self).__init__()

        self.magic.append('MD5Sum')
        self.magic.append('SHA1')
        self.magic.append('SHA256')
        self.magic.append('SHA512')

        self.files = {}

    def __setitem__(self, key: str, value: str) -> None:
        if key not in self.magic:
            super(ReleaseFile, self).__setitem__(key, value)
            return

        for [checksum, size_s, filename] in [x.split() for x in value.split('\n')]:
            size: int = int(size_s.strip(), 10)
            checksum: str = checksum.strip()
            filename: str = filename.strip()

            if filename not in self.files:
                self.files[filename] = FileHash(filename)
                self.files[filename].size = size

            self.files[filename].__setattr__(key, checksum)

    def __getitem__(self, key: str) -> Optional[str]:
        if key not in self.magic:
            return super(ReleaseFile, self).__getitem__(key)

        output = []
        file_list = self.files.values()
        file_list = sorted(file_list, key=lambda f: f['filename'])

        for info in file_list:
            if key not in info:
                continue

            output.append('{0} {1.size:>12} {1.filename}'.format(info.__getattribute__(key), info))

        if not output:
            return None

        return '\n'.join(output)

    def components(self) -> List[str]:
        """
        Returns the list of components as a python List

        :return List[str]:
        """
        return self['Components'].split(' ')

    def architectures(self) -> List[str]:
        """
        Returns the list of architectures as a python List

        :return List[str]:
        """
        return self['Architectures'].split(' ')
