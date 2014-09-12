#!/usr/bin/env python
# encoding: utf-8

"""
掠夺系统：
功能1. 返回对手列表
        a. 根据玩家需要掠夺的装备碎片，显示符合要求对手。
        b. 对手应该拥有该装备碎片
        c. 只显示和自己相同等级段的玩家
        b. 若没有足够符合条件玩家，则从c中玩家选作为ai返回                      
功能2. 进入掠夺战斗
功能3. 退出掠夺战斗
        a. 若胜利，根据概率判断是否掠夺对手碎片 
"""
import random
import datetime

from apps.models.equip_soul_user import EquipSoulUser
from apps.models.user_base import UserBase
from apps.models.user_cards import UserCards
from apps.common import utils
from apps.models import data_log_mod
from apps.config.game_config import game_config
from apps.models.user_souls import UserSouls
from apps.models.level_user import LevelUser


def __get_suitable_users(rk_user, params):
    equip_id = params['equip_id']
    equip_soul_type = params['equip_soul_type']
    soul_uids = EquipSoulUser.get_instance(equip_id, equip_soul_type).users
    lv_uids = LevelUser.get_instance(rk_user.subarea, rk_user.user_property.lv_region).users
    suitable_users = (set(soul_uids) & set(lv_uids)).discard(rk_user.uid)

    if not suitable_users:
        return ['npc']
    if len(suitable_users) > 4:
        suitable_users = random.sample(suitable_users, 4)
    return suitable_users


def get_rob_opponents(rk_user, params):
    """params参数：
        equip_id:  装备id
        equip_soul_type: 碎片类型序号
    """
    data = {'candidates': []}
    # 掠夺的时间不能在 禁止的范围内, 返回空的对手列表
    cannot_rob_time = game_config.rob_config.get('cannot_rob_time', ('00:00', '00:00'))
    now_min_secord = datetime.datetime.now().strftime('%H:%M')
    if cannot_rob_time[0] <= now_min_secord <= cannot_rob_time[1]:
        return 0, data
    
    suitable_users = __get_suitable_users(rk_user, params)
    if suitable_users == ['npc']:
        opponent_data = {}
        opponent_data = _npc_opponents(rk_user)
        data['candidates'].append(opponent_data)
        return 0, data
    for candidate in suitable_users:
        opponent_data = {}
        opponent_user_base_obj = UserBase.get(candidate)
        opponent_data['user_name'] = opponent_user_base_obj.username
        opponent_data['opponent_uid'] = candidate
        opponent_data['deck'] = opponent_user_base_obj.user_cards.get_deck_info()
        opponent_data['user_lv'] = opponent_user_base_obj.user_property.lv
        data['candidates'].append(opponent_data)
    return 0, data


def __can_rob(rk_user, params):
    """检查是否可以pvp
    """
    #检查是否重新编队
    if params.get("new_deck"):
        from apps.logics import card as cardmod
        rc, msg = cardmod.set_decks(rk_user, params)
        if rc :
            return msg
    #检查用户武将数量是否已经超过上限
    user_card_obj = UserCards.get(rk_user.uid)
    if user_card_obj.arrive_max_num():
        return utils.get_msg('card','max_num')
    #检查用户统御力是否超出
    if user_card_obj.arrive_max_cost():
        return utils.get_msg('card','over_cost')
    #减少竞技点
    if rk_user.user_pvp.pvp_stamina <= 0:
        return utils.get_msg('pvp','pvp_stamina_not_enough')

    # 不能掠夺已经拥有的碎片
    self_user_soul = UserSouls.get(rk_user.uid)
    if self_user_soul.is_equip_soul_enough(params['equip_id'], params['equip_soul_type'], 1):
        return "already has this equip_soul"
    # 掠夺的时间不能在 禁止的范围内
    cannot_rob_time = game_config.rob_config.get('cannot_rob_time', ('00:00', '00:00'))
    now_min_secord = datetime.datetime.now().strftime('%H:%M')
    if cannot_rob_time[0] <= now_min_secord <= cannot_rob_time[1]:
        return "cannot rob this time"
    return ""


def __check_start(rk_user, params):
    can_rob_msg = __can_rob(rk_user, params)
    if can_rob_msg:
        return 11, can_rob_msg

    if params['opponent_uid'] not in __get_suitable_users(rk_user, params):
        return 11, utils.get_msg('pvp', 'invalid_opponent')

    return 0, ""


def __check_end(rk_user, params):
    can_rob_msg = __can_rob(rk_user, params)
    if can_rob_msg:
        return 11, can_rob_msg

    if params['opponent_uid'] != rk_user.user_pvp.get_pvp_vs_player():
        return 11, utils.get_msg('pvp', 'invalid_opponent')

    return 0, ""


