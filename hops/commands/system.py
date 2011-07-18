import fabfile
from fabric.api import env, put, run, sudo
from fabric.colors import red
from fabric.contrib import files


ADMIN_EMAIL = getattr(fabfile, 'ADMIN_EMAIL', 'root@localhost')


def init_server():
    """
    Initial setup of a blank server. Prepares it for hosting hops-compatible
    Django projects.
    """
    from hops.commands.databases import install_postgresql
    from hops.commands.packages import setup_base_packages
    from hops.commands.users import init_users
    from hops.commands.webservers import install_apache
    setup_base_packages()
    setup_apticron()
    setup_hosts()
    # be sure to create your user accounts before locking down SSH
    init_users()
    setup_sudo()
    setup_sshd()
    install_apache()
    install_postgresql()


def hostname():
    """
    Run `hostname` on the remote machine.
    Useful as a smoke test.
    """
    run('hostname')


def setup_apticron():
    """
    Configure apticron to send email to address in fabfile.ADMIN_EMAIL
    whenever a new package update is available.
    """
    files.sed('/etc/apticron/apticron.conf', '^EMAIL.*',
              'EMAIL="%s"' % ADMIN_EMAIL, use_sudo=True)


def setup_hosts():
    """
    Configure /etc/hosts and /etc/hostname. Make sure that env.host is the
    server's IP address and that env.hostname is the server's hostname.
    """
    if not getattr(env, 'hostname', None):
        print(red("setup_hosts requires env.hostname. Skipping."))
        return None
    ## the following stuff will only be necessary if we need to put entries
    ## like "1.2.3.4 lrz15" into /etc/hosts, but that may not be necessary.
    ## i'll leave the code for now, but i suspect we can delete it.
    ## sanity check: env.host is an IP address, not a hostname
    #import re
    #assert(re.search(r'^(\d{0,3}\.){3}\d{0,3}$', env.host) is not None)
    #files.append("%(host)s\t%(hostname)s" % env, '/etc/hosts', use_sudo=True)
    files.append('/etc/hosts', "127.0.1.1\t%s" % env.hostname, use_sudo=True)
    sudo("hostname %s" % env.hostname)
    sudo('echo "%s" > /etc/hostname' % env.hostname)


def setup_sudo():
    """
    Allow members of the OS group 'admin' to run commands with sudo
    without typing a password every time.
    """
    text = (
        '# admin group members may gain root privileges without password',
        '%admin ALL=(ALL) NOPASSWD: ALL',
    )
    files.append('/etc/sudoers', text, use_sudo=True)


def setup_sshd():
    files.sed('/etc/ssh/sshd_config',
              r'PermitRootLogin\s+yes',
              r'PermitRootLogin no', use_sudo=True)
    files.sed('/etc/ssh/sshd_config',
              r'#PasswordAuthentication\s+yes',
              r'PasswordAuthentication no', use_sudo=True)
    # sleep for a second after restarting ssh. sometimes, the ssh daemon
    # fails to come back up after the restart command.
    sudo('/etc/init.d/ssh restart && sleep 1')
