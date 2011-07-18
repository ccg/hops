"""
Standard project configuration:
    * separate DB user account for each project (username=project_name)
    * each release is deployed into its own virtualenv
    * current release is symlinked (easy rollback)
    * releases are named numerically to simplify rollback
    * a separate directory for user uploads (user_uploads/) exists at the
      top level for Django 1.3's 'media' directory. This way, rolling back
      or deploying a different release will not affect the user-uploaded
      files

Structure of a project...

/<fabfile.DEPLOYMENT_ROOT>/<project_name>/
  releases/
    1/
    2/
    3/
  current -> releases/2     # currently active release
  user_uploads/
  log/

Structure of a release directory...
  1/
    bin/        # virtualenv
    code/       # your django project
      __init__.py
      apps/         # django apps
      settings/
        __init__.py
        common.py
        dev.py
        staging.py
        production.py
      requirements.txt  # pip requirements file
      static/
      templates/
      urls.py
    lib/        # virtualenv
    share/      # virtualenv
"""

import os.path
from pkg_resources import resource_filename
import fabfile
from fabric.api import cd, env, require, settings, run, sudo
from fabric.colors import green
from fabric.contrib.files import upload_template
import hops

__all__ = ['deploy']


require('ADMIN_EMAIL', 'APP_GIT_URL', 'APP_NAME', 'APP_ROOT',)


def get_highest_release_number():
    with cd(env.APP_ROOT):
        # if we go back to naming release directories with the Git
        # hash, e.g,. 1-d36b9b5e, then this will work:
        #latest_num = run('ls -1v releases/ | tail -n 1 | cut -d- -f 1')
        latest_num = run('ls -1v releases/ | tail -n 1')
        if not latest_num:
            return 0
        # TODO: filter out non-numeric entries
        return int(latest_num)


#def _ensure_directory_exists(path, owner=None, use_sudo=False):
#    runner = sudo if use_sudo else run
#    print 'path is', path
#    runner('mkdir -p %s' % path)
#    if owner:
#        runner('chown %(owner)s %(path)s' % locals())


# TODO: setting for project owner; probably shouldn't be apache-specific
env.PROJECT_OWNER = 'www-data'

def predeploy():
    # TODO: need to set pg passwd for django settings.py
    # TODO: make DB-independent?
    #pg_create_user(project_name)
    sudo('mkdir -p %(APP_ROOT)s' % env)
    sudo('mkdir -p %(APP_ROOT)s/releases' % env)
    #sudo('mkdir -p %(new_conf_dir)s' % env)


def get_hops_template_dir():
    import os.path
    cwd = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(cwd, '..', 'templates')


def upload_project_wsgi_conf():
    require('new_release_dir', 'new_conf_dir', 'new_code_dir',
            'new_site_packages', provided_by=['deploy'])
    require('django_settings_module',
            provided_by=['dev', 'staging', 'production'])
    sudo('mkdir -p %(new_conf_dir)s' % env)
    template_dir = get_hops_template_dir()
    wsgi_conf_template = os.path.join(template_dir, 'wsgi.py')
    env.wsgi_conf = "%(new_conf_dir)s/wsgi.py" % env
    upload_template(wsgi_conf_template, env.wsgi_conf, context=env,
                    use_sudo=True)


def upload_project_apache_conf():
    require('PROJECT_OWNER', 'ADMIN_EMAIL', 'APP_ROOT', 'APP_NAME',
            'APP_DOMAIN',)
    require('new_conf_dir', 'new_site_packages', 'new_static_dir',
            'apache_log_dir', provided_by='deploy')
    require('wsgi_conf', provided_by=['upload_project_wsgi_conf'])
    sudo('mkdir -p %(new_conf_dir)s' % env)
    sudo('mkdir -p %(apache_log_dir)s' % env)
    template_dir = get_hops_template_dir()
    apache_conf_template = os.path.join(template_dir, 'apache.conf')
    env.apache_conf = "%(new_conf_dir)s/apache.conf" % env
    upload_template(apache_conf_template, env.apache_conf, context=env,
                    use_sudo=True)


def install_app(rev=None):
    """
    This function is not meant to be called as a command.
    It operates in the env.APP_ROOT, creating a virtualenv in the new-release
    directory, cloning the project's git repository, and running pip on the
    requirements file, which is assumed to be requirements.txt at the top
    level of the source-code directory.
    """
    with cd(env.APP_ROOT):
        sudo('virtualenv --no-site-packages %s' % env.new_release_dir)
    with cd(env.new_release_dir):
        sudo('git clone %(APP_GIT_URL)s code' % env)
        #sudo('git submodule update --init') # --recursive')
        if rev:
            with cd('code'):
                sudo('git reset --hard %s' % rev)
        # TODO: get pip file name from env server definition
        sudo('PIP_LOG_FILE=/tmp/hops-pip.log '
             ' PIP_DOWNLOAD_CACHE=~/.pip '  # User's home dir can cache pkgs
             ' bin/pip install -r code/requirements.txt',
             shell=True)
        # psycopg2 -> egenix-mx-base -> mx.DateTime dependency STILL broken!
        # supposedly fixed in psycopg2 2.4.2
        sudo('bin/easy_install '
             ' -i http://downloads.egenix.com/python/index/ucs4/ '
             ' egenix-mx-base')


def deploy(rev=None):
    """
    Deploy the Django app specified in hops_config.
    """

    # predeploy MUST run first
    predeploy()

    # Set up a directory structure for the new release
    highest_rel = get_highest_release_number()
    env.new_release = (highest_rel + 1)
    print(green("Beginning deployment #%s" % env.new_release))
    with cd(env.APP_ROOT):
        # Build absolute paths
        env.new_release_dir = '%(cwd)s/releases/%(new_release)s' % env
        env.new_site_packages = (
            "%(new_release_dir)s/lib/python2.6/site-packages" % env)
        env.new_code_dir = "%(new_release_dir)s/code" % env
        env.new_static_dir = "%(new_code_dir)s/static" % env
        env.new_conf_dir = "%(new_release_dir)s/conf" % env
        env.apache_log_dir = "%(APP_ROOT)s/log" % env
    install_app(rev)
    upload_project_wsgi_conf()
    upload_project_apache_conf()
    # TODO: get apache conf dir from env server def
    sudo('ln -sfn %(APP_ROOT)s/current/conf/apache.conf '
         ' /etc/apache2/sites-available/%(APP_NAME)s.conf' % env,
         shell=True)
    # if env.user != env.PROJECT_OWNER...
    sudo('chown %(PROJECT_OWNER)s:%(PROJECT_OWNER)s -R %(APP_ROOT)s' % env)
    sudo('ln -sfn %(new_release_dir)s %(APP_ROOT)s/current' % env)
    sudo('a2ensite %(APP_NAME)s.conf' % env)
    hops.commands.webservers.apache_reload()
