# encoding: utf-8
""" level_user.py
"""
import copy
import random
from apps.oclib.model import BaseModel

class LevelUser(BaseModel):
    """ 各等级区间的用户id
    """
    pk = 'subarea_lv'
    MAX_USER_NUM = 500
    RANDOM_NUM = 10
    fields = ['subarea_lv','users']
    def __init__(self):
        """ 初始化当前排名数据
        """
        self.subarea_lv = '1_1'  # 一区  lv1 
        self.users = []

    @classmethod
    def _install(cls, subarea_lv='1_1'):
        lu = cls()
        lu.subarea_lv = subarea_lv
        lu.users = []
        lu.put()
        return lu

    @classmethod
    def get_instance(cls, subarea, lv):
        subarea_lv = '{subarea}_{lv}'.format(subarea=subarea, lv=lv)
        obj = cls.get(subarea_lv)
        if obj is None:
            obj = cls._install(subarea_lv)
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
        """随机取得用户id
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


