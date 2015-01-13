#-*- coding: utf-8 -*-
""" filename:gacha.py
    主要是招募抽将的功能
    有消耗金币抽将和消耗元宝抽奖两种
    每一种都有单抽和连抽  连抽次数通过配置进行获取
"""
import copy
import math
import datetime
import time
from apps.models.user_cards import UserCards
from apps.common import utils, tools
from apps.models.user_gacha import UserGacha
from apps.config.game_config import game_config
from apps.common.utils import datetime_toString
from apps.models.user_marquee import UserMarquee
from apps.common.exceptions import GameLogicError

    
def __select_gacha_thing(rate_conf):
    """选择gacha的卡
        当rate_conf为dict时：rate_conf 有两层：例如free_rate， charge_rate
        当rate_conf为list时：rate_conf 只有层：类似：:[('171_card',20),('172_card',10)]
    """
    #根据配置选出武将的id
    num = 1
    if isinstance(rate_conf, dict):
        #随机选取那一层
        select_level_list = [(level_k,level_v['weight']) for level_k,level_v in rate_conf.iteritems()]
        select_level = utils.get_item_by_random_simple(select_level_list)
        rate_conf_select = copy.deepcopy(rate_conf[select_level])
        if 'weight' in rate_conf_select:
            rate_conf_select.pop('weight')
        select_level_list_second = [(level_k,level_v['weight']) for level_k,level_v in rate_conf_select.iteritems()]
        select_level_second = utils.get_item_by_random_simple(select_level_list_second)
        thing_id = rate_conf_select[select_level_second]['id']
        num = rate_conf_select[select_level_second].get('num', 1)
    elif isinstance(rate_conf, list):
        thing_id = utils.get_item_by_random_simple(rate_conf)
    #结果返回
    return thing_id, num

def __get_rate_conf(gacha_type, rk_user):
    """
    获取gacha概率配置
    gacha_type:求将类型，'gold' or 'charge' or 'free'
    """
    
    if rk_user.user_gacha.first_single_gacha and not rk_user.user_property.newbie:
        rk_user.user_gacha.set_first_single_gacha()
        return game_config.gacha_config['black_box_c']
    #连抽权重与抽将配置进行计算
    if gacha_type == 'gold':
        return game_config.gacha_config['gold_rate']

    # 第十次抽将必选这里配置的武将
    if rk_user.user_gacha.gacha_cnt == 1:
        return game_config.gacha_config['black_box']
    elif gacha_type == 'charge':
        rate_conf = game_config.gacha_config['charge_rate']
        # 如果开启了保底机制
        if is_open_safty():
            rate_conf = __safety_charge_rate(rk_user, rate_conf)
    elif gacha_type == 'free':
        rate_conf = game_config.gacha_config['free']
    return rate_conf


def gold(rk_user,params):
    """
    消耗金币抽将
    """
    user_card_obj = UserCards.get_instance(rk_user.uid)
    #需要的金币
    cost_gacha_gold = game_config.gacha_config['cost_gacha_gold']
    if not rk_user.user_property.is_gold_enough(cost_gacha_gold):
        return 11,{'msg':utils.get_msg('user','not_enough_gold')}
    rate_conf = __get_rate_conf('gold',rk_user)
    cid,clv = __select_gacha_thing(rate_conf)
    #扣除抽奖的金币
    if rk_user.user_property.minus_gold(cost_gacha_gold):
        #加卡
        success_fg,p1,ucid,is_first = user_card_obj.add_card(cid,clv,where='gacha_gold')
        new_card = {
            'ucid':ucid,
            'is_first':is_first,
        }
        new_card.update(user_card_obj.get_card_dict(ucid))
        #写入跑马灯
        user_marquee_obj = UserMarquee.get(rk_user.subarea)
        marquee_params = {
            'type': 'gacha_gold',
            'username': rk_user.username,
            'cid': cid,
        }
        user_marquee_obj.record(marquee_params)
        return 0,{'new_card':new_card}
    else:
        #金币不够
        return 11,{'msg':utils.get_msg('user','not_enough_gold')}

