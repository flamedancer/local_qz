#!/usr/bin/env python
# encoding: utf-8

from apps.models import data_log_mod
import copy
from apps.oclib.model import TopModel
import datetime

#统一管理pvp的排行版
PVPREDIS = {}


class PvpRedis(TopModel):
    """pvp排名信息
    """
    def __init__(self, subarea='', top_name=''):
        self.subarea = subarea
        self.top_name = "".join(['PvpRedis_', top_name, subarea]) 

        # self.create_npc()

    def set(self, name, score):
        print(str(datetime.datetime.now()) + "  PvpRedis name: " + str(name) + " , set score: " + str(score))
        s = super(PvpRedis, self).set(name, score)
        return s

    def create_npc(self):
        """创建前5001位npc"""
        top_info = self.get()
        if not top_info:
            for i in range(1, 5001):
                name, score = "@npc" + str(i), i
                self.set(name, score)

    def pvp_exchange(self, name1, score1, name2, score2):
        """交换排名
            name1:挑战者
            name2:被挑战者
            score1:挑战者的排行
            score2:被挑战者的分数
            return 0：失败，1:交换成功
        """
        #挑战者的排行不能高于被挑战者
        score1, score2 = int(score1), int(score2)
        if score1 < score2:
            return 0
        fg = self.exchange(str(name1), score1, str(name2), score2)
        print(str(datetime.datetime.now()) + "  PvpRedis name1: " + str(name1) + " ,score1: " + str(score1) + " -> " + str(score2) + " name2: " + str(name2) + " ,score2: " + str(score2) + " -> " + str(score1))
        # if fg:
        #     log_data = {'uid': str(name1), 'subarea': self.subarea, 'self_rank': score2}
        #     data_log_mod.set_log('DLPvpRank',**log_data)
        #     log_data = {'uid': str(name2), 'subarea': self.subarea, 'self_rank': score1}
        #     data_log_mod.set_log('DLPvpRank',**log_data)
        return fg

    def get_arena_opponents_uids(self, rank):
        """当玩家排名200名之后，则对手等级间隔为int(玩家排名/100)
        当玩家排名在200名之内，等级间隔为2
        20名之内，等级间隔为1
        rank: 玩家排名
        return : uid_list:[(rank, '@npc1'), (2, '@npc2')]
        """
        rank = int(rank)
        if rank > 200:#当玩家排名200名之后，则对手等级间隔为int(玩家排名/100)
            rank_list = [rank - i*rank/100 for i in range(1, 10)]
        elif rank > 20:#当玩家排名在200名之内，等级间隔为2
            rank_list = [rank - i*2 for i in range(1, 10)]
        else:#20名之内，等级间隔为1
            rank_list = [rank - i for i in range(1, 10)]
        uid_list = copy.deepcopy([(int(rank), self.get_name_by_rank(int(rank-1), desc=False)) for rank in rank_list])
        return uid_list


def get_pvp_redis(subarea, top_name=''):
    # 获得实时的排行榜信息   
    subarea_top_name = "|".join([subarea, top_name])
    return PVPREDIS.setdefault(subarea_top_name, PvpRedis(subarea, top_name))


def get_yesterday_pvp_redis(subarea, top_name=''):
    #获得‘前一天’的排行榜信息  因为是每天22点刷新  所以不是真正的前一天  需要有定时脚本执行22点保存排行榜
    subarea_top_name = "|".join([subarea, top_name + "_yesterday"])
    return PVPREDIS.setdefault(subarea_top_name, PvpRedis(subarea, top_name + "_yesterday"))

