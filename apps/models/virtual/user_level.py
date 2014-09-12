#!/usr/bin/env python
# encoding: utf-8
"""
user_level.py
"""
from apps.config.game_config import game_config

class UserLevel(object):
    """
        用户等级相关信息
    """


    def __init__(self, lv = 1):
        self.lv = lv  # 用户等级
        self.max_data_detail = {}

    @classmethod
    def get(cls, lv = 1, game_config=game_config):
        obj = cls(lv)
        obj.max_data_detail = game_config.user_level_config.get(str(lv),{})
        return obj

    @property
    def exp(self):
        """
           达到该等级所具有的经验值
        """
        return self.max_data_detail.get('exp')

    @property
    def stamina(self):
        """
           达到该等级所具有的体力
        """
        return self.max_data_detail.get('stamina')

    @property
    def friend_num(self):
        """
           达到该等级能拥有的好友人数
        """
        return self.max_data_detail.get('friend_num')

    @property
    def lv_stamina(self):
        '''
        达到该等级所能获得的体力值
        '''
        return self.max_data_detail.get('lv_add_stamina',30)
    # @property
    # def cost(self):
    #     """
    #        达到该等级能拥有的卡片总cost
    #     """
    #     return self.max_data_detail.get('cost')

