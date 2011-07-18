import os.path

from fabric.api import abort, env


# The path where Django apps are deployed.
# Should NOT be same as, or subdirectory of, Apache's Document Root.
# So, if doc root is /var/www, do NOT deploy under /var/www
env.DEPLOYMENT_ROOT = '/opt/web/'

env.APP_GIT_URL = ''
env.APP_NAME = 'example'
env.APP_DOMAIN = 'example.com'
env.APP_ROOT = os.path.join(env.DEPLOYMENT_ROOT, env.APP_NAME)

# Apache/WSGI config needs needs a python interpreter. We'll create a
# virtualenv for it with no site packages:
env.SHARED_VIRTUALENV_PATH = '/var/www/virtualenv'

env.ADMIN_EMAIL = 'root'    # you@example.com

# Member of this UNIX group will be able to use 'sudo' without a password:
env.ADMIN_GROUP = 'admin'

env.USERS = {
    'chad': {'shell':'bash'},
}

# Packages to install during initial server setup:
env.BASE_PACKAGES = (
    'debconf-utils',
    'man',
    'manpages',
    'aptitude',
    'screen',
    'git-core',
    #'ipython',  # looks like this one pulled in X11 libs. :-(
    'vim-nox',
    'gcc',
    'python-dev',
    'python-virtualenv',
    'language-pack-en',   # so perl will STFU
    'exim4',
    'apticron',           # nag us when there are security updates
    'apt-listchanges',
    #'libmysqlclient-dev', # so that mysql plays nice with venvs
    'python-imaging', # because it is hard to install onto virtualenvs
    'python-psycopg2',
)

# ENVIRONMENTS
def dev(username=None):
    if username:
        env.user = username
    env.hostname = 'ubuntu'
    env.hosts = ['172.16.58.135',]

def staging():
    abort("You have not yet configured your staging environment.")

def production():
    abort("You have not yet configured your production environment.")
