#-*- coding: utf-8 -*-
""" soul.py
    该文件的主要功能函数有
    1  获取用户的所有的碎片信息 包括武将碎片和装备碎片
    2  使用武将碎片兑换武将
    3  使用装备碎片兑换装备
"""
from apps.models.user_souls import UserSouls
from apps.models.user_cards import UserCards
from apps.models.user_equips import UserEquips
from apps.common import utils
from apps.config.game_config import game_config


def get_all(rk_user, params):
    '''
    获取用户的所有的碎片信息
    miaoyichao
    '''
    user_souls_obj = UserSouls.get_instance(rk_user.uid)
    return 0, user_souls_obj.get_souls()

def get_card_souls(rk_user,params):
    '''
    获取用户的武将碎片信息
    miaoyichao
    '''
    user_souls_obj = UserSouls.get_instance(rk_user.uid)
    return 0, user_souls_obj.get_card_souls()

def get_equip_souls(rk_user,params):
    '''
    #获取用户的装备碎片信息
    miaoyichao
    '''
    user_souls_obj = UserSouls.get_instance(rk_user.uid)
    return 0, user_souls_obj.get_equip_souls()

def exchange_card(rk_user, params):
    """
    将魂卡兑换成武将
    miaoyichao
    """
    # 需要兑换的武将
    cid = params['cid']
    user_souls_obj = UserSouls.get_instance(rk_user.uid)
    user_card_obj = UserCards.get_instance(rk_user.uid)
    needed_souls = int(game_config.card_config[cid]['souls_needed'])
    #   将魂不足
    if not user_souls_obj.is_normal_soul_enough(cid,needed_souls):
        return 11, {'msg': utils.get_msg('soul','not_enough_soul')}
    #减武将碎片
    user_souls_obj.minus_card_soul(cid, needed_souls, 'soul_exchange_card')
    # 加武将
    success_fg, p1, ucid, is_first = user_card_obj.add_card(cid, where='soul_exchange_card')
    new_card = {
        'ucid':ucid,
        'is_first':is_first,
    }
    new_card.update(user_card_obj.get_card_dict(ucid))
    return 0, {
                'new_card': new_card,
    }

def tranform_equip_soul_to_equip(rk_user, params):
    """将装备碎片 合成 装备
        params： euqip_id
        必须集齐这个装备所有的碎片类型才能合成
    """
    equip_id = params['equip_id']
    user_souls_obj = UserSouls.get_instance(rk_user.uid)
    equip_type = int(game_config.equip_config.get(equip_id,{}).get('eqtype',7))

    if 1<=equip_type<=4:
        #处理普通装备的合成
        needed_souls = int(game_config.equip_config[equip_id]['need_souls'])
        if user_souls_obj.is_equip_soul_enough(equip_id,needed_souls):
            #添加装备 
            user_equip_obj = UserEquips.get(rk_user.uid)
            fg, all_equips_num, ueid, is_first = user_equip_obj.add_equip(equip_id, 'tranform_equip_soul_to_equip')
            data = {}
            if fg:
                tmp = {
                       'ueid':ueid,
                       'is_first':is_first,
                    }
                tmp.update(user_equip_obj.get_equip_dict(ueid))
                data['equips'] = tmp
            #删除碎片
            user_souls_obj.minus_equip_soul(equip_id,needed_souls)
            #结果返回
            return 0, data
        else:
            return 11, {'msg': utils.get_msg('pack','not_enough_material')}
    elif 5<=equip_type<=6:
        #处理宝物的合成
        need_soul_types_num = game_config.equip_config[equip_id].get('need_soul_types_num', 0)
        all_equips = [equip_id+'_'+str(i) for i in xrange(1,need_soul_types_num + 1)]
        #获取需要多少份碎片
        needed_souls = int(game_config.equip_config[equip_id].get('need_souls',1))
        #判断碎片是否足够
        for need_equip in all_equips:
            if not user_souls_obj.is_equip_soul_enough(need_equip,needed_souls):
                return 11, {'msg': utils.get_msg('pack','not_enough_material')}
        # 消耗  装备碎片
        for need_equip in all_equips:
            user_souls_obj.minus_equip_soul(need_equip, 1, 'tranform_equip_soul_to_equip')
        # 加 装备
        user_equip_obj = UserEquips.get(rk_user.uid)
        fg, all_equips_num, ueid, is_first = user_equip_obj.add_equip(equip_id, 'tranform_equip_soul_to_equip')
        data = {}
        if fg:
            tmp = {
                   'ueid':ueid,
                   'is_first':is_first,
                }
            tmp.update(user_equip_obj.get_equip_dict(ueid))
            data['equips'] = tmp
        #判断新手引导
        newbie_step = int(params.get('newbie_step',0))
        if newbie_step:
            rk_user.user_property.set_newbie_steps(newbie_step, "tranform_equip_soul_to_equip")
        return 0, data
    else:
        return 11, {'msg': utils.get_msg('pack','not_enough_material')}
