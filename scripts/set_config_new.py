import  os
import sys
import ast

print type(__file__)
cur_dir = os.path.dirname(os.path.abspath(__file__))
main_dir = os.path.dirname(cur_dir)
print cur_dir
print main_dir

sys.path.insert(0, main_dir)
import apps.settings as settings


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

config_path = 'config_file.txt'
if sys.argv == 2:
    config_path = os.path.join(cur_dir, sys.argv[1])
    assert os.path.exists(config_path), '!!!Can find COnfigfile!!'


from apps.models.config import Config

config_dict = ast.literal_eval(open("config_file.txt", "r").read())

for sconfig_name in config_dict:
    print "** load  :", sconfig_name

    config = Config.get(sconfig_name)
    if not config:
        config = Config.create(sconfig_name)
    config_value = config_dict[sconfig_name]
    config.data = config_value
    config.put()

print "****** load config  Success!!"
