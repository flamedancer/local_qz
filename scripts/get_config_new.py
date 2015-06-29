#! /usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import datetime

cwd = os.path.dirname(os.path.abspath(__file__))
print cwd
main_dir = os.path.dirname(cwd)
sys.path.insert(0, main_dir)
import apps.settings as settings
from  django.core.management import setup_environ
setup_environ(settings)
from apps.models.config import Config
from apps.oclib import app


from apps.config import config_list

dirpath = cwd + '/backup_configs'
if not os.path.exists(dirpath):
    print "*** mkdir", dirpath
    os.mkdir(dirpath)

daystr = str(datetime.date.today())
filepath = os.path.join(dirpath, daystr)

config_f = open(filepath, 'w')
print "**start backup to :", filepath
d = {}
for info in config_list.g_lConfig:
    config_name = info['name'] + '_1'
    c = Config.get(config_name)
    print config_name, len(c.data)
    d[config_name] = c.data if c else {}
config_f.write(str(d))
config_f.close()
print "**end backup!"

oldest_daystr = str(datetime.date.today() -
    datetime.timedelta(days=30))
oldest_filepath = os.path.join(dirpath, oldest_daystr)
if os.path.exists(oldest_filepath):
    print "****delet too old configfile:", oldest_filepath
    os.remove(oldest_filepath)
