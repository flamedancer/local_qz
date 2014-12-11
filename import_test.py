#-*- coding: utf-8 -*-

import django

if django.get_version() <= '1.3.1':
    import apps.settings as settings
    from django.core.management import setup_environ
    setup_environ(settings)
elif django.get_version() >= '1.7.0':   
    import os
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "apps.settings")
    django.setup()
elif django.get_version() >= '1.6.0':   #ubuntu 14.04 used 1.6.?
    import os
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "apps.settings")
    from django.conf import settings


import os
import os.path
import traceback

cur_dir = os.path.dirname(os.path.abspath(__file__))
LOGFILE = os.path.join(cur_dir,"logs","oneclick.log")
file_list = ['import_test', 'import_test_dev', 'import_test_local','settings', 'manage', 'settings_dev', 'manage_dev', 'settings_stg','manage_stg', 'settings_local','manage_local']
exclude_dir = ['.svn', 'realtime_pvp']

def run_dir(py_dir):
    log_f = open(LOGFILE, 'a+')
    try:
        for root, dirs, files in os.walk(py_dir):
            if os.path.basename(root) not in exclude_dir:
                for f in files:
                    name, ext = os.path.splitext(f)
                    if ext == '.py' and name not in file_list:
                        root = root.replace(py_dir, '').replace('/', '.').replace('\\', '.')
                        print root, name
                        log_f.write(str(root) + str(name) + '\n')
                        if root:
                            __import__('apps.' + root, globals(), locals(), [name], -1)
                        else:
                            __import__('apps.' + name, globals(), locals(), [], -1)
        log_f.close()
    except:
        err_info = traceback.format_exc()
        print err_info
        log_f.write(err_info+ '\n')
        log_f.close()

if __name__ == '__main__':
    run_dir(settings.BASE_ROOT+'/apps/')
