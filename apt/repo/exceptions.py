#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
All of the types of exception for APT repository interactions.
"""


class UnattachedAptObjectException(Exception):
    """
    Exception indicating that an AbstractRepoObject is being used outside
    of an existing :class:Repository content
    """


class NonExistentException(Exception):
    """
    The exception is raised where an :class:AbstractRepoObject is used
    but does not exist in the repo.

    Reliance on this exception is discouraged, and code should call
    .exists() on the object first.
    """


class MissingControlFieldException(Exception):
    """
    Exception that occurs when a deb file is added which lacks the
    required control fields
    """

    path: str
    field: str

    def __init__(self, path: str, field: str):
        super(MissingControlFieldException, self).__init__()

        self.path = path
        self.field = field


class IncorrectChecksumException(Exception):
    """
    The exception is raised where an :class:AbstractRepoObject is used
    but does not exist in the repo.

    Reliance on this exception is discouraged, and code should call
    .exists() on the object first.
    """

    path: str

    def __init__(self, path: str):
        super(IncorrectChecksumException, self).__init__()

        self.path = path
