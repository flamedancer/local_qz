#!/usr/bin/env python
# encoding: utf-8
"""
user_pk_store.py
"""
import copy
import datetime

from apps.common import utils
from apps.models import GameModel


class UserPkStore(GameModel):
    """
    用户pk商店信息
    """
    pk = 'uid'
    fields = ['uid', 'goods', 'next_auto_refresh_time', 'manual_refresh_times']

    def __init__(self):
        self.uid = None
        self.goods = []
        self.next_auto_refresh_time = 0     # 下次自动刷新的时间戳
        self.manual_refresh_times = 0      # 已手动刷新次数,随VIP等级提高,可手动刷新次数增加

    @classmethod
    def get_instance(cls, uid):
        obj = super(UserPkStore, cls).get(uid)
        if obj is None:
            obj = cls.create(uid)
            obj.put()
        return obj

    @classmethod
    def create(cls, uid):
        uc = cls()
        uc.uid = uid
        return uc

    def store_info(self):
        """
        返回玩家所有商店信息，以便前端显示
        """
        cur_vip_lv = self.user_property.vip_cur_level
        vip_conf = self.game_config.user_vip_config
        max_vip_lv = max([int(n) for n in copy.deepcopy(vip_conf.keys())])
        can_refresh_pk_store_cnt = vip_conf[str(cur_vip_lv)]['can_refresh_pk_store_cnt']
        refresh_times = str(self.manual_refresh_times + 1)
        pk_store_info = {
            'pk_store': self.goods,
            # 返回前端的是可刷新次数
            'manual_refresh_times': can_refresh_pk_store_cnt - self.manual_refresh_times,
            'next_auto_refresh_time': self.next_auto_refresh_time,
            'total_refresh_times': can_refresh_pk_store_cnt,
            'refresh_need_honor': self.game_config.pk_store_config['refresh_need_honor'].get(refresh_times, 1),
            'user_vip_lv': cur_vip_lv,
            'max_vip_lv': max_vip_lv,
        }
        return pk_store_info

    def refresh_store_goods(self):
        """
        刷新所有商店物品状态为可兑换
        """
        goods = copy.deepcopy(self.game_config.pk_store_config['goods_list'])
        self.goods = []
        for goods_info in goods.values():
            sale_goods_info = {
                "has_bought": False,
                "need_honor": goods_info["need_honor"],
                "goods": {"_id": goods_info["id"], "num": goods_info["num"]},
            }
            self.goods.append(sale_goods_info)
        self.put()
        return self.goods

    def auto_refresh_store(self):
        """
        根据 next_auto_refresh_time  判断是否刷新商品, 重置每日可刷新次数
        """
        now = datetime.datetime.now()
        now_timestamp = utils.datetime_toTimestamp(now)
        if now_timestamp > self.next_auto_refresh_time:
            # 时间点到，自动刷新pk商店
            now_date = now.strftime('%Y-%m-%d')
            now_time = now.strftime('%H:%M:%S')
            tomorrow_now = now + datetime.timedelta(days=1)
            tomorrow_date = tomorrow_now.strftime('%Y-%m-%d')
            pk_store_config = self.game_config.pk_store_config
            refresh_time = pk_store_config.get('auto_refresh_time', '22:00:00')
            if now_time > refresh_time:
                next_refresh_time_str = '%s %s' % (tomorrow_date, refresh_time)
            else:
                next_refresh_time_str = '%s %s' % (now_date, refresh_time)
            # 更新自动刷新时间
            next_refresh_time = utils.string_toTimestamp(next_refresh_time_str)
            self.next_auto_refresh_time = next_refresh_time
            # 重置可刷新次数
            self.manual_refresh_times = 0
            self.put()
            # 自动刷新时间，刷新商店物品
            self.refresh_store_goods()

        return self.store_info()

    def can_manual_refresh(self):
        '''
        判断能否手动刷新
        '''
        cur_vip_lv = self.user_property.vip_cur_level
        vip_conf = self.game_config.user_vip_config
        can_refresh_pk_store_cnt = vip_conf[str(cur_vip_lv)]['can_refresh_pk_store_cnt']
        if self.manual_refresh_times >= can_refresh_pk_store_cnt:
            return False
        return True

    def add_refresh_time(self):
        self.manual_refresh_times += 1
        self.put()

    def can_buy_this_goods(self, goods_index):
        return not self.goods[goods_index]['has_bought']

    def goods_has_bought(self, goods_index):
        self.goods[goods_index]['has_bought'] = True
        self.put()
