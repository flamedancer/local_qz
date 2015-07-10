# -*- coding: utf-8 -*-
"""	set_config_new.py
	
将备份的配置txt文件读取到redis中
参数 1：  指定配置文件的相对路径，默认为 config_file.txt
参数 2：  指定需要回退的配置字段 例如： equip_config_1，在参数1存在时可用，

"""
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

from  django.core.management import setup_environ
setup_environ(settings)


this_config_name = ''
config_path = 'config_file.txt'
assert len(sys.argv) >= 2, 'no config_file'
config_path = os.path.join(cur_dir, sys.argv[1])
assert os.path.exists(config_path), '!!!Can find COnfigfile!!'
if len(sys.argv) == 3:
	this_config_name = sys.argv[2]


from apps.models.config import Config

config_dict = ast.literal_eval(open("config_file.txt", "r").read())

for sconfig_name in config_dict:
    print "*Find config ", sconfig_name,  "*This_config", this_config_name
    if this_config_name and this_config_name != sconfig_name:
        continue
    print "** load  :", sconfig_name
    config = Config.get(sconfig_name)
    if not config:
        config = Config.create(sconfig_name)
    config_value = config_dict[sconfig_name]
    config.data = config_value
    config.put()

print "****** load config  Success!!"
