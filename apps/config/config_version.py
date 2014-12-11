#-*- coding: utf-8 -*-

import time
from apps.models.redis_tool import RedisTool


def get_config_version(subarea, config_name):
    subarea = str(subarea)
    redis_config_name = config_version_key(subarea, config_name)
    config_update_time = RedisTool.get(redis_config_name)
    if not config_update_time:
        config_update_time = set_config_version(subarea=subarea, config_name=config_name)
    else:
        config_update_time = config_update_time
    return config_update_time


def set_config_version(subarea='1', config_name=''):
    subarea = str(subarea)
    redis_config_name = config_version_key(subarea, config_name)
    set_time = time.time()
    RedisTool.set(redis_config_name, set_time, 72*60*60)
    return set_time


def config_version_key(subarea, config_name):
    redis_config_name = "_".join([config_name, subarea, "update_time"])
    return redis_config_name


def config_update(subarea, config_name):
    set_config_version(subarea, config_name)
    set_config_version("1", config_name="ALL_config")


