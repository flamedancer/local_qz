#!/usr/bin/env python
# encoding: utf-8
"""
user_equips.py
"""
import copy

import time
from apps.models.user_collection import UserCollection
from apps.common.utils import create_gen_id

from apps.models import data_log_mod
from apps.models import GameModel
from apps.common import utils

class UserEquips(GameModel):
    """
    用户游戏内部基本信息
    """
    pk = 'uid'
    fields = ['uid','equips']
    def __init__(self):
        """初始化用户游戏内部基本信息

        Args:
            uid: 用户游戏ID
            data:游戏内部基本信息
        """
        self.uid = None
        self.equips = {}

    @classmethod
    def get_instance(cls,uid):
        '''
        获取用户装备对象的内容
        '''
        obj = super(UserEquips,cls).get(uid)
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
        '''
        创建用户装备对象
        '''
        ue = cls()
        ue.uid = uid
        ue.equips = {}
        return ue

    def get_equips(self):
        """
        获得平台UID 对应的用户对象
        """
        return copy.deepcopy(self.equips)

    def get_equip_dict(self,ueid):
        """获取用户装备信息，字典结构
        """
        equip_info = copy.deepcopy(self.equips[ueid])
        return equip_info

    def has_equip(self, ueid):
        """判断用户是否有
        """
        return ueid in self.equips.keys()

    def get_equips_num(self):
        """
        获取用户的装备数
        """
        return len(self.equips)

    def add_equip(self,eid,where=None):
        """
        增加装备
        """
        addret,ueid,is_first = self.__add_equip(eid)
        if addret and where:
            log_data = {'where': where,
                        'equip_dict': self.get_equip_dict(ueid),
                        'name': self.game_config.equip_config[eid]['name'],
                        'user_lv': self.user_property.lv,
            }
            data_log_mod.set_log('EquProduct', self, **log_data)
        all_equips_num = self.get_equips_num()
        return True,all_equips_num,ueid,is_first

    def __add_equip(self,eid):
        """
        装备增加
        """
        ueid = create_gen_id()
        is_first = False
        ret = False
        if not self.equips.has_key(ueid):
            #获取装备的star和基础经验
            star = self.game_config.equip_config[eid].get('star',2)
            eqtype = self.game_config.equip_config[eid]['eqtype']
            #因为普通装备的经验和金钱是等价的所以这里使用common_gold
            if eqtype<=4:
                base_exp = self.game_config.equip_exp_conf['common_gold'].get('1',500)
                coefficient = self.game_config.equip_exp_conf['common_gold_coe'].get(str(star),1)
            else:
                base_exp = self.game_config.equip_exp_conf['treasure_exp'].get('1',50)
                coefficient = self.game_config.equip_exp_conf['treasure_exp_coe'].get(str(star),1)
            #系数coefficient
            real_exp = int(base_exp*coefficient)
            #取得卡片的技能ID
            self.equips[ueid] = {
                            'eid':eid,
                            'upd_time':int(time.time()),
                            'used_by':'',
                            'cur_lv':1,
                            'cur_experience':real_exp,
                            }
            is_first = UserCollection.get_instance(self.uid).add_collected_card(eid,'equips')
            ret = True
            self.put()
        return ret,ueid,is_first

    def add_equips(self,eid,num,where=None):
        '''
        *批量添加装备
        '''
        for i in xrange(num):
            self.add_equip(eid,where)
        self.put()

    def is_used(self,ueid):
        """
        是否被使用
        """
        if ueid in self.equips:
            return self.equips[ueid].get('used_by','')
        else:
            return ''

    def delete_equip(self,ueids,where=None):
        """
        删除装备
        """
        pt_fg = False
        for ueid in ueids:
            if ueid in self.equips:
                if where:
                    equip_dict = self.get_equip_dict(ueid)
                    eid = equip_dict['eid']

                    log_data = {'where': where,
                        'equip_dict': equip_dict,
                        'name': self.game_config.equip_config[eid]['name'],
                        'user_lv': self.user_property.lv,
                    }

                    data_log_mod.set_log('EquConsume', self, **log_data)
                self.equips.pop(ueid)
                pt_fg = True
        if pt_fg:
            self.put()



    def get_equips_exp(self,cost_params_list):
        '''
        * 获取装备列表的经验值
        '''
        up_exp = 0
        for cost in cost_params_list:
            up_exp += self.equips[cost]['cur_experience']
        up_exp = up_exp * self.game_config.equip_exp_conf['gold_exp_transform_coe'].get('1',100)
        return int(up_exp)

    
    def is_same_equip_type(self,equip_card_list,eqtype):
        '''
        * 检查装备是否是同一类型的
        * miaoyichao
        * 2014-03-26
        '''
        return_flag = 1
        try:
            for ueid in equip_card_list:
                #获取ueid的eid
                eid = self.equips[ueid]['eid']
                #根据eid获取该装备的类型
                cur_eqtype = self.game_config.equip_config[eid]['eqtype']
                #判断类型是否一致  一般情况下前台传递的数据时正确的  不排除伪造数据
                if eqtype == cur_eqtype:
                    pass
                else:
                    return_flag = 0
                    break
        except:
            return_flag = 0
        #结果返回
        return return_flag

    def del_equip(self,equip_card_dict):
        '''
        * miaoyichao
        * 卸载装备
        '''
        for ueid in equip_card_dict:
            self.equips[ueid]['used_by'] = ''
        self.put()

    def unbind_equip(self,ucid):
        '''
        解锁该武将的所有的装备
        input : ucid
        output : None
        '''
        put_flag = False
        for ueid in self.equips:
            if ucid == self.equips[ueid]['used_by']:
                self.equips[ueid]['used_by'] = ''
                put_flag = True
        if put_flag:
            self.put()


    def bind_equip(self,ucid,bind_ueids):
        '''
        绑定武将的装备
        input ucid ueids
        output None
        {
            'eid':eid,
            'upd_time':int(time.time()),
            'used_by':'',
            'cur_lv':1,
            'cur_experience':0
        }
        '''
        self.unbind_equip(ucid)
        for ueid in bind_ueids:
            self.equips[ueid]['used_by'] = ucid
        self.put()

    def remove_equip_user(self,ueid,rm_type,rm_user):
        '''
        * miaoyichao
        * 去除该装备类型的user
        '''
        put_flag = 0

        #遍历装备
        for ueid_check in self.equips:
            used_by_check = self.equips[ueid_check]['used_by']
            eid_check = self.equips[ueid_check]['eid']
            eqtype_check = self.game_config.equip_config[eid_check]['eqtype']
            #类型一致的时候
            if eqtype_check==rm_type:
                if ueid == ueid_check:
                    pass
                else:
                    #绑定用户相同的时候
                    if used_by_check == rm_user:
                        self.equips[ueid_check]['used_by'] = ''
                        put_flag=1
        #判断是否需要保存修改
        if put_flag:
            self.put()
        
    def get_can_use_ueids(self,eid):
        """
        获取到可以使用的装备数量
        """
        unused_ueids = [ueid for ueid in self.equips if self.equips[ueid]['eid']==eid and not self.equips[ueid].get('used_by')]
        return unused_ueids

    #锁定装备
    def lock(self,ueids):
        """
        锁定装备
        """
        pt_fg = False
        for ueid in self.equips:
            #查找装备是否被锁定
            if ueid in ueids:
                if not self.equips[ueid].get('lock',False):
                    self.equips[ueid]['lock'] = True
                    pt_fg = True
            else:
                if self.equips[ueid].get('lock',False):
                    self.equips[ueid]['lock'] = False
                    pt_fg = True
        if pt_fg:
            self.put()

    def is_locked(self,ueids):
        """
        ueids中如果有一个被锁定即返回True
        """
        for ueid in ueids:
            if self.equips[ueid].get('lock',False):
                return True
        return False

    def auto_update_equip(self,rk_user,base_ueid,vip_lv,user_lv,where=None):
        '''
        自动添加装备经验和扣除金币
        '''

        data = {}
        data_lv = []
        ueid_info = copy.deepcopy(self.equips[base_ueid])
        #该装备当前等级
        old_lv = ueid_info['cur_lv']
        game_config = self.game_config
        max_lv = game_config.equip_config[ueid_info['eid']].get('equipMaxLv',200)
        #获取装备的星级
        star = game_config.equip_config[ueid_info['eid']].get('star',2)
        for lv in xrange(old_lv,max_lv + 1):
            if old_lv >= 2 * user_lv:
                break
            elif old_lv >= max_lv:
                break
            else:
                cur_cost_gold = game_config.equip_exp_conf['common_gold'].get(str(old_lv),0)
                next_cost_gold = game_config.equip_exp_conf['common_gold'].get(str(old_lv + 1),100)
                #获取系数
                coefficient =  game_config.equip_exp_conf['common_gold_coe'][str(star)]
                #计算下一级所需到金钱
                update_gold = int((next_cost_gold - cur_cost_gold) * coefficient)
                #判断用户金币是否足够
                if not rk_user.user_property.is_gold_enough(update_gold):
                    break
                #添加装备经验
                self.add_com_equip_exp(base_ueid,vip_lv,user_lv,where)
                #扣除消费的金币
                rk_user.user_property.minus_gold(update_gold,'common_equip_update')
                equip_level = self.equips[base_ueid]['cur_lv']
                data_lv.append(equip_level)
                old_lv = equip_level
        data['up_lv'] = data_lv
        new_equip_info = {'ueid':base_ueid}
        new_equip_info.update(self.equips[base_ueid])
        data['new_equip_info'] = new_equip_info
        return data


    def add_com_equip_exp(self,ueid,vip_lv,user_lv,where=None):
        """
        增加装备经验值
        args:
            ueid:装备的唯一id
            exp:所要增加的经验值 也就是金币数目
        return:
            {
            }
        """
        equip = copy.deepcopy(self.equips[ueid])
        #获取该装备的最大的等级
        max_lv = self.game_config.equip_config[equip['eid']].get('equipMaxLv',3)
        crit_list = self.game_config.user_vip_conf[str(vip_lv)].get('crit')
        crit = utils.windex(crit_list)
        old_lv = equip['cur_lv']
        new_lv = old_lv + crit
        #不能大于当前用户和最大等级的2倍
        user_equip_max_lv = 2*user_lv
        if max_lv >=user_equip_max_lv:
            max_lv = user_equip_max_lv
        #判断要升的级数是不是大于可以升的级数
        if new_lv>=max_lv:
            new_lv = max_lv

        #装备升级 写日志
        if old_lv < new_lv and where:
            equip_msg = {
                'old_experience': equip['cur_experience'],
                'old_lv': old_lv,
                'new_experience': self.game_config.equip_exp_conf['common_gold'][str(new_lv)],
                'new_lv': new_lv,
            }

            log_data = {
                'where':where,
                'eid':equip['eid'],
                'equip_msg': equip_msg,
            }

            data_log_mod.set_log('EquProduct', self, **log_data)
        #获取装备的星级
        star = self.game_config.equip_config[equip['eid']].get('star',2)
        #获取系数
        coefficient = self.game_config.equip_exp_conf['common_gold_coe'][str(star)]

        #修改经验和等级
        self.equips[ueid]['cur_lv'] = new_lv
        self.equips[ueid]['upd_time'] = int(time.time())
        self.equips[ueid]['cur_experience'] = int(self.game_config.equip_exp_conf['common_gold'][str(new_lv)]*coefficient)
        #处理返回的数据
        data = {'ueid':ueid}
        data.update(self.equips[ueid])
        self.put()
        return data


    def add_treasure_equip_exp(self,base_ueid,up_exp,user_lv,where=None):
        '''
        * 给宝物添加经验和等级
        * miaoyichao
        * input:base_equip up_exp user_lv where
        * output:None
        '''
        equip = copy.deepcopy(self.equips[base_ueid])
        #获取该装备的最大的等级
        max_lv = min(self.game_config.equip_config[equip['eid']].get('equipMaxLv',3),2*user_lv)
        #获取装备的星级
        star = self.game_config.equip_config[equip['eid']].get('star',2)
        #获取系数 百分位的
        coefficient =  self.game_config.equip_exp_conf['treasure_exp_coe'][str(star)]
        old_lv = equip['cur_lv']
        old_experience = equip['cur_experience']
        all_exp = old_experience + up_exp
        #如果需要升级的话 当前等级
        can_up_lv = old_lv
        #计算所能升的最大的等级
        for lv in xrange(old_lv,max_lv+1):
            try:
                cur_lv_exp = int(self.game_config.equip_exp_conf['treasure_exp'][str(lv)]*coefficient)
                if cur_lv_exp<=all_exp:
                    can_up_lv = lv
                else:
                    continue
            except:
                pass
        #计算新的等级
        new_lv = can_up_lv 
        #判断要升的级数是不是大于可以升的级数
        if new_lv>=max_lv:
            #新的等级设置为最大
            new_lv = max_lv
            #新的经验设置为最大
            all_exp = int(self.game_config.equip_exp_conf['treasure_exp'][str(new_lv)]*coefficient)

        new_experience = all_exp
        #装备升级 写日志
        if old_lv < new_lv and where:
            equip_msg = {
                'old_experience': old_experience,
                'old_lv': old_lv,
                'new_experience': new_experience,
                'new_lv': new_lv,
            }
  
            log_data = {
                'where':where,
                'eid':equip['eid'],
                'equip_msg': equip_msg,
            }

            data_log_mod.set_log('EquProduct', self, **log_data)
        #修改经验和等级
        self.equips[base_ueid]['cur_lv'] = new_lv
        self.equips[base_ueid]['upd_time'] = int(time.time())
        self.equips[base_ueid]['cur_experience'] = new_experience
        data = {'ueid':base_ueid}
        data.update(self.equips[base_ueid])
        self.put()
        return data
        
    # @property
    # def user_base(self):
    #     if not hasattr(self, '_user_base'):
    #         from apps.models.user_base import UserBase
    #         self._user_base = UserBase.get(self.uid)
    #     return self._user_base
