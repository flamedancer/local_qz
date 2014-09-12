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
from apps.common import utils
from apps.models import data_log_mod
from apps.models.user_gacha import UserGacha
from apps.config.game_config import game_config
from apps.common.utils import datetime_toString
from apps.models.user_gift import UserGift
from apps.models.user_marquee import UserMarquee

def __get_soul(rk_user):
    """
    查看是否有碎片送
    """
    #获取抽将中的
    gacha_soul_conf = game_config.gacha_config.get('gacha_soul_conf',{})
    if not gacha_soul_conf or not gacha_soul_conf.get('souls',[]):
        return
    start_time = gacha_soul_conf['start_time']
    end_time = gacha_soul_conf['end_time']
    now_str = utils.datetime_toString(datetime.datetime.now())
    if now_str>end_time or now_str<start_time:
        return
    souls = gacha_soul_conf['souls']
    award = utils.get_item_by_random_simple(souls)
    UserGift.get(rk_user.uid).add_gift_by_dict(award, gacha_soul_conf.get('content',''))
    
def __select_gacha_card(rate_conf):
    """选择gacha的卡
        当rate_conf为dict时：rate_conf 有两层：例如free_rate， charge_rate
        当rate_conf为list时：rate_conf 只有层：类似：:[('171_card',20),('172_card',10)]
    """
    #根据配置选出武将的id
    if isinstance(rate_conf, dict):
        #随机选取那一层
        select_level_list = [(level_k,level_v['weight']) for level_k,level_v in rate_conf.iteritems()]
        select_level = utils.get_item_by_random_simple(select_level_list)
        rate_conf_select = copy.deepcopy(rate_conf[select_level])
        if 'weight' in rate_conf_select:
            rate_conf_select.pop('weight')
        select_level_list_second = [(level_k,level_v['weight']) for level_k,level_v in rate_conf_select.iteritems()]
        select_level_second = utils.get_item_by_random_simple(select_level_list_second)
        select_cards_list = rate_conf_select[select_level_second]['cards']
        select_card = utils.get_item_by_random(select_cards_list)
    elif isinstance(rate_conf, list):
        select_card = utils.get_item_by_random_simple(rate_conf)
    #根据 cid 分配等级
    if isinstance(select_card,str):
        cid = select_card
        clv = 1
    else:
        cid = select_card[0]
        clv = select_card[1]
    #结果返回
    return cid,clv

def __get_rate_conf(gacha_type, rk_user):
    """
    获取gacha概率配置
    gacha_type:求将类型，'gold' or 'charge' or 'timer_gacha'
    """
    #连抽权重与抽将配置进行计算
    if gacha_type == 'gold':
        #判断是否存在定时的gacha配置
        rate_conf = __get_gold_rate_conf('gold_rate')
        if rate_conf == {}:
            rate_conf = game_config.gacha_config['gold_rate']
    elif gacha_type == 'charge':
        #判断是否存在定时的gacha配置
        rate_conf = __get_gold_rate_conf('charge_rate')
        if rate_conf == {}:
            rate_conf = game_config.gacha_config['charge_rate']
        # 如果开启了保底机制
        if is_open_safty():
            rate_conf = __safety_charge_rate(rk_user, rate_conf)
    elif gacha_type == 'timer_gacha':
        #判断是否存在定时的gacha配置
        rate_conf = __get_gold_rate_conf('timer_gacha_rate')
        if rate_conf == {}:
            rate_conf = game_config.gacha_config['timer_gacha_rate']
    return rate_conf

