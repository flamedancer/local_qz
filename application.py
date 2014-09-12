import sys
import os
import django.core.handlers.wsgi

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
os.environ['DJANGO_SETTINGS_MODULE'] = 'apps.settings'

application = django.core.handlers.wsgi.WSGIHandler()
