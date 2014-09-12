#!/usr/bin/env python
# encoding: utf-8

from apps.models import pvp_redis

from apps.models import GameModel


class UserRealPvp(GameModel):
    """
    用户游戏内部基本信息
    """
    pk = 'uid'
    fields = ['uid','pvp_info']

    def __init__(self):
        """初始化用户游戏内部基本信息

        Args:
            uid: 用户游戏ID
            data:游戏内部基本信息
        """
        pass

    @classmethod
    def get_instance(cls,uid):
        obj = super(UserRealPvp,cls).get(uid)
        if obj is None:
            obj = cls._install(uid)
        return obj

    @classmethod
    def get(cls,uid):
        obj = super(UserRealPvp,cls).get(uid)
        return obj

    @classmethod
    def _install(cls,uid):
        obj = cls.create(uid)
        obj.put()
        return obj

    @classmethod
    def create(cls,uid):
        user_real_pvp = UserRealPvp()
        user_real_pvp.uid = uid
        user_real_pvp.pvp_info = {
            'pt': 1000,    # pk积分
            'honor': 0,     # 荣誉点, 每天系统结算 根据排名增加荣誉
            'last_refresh_time': 0,   # type is timestamp
            'pvp_title': '',    # pk称号
            # 其他不重要信息
            'detail_info':{
                'history_max_rank': 0,
                'total_win': 0,
                'total_lose': 0,
                'total_join': 0,
                'continue_win': 0,
                'defence_continue_win': 0,
                'defence_win': 0,
            },
        }
        return user_real_pvp

    @property
    def pvp_detail(self):
        self.pvp_info["pvp_title"] = self.pvp_title
        return self.pvp_info

    def get_pvp_need_info(self):
        tmp = {}
        user_prop_obj = self.user_property
        uc = self.user_cards
        base_info = self.pvp_detail
        tmp['pt'] = base_info['pt']
        tmp['pvp_title'] = base_info['pvp_title']
        tmp['win'] = base_info['detail_info']['total_win']
        tmp['lose'] = base_info['detail_info']['total_lose']

        tmp['name'] = self.user_base.username
        tmp['leader_card'] = uc.cards[uc.get_leader(uc.cur_deck_index)]
        tmp['lv'] = user_prop_obj.lv
        return tmp

    @property
    def pt(self):
        return self.pvp_info['pt']

    def add_pt(self, num):
        # 返回实际的pt变化值
        # pt_user
        old_pt = self.pvp_info['pt']
        new_pt = old_pt + num
        self.pvp_info['pt'] = new_pt if new_pt > 0 else 0
        self.put()
        return self.pvp_info['pt'] - old_pt

    @property
    def honor(self):
        return self.pvp_info['honor']

    def add_honor(self, num):
        # 返回实际的honor变化值
        old_honor = self.pvp_info['honor']
        new_honor = old_honor + num
        self.pvp_info['honor'] = new_honor if new_honor > 0 else 0
        self.put()
        return self.pvp_info['honor'] - old_honor

    @property
    def pvp_title(self):
        yesterday_rank = self.yesterday_pvp_rank()
        if yesterday_rank == 0:
            yesterday_rank = float("inf")
        return self.get_pvp_rank_conf(yesterday_rank).get('title', '')

    def pvp_rank(self):
        """返回自己pvp的排行，如果没有则添加最后一名到排行"""
        top_model = pvp_redis.get_pvp_redis(self.user_base.subarea, top_name='real_pvp')
        srank = top_model.rank(self.uid)
        # 不在排行榜内 返回 0
        if srank == None:
            return 0
        # top 的rank 第一名是 0
        return srank + 1

    def yesterday_pvp_rank(self):
        """返回昨天的排名"""
        top_model = pvp_redis.get_yesterday_pvp_redis(self.user_base.subarea, top_name='real_pvp')
        srank = top_model.rank(self.uid)
        # 不在排行榜内 返回 0
        if srank == None:
            return 0

        return srank + 1

    def get_pvp_rank_conf(self, rank):
        """根据排名  返回所属的pk配置  如 1 时 返回 pk_config['pk_rank_conf']['1']：
            {
                'get_honor':3000,
                'rank':'(1,1)',
                'title':unicode('皇帝','utf-8'),
            },
        """
        for rank_key, rank_conf in self.game_config.pk_config['pk_rank_conf'].iteritems():
            if len(rank_conf['rank']) == 1 and rank_conf['rank'][0] <= rank:
                return rank_conf
            elif rank_conf['rank'][0] <= rank <= rank_conf['rank'][1]:
                return rank_conf
        return {}

    def get_honor_everyday(self):
        yesterday_rank = self.yesterday_pvp_rank()
        if yesterday_rank == 0:
            yesterday_rank = float("inf")
        self.add_honor(self.get_pvp_rank_conf(yesterday_rank).get('get_honor', 0))
