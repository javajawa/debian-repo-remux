#!/usr/bin/python3
"""
Test a thing
"""

from apt.repo import Repository
from apt.transport import Apache


def main():
    """Main function"""
    repo = Repository('https://deb.tgvg.net/debian')
    print(vars(repo))

    print("Initial Scan:", repo.scan_distributions(), repo.distributions())
    repo.transport = Apache()
    print("Apache Scan: ", repo.scan_distributions(), repo.distributions())

    distribution = repo.distribution('stable')

    print(distribution.exists())

    if not distribution.exists():
        return

    print(distribution.components())
    print(distribution.architectures())
    print(distribution.release_data.files)
    print(distribution.package_list('main', 'amd64'))


if __name__ == "__main__":
    main()
