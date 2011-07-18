import site
site.addsitedir('%(new_site_packages)s')

import sys
sys.path.append('%(new_code_dir)s')
sys.path.append('%(new_code_dir)s/apps')

import os
os.environ['DJANGO_SETTINGS_MODULE'] = '%(django_settings_module)s'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
