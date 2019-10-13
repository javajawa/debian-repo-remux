#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utilities for manipulating debian archives
"""

import io
import struct
import tarfile
import dataclasses

from typing import Optional, Union, List, IO

from apt import tags

# 0   16  File name                       ASCII
# 16  12  File modification timestamp     Decimal
# 28  6   Owner ID                        Decimal
# 34  6   Group ID                        Decimal
# 40  8   File mode                       Octal
# 48  10  File size in bytes              Decimal
# 58  2   File magic                      0x60 0x0A

ArchiveHeader = struct.Struct('16s12s6s6s8s10s2s')


@dataclasses.dataclass(init=False, eq=False)
class ARRecord:
    """
    Header record for files in an AR-Archive
    """

    name: bytes
    modified: int
    owner: int
    group: int
    mode: int
    size: int

    # pylint: disable=R0913
    def __init__(
            self,
            name: bytes, modified: bytes,
            owner: bytes, group: bytes, mode: bytes,
            size: bytes, magic: bytes
    ):
        if magic != b'\x60\n':
            raise ValueError("Invalid file signature")

        self.name = name.rstrip(b' ')
        self.modified = int(modified, 10)
        self.owner = int(owner, 10)
        self.group = int(group, 10)
        self.mode = int(mode, 8)
        self.size = int(size, 10)


def _consume_ar_header(deb: IO) -> bool:
    # The ar-format starts with 8 magic bytes
    data = deb.read(8)

    return data == b'!<arch>\n'


def _read_file_header(deb: IO) -> Optional[ARRecord]:
    data: bytes = deb.read(60)

    if len(data) != 60:
        return None

    return ARRecord(*ArchiveHeader.unpack(data))


def _read_file(deb: IO, file: ARRecord) -> bytes:
    data: bytes = deb.read(file.size)

    if file.size % 2 != 0:
        deb.read(1)

    return data


def _skip_file(deb: IO, file: ARRecord) -> None:
    deb.seek(file.size + file.size % 2, 1)


def extract_control_file(deb: Union[bytes, IO]) -> Optional[tags.TagBlock]:
    """
    Extracts the control file from inside a debian package
    """

    if isinstance(deb, bytes):
        deb = io.BytesIO(deb)

    deb.seek(0)

    if not _consume_ar_header(deb):
        raise ValueError("Stream is not a valid debian archive")

    file = _read_file_header(deb)

    if file.name != b'debian-binary':
        raise ValueError("Archive does not start with debian-binary file")

    buffer = _read_file(deb, file)

    if buffer != b'2.0\n':
        raise ValueError("Archive does not have debian-binary version 2.0")

    file = _read_file_header(deb)

    if not file.name.startswith(b'control.tar'):
        raise ValueError("Archive does not have control.tar.*")

    control_data: bytes = _read_file(deb, file)
    with io.BytesIO(control_data) as control_io:
        with tarfile.open(fileobj=control_io) as data:
            for name in data.getnames():
                if name not in ['./control', 'control']:
                    continue

                control = data.extractfile(name)
                return next(tags.read_tag_file(control.read()))

    raise ValueError("Archive's control.tar.* does not contain a control file")


def extract_contents_list(deb: Union[bytes, IO]) -> Optional[List[str]]:
    """
    Extracts the control file from inside a debian package
    """

    if isinstance(deb, bytes):
        deb = io.BytesIO(deb)

    deb.seek(0)

    if not _consume_ar_header(deb):
        raise ValueError("Stream is not a valid debian archive")

    file = _read_file_header(deb)

    if file.name != b'debian-binary':
        raise ValueError("Archive does not start with debian-binary file")

    buffer = _read_file(deb, file)

    if buffer != b'2.0\n':
        raise ValueError("Archive does not have debian-binary version 2.0")

    while True:
        file = _read_file_header(deb)

        if file is None:
            return None

        if not file.name.startswith(b'data.tar'):
            _skip_file(deb, file)
            continue

        with io.BytesIO(deb.read(file.size)) as control_io:
            with tarfile.open(fileobj=control_io) as data:
                return [file.lstrip('.') for file in data.getnames() if file != '.']
