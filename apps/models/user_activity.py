#!/usr/bin/env python
# encoding: utf-8
"""
user_activity.py
miaoyichao
"""
import copy
import math
import time
import random
from apps.common import utils
from apps.models import data_log_mod
from apps.models import GameModel


class UserActivity(GameModel):
    """用户基本信息
    Attributes:
        uid: 用户ID str
        explore: 探索 dic
        banquet: 性别 dic
    """
    pk = 'uid'
    fields = ['uid','explore','banquet']
    def __init__(self):
        """初始化用户活动信息

        Args:
            uid: 用户游戏ID
        """
        self.uid = None
        self.explore = {}
        self.banquet = {}

    @classmethod
    def get_instance(cls,uid):
        #初始化用户活动
        obj = super(UserActivity,cls).get(uid)
        if obj is None:
            obj = cls._install(uid)
        return obj

    @classmethod
    def _install(cls,uid):
        obj = cls.create(uid)
        obj.put()
        return obj

    @classmethod
    def create(cls,uid):
        #初始化活动对象
        uactivity = cls()
        uactivity.uid = uid
        #探索内容
        uactivity.explore = {}
        uactivity.explore = uactivity.reset_explore_times()
        #美味大餐
        uactivity.banquet = {}
        return uactivity

    def reset_explore_times(self):
        #重置可探索的次数
        self.explore = {}
        self.explore['today_str'] = utils.get_today_str()
        explore_times_config = self.game_config.operat_config.get('can_explore_times',{})
        #重置次数
        for explore_type in ['gold','silver','copper']:
            self.explore[explore_type] = explore_times_config.get(explore_type,3)
        #结果保存
        self.put()
        return self.explore

    def get_explore_times(self):
        #获取可探索的次数
        today_str = utils.get_today_str()
        if 'today_str' not in self.explore or today_str != self.explore['today_str']:
            self.reset_explore_times()
        explore_copy = copy.deepcopy(self.explore)
        explore_copy.pop('today_str')
        return explore_copy

    def min_explore_times(self,explore_type,num):
        #减去该探索类型的探索次数
        self.explore[explore_type] -= num
        if not self.explore[explore_type]:
            self.explore[explore_type] = 0
        self.put()

