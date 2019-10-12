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
    print(vars(upstream_debian_repo))

    print("Initial Scan:", upstream_debian_repo.scan_distributions(), upstream_debian_repo.distributions())

    distribution = upstream_debian_repo.distribution('stable')

    print(distribution.exists())

    if not distribution.exists():
        return

    print(distribution.components())
    print(distribution.architectures())
    print(distribution.release_data.files)
    packages = distribution.package_list('main', 'amd64')

    print(packages)
    print(len(packages))
    print(len(upstream_debian_repo._pool))


if __name__ == "__main__":
    main()