def gold_multi(rk_user,params):
    """
    金币gacha连抽
    """
    user_card_obj = UserCards.get_instance(rk_user.uid)
    #获取配置里面的多次抽将的次数
    multi_gacha_cnt = game_config.gacha_config.get('multi_gacha_cnt',10)
    cost_gacha_gold = int(game_config.gacha_config['cost_gacha_gold'])*int(multi_gacha_cnt)
    if not rk_user.user_property.is_gold_enough(cost_gacha_gold):
        return 11,{'msg':utils.get_msg('user','not_enough_gold')}
    #只可以进行配置要求的次数
    if rk_user.user_property.minus_gold(cost_gacha_gold):
        #抽卡
        rate_conf = __get_rate_conf('gold',rk_user)
        cards = __select_gacha_multi_cards(rate_conf, 10)
        #加卡
        new_cards = []
        for cid,clv in cards:
            success_fg,p1,ucid,is_first = user_card_obj.add_card(cid,clv, where = 'free_multi')
            new_card = {
                'ucid':ucid,
                'is_first':is_first,
            }
            new_card.update(user_card_obj.get_card_dict(ucid))
            new_cards.append(new_card)
        return 0,{'new_cards':new_cards}
    else:
        #金币不够
        return 11,{'msg':utils.get_msg('user','not_enough_gold')}

def __select_gacha_multi_cards(rate_conf, gacha_cnt):
    """
    选择gacha多连抽的卡
    """
    cards = []
    select_level_list = [(level_k,level_v['weight']) for level_k,level_v in rate_conf.iteritems()]
    for i in range(gacha_cnt):
        #获取抽奖的选卡
        select_level = utils.get_item_by_random_simple(select_level_list)
        rate_conf_select = copy.deepcopy(rate_conf[select_level])
        #将权重剔除 方便后面计算
        if 'weight' in rate_conf_select:
            rate_conf_select.pop('weight')
        select_level_list_second = [(level_k,level_v['weight']) for level_k,level_v in rate_conf_select.iteritems()]
        select_level_second = utils.get_item_by_random_simple(select_level_list_second)
        select_cards_list = rate_conf_select[select_level_second]['cards']
        select_card = utils.get_item_by_random(select_cards_list)
        #格式化返回
        if isinstance(select_card,str):
            #以前的代码  暂未发现缝合要求的格式  过段时间看 能否删除
            cid = select_card
            clv = 1
        else:
            #目前配置中有的配置格式
            cid = select_card[0]
            clv = int(select_card[1])
        cards.append((cid, clv))
    return cards

def charge(rk_user,params):
    """
    收费gacha抽将
    """
    ug = rk_user.user_gacha

    # 先尝试倒计免费时求将
    timer_rate_conf = __free_gacha(rk_user,params)
    if timer_rate_conf:
        cost_coin = 0
        rate_conf = timer_rate_conf
        # 更新免费抽的上次时间
        ug.set_last_gacha_time()
    else:
        cost_coin = game_config.gacha_config['cost_coin']
        rate_conf = __get_rate_conf('charge', rk_user)

    if not rk_user.user_property.is_coin_enough(cost_coin):
        raise GameLogicError('user', 'not_enough_coin')
    # 随机抽取， 获得武将或武将碎片
    thing_id, num = __select_gacha_thing(rate_conf)
    add_info = tools.add_things(
        rk_user, 
        [{"_id": thing_id, "num": num}],
        where="gacha"
    )
    # 扣元宝
    rk_user.user_property.minus_coin(cost_coin, 'gacha')


    # user_card_obj = UserCards.get_instance(rk_user.uid)
    # # 加卡
    # success_fg,p1,ucid,is_first = user_card_obj.add_card(cid, where='gacha_charge')
    # new_card = {
    #     'ucid':ucid,
    #     'is_first':is_first,
    # }
    # new_card.update(user_card_obj.get_card_dict(ucid))
    
    if 'card' in add_info:
        # 保底开关
        if is_open_safty():
            for card_info in add_info['card']:
                cid = card_info['cid']
                __set_safety_coin(rk_user, cid, cost_coin)
                # 写入跑马灯
                user_marquee_obj = UserMarquee.get(rk_user.subarea)
                marquee_params = {
                    'type': 'gacha_charge',
                    'username': rk_user.username,
                    'cid': cid,
                }
                user_marquee_obj.record(marquee_params)
    # cardSoul 加传  card 的星级
    elif 'cardSoul' in add_info:
        card_config = rk_user.game_config.card_config
        for card_id in add_info['cardSoul']:
            num = add_info['cardSoul'][card_id]
            star = card_config[card_id]['star']
            add_info['cardSoul'][card_id] = {'num': num, 'star': star}

    # 抽将必送的物品.
    get_things = __gacha_must_get(rk_user)

    ug.set_gacha_cnt()

    # 判断新手引导
    newbie_step = int(params.get('newbie_step',0))
    if newbie_step:
        rk_user.user_property.set_newbie_steps(newbie_step, "gacha")
    return {
        'add_info': add_info,
        'get_things': get_things,
        'gacha_cnt': ug.gacha_cnt,
    }


