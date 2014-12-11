#!/usr/bin/env python
# encoding: utf-8
"""
session.py
"""
from apps.oclib.model import TmpModel

class Session(TmpModel):
    """redis实现tmpModel
    """
    pk = 'session_key'
    fields = ['session_key','platform','pid','access_token','refresh_token','expires_time']
    ex=24*60*60
    def __init__(self):
        """初始化用户好友信息

        Args:
            uid: 平台用户ID
        """
        self.session_key = ''
        self.platform = None
        self.pid = None
        self.access_token = None
        self.refresh_token = None
        self.expires_time = None

    @classmethod
    def set(cls,platform,pid,access_token='',refresh_token='',expires_time=''):
        obj = cls()
        obj.session_key = platform+':'+pid
        obj.platform = platform
        obj.pid = pid
        obj.access_token = access_token
        obj.refresh_token = refresh_token
        obj.expires_time = expires_time
        obj.put(24*60*60)
        return obj

    @classmethod
    def get(cls,key):
        obj = super(Session,cls).get(key)
        if obj:
            return obj.platform,obj.pid
        else:
            return '',''
    
    @classmethod
    def new_get(cls,key):
        obj = super(Session,cls).get(key)
        data = {
                'platform':obj.platform,
                'pid':obj.platform,
                'access_token':obj.access_token,
                'refresh_token':obj.refresh_token,
                'expires_time':obj.expires_time,
                }
        if obj:
            return data
        else:
            return {}
