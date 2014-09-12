#!/usr/bin/env python
# encoding: utf-8
"""
filename:user_name.py
"""
from apps.oclib.model import MongoModel
from apps.common.utils import datetime_toString
import datetime

class UserName(MongoModel):
    """
    存储用户名字，名字唯一
    """
    pk = 'name'
    fields = ['uid','name','createtime']
    def __init__(self):
        pass

    @classmethod
    def set_name(cls, uid=None, name=None,createtime=datetime.datetime.now()):
        obj = cls()
        obj.uid = uid
        obj.createtime = datetime_toString(createtime)
        obj.name = name
        #插入，如果有重复会报异常
        obj.insert()

