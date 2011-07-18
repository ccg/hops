from fabric.api import cd, settings, sudo
from fabric.contrib import files


def install_apache():
    pkgs = ('apache2', 'apache2-utils', 'libapache2-mod-wsgi', )
    for pkg in pkgs:
        sudo('apt-get -y install %s' % pkg)
    sudo('virtualenv --no-site-packages /var/www/virtualenv')
    files.append('/etc/apache2/conf.d/wsgi-virtualenv',
                 'WSGIPythonHome /var/www/virtualenv', use_sudo=True)
    # echo 'ServerName localhost' >> /etc/apache2/conf.d/servername
    files.append('/etc/apache2/conf.d/servername',
                 'ServerName localhost',
                 use_sudo=True)
    sudo('a2enmod ssl')
    apache_reload()


def apache_reload():
    """
    Do a graceful restart of Apache. Reloads the configuration files and the
    client app code without severing any active connections.
    """
    sudo('/etc/init.d/apache2 reload')


def apache_restart():
    """
    Restarts Apache2. Only use this command if you're modifying Apache itself
    in some way, such as installing a new module. Otherwise, use
    ``apache reload`` to do a graceful restart.
    """
    sudo('/etc/init.d/apache2 restart')
