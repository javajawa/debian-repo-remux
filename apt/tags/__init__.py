#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Classes for handling APT/DPKG Style tag files.

Tag files can be created from an IO-like object.
Subclasses are provided to add extra logic and validation.
"""

import typing

from .filehash import FileHash
from .tagblock import TagBlock
from .releasefile import ReleaseFile


def read_tag_file(data: bytes, template: callable(TagBlock)=TagBlock)\
        -> typing.Generator[TagBlock, None, None]:
    """
    Loads in a list of TagBlocks from a data block.

    :param bytes data:
    :param callable(TagBlock) template:
    :return:
    """
    tags: TagBlock = template()
    key = None

    for line in data.decode('utf-8').split('\n'):
        line = line.rstrip()

        if not line:
            if len(tags) > 0:
                yield tags

            tags: TagBlock = template()
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

    if len(tags) > 0:
        yield tags
