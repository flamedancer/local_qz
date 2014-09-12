#-*- coding: utf-8 -*-
""" vip.py
主要包括 获取vip的配置信息 VIP的配置信息  get_vip_config
检查各种需求的回复次数  以及 vip 礼包的内容
"""
import copy
import time
from apps.config.game_config import game_config
from apps.models.user_property import UserProperty
from apps.models.user_gift import UserGift
from apps.common import utils

def get_vip_config(rk_user,params):
    '''
    * 获取vip的配置信息
    * miaoyichao
    '''
    data = {}
    data['vip_config'] = game_config.user_vip_conf
    return 0,data

def check_limit_recover(rk_user,where,dtype=None):
    '''
    * 根据用户的vip等级判断用户当天是否达到回复次数
    * miaoyichao
    '''
    #获取用户的属性信息
    user_property_obj = UserProperty.get(rk_user.uid)
    vip_lv = user_property_obj.vip_cur_level
    today_str = utils.get_today_str()
    if today_str == user_property_obj.property_info['recover_times']['today_str']:
        if where in ['recover_stamina','recover_pvp_stamina','recover_mystery_store','recover_copy']:
            #回复体力的处理
            recover_stamina_times = game_config.user_vip_conf[str(vip_lv)].get('can_'+where+'_cnt',10)
            if recover_stamina_times > user_property_obj.property_info['recover_times'][where]:
                return True
            else:
                return False
        elif where == 'recover_copy':
            #重置战场的处理
            recover_times = game_config.user_vip_conf[str(vip_lv)].get('can_'+where+'_cnt',{}).get(dtype,5)
            if recover_times > user_property_obj.property_info['recover_times'][where].get(dtype,0):
                return True
            else:
                return False
        else:
            #不在那些要检测的里面 可以无限制刷新
            return True
    else:
        #重置时间和副本次数
        user_property_obj.reset_recover_times()
        return True

def vip_gift_sale_list(uid):
    '''
    vip用户礼包列表
    '''
    data = {}
    user_property_obj = UserProperty.get_instance(uid)
    user_gift_obj = UserGift.get_instance(uid)
    vip_charge_info = user_property_obj.property_info['vip_charge_info']
   #读取商店vip礼包配置
    vip_gift_sale_config = game_config.shop_config.get('vip_gift_sale',{})
    if vip_gift_sale_config:
        #vip礼包格式化函数
        data = user_gift_obj.vip_gift_format(vip_gift_sale_config,vip_charge_info)
    return data


def test(uid):
    '''
    格式化礼包信息
    '''
    data = {}
    #获取用户属性信息
    user_property_obj = UserProperty.get(uid)
    #获取已经购买的 vip 礼包的 id
    vip_charge_info = user_property_obj.property_info['vip_charge_info']
    #获取 vip 礼包的配置
    vip_gift_sale_conf = game_config.shop_config.get('vip_gift_sale',{})
    for vip_lv in vip_gift_sale_conf:
        #遍历 所哟 vip 等级礼包内容
        data = format_vip_gift(data,vip_lv,vip_gift_sale_conf,vip_charge_info)
    print data 


def format_vip_gift(data,vip_lv,vip_gift_sale_conf,vip_charge_info):
    '''
    格式化vip等级礼包的信息
    '''
    data[vip_lv] = {}
    #获取购买的价格
    coin = vip_gift_sale_conf[vip_lv].get('coin',0)
    #获取礼包内容
    gift = vip_gift_sale_conf[vip_lv].get('gift',{})
    tmp = {}
    for gift_info in gift:
        #遍历礼包内容
        if gift_info:
            gift_id , num = gift_info
            #碎片
            if 'soul' in gift_id:
                gift_id = gift_id.replace('_soul','')
                if 'soul' not in tmp:
                    tmp['soul'] = {}
                if gift_id not in tmp['soul']:
                    tmp['soul'][gift_id] = 0
                tmp['soul'][gift_id] += num
            else:
                return_type = gift_id.split('_')[1]
                if return_type not in tmp:
                    tmp[return_type] = {}
                if gift_id not in tmp[return_type]:
                    tmp[return_type][gift_id] = 0
                tmp[return_type][gift_id] += num
    if 'mat' in tmp:
        tmp['materils'] = tmp['mat']
        tmp.pop('mat')
    data[vip_lv]['coin'] = coin
    data[vip_lv]['gift'] = tmp
    data[vip_lv]['has_buy'] = vip_lv in vip_charge_info
    return data