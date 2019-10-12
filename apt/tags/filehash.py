#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Class representing all the hashes APT makes allowances for.
"""

from typing import Optional


class FileHash:
    """
    Class representing all the hashes APT makes allowances for.
    """

    filename: str
    size: Optional[int] = None
    md5: Optional[str] = None
    sha1: Optional[str] = None
    sha256: Optional[str] = None
    sha512: Optional[str] = None

    def __init__(self, filename: str):
        self.filename = filename

    def __setattr__(self, key: str, value):
        key = key.lower().replace('sum', '')

        return object.__setattr__(self, key, value)

    def __getattr__(self, key: str):
        key = key.lower().replace('sum', '')

        return object.__getattribute__(self, key)

    def __getitem__(self, key: str):
        key = key.lower().replace('sum', '')

        return object.__getattribute__(self, key)
