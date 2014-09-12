#!/usr/bin/env python
# encoding: utf-8

from django.conf import settings
from apps.oclib.model import TmpModel
import time

class RedisTool(TmpModel):
    """redis临时存储
    """
    pk = 'redis_key'
    fields = ['redis_key','redis_value']
    def __init__(self):
        """初始化用户好友信息

        Args:
            uid: 平台用户ID
        """
        self.redis_key = ''
        self.redis_value = None

    @classmethod
    def set(cls,key,value,ex=None):
        obj = cls()
        obj.redis_key = key
        obj.redis_value = value
        obj.put(ex)
        return obj

    @classmethod
    def get(cls,key,default=''):
        obj = super(RedisTool,cls).get(key)
        if obj:
            return obj.redis_value
        else:
            return default

def get_config_version(subarea, config_name):
    subarea = str(subarea)
    redis_config_name = config_version_key(subarea, config_name)
    config_update_time = RedisTool.get(redis_config_name)
    if not config_update_time:
        config_update_time = set_config_version(subarea=subarea, config_name=config_name)
    else:
        config_update_time = config_update_time
    return int(config_update_time)

def set_config_version(subarea='1', config_name=''):
    subarea = str(subarea)
    redis_config_name = config_version_key(subarea, config_name)
    set_time = str(int(time.time()))
    RedisTool.set(redis_config_name, set_time, 72*60*60)
    return set_time

def config_version_key(subarea, config_name):
    redis_config_name = settings.CACHE_PRE +'subarea_' + subarea + "_" + config_name + "update_time"
    return redis_config_name
