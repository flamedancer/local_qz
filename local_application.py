import sys
import os
print "debug application"
print os.popen("which python").readlines()
print os.popen('''python -c "import sys; print sys.path"''').readlines()
sys.path = eval(os.popen('''python -c "import sys; print sys.path"''').readlines()[0])
print "debug 1 ", sys.path
import django.core.handlers.wsgi
print "debug 1 ", sys.path

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
os.environ['DJANGO_SETTINGS_MODULE'] = 'apps.settings_local'

application = django.core.handlers.wsgi.WSGIHandler()


print "debug 2 ", sys.path
