#!/usr/bin/python3
"""
Test a thing
"""

from apt.repo import Repository


# noinspection PyProtectedMember
def main():
    """
    Main function
    """
    repo = Repository('file://C:/svn/debian-remux/debian')

    with open('bind9-dev.deb', 'rb') as debian_file:
        package = repo.adopt(debian_file)

    print(repo)

    dist = repo.distribution('stable')
    packages = dist.package_list('main', 'amd64')
    packages.add(package)

    print(dist)


if __name__ == "__main__":
    main()
