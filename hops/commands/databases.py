from fabric.api import sudo
from hops.commands.packages import install_packages

POSTGRES_USER = 'postgres'


def install_postgresql():
    postgres_packages = ('postgresql', 'python-egenix-mxdatetime',)
    install_packages(postgres_packages)
    # also need dependencies to compile psycopg2 inside virtualenvs:
    sudo('apt-get -y build-dep psycopg2')


def pg_create_user(username):
    sudo('createuser --no-superuser --createdb --no-createrole'
         ' --encrypted --pwprompt %s' % username, user=POSTGRES_USER)


def pg_create_db(db_name, owner):
    #sudo('createdb -U postgres -O %s -E UTF8 -T template_postgis')
    sudo('createdb -O %(owner)s -E UTF8 %(db_name)s' % locals(),
         user=POSTGRES_USER)


def pg_delete_db(db_name):
    sudo('dropdb %s' % db_name, user=POSTGRES_USER)


def pg_delete_user(user):
    sudo('dropuser %s' % user, user=POSTGRES_USER)
