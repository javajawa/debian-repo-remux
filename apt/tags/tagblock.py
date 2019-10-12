#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Base class that describes an arbitrary tag-block in a APT / DPKG style
file.

FIXME: This class acts as if it is a dict/hash, and provides
"""

from typing import List, Dict, Optional


class TagBlock:
    """
    Base class that describes an arbitrary tag-block in a APT / DPKG style
    file.

    FIXME: This class acts as if it is a dict/hash, and provides
    """
    required: List[str]
    order_first: List[str]
    order_last: List[str]
    magic: List[str]
    dict: Dict[str, str]

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
            raise KeyError(
                'Set on magic field {0} was not handled in class {1}'.format(
                    key, type(self).__name__
                )
            )

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
        value: str = self[key]

        if value is None or value is Ellipsis:
            return None

        if '\n' in value:
            return key + ':\n ' + value.replace('\n', '\n ')

        return key + ': ' + value