def __get_gold_rate_conf(gacha_type):
    #是否存在gacha求将定时配置，输入gacha类型，返回对应类型的定时配置
    rate_conf = {}
    gacha_timing_config = game_config.gacha_timing_config
    for time_tuple in gacha_timing_config:
        if isinstance(time_tuple, (list,tuple)) is True and len(time_tuple) == 2:
            start = time_tuple[0]
            end = time_tuple[1]
            today_time = str(datetime.datetime.now())
            if today_time > start and today_time < end:
                rate_conf = gacha_timing_config[time_tuple].get(gacha_type, {})
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
    cid,clv = __select_gacha_card(rate_conf)
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
    #先尝试倒计时求将
    rc,data = __timer_gacha(rk_user,params)
    if rc==0:
        return rc,data
    user_card_obj = UserCards.get_instance(rk_user.uid)
    cost_coin = game_config.gacha_config['cost_coin']
    if not rk_user.user_property.is_coin_enough(cost_coin):
        return 11,{'msg':utils.get_msg('user','not_enough_coin')}
    can_get_soul = False
    # newbie = rk_user.user_property.newbie
    # #新手取newbie_gacha_list
    # if newbie and rk_user.client_type in settings.ANDROID_CLIENT_TYPE and 'newbie_gacha_list' in game_config.android_config:
    #     newbie_gacha_list = game_config.android_config['newbie_gacha_list']
    #     cid = utils.get_item_by_random_simple(newbie_gacha_list)
    #     clv = 1
    # elif newbie and 'newbie_gacha_list' in game_config.gacha_config:
    #     newbie_gacha_list = game_config.gacha_config['newbie_gacha_list']
    #     cid = utils.get_item_by_random_simple(newbie_gacha_list)
    #     clv = 1
    # else:
    #     #选卡
    rate_conf = __get_rate_conf('charge', rk_user)
    cid,clv = __select_gacha_card(rate_conf)
    can_get_soul = True
    if rk_user.user_property.minus_coin(cost_coin,'charge'):
        #加卡,初始6级
        success_fg,p1,ucid,is_first = user_card_obj.add_card(cid,clv,where='gacha_charge')
        new_card = {
            'ucid':ucid,
            'is_first':is_first,
        }
        new_card.update(user_card_obj.get_card_dict(ucid))
        #保底开关
        if is_open_safty():
            __set_safety_coin(rk_user, cid, cost_coin)
        if can_get_soul:
            __get_soul(rk_user)
        #记录消费日志信息
        data_log_mod.set_log("ConsumeRecord", rk_user, 
                        lv=rk_user.user_property.lv,
                        num=cost_coin,
                        consume_type='gacha_record',
                        before_coin=rk_user.user_property.coin + cost_coin,
                        after_coin=rk_user.user_property.coin
        )
        #写入跑马灯
        user_marquee_obj = UserMarquee.get(rk_user.subarea)
        marquee_params = {
            'type': 'gacha_charge',
            'username': rk_user.username,
            'cid': cid,
        }
        user_marquee_obj.record(marquee_params)

        return 0,{'new_card':new_card}
    else:
        return 2,{'msg':utils.get_msg('user','not_enough_coin')}

def __timer_gacha(rk_user,params):
    """
    倒计时gacha(消耗元宝类型的  免费)
    """
    user_gacha_obj = UserGacha.get_instance(rk_user.uid)
    #获取下一次免费抽时间
    next_free_gacha_time = user_gacha_obj.next_free_gacha_time
    #获取当前时间
    now_time = int(time.time())
    #免费倒计时未到，则返回
    if next_free_gacha_time>now_time:
        return 11,{'msg':utils.get_msg('gacha','timer_gacha_not_in_time')}
    #是否是新手
    newbie = rk_user.user_property.newbie
    if newbie and 'newbie_gacha_list' in game_config.gacha_config:
        newbie_gacha_list = game_config.gacha_config['newbie_gacha_list']
        cid = utils.get_item_by_random_simple(newbie_gacha_list)
        clv = 1
    else:
        rate_conf = __get_rate_conf('timer_gacha',rk_user)
        cid,clv = __select_gacha_card(rate_conf)
        __get_soul(rk_user)
    user_card_obj = UserCards.get_instance(rk_user.uid)
    #加卡
    success_fg,p1,ucid,is_first = user_card_obj.add_card(cid,clv,where='timer_gacha')
    new_card = {
        'ucid':ucid,
        'is_first':is_first,
    }
    new_card.update(user_card_obj.get_card_dict(ucid))
    #更新免费抽的上次时间
    user_gacha_obj.set_last_gacha_time()
    #判断新手引导
    newbie_step = int(params.get('newbie_step',0))
    if newbie_step:
        rk_user.user_property.set_newbie_steps(newbie_step)
    #结果返回
    return 0,{'new_card':new_card}

