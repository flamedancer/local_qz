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


class UserMysteryStore(GameModel):
    """
    用户神秘商店信息
    """
    pk = 'uid'
    fields = ['uid', 'start_time', 'has_bought_packages', 'gold_store', 'coin_store', 'next_auto_refresh_time']

    def __init__(self):
        """初始化用户神秘商店信息
            self.gold_store = [
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
        self.start_time = None
        self.has_bought_packages =[]         # 已购买的大礼包 ids
        self.gold_store = []                # 现有铜钱商品
        self.coin_store = []                # 现有元宝商品
        self.next_auto_refresh_time = 0     # 下次自动刷新的时间戳

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
        return uc

    def _trans_goods_list_to_store(self, goods_list):
        """
         将商品配置列表转换成需存储的格式  例如：
            [{'2_card': {'lv': 1, 'category': 2, 'num': 3}, 'gold': 500}]
        转换成：
            [
                {  "goods": {'1_soul': 10},
                    "has_bought": False,
                    "gold": 300,
                },
            ]
        """
        store = []
        for goods in goods_list:
            sale_goods_info = {"has_bought": False}
            for key, value in goods.items():
                if key in ('gold', 'coin'):
                    sale_goods_info[key] = value
                else:
                    sale_goods_info['goods'] = {key: value}
            store.append(sale_goods_info)
        return store

    def refresh_store(self, store_type):
        """
        刷新商店物品，  store_type  可取  "coin_store" or "gold_store"
        """
        conf = copy.deepcopy(self.game_config.mystery_store[store_type + "_conf"])
        selected_goods = utils.get_items_by_random_simple(conf, 4)      # 按概率取四个，不足全取
        setattr(self, store_type, self._trans_goods_list_to_store(selected_goods))
        self.put()

    def store_info(self):
        """
        返回玩家所有神秘商店信息，以便前端显示
        """
        # 
        package_conf = copy.deepcopy(self.game_config.mystery_store["packages"])

        packages_info = []
        for package in package_conf:
            if package['id'] in self.has_bought_packages:
                package.update({"has_bought": True})
            else:
                package.update({"has_bought": False})
            packages_info.append(package)

        mystery_store_info = {
            "packages": packages_info,
            "gold_store": self.gold_store,
            "coin_store": self.coin_store,
            "next_auto_refresh_time": self.next_auto_refresh_time,
        }
        return mystery_store_info

    def auto_refresh_store(self):
        """
        根据 next_auto_refresh_time  判断是否刷新商品
        """
        start_time = datetime.datetime.strptime(self.game_config.mystery_store["start_time"], "%Y-%m-%d %H:%M:%S")

        #当调整过自动刷新开始时间时，重置 next_refresh_datetime
        if self.start_time != str(start_time):
            self.start_time = str(start_time)
            next_refresh_datetime = start_time
            self.put()

        elif self.next_auto_refresh_time:
            next_refresh_datetime = datetime.datetime.fromtimestamp(self.next_auto_refresh_time)
        else:
            next_refresh_datetime = start_time

        now_datetime = datetime.datetime.now()
        if now_datetime < next_refresh_datetime:
            return self.store_info()

        self.refresh_store("coin_store")
        self.refresh_store("gold_store")

        # 距离下一次自动刷新所需秒数
        refresh_hours_gap = self.game_config.mystery_store["refresh_hours_gap"]
        refresh_seconds_gap = refresh_hours_gap * 3600
        seconds_gap = refresh_seconds_gap * ((1 + int((now_datetime - start_time).total_seconds() / refresh_seconds_gap)))
        self.next_auto_refresh_time = time.mktime(start_time.timetuple()) + seconds_gap
        self.put()
        return self.store_info()


    def update_goods_info(self, store_type, goods):
        """
        store_type  可取  "packages"    "coin_store"  "gold_store"
        购买物品后，将has_bought 字段改成 True 或 添加入 self.has_bought_packages
        """
        if store_type == "packages":
            self.has_bought_packages.append(goods)
        else:
            all_goods_info = getattr(self, store_type)
            sale_goods = [sale['goods'] for sale in all_goods_info]
            index = sale_goods.index(goods)

            all_goods_info[index]['has_bought'] = True 
            setattr(self, store_type, all_goods_info)
        self.put()


    def update_goods_info_by_index(self, store_type, index):
        """
        # 根据index 来 定位goods
        store_type  可取  "packages"    "coin_store"  "gold_store"
        购买物品后，将has_bought 字段改成 True 或 添加入 self.has_bought_packages
            返回True代表可购买  Fasle为已购买
        """
        can_buy = True
        if store_type == "packages":
            goods = self.game_config.mystery_store["packages"][index]
            if goods['id'] in self.has_bought_packages:
                can_buy = False
            else:
                self.has_bought_packages.append(goods['id'])
        else:
            all_goods_info = getattr(self, store_type)
            if all_goods_info[index]['has_bought']:
                can_buy = False
            else:
                all_goods_info[index]['has_bought'] = True
                setattr(self, store_type, all_goods_info)
        self.put()
        return can_buy

