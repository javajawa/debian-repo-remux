#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utilities for manipulating debian archives
"""

import io
import struct
import tarfile
import typing

from apt import tags


ARRecord = typing.NamedTuple('ARRecord', [('name', bytes), ('size', int)])


def _consume_ar_header(deb: typing.IO) -> bool:
    # The ar-format starts with 8 magic bytes
    data = deb.read(8)

    return data == b'!<arch>\n'


def _read_file_header(deb: typing.IO) -> ARRecord:
    buffer = deb.read(60)
    name, _, _, _, _, size, magic = (struct.unpack('16s12s6s6s8s10s2s', buffer))

    if magic != b'\x60\n':
        raise ValueError("Invalid file signature")

    size = int(size, 10)

    return ARRecord(name, size)


def _read_file(deb: typing.IO, file: ARRecord) -> bytes:
    data: bytes = deb.read(file.size)

    if file.size % 2 != 0:
        deb.read(1)

    return data


def _skip_file(deb: typing.IO, file: ARRecord) -> None:
    deb.seek(file.size + file.size % 2)


def extract_control_file(deb: typing.Union[bytes, typing.IO]) -> typing.Optional[tags.TagBlock]:
    """
    Extracts the control file from inside a debian package
    """
    # 0   16  File name                       ASCII
    # 16  12  File modification timestamp     Decimal
    # 28  6   Owner ID                        Decimal
    # 34  6   Group ID                        Decimal
    # 40  8   File mode                       Octal
    # 48  10  File size in bytes              Decimal
    # 58  2   File magic                      0x60 0x0A

    if isinstance(deb, bytes):
        deb = io.BytesIO(deb)

    if not _consume_ar_header(deb):
        raise ValueError("Stream is not a valid debian archive")

    file = _read_file_header(deb)

    if file.name.rstrip(b' ') != b'debian-binary':
        raise ValueError("Archive does not start with debian-binary file")

    buffer = _read_file(deb, file)

    if buffer != b'2.0\n':
        raise ValueError("Archive does not have debian-binary version 2.0")

    file = _read_file_header(deb)

    name = file.name.rstrip(b' ')

    if name[:11] != b'control.tar':
        raise ValueError("Archive does not have control.tar.*")

    with tarfile.open(fileobj=io.BytesIO(_read_file(deb, file))) as data:
        for name in data.getnames():
            if name in ['./control', 'control']:
                control = data.extractfile(name)
                return next(tags.read_tag_file(control.read()))

    raise ValueError("Archive's control.tar.* does not contain a control file")
