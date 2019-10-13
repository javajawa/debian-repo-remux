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
    upstream_debian_repo = Repository('https://cdn-aws.deb.debian.org/debian/')
    print(upstream_debian_repo)

    distribution = upstream_debian_repo.distribution('stable')

    if not distribution.exists():
        return

    print(distribution.components())
    print(distribution.architectures())

    packages = distribution.package_list('main', 'amd64')

    print(upstream_debian_repo)
    print(distribution)
    print(packages)


if __name__ == "__main__":
    main()
