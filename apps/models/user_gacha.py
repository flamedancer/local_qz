#!/usr/bin/env python
# encoding: utf-8
"""
user_gacha.py
"""
import time
from apps.models import GameModel

class UserGacha(GameModel):
    """
    用户游戏内部基本信息
    """
    pk = 'uid'
    fields = ['uid','gacha_info','free_timer_gacha']

    def __init__(self):
        """初始化用户游戏内部基本信息

        Args:
            uid: 用户游戏ID
            data:游戏内部基本信息
        """
        self.uid = None
        self.gacha_info = {}
        self.free_timer_gacha = {
                                 'last_gacha_time':None,#上次免费抽将时间
                                }

    @classmethod
    def get_instance(cls,uid):
        obj = super(UserGacha,cls).get(uid)
        if obj is None:
            obj = cls._install(uid)
        return obj

    @classmethod
    def _install(cls,uid):
        obj = cls()
        obj.uid = uid
        obj.gacha_info = {
                          'coin':0,#累积抽将花费的元宝
                          'first_tenth_charge_multi': True,     # 首次十连抽，抽了十次
                          'gacha_cnt': obj.game_config.gacha_config['first_gacha_cnt'] + 1,  # 必中5星武将的计数,+1是新手引导那一次
                          'first_gacha': True,  # 玩家首次单抽
                          }
        obj.free_timer_gacha = {
                             'last_gacha_time':None,#上次免费抽将时间
                            }
        obj.put()
        return obj
    
    def add_cost_coin(self,coin):
        self.gacha_info['coin'] += coin
        self.put()
        
    def get_cost_coin(self):
        '''
        获取抽将消耗的元宝数量
        '''
        return self.gacha_info['coin']
    
    def reset_cost_coin(self):
        self.gacha_info['coin'] = 0
        self.put()

    def is_first_tenth_charge_multi(self):
        return self.gacha_info.get('first_tenth_charge_multi', True)

    def set_first_tenth_charged(self):
        self.gacha_info['first_tenth_charge_multi'] = False
        self.put()
    
    @property
    def next_free_gacha_time(self):
        """
        用户下一次免费gacha时间
        """
        if not self.free_timer_gacha['last_gacha_time']:
            return int(time.time())
        return self.free_timer_gacha['last_gacha_time'] + self.game_config.gacha_config.get('free_internal_hours', 48) * 3600
    
    def set_last_gacha_time(self):
        """
        记录免费抽时间
        """    
        self.free_timer_gacha['last_gacha_time'] = int(time.time())
        self.put()
    
    @property
    def gacha_cnt(self):
        gc = self.gacha_info.get('gacha_cnt')
        if not gc:
            self.gacha_info['gacha_cnt'] = 10
            self.put()
            return 10
        else:
            return gc

    def set_gacha_cnt(self):
        if self.gacha_info['gacha_cnt'] == 0:
            self.gacha_info['gacha_cnt'] = 10
        else:
            self.gacha_info['gacha_cnt'] -= 1
        self.put()

    @property
    def first_single_gacha(self):
        return self.gacha_info.get('first_gacha', False)

    def set_first_single_gacha(self):
        del self.gacha_info['first_gacha']
        self.put()
