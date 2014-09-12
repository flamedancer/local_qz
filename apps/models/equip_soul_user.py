# encoding: utf-8
""" level_user.py
"""
import copy
import random
from apps.oclib.model import BaseModel

class EquipSoulUser(BaseModel):
    """ 拥有装备碎片的用户id
    """
    pk = 'equip_soul'
    MAX_USER_NUM = 1000
    RANDOM_NUM = 10
    fields = ['equip_soul','users']
    def __init__(self):
        """ 初始化当前排名数据
        """
        self.equip_soul = ''  #   格式为： 50_1, 装备id为50_equip，equip_soul_type为1的碎片
        self.users = []

    @classmethod
    def _install(cls, equip_soul):
        ESU = cls()
        ESU.equip_soul = equip_soul
        ESU.users = []
        ESU.put()
        return ESU

    @classmethod
    def get_instance(cls, equip_id, equip_soul_type):
        equip_soul = '{}_{}'.format(equip_id, equip_soul_type)
        obj = cls.get(equip_soul)
        if obj is None:
            obj = cls._install(equip_soul)
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

    def del_user(self,uid):
        """
        Args:
            uid:
        """
        if uid in self.users:
            self.users.remove(uid)
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



