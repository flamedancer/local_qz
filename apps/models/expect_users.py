#!/usr/bin/env python
# encoding: utf-8
"""
user_gift.py
"""
import time
from apps.oclib.model import BaseModel
class ExceptUsers(BaseModel):
    """
    收集有可能为作弊的玩家
      比如  战场掉落铜钱过高玩家
    """
    max_user = 5000
    pk = 'except_type'
    fields = ['except_type','except_info']

    def __init__(self):
        """初始化用户游戏内部基本信息

        Args:
            except_type: 异常类型
            except_info:游戏内部基本信息
        """
        self.except_type = ''
        self.except_info = {}

    @classmethod
    def get_instance(cls,except_type):
        obj = super(ExceptUsers,cls).get(except_type)
        if obj is None:
            obj = cls._install(except_type)
        return obj

    @classmethod
    def _install(cls,except_type):
        obj = ExceptUsers()
        obj.except_type = except_type
        obj.except_info = {}
        obj.put()
        return obj

    def set_users(self,key,uid):
        #结构 [(uid,time),(uid,time)]
        total_users = self.except_info.get(key,[])
        if len(total_users) > self.max_user:
            total_users.pop(0)
        total_users.append((uid,int(time.time())))
        self.put()

    def get_users(self,key):
        return self.except_info.get(key,[])



