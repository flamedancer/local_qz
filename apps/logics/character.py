# encoding: utf-8
"""
file: apps/logics/character.py
start: 2015-03-01
"""
import copy
from apps.common import tools
from apps.common import utils
from apps.config.game_config import game_config
from apps.common.exceptions import GameLogicError


def get_talent_info(rk_user, params):
    '''获取玩家天赋信息'''
    data = {}

    uc = rk_user.user_character
    data['fb_star'] = rk_user.user_dungeon.total_got_star            # 副本星数
    data['star_num'] = uc.star_num  # 可用星数
    data['talent_tree'] = uc.cur_talent
    #data['talent_tree'] = __filter(uc.cur_talent)
    data['refresh_times'] = uc.refresh_times
    data['refresh_cost_coin'] = __get_cost_coin(rk_user)
    return 0, data


def __filter(talent_tree):
    '''
    返回给前端的数据作处理

    '''
    data = copy.deepcopy(talent_tree)
    lock_layer = None  # 在lock_layer以下的层都显示未开启
    skeys = sorted(talent_tree.keys())  # 天赋层>=10层时 不能这样写了 因为排序是'1' '10' '2' ....
    # 上级天赋已学习过,这级天赋才开启,
    for layer in skeys:
        
        if not lock_layer and talent_tree[layer]['lv'] <= 0:
            lock_layer = layer

        if lock_layer:
            if int(layer) > int(lock_layer):
                data[layer]['lv'] = -1
    return data


def learn_talent(rk_user, params):
    '''学习新天赋'''
    new_talent = params['new_talent']  # 
    #page = 0                 # 现在只有一页
    conf = game_config.character_talent_config

    cost_star = conf['learn_cost_star']
    cost_gold = conf['learn_cost_gold']
    uc = rk_user.user_character
    if not uc.is_star_enough(cost_star):
        return 11,{'msg':utils.get_msg('talent','star_not_enough')}
    if not rk_user.user_property.is_gold_enough(cost_gold):
        return 11,{'msg':utils.get_msg('user', 'not_enough_gold')}

    learn_result = uc.learn_talent(new_talent)

    if learn_result == 1:
        return 11,{'msg':utils.get_msg('talent','no_this_layer')}
    if learn_result == 2:
        return 11,{'msg':utils.get_msg('talent','has_not_open')}
    if learn_result == 3:
        return 11,{'msg':utils.get_msg('talent','lv_cant_back')}
    if learn_result == 4:
        return 11,{'msg':utils.get_msg('talent','max_lv')}
    if learn_result in [5,6,7,8,9]:
        return 11,{'msg':utils.get_msg('talent','cant_close')}
    if learn_result == 10:
        return 11,{'msg':utils.get_msg('talent','error_talent_tree')}
    if learn_result == 11:
        return 11,{'msg':utils.get_msg('talent','atleast_one_zhuzi')}
    if learn_result == 12:
        return 11,{'msg':utils.get_msg('talent','cant_open_zhuzi')}
    if learn_result == 13:
        return 11,{'msg':utils.get_msg('talent','no_change')}
        
    uc.consume_star(cost_star)
    uc.consume_gold(cost_gold)
    rk_user.user_property.minus_gold(cost_gold, 'learn_character_talent')
    return get_talent_info(rk_user, params)


def refresh_talent(rk_user, params):
    '''重洗天赋'''
    cost_what = params['cost_what']
    
    # 重洗令不足
    if cost_what == 'props':
        if not rk_user.user_pack.is_props_enough('33_props', 1):
            return 11,{'msg':utils.get_msg('talent', 'refresh_token_not_enough')}
    elif cost_what == 'yuanbao':
        cost_coin = __get_cost_coin(rk_user)
        if not rk_user.user_property.is_coin_enough(cost_coin):
            return 11,{'msg':utils.get_msg('user', 'not_enough_coin')}
    else:
        pass

    rk_user.user_character.refresh_talent()

    minus_cost = {
        'props': rk_user.user_pack.minus_props('33_props', 1),
        'yuanbao': rk_user.user_property.minus_coin(cost_coin, where='refresh_talent')
    }
    minus_cost[cost_what]
    return get_talent_info(rk_user, params)


def __get_cost_coin(rk_user):
    conf = game_config.character_talent_config['refresh_cost_coin']
    refresh_times = rk_user.user_character.refresh_times
    # 有  取,    没有  取最大值
    cost_coin = conf.get( refresh_times, conf[max(conf.keys())] )

    return  cost_coin



# ------------- test --------------------------------------------

def open_talent_test(rk_user, params):
    uc = rk_user.user_character
    uc.check_open_talent()
    return get_talent_info(rk_user, params)


