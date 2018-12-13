#!/usr/bin/python3
"""
Test a thing
"""

from apt.repo import Repository

def main():
    """Main function"""
    repo = Repository('https://deb.tgvg.net/debian')
    print(vars(repo))

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