#!/usr/bin/env python
# encoding: utf-8
"""
user_souls.py
"""

from apps.models import data_log_mod
from apps.models import GameModel


class UserSouls(GameModel):
    """
    用户魂卡信息
    """
    pk = 'uid'
    fields = ['uid', 'normal_souls', 'equip_souls_info']

    def __init__(self):
        """初始化用户魂卡信息

            normal_souls: 普通将魂  {soul_id: num ,...} 
                          因为特定的魂卡只能换特定的将， 所以可以用 cid 来表示soul_id

            equip_souls_info:  装备碎片的信息：  {equip_id: {num: num}}
        """
        self.uid = None
        self.normal_souls = {}
        self.equip_souls_info = {}

    @classmethod
    def get_instance(cls, uid):
        obj = super(UserSouls, cls).get(uid)
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
        uc.normal_souls = {}
        return uc

    def get_souls(self):
        """
        获得平台UID 所有的普通将魂dict和装备的碎片
        miaoyichao
        """
        return {
            'normal_souls': self.normal_souls,
            'equip_souls_info': self.equip_souls_info,
            }

    def get_card_souls(self):
        '''
        获取武将的魂碎片
        miaoyichao
        '''
        return {'card_souls':self.normal_souls}

    def get_equip_souls(self):
        '''
        获取装备的魂碎片
        '''
        data = {'equip_souls_info': self.equip_souls_info}
        return data

    def get_normal_soul_num(self, soul_id):
        '''
        获取武将碎片的数量
        输入 soul_id 
        输出 num
        '''
        return self.normal_souls.get(soul_id, {}).get('num', 0)

    def get_equip_soul_num(self, equip_id):
        '''
        获取装备(宝物)碎片的数量
        输入 soul_id 
        输出 num
        '''
        return self.equip_souls_info.get(equip_id, {}).get('num', 0)

    def add_normal_soul(self, soul_id, num, where=None):
        """
        添加武将碎片
        输入  碎片 id 数量
        输出 保存成功与否 碎片 id 数量
        """
        num = abs(num)
        #  判断魂卡id是否存在
        #  card_config没有配souls_needed或者配的是0
        if self.game_config.card_config[soul_id].get('souls_needed', 0) == 0:
            return False,'',0
        if soul_id in self.normal_souls:
            self.normal_souls[soul_id]['num'] += num
        else:
            self.normal_souls[soul_id] = {'num': num}
        self.put()
        if where:
            log_data = {
                'where':where, 
                'soul_id':soul_id,
                'num': num,
            }
            data_log_mod.set_log('SoulProduct', self, **log_data)
        return True, soul_id, num

    def add_equip_soul(self, soul_id, num, where=None):
        """
        添加装备碎片 
        输入 碎片 id 数量
        输出 成功标志 碎片 id 数量
        """
        num = abs(num)
        #获取长度
        soul_id_split_len = len(soul_id.split('_'))
        if 2<=soul_id_split_len<=3:
            #符合要求的长度
            if soul_id_split_len == 2:
                #普通装备
                check_id = soul_id
            else:
                #宝物装备
                check_id = '%s_%s' %(soul_id.split('_')[0],soul_id.split('_')[1])
        else:
            #不符合要求
            return False,'',0
        #判断 equip_id 是否存在配置中, 并且可以用碎片合成（有need_souls且不为0）
        if not self.game_config.equip_config.get(check_id, {}).get('need_souls'):
            return False,'',0
        #判断equip_souls_info 是否为空
        if not self.equip_souls_info:
            self.equip_souls_info = {}
        #装备 id 是否已经存在
        if soul_id in self.equip_souls_info:
            self.equip_souls_info[soul_id]['num'] += num
        else:
            self.equip_souls_info[soul_id] = {'num': num}
        #数据保存
        self.put()
        if where:
            #写日志
            log_data = {
                'where':where,
                'soul_id':soul_id,
                'num': num,
            }
            data_log_mod.set_log('SoulProduct', self, **log_data)
        return True, soul_id, num

    def is_normal_soul_enough(self, soul_id, num):
        """
        判断武将碎片是否足够 
        输入 碎片id 数量
        输出 True or False 
        """
        return self.get_normal_soul_num(soul_id) >= abs(num)

    def is_equip_soul_enough(self, equip_id, num):
        """
        判断装备(宝物)碎片是否足够 
        输入 碎片id 类型 数量
        输出 True or False 
        """
        return self.get_equip_soul_num(equip_id) >= abs(num)

    def minus_card_soul(self, soul_id, num, where=None):
        """
        删除武将碎片 
        输入 碎片id 数量
        输出 True or False 
        """
        num = abs(num)
        if num == 0:
            return False
        if self.is_normal_soul_enough(soul_id, num):
            #  判断魂卡id是否存在
            #  card_config没有配souls_needed或者配的是0
            if self.game_config.card_config[soul_id].get('souls_needed', 0) == 0:
                return False
            self.normal_souls[soul_id]['num'] -= num
            if self.normal_souls[soul_id]['num'] <= 0:
                self.normal_souls.pop(soul_id)
        else:
            return False
        self.put()

        if where:
            log_data = {
                'where': where,
                'soul_id': soul_id,
                'num': num,
            }
            data_log_mod.set_log('SoulConsume', self, **log_data)
        return True

    def minus_equip_soul(self, soul_id, num, where=None):
        """
        删除装备碎片
        输入 碎片id 数量
        输出 True or False 
        """
        num = abs(num)
        if num == 0:
            return False
        if self.is_equip_soul_enough(soul_id, num):
            self.equip_souls_info[soul_id]['num'] -= num
            if self.equip_souls_info[soul_id]['num'] <= 0:
                self.equip_souls_info.pop(soul_id)
        else:
            return False
        self.put()
        #写日志
        if where:
            log_data = {
                'where': where,
                'soul_id': soul_id,
                'num': num,
            }
            data_log_mod.set_log('SoulConsume', self, **log_data)
        return True


