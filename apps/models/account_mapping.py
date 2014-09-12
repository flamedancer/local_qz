#!/usr/bin/env python
# encoding: utf-8
"""
account_mapping.py
"""
import time

from apps.oclib.model import BaseModel
from apps.common import sequence

class AccountMapping(BaseModel):
    """用户账号映射信息

    Attributes:
        pid: 用户openid str
        uid: 应用自身用户ID str
        created_at: 创建时间 date
    """
    pk = 'pid'
    fields = ['openid', 'access_token', 'pid', 'created_at', 'subarea_uids']
    def __init__(self):
        """初始化用户账号映射信息

        Args:
            id: openid
        """
        self.openid = ''
        self.access_token = ''
        self.pid = None
        self.created_at = int(time.time())
        # 各分区对应的uid
        self.subarea_uids = {}

    @classmethod
    def create(cls,pid):
        am = AccountMapping()
        am.openid = ''
        am.access_token = ''
        am.pid = pid
        am.created_at = int(time.time())
        return am

    def get_subarea_uid(self, subarea):
        return self.subarea_uids.get(subarea, '')

    @classmethod
    def get_user_id(cls, pid, subarea):
        """为每一个用户生成对应的应用自身维护的用户ID
        Args:
            id: openid
            subarea: 分区号
        Returns:
            uid: 应用自身维护的用户ID
        """
        account_mapping_obj = cls.get(pid)

        if not isinstance(account_mapping_obj,cls):
            account_mapping_obj = cls.create(pid)

        uid = account_mapping_obj.subarea_uids.get(subarea) 

        if not uid :
            uid = sequence.generate()
            account_mapping_obj.subarea_uids[subarea] = uid
            account_mapping_obj.put()
        return uid

    def update_info(self,openid,access_token):
        """更新平台的access_token
        """
        if openid != self.openid or access_token != self.access_token:
            self.openid = openid
            self.access_token = access_token
            self.put()
