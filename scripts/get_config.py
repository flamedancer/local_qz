#-*- coding: utf-8 -*-
import importlib
import datetime,traceback,os
import ast
import sys
sys.path.insert(0, '/data/sites/op/qz')
import apps.settings_dev as settings
from django.core.management import setup_environ
setup_environ(settings)
from apps.models.config import Config
from apps.oclib import app
from apps.oclib.storage import StorageRedis
#op_redis_store = StorageRedis([{'host':'10.200.55.32','port':6394,'db':'0'}])
from apps.config import config_list

config_f = open('config_file.txt', 'w')
d = {}
for info in config_list.g_lConfig:
    config_name = info['name'] + '_1'
    c = Config.get(config_name)
    print config_name, len(c.data)
    d[config_name] = c.data if c else {}
config_f.write(str(d))