# encoding: utf-8
""" level_user.py
"""
import copy
import random
from apps.oclib.model import BaseModel

class PtUsers(BaseModel):
    """ 各等级区间的用户id
    """
    pk = 'pt_lv'
    MAX_USER_NUM = 500
    RANDOM_NUM = 10
    fields = ['pt_lv','users']
    def __init__(self):
        """ 初始化当前排名数据
        """
        self.pt_lv = 1
        self.users = []

    @classmethod
    def _install(cls,pt_lv = 1):
        pu = cls()
        pu.pt_lv = pt_lv
        pu.users = []
        pu.put()
        return pu

    @classmethod
    def get_instance(cls,pt_lv):
        obj = cls.get(pt_lv)
        if obj is None:
            obj = cls._install(pt_lv)
        return obj

    def add_user(self,uid):
        """
        Args:
            uid:
        """
        if uid not in self.users:
            self.users.insert(0,uid)
            self.users = self.users[0:self.MAX_USER_NUM]
            self.put()


    def random_user(self,except_uids=None,num=1):
        """
        随机取得用户id
        """
        users = copy.deepcopy(self.users)
        if except_uids:
            for uid in except_uids:
                if uid in users:
                    users.remove(uid)
        if len(users) > 0:
            if num > len(users):
                num = len(users)
            return random.sample(users,num)
        else:
            return []

    def remove_user(self,uid):
        users = self.users
        if uid in users:
            users.remove(uid)
            self.put()




