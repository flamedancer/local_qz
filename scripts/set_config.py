import os
import sys
cur_dir = os.path.dirname(os.path.abspath(__file__))
setting_dir = cur_dir + "/.."
print setting_dir
sys.path.insert(0, setting_dir)
import apps.settings_local
#from django.core.management import setup_environ
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "apps.settings_local")
#setup_environ(settings)
print cur_dir
from apps.config.config import Config
config_dict = eval(open("config_file.txt", "r").read())
for sconfig_name in config_dict:

    config = Config.get(sconfig_name)
    if not config:
        config = Config.create(sconfig_name)
    config_value = config_dict[sconfig_name]
    config.data = config_value
    config.put()