def __free_gacha(rk_user, params):
    """
    倒计时gacha(消耗元宝类型的  免费)
    """
    rate_conf = {}
    user_gacha_obj = UserGacha.get_instance(rk_user.uid)
    #获取下一次免费抽时间
    next_free_gacha_time = user_gacha_obj.next_free_gacha_time
    #获取当前时间
    now_time = int(time.time())
    #免费倒计时未到，则返回
    if next_free_gacha_time>now_time:
        return
    #是否是新手
    newbie = rk_user.user_property.newbie
    if newbie and 'newbie_gacha_list' in game_config.gacha_config:
        rate_conf = game_config.gacha_config['newbie_gacha_list']
    else:
        rate_conf = __get_rate_conf('free', rk_user)
    return rate_conf

def charge_multi(rk_user,params):
    """
    收费gacha多连抽
    """
    user_gacha_obj = rk_user.user_gacha
    user_card_obj = UserCards.get_instance(rk_user.uid)
    #元宝是否足够连抽
    multi_gacha_cnt = game_config.gacha_config.get('multi_gacha_cnt',10)
    cost_coin = game_config.gacha_config['cost_coin']

    
    total_cost_coin = cost_coin * multi_gacha_cnt * game_config.gacha_config['multi_discount'] # 10连抽打折（9折）
    if not rk_user.user_property.is_coin_enough(total_cost_coin):
        raise GameLogicError('user', 'not_enough_coin')
    cids = []

    get_list = []
    for cnt in range(multi_gacha_cnt):
        if cnt == 9:
            rate_conf = __multi_tenth_charge_rate(rk_user, cids) or __get_rate_conf('charge', rk_user)
        else:
            rate_conf = __get_rate_conf('charge', rk_user)
        thing_id, num = __select_gacha_thing(rate_conf)
        get_list.append({'_id': thing_id, 'num': num})
        user_gacha_obj.set_gacha_cnt()


        # success_fg, p1, ucid, is_first = user_card_obj.add_card(cid, clv, where='gacha_multi')
        # new_card = {
        #     'ucid':ucid,
        #     'is_first':is_first,
        # }
        # if is_open_safty():
        #     __set_safety_coin(rk_user, cid, cost_coin)

        # cids.append(cid)
        # new_card.update(user_card_obj.get_card_dict(ucid))
        # new_cards.append(new_card)

    add_info = tools.add_things(
        rk_user, 
        get_list,
        where="gacha_multi"
    )

    # cardSoul 加传  card 的星级
    if 'cardSoul' in add_info:
        card_config = rk_user.game_config.card_config
        for card_id in add_info['cardSoul']:
            num = add_info['cardSoul'][card_id]
            star = card_config[card_id]['star']
            add_info['cardSoul'][card_id] = {'num': num, 'star': star}
    rk_user.user_property.minus_coin(total_cost_coin, 'gacha_multi')
    get_things = __gacha_must_get(rk_user, multi_gacha_cnt)
    return {
        'add_info': add_info,
        'get_things': get_things
    }


def __gacha_must_get(rk_user, gacha_times=1):
    # 抽将必送的物品.
    gacha_things = game_config.gacha_config['gacha_things']
    rtn_data = {}
    data = tools.add_things(
        rk_user, 
        [{"_id": goods, "num": gacha_things[goods] * gacha_times} for goods in gacha_things if goods],
        where="gacha_must_get_things"
    )
    for v in data.values():
        rtn_data.update(v)
    return rtn_data

