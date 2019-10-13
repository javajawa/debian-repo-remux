#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FIXME: Write docstring
"""

import dataclasses
import typing


@dataclasses.dataclass
class DirectoryListing:
    """
    Class showing files and folders in a directory
    """
    files: typing.List[str] = dataclasses.field(default_factory=list)
    directories: typing.List[str] = dataclasses.field(default_factory=list)
