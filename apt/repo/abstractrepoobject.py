#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
The AbstractRepoObject represents any part of an APT repository,
and provides implementations the required logic for reading and writing
files to that repository.
"""

import io
import hashlib
import urllib.request

from typing import Optional, Type, List, IO, Callable

from apt import tags, transport
from .exceptions import UnattachedAptObjectException, IncorrectChecksumException

StreamDecoder = Callable[[bytes], bytes]


class AbstractRepoObject:  # pylint: disable=R0903
    """
    The AbstractRepoObject represents any part of an APT repository,
    and provides implementations the required logic for reading and writing
    files to that repository.
    """

    # noinspection PyUnresolvedReferences
    repo: 'apt.repo.Repository'
    parent: Optional['AbstractRepoObject']

    # noinspection PyUnresolvedReferences
    def __init__(self, repository: 'apt.repo.Repository', parent: Optional['AbstractRepoObject']):
        self.parent = parent
        self.repo = repository

    def get_parent_of_type(self, object_type: Type['AbstractRepoObject'])\
            -> Optional['AbstractRepoObject']:
        """
        Traverse up this object ancestry to find the nearest object of
        te type supplied

        :param Type[AbstractRepoObject] object_type: The type that is requested
        :return AbstractRepoObject:
        """
        parent = self

        while parent:
            if isinstance(parent, object_type):
                return parent

            parent = self.parent

        return None

    def _file_exists(self, relative_path: List[str]) -> bool:
        """
        Check if a file exists in the repo

        :param List[str] relative_path:

        :return bool:

        :raises UnattachedAptObjectException:
        :raises URIMismatchError:
        """
        if not self.repo:
            raise UnattachedAptObjectException()

        path = urllib.request.urljoin(self.repo.base_uri, '/'.join(relative_path))

        return self.repo.transport.exists(path)

    def _open_file(self, relative_path: List[str]) -> IO:
        """
        Opens a repo in the file for read

        :param List[str] relative_path:

        :return IO:

        :raises UnattachedAptObjectException:
        :raises NotImplementedError:
        :raises URIMismatchError:
        :raises FileNotFoundError:
        """
        if not self.repo:
            raise UnattachedAptObjectException()

        path = urllib.request.urljoin(self.repo.base_uri, '/'.join(relative_path))

        return self.repo.transport.open_read(path)

    def _write_file(self, relative_path: List[str]) -> IO:
        """
        Opens a repo in the file for read

        :param List[str] relative_path:

        :return IO:

        :raises UnattachedAptObjectException:
        :raises NotImplementedError:
        :raises URIMismatchError:
        :raises FileNotFoundError:
        """
        if not self.repo:
            raise UnattachedAptObjectException()

        path = urllib.request.urljoin(self.repo.base_uri, '/'.join(relative_path))

        return self.repo.transport.open_write(path)

    def _list_dir(self, relative_path: List[str]) -> transport.DirectoryListing:
        """
        Gets a Directory listing for a directory relative to the Repo

        :param List[str] relative_path:

        :return transport.DirectoryListing:

        :raises UnattachedAptObjectException:
        :raises NotImplementedError:
        :raises URIMismatchError:
        :raises FileNotFoundError:
        """
        if not self.repo:
            raise UnattachedAptObjectException()

        path = urllib.request.urljoin(self.repo.base_uri, '/'.join(relative_path))

        return self.repo.transport.list_directory(path)

    def _download_file(
            self,
            path: List[str],
            hashes: tags.FileHash,
            decoder: Optional[StreamDecoder] = None
    ) -> bytes:
        """

        :param List[str] path:
        :param FileHash hashes:
        :param Callable decoder:

        :return bytes:

        :raise IncorrectChecksumException:
        """
        if not self.repo:
            raise UnattachedAptObjectException()

        hash_func: hashlib
        hash_value: str
        output = io.BytesIO()
        size = 0

        for hash_name in ['sha256', 'sha512', 'sha1', 'md5']:
            if hashes[hash_name] != Ellipsis:
                hash_value = hashes[hash_name]
                hash_func: hashlib = hashlib.new(hash_name)

                break

        if hashes.size == Ellipsis:
            raise ValueError('File size missing from hash')

        if Ellipsis in (hash_func, hash_value):
            raise ValueError('No valid hash supplied')

        with self._open_file(path) as stream:
            for block in iter(lambda: stream.read(4096), b""):
                hash_func.update(block)
                size += len(block)
                output.write(decoder(block) if decoder else block)

        valid = (hash_func.hexdigest() == hash_value) and (size == hashes.size)

        if not valid:
            raise IncorrectChecksumException('Invalid checksum for {0}'.format('/'.join(path)))

        output.seek(0)

        return output.read()
