import types
from fabric.api import sudo
from fabric.contrib import files
import fabfile


def upgrade_packages():
    """
    Updates package list and upgrades any outdated packages.
    """
    # Activate Ubuntu's "Universe" repositories.
    files.uncomment('/etc/apt/sources.list', regex=r'deb.*universe',
                    use_sudo=True)
    sudo('apt-get update -y')
    sudo('apt-get upgrade -y')


def install_packages(packages):
    if type(packages) == types.TupleType or type(package) == types.ListType:
        packages = ' '.join(packages)
    sudo('apt-get install -y %s' % packages)


def setup_base_packages():
    upgrade_packages()
    install_packages(fabfile.BASE_PACKAGES)
