#!/usr/bin/env python
# encoding: utf-8
"""
equip_level.py
"""
from apps.config.game_config import game_config

class EquipLevel(object):
    """
        装备等级相关信息
        有装备等级和该等级的经验
    """
    def __init__(self, lv = 1):
        self.lv = lv  # 装备等级
        self.exp = 0

    @classmethod
    def get(cls, lv = 1, game_config=game_config):
        '''
        * 获取该等级所需要的经验
        '''
        obj = cls(lv)
        obj.exp = game_config.equip_exp_config.get(str(lv),0)
        return obj