def is_open_safty():
    """
    保底求将开关
    输入 无
    输出 保底开关是否开启
    """
    #获取抽将保底开关配置
    gacha_black_conf = game_config.gacha_config.get('gacha_black_conf', {})
    if not gacha_black_conf:
        return False
    #获取时间区间段
    start_time = gacha_black_conf.get('start_time')
    end_time = gacha_black_conf.get('end_time','2111-11-11 11:11:11')
    now_str = datetime_toString(datetime.datetime.now())
    #开放
    if start_time <= now_str <= end_time:
        #在区间段内 返回开标志
        return True
    return False


def  __safety_charge_rate(rk_user, rate_conf):
    """  保底元宝求将， 根据条件对抽将概率配置rate_conf进行调整
    """
    user_gacha_obj = UserGacha.get_instance(rk_user.uid)
    has_consume_coin = user_gacha_obj.get_cost_coin()
    # 是否达到了低保要求
    is_reach_safety = __is_reach_safety_gacha_condition(has_consume_coin)
    # 是否是付费用户
    is_charge_user = rk_user.user_property.charged_user
    # 没有达到低保要求，且不是付费玩家，降低权重
    if not is_reach_safety and not is_charge_user:
        weight_down = __get_weight_down(rk_user)
        rate_conf = __calculate_gacha_rate(rk_user, rate_conf, weight_down)

    # 达到低保要求  而且 没有低保武将
    elif is_reach_safety:
        # 变更为保底武将配置
        rate_conf = game_config.gacha_config['gacha_black_conf']['safety_cards']

    return rate_conf

def __is_reach_safety_gacha_condition(has_consume_coin):
    """
    是否达到保底条件
    """
    #获取抽将累计消耗的元宝
    cost_coin = game_config.gacha_config['cost_coin']
    #获取黑盒条件
    gacha_black_conf = game_config.gacha_config.get('gacha_black_conf',{})
    if not gacha_black_conf.get('coin',0):
        return False
    return  has_consume_coin + cost_coin >= gacha_black_conf.get('coin', 20000)

def __has_safety_card(rk_user):
    """
    是否有保底卡
    """
    safety_cards = [card_conf[0] for card_conf in game_config.gacha_config['gacha_black_conf']['safety_cards']]
    user_card_obj = UserCards.get_instance(rk_user.uid)
    return user_card_obj.has_card_in_list(safety_cards)

def __set_safety_coin(rk_user, cid, cost_coin):
    """
    修改保底机制中的consume——coin记录
    """
    user_gacha_obj = UserGacha.get_instance(rk_user.uid)
    if cid in [card_conf[0] for card_conf in game_config.gacha_config['gacha_black_conf']['safety_cards']]:
        # 重置用于记录的玩家触发保底的消费coin
        user_gacha_obj.reset_cost_coin()
    else:
        user_gacha_obj.add_cost_coin(cost_coin)

def  __multi_tenth_charge_rate(rk_user, forword_cards):
    """
    付费用户，第一次十连抽时，判定是否抽到给定tenth_charge_conf中的将，
        如果前9抽没有抽中，则第10抽必出。
        列表中的将给出card和相应权重

    """
    user_gacha_obj = UserGacha.get_instance(rk_user.uid)
    tenth_charge_conf = game_config.gacha_config.get('tenth_charge_conf',{})
    is_charge_user = rk_user.user_property.charged_user

    if tenth_charge_conf.get('is_open', False) and \
        is_charge_user and \
        user_gacha_obj.is_first_tenth_charge_multi() and \
        not set(forword_cards) & set([card_conf[0] for card_conf in tenth_charge_conf['cards']]):
        user_gacha_obj.set_first_tenth_charged()
        return tenth_charge_conf['cards']
    else:
        return

def __calculate_gacha_rate(rk_user, rate_conf, weight_down):
    """
    计算求将权重
    """
    rate_conf_copy = copy.deepcopy(rate_conf)
    factor, weight_down_cards = weight_down
    for level_k, level_v in rate_conf_copy.iteritems():
        for _kk, _vv in level_v.iteritems():
            if _kk == 'weight':
                continue
            cids = set([i[0] for i in _vv['cards']])
            if cids & set(weight_down_cards):
                _vv['weight'] = int(math.ceil(_vv['weight'] * factor))
    return rate_conf_copy

def __get_weight_down(rk_user):
    gacha_black_conf = game_config.gacha_config.get('gacha_black_conf',{})
    #未达到条件的非付费用户权重调低
    weight_down = (gacha_black_conf['weight_factor'], gacha_black_conf['weight_down'])
    return weight_down
