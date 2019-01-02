#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Classes for handling APT/DPKG Style tag files.

Tag files can be created from an IO-like object.
Subclasses are provided to add extra logic and validation.
"""

from typing import List, Generator, Dict, Optional


class TagBlock:
    """
    Base class that describes an arbitrary tag-block in a APT / DPKG style
    file.

    This class acts as if it is a dict/hash, and provides
    """
    required = ...  # type: List[str]
    order_first = ...  # type: List[str]
    order_last = ...  # type: List[str]
    magic = ...  # type: List[str]
    dict = ...  # type: Dict[str, str]

    def __init__(self):
        self.required = []
        self.order_first = []
        self.order_last = []
        self.magic = []
        self.dict = {}

    def __contains__(self, item: str) -> bool:
        return item in self.dict

    def __getitem__(self, item: str) -> str:
        return self.dict[item]

    def __setitem__(self, key: str, value: str) -> None:
        if key in self.magic:
            raise KeyError("Set on magic field " + key + " was not handled in class " + type(self).__name__)

        if key not in self.order_first and key not in self.order_last:
            self.order_first.append(key)

        self.dict[key] = value

    def __delitem__(self, key: str) -> None:
        del self.dict[key]

    def __len__(self) -> int:
        return len(self.dict)

    def __str__(self) -> str:
        elements = []
        keys_done = []

        # Output the elements which have a fixes order
        for key in self.order_first:  # type: str
            if key in keys_done:
                continue
            if key not in self.dict:
                continue

            elements.append(self._write_property(key))
            keys_done.append(key)

        # Output for fields that we have
        for key in self.dict:
            if key in keys_done:
                continue
            if key in self.order_last:
                continue

            elements.append(self._write_property(key))
            keys_done.append(key)

        # Output for fields that are 'magic'
        for key in self.magic:
            if key in keys_done:
                continue

            elements.append(self._write_property(key))
            keys_done.append(key)

        # Output the elements which have a fixes order
        for key in self.order_last:  # type: str
            if key in keys_done:
                continue

            elements.append(self._write_property(key))
            keys_done.append(key)

        # Output the resulting string
        return '\n'.join(filter(None, elements))

    def _write_property(self, key: str) -> Optional[str]:
        value = self[key]  # type: str

        if value is None:
            return None

        if '\n' in value:
            return key + ':\n ' + value.replace('\n', '\n ')
        else:
            return key + ': ' + value


class ReleaseFile(TagBlock):
    """Release File wrapper.
    
    The ReleaseFile is the overall meta data file of a :class:apt.repo.Distribution
    """
    files = ...  # type: Dict[str, FileHash]

    def __init__(self):
        super(ReleaseFile, self).__init__()

        self.magic.append('MD5Sum')
        self.magic.append('SHA1')
        self.magic.append('SHA256')
        self.magic.append('SHA512')

        self.files = {}

    def __setitem__(self, key: str, value: str) -> None:
        if key not in self.magic:
            return super(ReleaseFile, self).__setitem__(key, value)

        for [checksum, size, filename] in [x.split() for x in value.split('\n')]:  # type: [str, str, str]
            size = int(size.strip(), 10)
            checksum = checksum.strip()
            filename = filename.strip()

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

            output.append('{0} {1:>12} {2}'.format(info.__getattribute__(key), info.size, info.filename))

        if not output:
            return None

        return '\n'.join(output)

    def components(self) -> List[str]:
        """Returns the list of components as a python List

        :return List[str]:
        """
        return self['Components'].split(' ')

    def architectures(self) -> List[str]:
        """Returns the list of architectures as a python List

        :return List[str]:
        """
        return self['Architectures'].split(' ')


def read_tag_file(data: bytes, template: callable(TagBlock) = TagBlock) -> Generator[TagBlock, None, None]:
    """Loads in a list of TagBlocks from a data block.

    :param bytes data:
    :param callable(TagBlock) template:
    :return:
    """
    tags = template()  # type: TagBlock
    key = None

    for line in data.decode('utf-8').split('\n'):
        line = line.rstrip()

        if not line:
            if len(tags):
                yield tags

            tags = template()  # type: TagBlock
            key = None
            continue

        if line[0] == ' ':
            if not key:
                continue

            if key not in tags:
                tags[key] = line.strip()
            else:
                tags[key] += '\n' + line.strip()

        else:
            try:
                [key, value] = line.split(':', 1)
            except ValueError as ex:
                print(line)
                raise ex

            value = value.strip()

            if value:
                tags[key] = value

    if len(tags):
        yield tags


class FileHash(object):
    """Class representing all the hashes APT makes allowances for."""

    filename = ...  # type: str
    size = ...  # type: int
    md5 = ...  # type: str
    sha1 = ...  # type: str
    sha256 = ...  # type: str
    sha512 = ...  # type: str

    def __init__(self, filename: str):
        self.filename = filename

    # _file = ...  # type: Optional[AbstractRepoObject]
    #
    # def __init__(self, parent: AbstractRepoObject, filename: str):
    #     super().__init__(parent, parent.repo)
    #
    #     self.filename = filename
    #     self._file = None

    def __setattr__(self, key: str, value):
        key = key.lower().replace('sum', '')
        
        return super(FileHash, self).__setattr__(key, value)

    def __getattr__(self, key: str):
        key = key.lower().replace('sum', '')

        return super(FileHash, self).__getattribute__(key)

    def __getitem__(self, key: str):
        key = key.lower().replace('sum', '')

        return super(FileHash, self).__getattribute__(key)
