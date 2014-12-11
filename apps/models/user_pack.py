#!/usr/bin/env python
# encoding: utf-8
"""
user_pack.py
"""
import copy

from apps.models.user_collection import UserCollection

from apps.models import data_log_mod
from apps.models import GameModel
from apps.common.exceptions import GameLogicError

class UserPack(GameModel):
    """
    用户游戏内部基本信息
    """
    pk = 'uid'
    fields = ['uid', 'materials', 'props', 'store_has_bought']
    def __init__(self):
        """初始化用户游戏内部基本信息

        Args:
            uid: 用户游戏ID
        """
        self.uid = None
        self.materials = {}
        self.props = {}
        self.store_has_bought = {}

    @classmethod
    def get_instance(cls,uid):
        #初始化用户背包对象
        obj = super(UserPack,cls).get(uid)
        if obj is None:
            obj = cls.create(uid)
            obj.put()
        return obj

    @classmethod
    def create(cls,uid):
        #初始化背包内容
        upack = cls()
        upack.uid = uid

        #材料
        upack.materials = {}
        #道具
        upack.props = {}

        # 初始用户物品
        init_config = upack.game_config.user_init_config
        for mat_id, num in init_config.get("init_mat", {}).items():
            upack.add_material(mat_id, 50, where='init_user')
        for props_id, num in init_config.get("init_props", {}).items():
            upack.add_props(props_id, 50, where='init_user')
        return upack

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
            self.materials[material_id] -= num
            #获取扣除后的数量
            after  = self.materials[material_id]
            if after<=0:
                self.materials.pop(material_id)
            self.put()
            if where:
                log_data = {'where':where, 'mat_id': material_id, 'num': num}
                data_log_mod.set_log('MatConsume', self, **log_data)
            return True
        return False
    
    def minus_materials(self, materials, where=""):
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
                        'mat_id':material_id,
                        'num':num,
                        'after': after,
                        'before': before
                    }
                    data_log_mod.set_log('MatConsume', self, **log_data)
        if pt_fg:
            #保存修改内容
            self.put()


    def minus_props(self, props_id, num, where=None):
        '''
        * 一次扣除一种道具
        '''
        num = abs(num)
        if self.is_props_enough(props_id,num):
            before = self.props[props_id]
            #获取扣除前的数量
            self.props[props_id] -= num
            #获取扣除后的数量
            after  = self.props[props_id]
            if after<=0:
                self.props.pop(props_id)
                after = 0
            self.put()
            if where:
                log_data = {'where': where, 'props_id': props_id, 'num':num, 'after': after, 'before': before}
                data_log_mod.set_log('PropsConsume', self, **log_data)
            return True
        return False
    
    def minus_multi_props(self, all_props, where=None):
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
                        'num':num,
                        'after': after,
                        'before': before,
                    }
                    data_log_mod.set_log('PropsConsume', self, **log_data)
        if pt_fg:
            #保存修改内容
            self.put()


    def add_material(self, mat_id, num, where=""):
        '''
        *添加素材
        '''
        #获取添加前的数量
        before = self.materials.get(mat_id, 0)
        if mat_id not in self.materials:
            self.materials[mat_id] = abs(num)
        else:
            self.materials[mat_id] += abs(num)
        #获取添加后的数量
        after = self.materials[mat_id]

        log_data = {'where': where, 'mat_id':mat_id, 'num':num, 'after': after, 'before': before}
        data_log_mod.set_log('MatProduct', self, **log_data)
        #加入图鉴
        UserCollection.get_instance(self.uid).add_collected_card(mat_id, 'materials')
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
            log_data = {'where':where, 'props_id':props_id, 'num':props_num, 'after': after, 'before': before}
            data_log_mod.set_log('PropsProduct', self, **log_data)
        #加入图鉴  暂无图片 和id所以先不加图鉴信息
        #UserCollection.get_instance(self.uid).add_collected_card(props_id,'props')
        self.put()

    def is_material_enough(self, material_id,num):
        #判断素材是否足够
        return self.materials.get(material_id,0) >= abs(num)

    def is_props_enough(self, props_id,num):
        #判断道具是否足够
        return self.props.get(props_id,0) >= abs(num)

    def get_material_total_num(self):
        #获取素材的总数量
        num = 0
        for mat in self.materials:
            num += self.materials[mat]
        return num

    def add_store_has_bought_cnt(self, props_index):
        self.store_has_bought.setdefault(props_index, 0)
        vip_can_buy_cnt_conf = self.game_config.props_store_config['props_sale'][props_index]['vip_can_buy_cnt']

        user_property_obj = self.user_property
        vip_cur_level = user_property_obj.vip_cur_level
        print "debug guochen", self.store_has_bought.get(props_index, 0), vip_can_buy_cnt_conf.get(str(vip_cur_level), 0)
        if self.store_has_bought.get(props_index, 0) >= vip_can_buy_cnt_conf.get(str(vip_cur_level), 0):
            raise GameLogicError(u'购买次数已达到当前vip等级上限')
        self.store_has_bought[props_index] += 1
        self.put()

    def reset_store_has_bought_cnt(self):
        self.store_has_bought = {}
        self.put()