def start(rk_user, params):
    """params参数：
        opponent_uid：  对手  uid
        equip_id:  装备id
        equip_soul_type: 碎片类型序号
    """
    rc,msg = __check_start(rk_user,params)
    if rc:
        return rc, {'msg': msg,}
    #对手id
    opponent_uid = params['opponent_uid']
    print 'rob_debug', rk_user.user_pvp.pvp_stamina
    #扣除玩家的pvp耐力值
    rk_user.user_pvp.minus_pvp_stamina(1)

    #记录下挑战的对手id，在出战场的时候用于验证
    rk_user.user_pvp.set_pvp_vs_player(opponent_uid)

    log_data = {}
    
    log_data['uid'] = rk_user.uid
    log_data['type'] = 'rob'
    log_data['statament'] = 'start'
    log_data['card_deck'] = rk_user.user_cards.deck
    log_data['subarea'] = rk_user.subarea
    log_data['opponent_uid'] = opponent_uid
    log_data['renown'] = rk_user.user_pvp.get_renown()
    data_log_mod.set_log('PvpRecord', rk_user, **log_data)
    print 'rob_debug', rk_user.user_pvp.pvp_stamina
    return 0, log_data


def end(rk_user, params):
    """params参数：
        opponent_uid：  对手  uid
        equip_id:  装备id
        equip_soul_type: 碎片类型序号
        self_result：  win or lose
    """

    equip_id, equip_soul_type = params['equip_id'], params['equip_soul_type']
    self_result = params.get('self_result','win')  # win or lose

    log_data = {}
    log_data['uid'] = rk_user.uid
    log_data['type'] = 'rob'
    log_data['user_level'] = rk_user.user_property.lv
    log_data['statament'] = 'end'
    log_data['card_deck'] = rk_user.user_cards.deck
    log_data['subarea'] = rk_user.subarea
    log_data['reuslt'] = self_result
    log_data['opponent_uid'] = params['opponent_uid']
    log_data['get_equip_soul'] = None
    log_data['renown'] = rk_user.user_pvp.get_renown()


    return_data = {
        'get_equip_soul': None,
    }

    # 失败 或 人品不够 时，夺不到装备碎片
    get_equip_soul_rate = get_equip_soul_rate_when_win(equip_id, params['opponent_uid'])
    print 'rob_debug', self_result, get_equip_soul_rate
    if self_result == 'lose' or random.random() > get_equip_soul_rate:
        data_log_mod.set_log('PvpRecord', rk_user, **log_data)
        print 'rob_debug not get', return_data
        return 0, return_data

    # 获得 对手的 装备碎片  1个
    self_user_soul = UserSouls.get(rk_user.uid)
    self_user_soul.add_equip_soul(equip_id, equip_soul_type, 1)
    log_data['get_equip_soul'] = ':'.join([equip_id, equip_soul_type])
    if params['opponent_uid'] != 'npc':
        # 对手的装备碎片  减1
        opponent_user_soul = UserSouls.get(params['opponent_uid'])
        opponent_user_soul.del_equip_soul(equip_id, equip_soul_type, 1)
    return_data['get_equip_soul'] = log_data['get_equip_soul']
    data_log_mod.set_log('PvpRecord', rk_user, **log_data)
    print 'rob_debug get', return_data
    return 0, return_data


def get_equip_soul_rate_when_win(equip_id, opponent_uid):
    equip_star = str(game_config.equip_config[equip_id]['star'])
    if opponent_uid == 'npc':
        rate_conf = game_config.rob_config.get('get_player_equip_soul_rate', {})
    else:
        rate_conf = game_config.rob_config.get('get_npc_equip_soul_rate', {})
    return rate_conf.get(equip_star, 0)


def _npc_opponents(rk_user):
    npc_data = {}

    lv = rk_user.user_property.lv
    npc_config = game_config.rob_config.get('npc', {})
    this_lv_npc_conf = {}
    suitable_gap = utils.between_gap(lv, npc_config)

    this_lv_npc_conf = npc_config[suitable_gap]
    npc_data['user_lv'] = random.randrange(suitable_gap[0], suitable_gap[1] + 1)

    deck = []
    for index in range(1, 6):
        dfs_index = 'deck%s_for_star' % index
        star = str(this_lv_npc_conf[dfs_index])
        clist = [cid for cid in game_config.card_config 
        if game_config.card_config[cid].get('star', '1') == star and 
        not game_config.card_config[cid].get('category', '') in ['7', '8']]
        

        card_info = {
            "category": "4",
            "exp": 0,
            "cid": "1_card",
            "upd_time": 1395231243,
            "lv": 1,
            "eid": "",
            "sk_lv": 1
        }
        card_info['cid'] = random.choice(clist)
        card_info['category'] = game_config.card_config[card_info['cid']].get('category', '')
        cards_lv_range = this_lv_npc_conf['cards_lv']
        card_info['lv'] = random.randrange(cards_lv_range[0], cards_lv_range[1] + 1)
        deck.append(card_info)

    # 设置编队队长
    leader_index = random.randint(0, len(deck) - 1)
    deck[leader_index]['leader'] = 1

    npc_data['user_name'] = 'NPC'
    npc_data['opponent_uid'] = 'npc'
    npc_data['deck'] = deck
    return npc_data


