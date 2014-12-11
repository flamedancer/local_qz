#!/usr/bin/env python
# encoding: utf-8

from apps.oclib.model import TmpModel


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
