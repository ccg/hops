import getpass
import os.path
from fabric.api import abort, run, settings, sudo
from fabric.colors import red
from fabric.context_managers import hide
from fabric.contrib import files
from fabric.contrib.console import confirm
import fabfile


ADMIN_GROUP = getattr(fabfile, 'ADMIN_GROUP', 'admin')


def remote_check(cmd):
    """
    Run a remote command that returns exit code 0 to indicate True
    and non-zero to indicate False.
    """
    with settings(hide('warnings'), warn_only=True):
        retval = run(cmd)
    return retval.succeeded


def user_exists(username):
    """
    Does the user exist? Return True or False
    """
    return remote_check("grep -e '^%s:' /etc/passwd" % username)


def group_exists(group_name):
    """
    Does the group exist? Return True or False
    """
    return remote_check("grep -e '^%s:' /etc/group" % group_name)


def get_remote_home_directory(username):
    """
    Get the path to the user's home directory on the remote machine.
    """
    retval = run("echo ~%s" % username, shell=True)
    if retval.succeeded:
        return retval.stdout
    else:
        print(red("Could not determine home directory for user '%s'" %
                  username))


def ensure_admin_group_exists(admin_group=ADMIN_GROUP):
    """
    Create the admin group if it does not already exist.
    """
    if not group_exists(admin_group):
        sudo("groupadd '%s'" % admin_group)


def create_user(username=None, shell='/bin/bash', admin=False):
    """
    Create the user. If admin=True, the user will be added to whatever
    group is defined in the ADMIN_GROUP setting.
    If no username is given, look up the username of the user running the
    command and create an account with same username on the remote machine.
    """
    if not username:
        username = getpass.getuser()
    if user_exists(username):
        print(red("User '%s' already exists." % username))
        return
    sudo("useradd -m -s '%s' '%s'" % (shell, username))
    if admin:
        ensure_admin_group_exists(ADMIN_GROUP)
        sudo("usermod -aG '%s' '%s'" % (ADMIN_GROUP, username))


def delete_user(username):
    """
    Remove a given user from the remote system. Warns but does not fail
    if the user does not exist.
    """
    if not user_exists(username):
        print(red("User '%s' does not exist." % username))
    else:
        sudo("deluser --remove-home '%s'" % username)


def upload_user_ssh_pub_key(username=None, local_key_file='~/.ssh/id_rsa.pub'):
    """
    Add the given (local) user's SSH public key to the .ssh/authorized_keys
    file of the user with the same username on the remote system.

    If no username is given, it will attempt to upload the SSH public key of
    the local user running the command.

    This command assumes that local usernames map to remote usernames.
    """
    if not username:
        username = getpass.getuser()
    if not user_exists(username):
        abort("User '%s' does not exist on remote machine." % username)
    remote_home = get_remote_home_directory(username)
    remote_ssh_dir = remote_home + "/.ssh"
    remote_key_file = remote_ssh_dir + "/authorized_keys"
    path = os.path.expanduser(local_key_file)
    with open(path, 'r') as f:
        keys = [line.rstrip() for line in f.readlines()]
        sudo("mkdir -p '%s'" % remote_ssh_dir)
        files.append(remote_key_file, keys, use_sudo=True)
        sudo("chown %s:%s -R '%s'" % (username, username, remote_ssh_dir))


def init_users():
    # Just to ensure there's a usable account on the remote system, give
    # the user the opportunity to duplicate their local user on the remote
    # machine, in case no users are specified in configuration
    username = getpass.getuser()
    if not user_exists(username) and confirm(
        "Create an admin account for yourself? (user '%s')" % username):
        create_user(username, admin=True)
        if confirm('Upload your SSH public key?'):
            upload_user_ssh_pub_key()
