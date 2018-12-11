#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List, Generator, Dict, Optional


class TagBlock:
    """
    Base class that describes an arbitary tag-block in a Apt/Dpkg style
    file.

    This class acts as if it is a dict/hash, and provides
    """

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
    def __init__(self):
        super(ReleaseFile, self).__init__()

        self.magic.append('MD5')
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

            if filename in self.files:
                self.files[filename][key] = checksum
            else:
                self.files[filename] = {
                    'filename': filename,
                    'size': size,
                    key: checksum
                }

    def __getitem__(self, key: str) -> Optional[str]:
        if key not in self.magic:
            return super(ReleaseFile, self).__getitem__(key)

        output = []
        file_list = self.files.values()
        file_list = sorted(file_list, key=lambda f: f['filename'])

        for info in file_list:
            if key not in info:
                continue

            output.append('{0} {1:>12} {2}'.format(info[key], info['size'], info['filename']))

        if not output:
            return None

        return '\n'.join(output)

    def components(self) -> List[str]:
        """Returns the list of components

        :return:
        """
        return self['Components'].split(' ')

    def architectures(self) -> List[str]:
        return self['Architectures'].split(' ')


def read_tag_file(data: bytes, template: callable(TagBlock) = TagBlock) -> Generator[Dict[str, str], None, None]:
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
