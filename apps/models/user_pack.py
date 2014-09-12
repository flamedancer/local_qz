#!/usr/bin/env python
# encoding: utf-8
"""
user_pack.py
"""
import copy
import math
import time
import random
from apps.common import utils
from apps.models.user_collection import UserCollection
from apps.models.user_equips import UserEquips
from apps.models import data_log_mod
from apps.models import GameModel

class UserPack(GameModel):
    """
    用户游戏内部基本信息
    """
    pk = 'uid'
    fields = ['uid','items','materials','props','max_store_num','item_deck']
    def __init__(self):
        """初始化用户游戏内部基本信息

        Args:
            uid: 用户游戏ID
        """
        self.uid = None
        self.items = {}
        self.materials = {}
        self.props = {}
        self.max_store_num = 0
        self.item_deck = [{},{},{},{},{}]

    @classmethod
    def get_instance(cls,uid):
        #初始化用户背包对象
        obj = super(UserPack,cls).get(uid)
        if obj is None:
            obj = cls._install(uid)
        return obj

    @classmethod
    def _install(cls,uid):
        obj = cls.create(uid)
        return obj

    @classmethod
    def create(cls,uid):
        #初始化背包内容
        upack = cls()
        upack.uid = uid

        #初始y药品
        #药品
        upack.items = {}
        #材料
        upack.materials = {}
        #道具
        upack.props = {}
        upack.max_store_num = upack.game_config.user_init_config['init_max_store_num']
        upack.item_deck = [{},{},{},{},{}]

        init_items = upack.game_config.user_init_config['init_items']
        # 用户初始化
        # for item in upack.game_config.item_config:
        #     upack.add_item(item,int(init_items[item]),where='init_user')
        for item in upack.game_config.item_config:
            upack.add_item(item,50,where='init_user')
        for mat_id in upack.game_config.material_config:
            upack.add_material(mat_id,50,where='init_user')
        for props_id in upack.game_config.props_config:
            upack.add_props(props_id,50,where='init_user')
        upack.add_props('8_props',10000,where='init_user')

        upack.put()
        return upack

    def clear_item_deck(self):
        """初始化给的物品
        """
        self.item_deck = [{},{},{},{},{}]
        self.put()

    def get_cnt_in_item_deck(self,item_id):
        """
        *获取item deck中的item数
        """
        for item in self.item_deck:
            if item_id in item:
                return item[item_id]
        return 0
    
    def get_item_can_use_cnt(self,item_id):
        """
        *可用道具数量，扣除编队中的数量
        """
        deck_cnt = self.get_cnt_in_item_deck(item_id)
        total_cnt = self.items.get(item_id,0)
        return total_cnt-deck_cnt
        

    def get_items(self):
        """
        *获得平台UID 对应的用户对象的药品
        """
        return copy.deepcopy(self.items)

    def get_materials(self):
        """
        获得平台UID 对应的用户对象的素材
        """
        return copy.deepcopy(self.materials)

    def get_props(self):
        """
        获得平台UID 对应的用户对象的道具
        """
        return copy.deepcopy(self.props)


    def has_item(self,item_id):
        '''
        判断是否有该药品
        '''
        return item_id in self.items.keys()

    def has_mat(self,mat_id):
        '''
        判断是否有该素材
        '''
        return mat_id in self.materials.keys()

    def has_props(self,props_id):
        '''
        判断是否有该道具
        '''
        return props_id in self.props.keys()

    def minus_material(self,material_id,num,where=None):
        '''
        * 一次扣除一种素材
        '''
        num = abs(num)
        if self.is_material_enough(material_id,num):
            #获取扣除前的数量
            before = self.materials[material_id]
            self.materials[material_id] -= num
            #获取扣除后的数量
            after  = self.materials[material_id]
            if after<=0:
                self.materials.pop(material_id)
            self.put()
            if where:
                log_data = {'where':where, 'm_id':material_id, 'sum':num, 'after': after, 'before': before, }
                data_log_mod.set_log('MatConsume', self, **log_data)
            return True
        return False
    
    def minus_materials(self,materials,where=None):
        """
        批量扣除材料
        """
        pt_fg = False
        for material_id in materials:
            num = abs(materials[material_id])
            if self.is_material_enough(material_id,num):
                #获取扣除前的数量
                before = self.materials[material_id]
                self.materials[material_id] -= num
                #获取扣除后的数量
                after  = self.materials[material_id]
                if after<=0:
                    self.materials.pop(material_id)
                pt_fg = True
                if where:
                    log_data = {
                        'where':where,
                        'm_id':material_id,
                        'sum':num,
                        'after': after,
                        'before': before
                    }
                    data_log_mod.set_log('MatConsume', self, **log_data)
        if pt_fg:
            #保存修改内容
            self.put()

    def minus_item(self,item_id,item_num,where=None):
        '''
        * 一次扣除一种药品
        '''
        item_num = abs(item_num)
        if self.is_item_enough(item_id,item_num):
            #获取扣除前的数量
            before = self.items[item_id]
            self.items[item_id] -= item_num
            #获取扣除后的数量
            after = self.items[item_id]
            if after<=0:
                self.items.pop(item_id)
            self.put()
            if where:
                log_data = {
                    'where':where,
                    'item_id':item_id,
                    'sum':item_num,
                    'after': after,
                    'before': before
                }
                data_log_mod.set_log('ItemConsume', self, **log_data)
            #去查看是否需要重新设置药品编队
            self.is_need_reset_deck(item_id)
            return True
        return False
    
    def minus_items(self,items,where=None):
        """
        批量扣除药品
        """
        pt_fg = False
        for item_id in items:
            item_num = abs(items[item_id])
            if self.is_item_enough(item_id,item_num):
                #获取扣除前的数量
                before = self.items[item_id]
                self.items[item_id] -= item_num
                #获取扣除后的数量
                after = self.items[item_id]
                if after<=0:
                    self.items.pop(item_id)
                pt_fg = True
                #去查看是否需要重新设置药品编队
                self.is_need_reset_deck(item_id)
                if where:
                    log_data = {
                        'where':where,
                        'item_id':item_id,
                        'sum':item_num,
                        'after': after,
                        'before': before
                    }
                    data_log_mod.set_log('ItemConsume', self, **log_data)
        if pt_fg:
            #保存修改的内容
            self.put()

    def minus_props(self,props_id,num,where=None):
        '''
        * 一次扣除一种道具
        '''
        num = abs(num)
        if self.is_props_enough(props_id,num):
            #获取扣除前的数量
            before = self.props[props_id]
            self.props[props_id] -= num
            #获取扣除后的数量
            after  = self.props[props_id]
            if after<=0:
                self.props.pop(props_id)
            self.put()
            if where:
                log_data = {'where':where, 'props_id':props_id, 'sum':num, 'after': after, 'before': before, }
                data_log_mod.set_log('PropsConsume', self, **log_data)
            return True
        return False
    
    def minus_multi_props(self,all_props,where=None):
        """
        批量扣除道具
        """
        pt_fg = False
        for props_id in all_props:
            num = abs(all_props[props_id])
            if self.is_props_enough(props_id,num):
                #获取扣除前的数量
                before = self.props[props_id]
                self.props[props_id] -= num
                pt_fg = True
                #获取扣除后的数量
                after  = self.props[props_id]
                if after<=0:
                    self.props.pop(props_id)
                if where:
                    log_data = {
                        'where':where,
                        'props_id':props_id,
                        'sum':num,
                        'after': after,
                        'before': before,
                    }
                    data_log_mod.set_log('PropsConsume', self, **log_data)
        if pt_fg:
            #保存修改内容
            self.put()

    def add_item(self,item_id,item_num,where=None):
        '''
        * 添加药品
        '''
        #获取添加前的数量
        before = self.items.get(item_id, 0)
        if item_id not in self.items:
            self.items[item_id] = abs(item_num)
        else:
            self.items[item_id] += abs(item_num)
        #获取添加后的数量
        after = self.items.get(item_id, 0)
        if where:
            log_data = {'where':where, 'item_id':item_id, 'sum':item_num, 'after': after, 'before': before, }
            data_log_mod.set_log('ItemProduct', self, **log_data)
        #加入图鉴
        UserCollection.get_instance(self.uid).add_collected_card(item_id,'items')
        self.put()
        #去查看是否需要重新设置药品编队
        self.is_need_reset_deck(item_id)


    def add_material(self,m_id,num,where=None):
        '''
        *添加素材
        '''
        #获取添加前的数量
        before = self.materials.get(m_id, 0)
        if m_id not in self.materials:
            self.materials[m_id] = abs(num)
        else:
            self.materials[m_id] += abs(num)
        #获取添加后的数量
        after = self.materials[m_id]
        if where:
            log_data = {'where': where, 'm_id':m_id, 'sum':num, 'after': after, 'before': before}
            data_log_mod.set_log('MatProduct', self, **log_data)
        #加入图鉴
        UserCollection.get_instance(self.uid).add_collected_card(m_id,'materials')
        self.put()

    def add_props(self,props_id,props_num,where=None):
        '''
        * 添加道具
        '''
        #获取添加前的数量
        before = self.props.get(props_id, 0)
        if props_id not in self.props:
            self.props[props_id] = abs(props_num)
        else:
            self.props[props_id] += abs(props_num)
        #获取添加后的数量
        after = self.props.get(props_id, 0)
        if where:
            log_data = {'where':where, 'props_id':props_id, 'sum':props_num, 'after': after, 'before': before, }
            data_log_mod.set_log('ItemProduct', self, **log_data)
        #加入图鉴  暂无图片 和id所以先不加图鉴信息
        #UserCollection.get_instance(self.uid).add_collected_card(props_id,'props')
        self.put()

    def is_material_enough(self, material_id,num):
        #判断素材是否足够
        return self.materials.get(material_id,0) >= abs(num)

    def is_item_enough(self, item_id,num):
        #判断药品是否足够
        return self.items.get(item_id,0) >= abs(num)

    def is_props_enough(self, props_id,num):
        #判断道具是否足够
        return self.props.get(props_id,0) >= abs(num)

    def set_item_deck(self,item_deck):
        #设置道具编队
        self.item_deck = item_deck
        self.put()

    def get_item_total_num(self):
        #获取药品的总数量
        num = 0
        for item in self.items:
            num += self.items[item]
        return num

    def get_item_num(self,item_id):
        '''
        根据 item_id 获取该药品的数量
        '''
        return self.items.get(item_id,0)

    def get_material_total_num(self):
        #获取素材的总数量
        num = 0
        for mat in self.materials:
            num += self.materials[mat]
        return num

    def get_props_total_num(self):
        #获取道具的总数量
        num = 0
        for props_id in self.props:
            num += self.props[props_id]
        return num

    def is_need_reset_deck(self,item_id):
        '''
        判断是否需要重置药品编队
        '''
        #遍历药品编队 根据药品编队里面的item_id 来确定是否需要更新
        for item_info in self.item_deck:
            if item_id not in item_info.keys():
                self.reset_item_deck()
                return

    def reset_item_deck(self):
        '''
        重置药品编队
        '''
        #获取药品编队信息
        item_deck = self.item_deck
        #初始化新的药品编队
        new_item_deck = []
        for item_info in item_deck:
            #判断药品队列的内容是否为空
            if not item_info:
                new_item_deck.append(item_info)
            else:
                item_id = item_info.keys()[0]
                #获取最最大容量和用户背包中药品数量的最小值
                user_item_num = self.get_item_num(item_id)
                max_item_num = self.game_config.item_config.get(item_id,{}).get('max_num',0)
                set_num = min(max_item_num,user_item_num)
                #可用数不为0
                if set_num:
                    new_item_deck.append({item_id:set_num})
                else:
                    #用户背包已经没有该药品
                    new_item_deck.append({})
        self.item_deck = new_item_deck
        self.put()

