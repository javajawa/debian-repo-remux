#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Class structure for containing the conceptual view of an APT Repository.

A complete repository is represented by the Repository class, with subsections
handled by classes that extend the abstract AbstractRepoObject class.

Each AbstractRepoObject is expects to belong to a Repository, from where
it inherits information like its URI for reading and writing data.
"""

from .repository import Repository
from .distribution import Distribution
from .package import Package
from .packagelist import PackageList