def charge_multi(rk_user,params):
    """
    收费gacha多连抽
    """
    user_card_obj = UserCards.get_instance(rk_user.uid)
    #元宝是否足够连抽
    multi_gacha_cnt = game_config.gacha_config.get('multi_gacha_cnt',10)
    cost_coin = game_config.gacha_config['cost_coin']
    if not rk_user.user_property.is_coin_enough(cost_coin):
        return 11,{'msg':utils.get_msg('user','not_enough_coin')}

    total_cost_coin = cost_coin * multi_gacha_cnt
    if rk_user.user_property.minus_coin(total_cost_coin,'charge_multi'):
        new_cards = []
        cids = []
        for cnt in range(multi_gacha_cnt):
            if cnt == 9:
                rate_conf = __multi_tenth_charge_rate(rk_user, cids) or __get_rate_conf('charge', rk_user)
            else:
                rate_conf = __get_rate_conf('charge', rk_user)
            cid, clv = __select_gacha_card(rate_conf)
            success_fg, p1, ucid, is_first = user_card_obj.add_card(cid, clv, where='gacha_multi')
            new_card = {
                'ucid':ucid,
                'is_first':is_first,
            }
            if is_open_safty():
                __set_safety_coin(rk_user, cid, cost_coin)

            cids.append(cid)
            new_card.update(user_card_obj.get_card_dict(ucid))
            new_cards.append(new_card)
            #__get_soul(rk_user)
        #增加消费记录
        data_log_mod.set_log("ConsumeRecord", rk_user, 
                        lv=rk_user.user_property.lv,
                        num=total_cost_coin,
                        consume_type='gacha_multi',
                        before_coin=rk_user.user_property.coin + total_cost_coin,
                        after_coin=rk_user.user_property.coin
        )
        return 0,{'new_cards':new_cards}

    else:
        return 2,{'msg':utils.get_msg('user','not_enough_coin')}

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

def is_open_tenth_coin_gacha_safty():
    """
    十连抽求将 保底开关
    输入 无
    输出 十连抽求将 保底开关是否开启
    """
    #获取十连抽求将保底配置
    tenth_coin_gacha_conf = game_config.gacha_config.get('tenth_coin_gacha_conf', {})
    if not tenth_coin_gacha_conf:
        return False
    #获取时间区间段
    start_time = tenth_coin_gacha_conf.get('start_time')
    end_time = tenth_coin_gacha_conf.get('end_time','2111-11-11 11:11:11')
    now_str = datetime_toString(datetime.datetime.now())
    #开放
    if start_time <= now_str <= end_time:
        #开放了保底求将
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

def __is_reach_safety_gacha_condition(has_consuem_coin):
    """
    是否达到保底条件
    """
    #获取抽将累计消耗的元宝
    cost_coin = game_config.gacha_config['cost_coin']
    #获取黑盒条件
    gacha_black_conf = game_config.gacha_config.get('gacha_black_conf',{})
    if not gacha_black_conf.get('coin',0):
        return False
    return  has_consuem_coin + cost_coin >= gacha_black_conf.get('coin', 20000)

def __has_safety_card(rk_user):
    """
    是否有保底卡
    """
    safety_cards = [card_conf[0] for card_conf in game_config.gacha_config['gacha_black_conf']['safety_cards']]
    user_card_obj = UserCards.get_instance(rk_user.uid)
    return user_card_obj.has_card_in_list(safety_cards)

def __set_safety_coin(rk_user, cid, cost_coin):
    """
    修改保底机制中的consuem——coin记录
    """
    user_gacha_obj = UserGacha.get_instance(rk_user.uid)
    if cid in [card_conf[0] for card_conf in game_config.gacha_config['gacha_black_conf']['safety_cards']]:
        # 重置用于记录的玩家触发保底的消费coin
        user_gacha_obj.reset_cost_coin()
    else:
        user_gacha_obj.add_cost_coin(cost_coin)

def  __multi_tenth_charge_rate(rk_user, forword_cards):
    """
    1. 付费用户，第一次十连抽时，判定是否抽到给定tenth_charge_conf中的将，
        如果前9抽没有抽中，则第10抽必出。
        列表中的将给出card和相应权重

    2. 若不满足1， 所有用户，十连抽时，判定是否抽到tenth_coin_gacha_conf中的将
        如果前9抽没有抽中，则第10抽必出。
        列表中的将给出card和相应权重
    """
    user_gacha_obj = UserGacha.get_instance(rk_user.uid)
    tenth_charge_conf = game_config.gacha_config.get('tenth_charge_conf',{})
    is_charge_user = rk_user.user_property.charged_user
    is_first_tenth_charge_multi = user_gacha_obj.is_first_tenth_charge_multi()

    tenth_coin_gacha_conf = game_config.gacha_config.get('tenth_coin_gacha_conf',{})
    if tenth_charge_conf.get('is_open', False) and \
        is_charge_user and \
        user_gacha_obj.is_first_tenth_charge_multi() and \
        not set(forword_cards) & set([card_conf[0] for card_conf in tenth_charge_conf['cards']]):
        user_gacha_obj.set_first_tenth_charged()
        return tenth_charge_conf['cards']
    elif is_open_tenth_coin_gacha_safty() and \
        not set(forword_cards) & set([card_conf[0] for card_conf in tenth_charge_conf['cards']]):
        return tenth_coin_gacha_conf['cards']
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
