#!/usr/bin/python3
"""
Test a thing
"""

from apt_repo import Repo

if __name__ == "__main__":
    repo = Repo('https://deb.tgvg.net/debian')
    print(vars(repo))

    distribution = repo.distribution('stable')

    print(distribution.exists())

    if distribution.exists():
        print(distribution.components())
        print(distribution.architectures())
        print(distribution.release_data.files)
        print(distribution.package_list('main', 'amd64'))
