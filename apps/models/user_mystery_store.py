#!/usr/bin/env python
# encoding: utf-8
"""
user_mystery_store.py
"""
import copy
import datetime
import time
    
from apps.common import utils
from apps.models import GameModel
from apps.models.user_property import UserProperty


class UserMysteryStore(GameModel):
    """
    用户神秘商店信息
    """
    pk = 'uid'
    fields = ['uid', 'store', 'free_refresh_cnt', 'last_incre_refresh_cnt_timestr']

    def __init__(self):
        """初始化用户神秘商店信息
            self.store = [
                {  "goods": {'1_card': {'lv': 1, 'category': 2, 'num': 1}},
                    "has_bought": True,
                    "coin": 300,
                },
                {  "goods": {'1_soul': 10},
                    "has_bought": False,
                    "coin": 300,
                },

            ]
        """
        self.uid = None
        self.free_refresh_cnt = 0           # 免费刷洗次数
        self.last_incre_refresh_cnt_timestr = ''     # 最后一次更新免费刷新次数时间,例如:  2015-07-06 12:00:00
        self.store = []

    @classmethod
    def get_instance(cls, uid):
        obj = super(UserMysteryStore, cls).get(uid)
        if obj is None:
            obj = cls._install(uid)
        return obj

    @classmethod
    def _install(cls, uid):
        obj = cls.create(uid)
        obj.put()
        return obj

    @classmethod
    def create(cls, uid):
        uc = cls()
        uc.uid = uid
        uc.refresh_store()
        return uc

    def _trans_goods_list_to_store(self, goods_list):
        """
        Returns:
            [
                {  "goods": {"_id": '1_soul': "num": 10},
                    "has_bought": False,
                    "gold": 300,
                },
                ...
            ]
        """
        store = []
        for goods in goods_list:
            need_what = set(goods.keys()) & set(['need_gold', 'need_coin', 'need_fight_soul'])
            if need_what and "num" in goods:
                need_what = list(need_what)[0]
                sale_goods_info = {
                    "has_bought": False,
                    need_what: goods[need_what],
                    "goods": {"_id": goods["id"], "num": goods["num"]},
                }
            store.append(sale_goods_info)

        return store

    def refresh_store(self):
        """
        刷新商店物品
        """
        conf = copy.deepcopy(self.game_config.mystery_store_config["store_conf"])
        selected_goods = utils.get_items_by_weight_dict(conf, 8)      # 按概率取8个，不足全取
        self.store = self._trans_goods_list_to_store(selected_goods)
        self.put()

    def store_info(self):
        """
        返回玩家所有神秘商店信息，以便前端显示
        """
        user_property_obj = self.user_property
        refresh_hours_gap = self.game_config.mystery_store_config["refresh_hours_gap"]
        now = datetime.datetime.now()
        max_free_fresh_cnt = vip_conf[str(cur_vip_lv)].get('max_free_fresh_mystery_store_cnt', 4)
        # 如果已近达到最大免费刷新数, next_auto_refresh_time为 0
        if self.free_refresh_cnt >= max_free_fresh_cnt:
            next_auto_refresh_time = 0
        else:
            next_refresh_hour = ((now.hour / refresh_hours_gap) + 1) * refresh_hours_gap
            next_auto_refresh_time = str(datetime.datetime(now.year, now.month, now.day, next_refresh_hour))

        mystery_store_info = {
            "store": self.store,
            "fight_soul": user_property_obj.get_fight_soul,
            "next_auto_refresh_time": next_auto_refresh_time,
            "free_refresh_cnt": self.free_refresh_cnt, 
        }
        return mystery_store_info

    def incre_free_refresh_cnt(self):
        """
        根据 next_auto_refresh_time  判断是否增加 free_refresh_cnt
        """
        # 刷新间隔 （小时）
        refresh_hours_gap = self.game_config.mystery_store_config["refresh_hours_gap"]
        now = datetime.datetime.now()
        if not self.last_incre_refresh_cnt_timestr:
            last_incre_hour = (now.hour / refresh_hours_gap) * refresh_hours_gap
            self.last_incre_refresh_cnt_timestr = str(datetime.datetime(now.year, now.month, now.day, last_incre_hour))
            self.put()
            return self.store_info()
        deltatime = now - utils.transtr2datetime(self.last_incre_refresh_cnt_timestr)
        # 最大可有免费刷新次数
        cur_vip_lv = self.user_property.vip_cur_level
        vip_conf = self.game_config.user_vip_config
        max_free_fresh_cnt = vip_conf[str(cur_vip_lv)].get('max_free_fresh_mystery_store_cnt', 4)
        # 计算可产生多少刷新次数：间隔的小时数 / 刷新间隔
        may_product_cnt = int((deltatime.total_seconds() // 3600) // refresh_hours_gap)
        print self.last_incre_refresh_cnt_timestr, now
        print "may_product_cnt", may_product_cnt
        # 更新刷新次数
        self.free_refresh_cnt = min(int(may_product_cnt + self.free_refresh_cnt), max_free_fresh_cnt)
        # 更新刷新时间
        self.last_incre_refresh_cnt_timestr = str(datetime.datetime(now.year, now.month, now.day, now.hour))
        self.put()
        return self.store_info()


    def update_goods_info_by_index(self, index):
        """
        # 根据index 来 定位goods
        store_type  可取  "packages"    "coin_store"  "gold_store"
        购买物品后，将has_bought 字段改成 True 或 添加入 self.has_bought_packages
            返回True代表可购买  Fasle为已购买
        """
        can_buy = True
        all_goods_info = self.store
        if all_goods_info[index]['has_bought']:
            can_buy = False
        else:
            all_goods_info[index]['has_bought'] = True
            self.store = all_goods_info
        self.put()
        return can_buy
