#-*- coding: utf-8 -*-
""" filename:main.py

"""
import copy
import datetime
import random

from apps.models.user_dungeon import UserDungeon
from apps.common import utils
from apps.common import tools
from apps.config.game_config import game_config
from apps.models.user_gift import UserGift
from apps.logics.card import get_card_soul_drop_info 
from apps.logics.equip import get_equip_drop_info
from apps.models.gift_code import GiftCode

from django.conf import settings
from apps.logics import vip
from apps.common.random_name_male import male_name_parts
from apps.common.random_name_female import female_name_parts
from apps.common.exceptions import GameLogicError
from apps.models.names import Names



def index(rk_user,params):
    data = {}
    # 登录奖励
    data['login_bonus'] = rk_user.user_login.login(params)

    #邀请奖励信息
    #data['invited_award'] = rk_user.user_property.read_invite_award(params)

    # 用户卡片信息
    user_card_obj = rk_user.user_cards
    data['user_cards'] = user_card_obj.cards
    data['user_decks'] = user_card_obj.decks
    data['yuanjun_decks'] = user_card_obj.yuanjun_decks
    data['deck_index'] = user_card_obj.cur_deck_index
    # 获取用户的装备信息
    user_equips_obj = rk_user.user_equips
    data['user_equips'] = user_equips_obj.equips
    # s获取战场信息
    #data['weekly_info'] = rk_user.user_dungeon.get_weekly_info()
    user_dungeon_obj = rk_user.user_dungeon
    data['daily_info'] = user_dungeon_obj.get_daily_info()
    data['user_dungeon_info'] = user_dungeon_obj.get_dungeon_info()

    data['gacha'] = __gacha_info(rk_user)
    data['today_can_sign'] = rk_user.user_gift.today_can_sign()

    return 0,data


def __gacha_info(rk_user):
    data = {}
    gacha_conf = game_config.gacha_config
    data['one_need_coin'] = gacha_conf['cost_coin']
    data['ten_need_coin'] = int(gacha_conf['cost_coin'] * 10 * gacha_conf['multi_discount'])
    data['gacha_cnt'] = rk_user.user_gacha.gacha_cnt
    return data

def get_config(rk_user, params):
    config_info = {}

    subarea_notice_config = game_config.get_game_config('subarea_notice_config', '1')

    this_subarea_notice = ''
    this_subarea_timed_notice_conf = {}
    for nc in subarea_notice_config:
        if game_config.subarea_num in nc['subarea_list']:
            this_subarea_notice = nc['notice']
            this_subarea_timed_notice_conf = nc['timed_notice_conf']
            break

    # 一些系统配置
    config_info['common'] = {
        'stamina_recover_time': game_config.system_config['stamina_recover_time'],
        'revive_coin': game_config.system_config['revive_coin'],

        'dungeon_clear_coin': game_config.system_config['dungeon_clear_coin'],

        'coin_recover_stamina': game_config.system_config['coin_recover_stamina'],
        'recover_stamina_need': game_config.system_config['recover_stamina_need'],
        'recover_normal_copy_need': game_config.system_config['recover_normal_copy_need'],
        'recover_daily_copy_need': game_config.system_config['recover_daily_copy_need'],

        'gacha_cost_coin': game_config.gacha_config['cost_coin'],
        'agreement': game_config.system_config.get('agreement',''),
        'help_links': game_config.system_config.get('help_links',[]),
        'aboutus': game_config.system_config['aboutus'],
        'praise': utils.get_msg('login','praise'),
        'weixin_voice_fg':game_config.weibo_config.get('weixin_voice_fg', False),
        'app_url':game_config.system_config['app_url'],
        'bbs_url': game_config.system_config.get('bbs_url',''),
        # 'special_bg':game_config.system_config.get('special_bg',''),
        'card_update_conf': game_config.card_update_config,
        # #商店充值活动
        # "charge_url": game_config.shop_config.get("charge_award", {}).get("charge_url", ''),
        # # 微信分享类型1:到个人,2:朋友圈
        # "weixin_share_type": game_config.weibo_config.get('weixin_share_type', 1),
        # 'notice': game_config.system_config['notice'],
        'notice':this_subarea_notice,
        'multi_gacha_cnt': game_config.gacha_config.get('multi_gacha_cnt', 0), #连抽次数
        'gift_code_fg': game_config.gift_config.get('is_open', False),
        'invite_fg': game_config.invite_config.get('open_invite', False),
        'app_comment_url': game_config.system_config.get('app_comment_url',''),
        # 'contact_us': game_config.system_config.get('contact_us',''),
        # 'free_gacha_notice':game_config.system_config.get('free_gacha_notice',''),

        # 'weixin_fg': game_config.weibo_config.get('weixin_fg',False),

        # 'auto_fight_is_open':game_config.system_config.get('auto_fight_is_open', False),#自动战斗总开关
        'monthCard_is_open': game_config.system_config.get('monthCard_is_open',False),#月卡开关
        # 'stamina_conf': game_config.operat_config.get('stamina_conf', {}),#领取体力配置
        # 'stamina_award_is_open':game_config.operat_config.get('stamina_award_is_open',False),#领取体力配置开关
        'open_special_is_open':game_config.dungeon_world_config.get('open_special_is_open',False),#花费元宝开启loopgap战场开关
        # 'mycard_is_open':game_config.shop_config.get('mycard_is_open', False),#mycard 开关
        # 'mystery_store_is_open':game_config.mystery_store_config.get('mystery_store_is_open', True),# 神秘商店开关
        'mystery_store_refresh_coin': game_config.mystery_store_config.get('store_refresh_cost', True),# 神秘商店刷新所需元宝
        'pvp_server_close': game_config.system_config.get('pvp_server_close', True),# pvp开关
    }

    version = float(params['version'])

    # config_info['gacha_card_up'] = game_config.gacha_config.get('gacha_card_up',[])

    #安卓配置兼容
    if rk_user.client_type in settings.ANDROID_CLIENT_TYPE:
        if 'notice' in game_config.android_config:
            config_info['common']['notice'] = game_config.android_config['notice']
        if 'agreement' in game_config.android_config:
            config_info['common']['agreement'] = game_config.android_config['agreement']
        if 'gacha_notice' in game_config.android_config:
            config_info['common']['gacha_notice'] = game_config.android_config['gacha_notice']
        if 'open_invite' in game_config.android_config:
            config_info['common']['invite_fg'] = game_config.android_config['open_invite']
        if 'is_open' in game_config.android_config:
            config_info['common']['gift_code_fg'] = game_config.android_config['is_open']
        if 'gacha_card_up' in game_config.android_config:
            config_info['gacha_card_up'] = game_config.android_config['gacha_card_up']
        # if 'free_gacha_notice' in game_config.android_config:
        #     config_info['common']['free_gacha_notice'] = game_config.android_config['free_gacha_notice']
        # if 'auto_fight_is_open' in game_config.android_config:
        #     config_info['common']['auto_fight_is_open'] = game_config.android_config['auto_fight_is_open']
    #ios审核特殊处理
    if rk_user.client_type not in settings.ANDROID_CLIENT_TYPE and \
        version>float(game_config.system_config['version']) and \
        game_config.system_config.get('in_review',False):
            config_info['common']['invite_fg'] = False
            config_info['common']['gift_code_fg'] = False
            config_info['common']['gacha_notice'] = game_config.system_config.get('gacha_notice_in_review','')
            config_info['common']['notice'] = game_config.system_config.get('notice_in_review','')
            # config_info['common']['free_gacha_notice'] = game_config.system_config.get('free_gacha_notice_in_review','')
            # config_info['common']['auto_fight_is_open'] = False
            # config_info['common']['stamina_award_is_open'] = False
            config_info['common']['open_special_is_open'] = False
            config_info['common']['monthCard_is_open'] = False
            config_info['common']['mystery_store_is_open'] = False
            if 'gacha_card_up_in_review' in game_config.gacha_config:
                config_info['gacha_card_up'] = game_config.gacha_config['gacha_card_up_in_review']
    else:
        #定时公告
        if rk_user.client_type in settings.ANDROID_CLIENT_TYPE and 'timing_notice_conf' in game_config.android_config:
            timing_notice_conf = game_config.android_config.get('timing_notice_conf',{})
        else:
            #timing_notice_conf = game_config.system_config.get('timing_notice_conf',{})
            timing_notice_conf = this_subarea_timed_notice_conf
        now_str = utils.datetime_toString(datetime.datetime.now())
        for notice_type in ['notice', 'gacha_notice']:
            if notice_type not in timing_notice_conf:
                continue
            notice_conf = timing_notice_conf[notice_type]
            for k in notice_conf:
                if now_str>k[0] and now_str<k[1]:
                    config_info['common'][notice_type] = notice_conf[k]
                    break

    #武将等级配置
    config_info['card_level'] = game_config.card_level_config
    #好友送礼配置
    config_info['friend_gift_conf'] = game_config.invite_config['friend_gift_conf']
    #战场配置
    rc,config_info['dungeon'] = get_dungeon_config(rk_user,params)
    config_info['dungeon_world'] = game_config.dungeon_world_config['world']

    # # mycard 商品配置
    # config_info['mycard_sale'] = game_config.shop_config.get('mycard_sale', {})
    
    # sale 元宝商品配置   要减去已经特惠次数
    sale_conf = copy.deepcopy(game_config.shop_config.get('sale', {}))
    each_item_bought_times = rk_user.user_property.property_info['charge_item_bought_times']
    for item in each_item_bought_times:
        if item in sale_conf:
            sale_conf[item]['extreme_cheap_time'] = max(sale_conf[item]['extreme_cheap_time'] - each_item_bought_times[item], 0)
    config_info['sale_conf'] = sale_conf

    # 月卡商品配置  要添加是否购买此月卡 和  剩余返还天数
    if config_info['common']['monthCard_is_open']:
        monthCard_sale_conf = copy.deepcopy(game_config.shop_config.get('monthCard', {}))
        monthCard_remain_days = rk_user.user_property.property_info.get('monthCard_remain_days', {})
        for item in monthCard_sale_conf:
            if item in monthCard_remain_days:
                monthCard_sale_conf[item]['remain_days'] = monthCard_remain_days[item]
                monthCard_sale_conf[item]['has_bought'] = True
            else:
                monthCard_sale_conf[item]['remain_days'] = 29
                monthCard_sale_conf[item]['has_bought'] = False
    else:
        monthCard_sale_conf = {}
    config_info['monthCard_sale_conf'] = monthCard_sale_conf

    config_info['vip_gift_sale'] = vip.vip_gift_sale_list(rk_user)

    #指定floor里面的内容信息
    config_info['all_floor_info'] = UserDungeon.get_instance(rk_user.uid).get_all_floor_info()

    config_info['common']['exp_gold_rate'] = game_config.card_update_config['exp_gold_rate']
    #战斗参数配置
    config_info['fight_params_conf'] = {
                        'hc_drop_rate':game_config.skill_params_config.get('hc_drop_rate',0.1),
                        'bc_drop_rate':game_config.skill_params_config.get('bc_drop_rate',0.1),
                    }

    # 探索展示物品配置
    # config_info['explore_show'] = {}
    # explore_show_can_get = game_config.explore_config.get('show_can_get', {})
    # for explore_type, goods_info in explore_show_can_get.items():
    #     config_info['explore_show'][explore_type] = [tools.pack_good(goods_id, num) for goods_id, num in goods_info.items()]
    # 珠子掉落配置
    # config_info['bead_config'] = game_config.bead_config

    # 各功能开放的等级
    config_info["open_lv"] = game_config.user_init_config['open_lv']
    # VIP玩家每天福利
    config_info['vip_daily_bonus'] = game_config.loginbonus_config['vip_daily_bonus']
    # 道具商店   在道具商店配置中多添加字段 玩家当前已购买次数
    user_pack_obj = rk_user.user_pack
    props_sale = copy.deepcopy(game_config.props_store_config.get('props_sale', {}))
    for index, sale_conf in props_sale.items():
        sale_conf['now_buy_cnt'] = user_pack_obj.store_has_bought.get(index, 0)
    config_info['props_sale'] = props_sale
    return config_info

def get_equip_config(rk_user, params):
    """获得装备的配置
    """
    data = {}
    #获取装备配置信息

    data['equip_conf'] = game_config.equip_config
    #获取装备等级经验配置信息
    data['equip_exp_conf'] = game_config.equip_exp_config
    #获取套装配置信息
    data['suit_type_conf'] = game_config.suit_type_config
    #获取武器和碎片的掉落来源信息
    # data.update(get_equip_drop_info())
    # data['equip_upgrade_config'] = game_config.equip_upgrade_config  # 装备升品配置
    return 0, data

def get_yuan_fen(rk_user,params):
    '''
    * miaoyichao
    * 获取缘分系统的配置信息
    '''
    return 0,{'fate_conf':game_config.fate_config}


#  需要和前端协商  转成  get_skill_params_config
def get_item_config(rk_user, params):
    """获得技能的配置
    """
    return get_skill_params_config(rk_user, params)

def get_skill_params_config(rk_user, params):
    """获得技能的配置
    """
    return 0, game_config.skill_params_config

def get_character_talent_config(rk_user, params):
    """获得主角天赋的配置
    """
    return 0, game_config.character_talent_config

def get_material_config(rk_user, params):
    """获得材料的配置
    """
    return 0, {'material_conf':game_config.material_config,
                'props_conf':game_config.props_config
            }

def get_props_config(rk_user, params):
    """获得道具的配置
    """
    data = {'props_conf':game_config.props_config}
    return 0, data

def get_card_config(rk_user, params):
    """
    获得卡的配置
    """
    data = {}
    data['card_conf'] = game_config.card_config
    data['talent_config'] = game_config.talent_skill_config
    data['talent_value_config'] = game_config.talent_value_config
    # data['soul_drop_info'] = get_card_soul_drop_info()
    return 0, data

def get_monster_config(rk_user, params):
    """获得敌将的配置
    """
    return 0, {'monster_conf':game_config.monster_config}

def __calculate_loopgap_dungeon_time(floor_conf):
    """
    计算循环战场还有多长时间开启
    """
    time_now = datetime.datetime.now()
    time_now_str = utils.datetime_toString(time_now)
    return_start_time = floor_conf['start_time']
    return_end_time = floor_conf['end_time']
    loop_gap = int(floor_conf['loop_gap'])
    if return_start_time[:10] > time_now_str[:10]:
        return_end_time = return_start_time[:10] + floor_conf['end_time'][10:]
    else:
        temp_today = utils.string_toDatetime(time_now_str[:10] + ' 00:00:00')
        temp_start = utils.string_toDatetime(floor_conf['start_time'][:10] + ' 00:00:00')
        #小时数分钟数未到时间并且当天是循环开放时间，则给当天时间
        delta_days = (temp_today - temp_start).days
        if time_now_str[10:] < return_end_time[10:] and\
        not delta_days % loop_gap:
            return_start_time = time_now_str[:10] + floor_conf['start_time'][10:]
            return_end_time = time_now_str[:10] + floor_conf['end_time'][10:]
        else:
            #则计算后面开放时间
            _start_time = temp_today + datetime.timedelta(days=loop_gap-delta_days%loop_gap)
            _start_time = utils.datetime_toString(_start_time)
            return_start_time = _start_time[:10] + floor_conf['start_time'][10:]
            return_end_time = _start_time[:10] + floor_conf['end_time'][10:]
    next_start_time = utils.datetime_toString(utils.string_toDatetime(return_start_time) + datetime.timedelta(days=loop_gap))
    next_end_time = utils.datetime_toString(utils.string_toDatetime(return_end_time) + datetime.timedelta(days=loop_gap))
    return (return_start_time,return_end_time),(next_start_time,next_end_time)
            
def get_dungeon_config(rk_user,params):
    """
    取得目前的迷宫配置及用户关于迷宫的数据
    """
    #from apps.logics.dungeon import get_eff_id
    data = {
        # 'effect':game_config.dungeon_effect_config,
    }
    # dungeon_effect_config = game_config.dungeon_effect_config
    # now = datetime.datetime.now()
    # now_str = now.strftime('%Y-%m-%d %H:%M:%S')
    # now_week_str = now.strftime('%w')
    # today_str = now.strftime('%Y-%m-%d')

    # normal_conf = game_config.normal_dungeon_config
    # normal_copy = copy.deepcopy(normal_conf)

    # special_conf = game_config.special_dungeon_config
    # special_copy = copy.deepcopy(special_conf)
    
    # weekly_conf = game_config.weekly_dungeon_config
    # weekly_copy = copy.deepcopy(weekly_conf)

    # daily_conf = game_config.daily_dungeon_config
    # daily_copy = copy.deepcopy(daily_conf)

    # normal_effect_conf = game_config.normal_dungeon_effect_config
    # floor_effect = normal_effect_conf['rule'][now_week_str]
    # floor_special_effect = normal_effect_conf.get("special", {})

    #获得玉玺等循环副本的打法
    lstcycle_floor_id = []
    #给前端的配置需要处理
    # for conf_type in ['normal','special','daily','weekly']:
    for conf_type in ['normal', 'daily']:
        local_conf = getattr(game_config, conf_type + "_dungeon_config")
        local_copy = copy.deepcopy(local_conf)

        for floor_key,floor_value in local_conf.iteritems():
            if conf_type == 'special':
                if floor_key not in lstcycle_floor_id:
                    tag,return_start_time,return_end_time = utils.in_speacial_time(floor_value)
                    #循环战场显示即将开启时间
                    if 'loop_gap' in floor_value:
                        local_copy[floor_key]['loop_dungeon'] = True
                        loop_dungeon_time = __calculate_loopgap_dungeon_time(floor_value)
                        local_copy[floor_key]['start_time'] = loop_dungeon_time[0][0]
                        local_copy[floor_key]['end_time'] = loop_dungeon_time[0][1]
                        local_copy[floor_key]['loop_dungeon_time'] = loop_dungeon_time[1]
                    else:
                        if tag:
                            local_copy[floor_key]['start_time'] = return_start_time
                            local_copy[floor_key]['end_time'] = return_end_time
                        else:
                            local_copy.pop(floor_key)
                            continue
            else:
                pass
            for room_key in local_conf[floor_key]['rooms']:
                if str(room_key) == '0':
                    local_copy[floor_key]['rooms'].pop(str(room_key))
                    continue
                #给前端返回的时候把不需要的内容给去除
                #去除小节的信息
                if 'steps_info' in local_copy[floor_key]['rooms'][room_key]:
                    local_copy[floor_key]['rooms'][room_key].pop('steps_info')
                #去除可见掉落的信息
                # if 'drop_info' in local_copy[floor_key]['rooms'][room_key]:
                #     local_copy[floor_key]['rooms'][room_key].pop('drop_info')
                #去除不可见掉落信息
                if 'invisible_drop' in local_copy[floor_key]['rooms'][room_key]:
                    local_copy[floor_key]['rooms'][room_key].pop('invisible_drop')
                #去除通关经验
                # if 'exp' in local_copy[floor_key]['rooms'][room_key]:
                #     local_copy[floor_key]['rooms'][room_key].pop('exp')
                # #去除通关金币
                # if 'gold' in local_copy[floor_key]['rooms'][room_key]:
                #     local_copy[floor_key]['rooms'][room_key].pop('gold')
                #去除可打次数信息
                if 'can_make_copy_cn' in local_copy[floor_key]['rooms'][room_key]:
                    local_copy[floor_key]['rooms'][room_key].pop('can_make_copy_cn')
                # #去除通关经验点信息
                # if 'exp_point' in local_copy[floor_key]['rooms'][room_key]:
                #     local_copy[floor_key]['rooms'][room_key].pop('exp_point')

            data[conf_type] = local_copy

    return 0,data


def get_shop(rk_user,params):
    """
    商店配置信息：{   'com.oneclick.sango.coin01':1,#状态：0-default;1-热销;2-超值
                  'com.oneclick.sango.coin02':3,
                  'com.oneclick.sango.coin03':2,
                  'com.oneclick.sango.coin04':1,
                  'com.oneclick.sango.coin05':2,
                 'com.oneclick.sango.coin06':2,
              }
    """
    result = {}
    for sale_k,sale_v in game_config.shop_config['sale'].iteritems():
        result[sale_k] = sale_v.get('state',0)
    return 0,{'shop_info':result}


def get_random_names(rk_user,params):
    """
    取得随机名字
    返回：man_names:['xxx','yyy'], female_names:['xxx','yyy']

    当我们随机选名字，有 300 * 300 * 300 = 2700万, 同名总概率会很低，
    并且大多用户会改用自己喜欢的名字？

    纯随机选名，是简单的，可行的。 反正最后把用户选择的名字存到数据库时，
    都是要查是否重名的。

    rk_user.set_name 调用 UserName.set_name, UserName的 pk 是 name, 
    若重复，报错
    """

    random_list_man = []
    random_list_female = []

    for i in range(20):
        while True:
            male_name = (random.choice(male_name_parts['1']) +
                    random.choice(male_name_parts['2']) +
                    random.choice(male_name_parts['3']))
            if not (utils.is_sense_word(male_name) or 
                Names.get(male_name)):
                break

        while True:
            female_name = (random.choice(female_name_parts['1']) +
                    random.choice(female_name_parts['2']) +
                    random.choice(female_name_parts['3']))
            if not (utils.is_sense_word(female_name) or 
                Names.get(female_name)):
                break

        #if Random_Names.find({'name': male_name}):
        #    #重名的概率更小一次
        #    male_name = random.choice(male_name_parts['1']) + \
        #        random.choice(male_name_parts['2']) + \
        #        random.choice(male_name_parts['3']) 

        #if Random_Names.find({'name': female_name}):
        #    #重名的概率更小一次
        #    female_name = random.choice(female_name_parts['1']) + \
        #        random.choice(female_name_parts['2']) + \
        #        random.choice(female_name_parts['3']) 

        random_list_man += [ male_name ]
        random_list_female += [ female_name ]

    data = {}
    data['man_names'] = random_list_man
    data['female_names'] = random_list_female
    return data
 

def set_name(rk_user, params):
    '''
    新手引导设置名称和性别
    name   名字
    sex    性别 man  / woman

    '''
    name = params.get('name', '')
    
    step = int(params.get('step', 0))

    if len(name.strip()) <= 0:
        raise GameLogicError('user', 'name_cannot_null')
    if utils.is_sense_word(name):
        raise GameLogicError('user', 'wrong_words')
    if Names.get(name):
        #rk_user调用 UserName.set_name, UserName的 pk 是 name, 若重复，报错
        raise GameLogicError('user', 'name_exist')
    rk_user.set_name(name)
    Names.set_name(rk_user.uid, name)
    if step:
        #设置新手引导的步骤
        rk_user.user_property.set_newbie_steps(step, "set_name")
        sex = params.get('sex', 'man')
        rk_user.set_sex(sex)
    return {}


def show_vedio(rk_user,params):
    '''
    新手引导片头动画
    '''
    #获取新手引导的额步骤
    step = params.get('step',0)
    if step:
        #设置新手引导的步骤
        rk_user.user_property.set_newbie_steps(step, "show_vedio")
        return 0,{}
    else:
        #参数错误
        return 11,{'msg':utils.get_msg('card','params_wrong')}


def get_giftCode_gift(rk_user, params):
    """兑换礼品码

    Args:
        gift_code:   礼品码
    """
    gift_keys = game_config.gift_config.get('gift_config', {})
    if rk_user.client_type in settings.ANDROID_CLIENT_TYPE and 'is_open' in game_config.android_config:
        is_open = game_config.android_config.get('is_open', True)
    else:
        is_open = game_config.gift_config.get('is_open', True)
    if not is_open:
        msg = utils.get_msg('gift', 'gift_not_open')
        return 11, {'msg': msg}
    # 校验礼品码
    gift_code = params['gift_code']
    gift_code = gift_code.strip()
    gift_id = gift_code[:-5]
    if gift_id not in gift_keys:
        msg = utils.get_msg('gift', 'gift_code_not_exist')
        return 11, {'msg': msg}
    gift_conf = game_config.gift_config['gift_config'][gift_id]
    start_time = utils.string_toDatetime(gift_conf.get('start_time', '2013-05-29 00:00:00'))
    end_time = utils.string_toDatetime(gift_conf.get('end_time', '2020-05-29 00:00:00'))
    now_time = datetime.datetime.now()
    if now_time < start_time or now_time > end_time:
        return 11, {'msg': utils.get_msg('gift', 'gift_not_in_right_time')}

    gift_code_obj = GiftCode.get(gift_id)
    user_gift_obj = UserGift.get_instance(rk_user.uid)

    # 平台限制判断
    gift_platform_list = gift_conf.get('platform_list', [])
    if gift_platform_list and rk_user.platform not in gift_platform_list:
        return 11, {'msg': utils.get_msg('gift', 'platform_not_allowed')}
    # 分区限制判断
    gift_subarea_list = gift_conf.get('subarea_list', [])
    if gift_subarea_list and rk_user.subarea not in gift_subarea_list:
        return 11, {'msg': utils.get_msg('gift', 'subarea_not_allowed')}

    if gift_id in user_gift_obj.gift_code_type:
        return 11, {'msg': utils.get_msg('gift', 'this_type_already_get')}
    if not gift_code_obj or gift_code not in gift_code_obj.codes:
        return 11, {'msg': utils.get_msg('gift', 'gift_code_not_exist')}
    # 是否允许不同uid领取相同礼品码
    recycling = gift_conf.get('recycling', False)
    if not recycling:
        if gift_code_obj.codes[gift_code]:
            return 11, {'msg': utils.get_msg('gift', 'gift_code_gived')}
    # 玩家是否已经领取了此礼品码
    if not user_gift_obj.add_has_got_gift_code(gift_code):
        return 11, {'msg': utils.get_msg('gift', 'gift_code_gived')}

    # 记录该礼品码被最后一次领取的uid
    gift_code_obj.codes[gift_code] = rk_user.uid
    gift_code_obj.put()
    # 记录玩家已领的礼品码
    user_gift_obj.gift_code_type.append(gift_id)
    # 发礼品
    all_get_things = tools.add_things(rk_user, [{'_id': thing_id, 'num': num} for thing_id, num
       in gift_conf.get('gift', {}).items()], where=u"giftCode_award")
    #对于可以升级获得的奖励
    # if gift.get('lv_up_gift',{}):
    #     user_gift_obj.add_lv_up_giftcode(gift_id)
    #     user_gift_obj.get_giftcode_lv_up_award(gift_id)
    user_gift_obj.put()
    return {'get_info': all_get_things}


def get_first_charge_award_info(rk_user, params):
    first_charge_award = game_config.operat_config.get('first_charge_award', {})
    award_info = []
    for thing_id, num in first_charge_award.items():
        award_info.append(tools.pack_good(thing_id, num))
    return {"award": award_info}


def get_charge_award_info(rk_user,params):
    """
    充值礼包信息
    """
    return new_get_charge_award_info(rk_user,params)


def new_get_charge_award_info(rk_user,params):
    """
    用户最接近的充值礼包信息
    """
    if rk_user.client_type in settings.ANDROID_CLIENT_TYPE and 'charge_award' in game_config.android_config:
        charge_award = game_config.android_config['charge_award']
    else:
        charge_award = game_config.shop_config.get('charge_award',{})
    charge_award_copy = copy.deepcopy(charge_award)
    charge_award_info = rk_user.user_property.charge_award_info
    for gift_id in charge_award:
        gift_conf = charge_award_copy[gift_id]
        start_time = gift_conf.get('start_time')
        end_time = gift_conf.get('end_time','2111-11-11 11:11:11')
        now_str = utils.datetime_toString(datetime.datetime.now())
        #未开放或已过期的礼包
        if now_str>end_time or now_str<start_time:
            charge_award_copy.pop(gift_id)
    if not charge_award_copy:
        return 11,{'msg':utils.get_msg('active','not_open')}
    gift_list = []
    end_time = None
    for gift_id in charge_award_copy:
        end_time = charge_award_copy[gift_id]['end_time']
        if gift_id in charge_award_info:
            has_charge_coin = charge_award_info[gift_id]['charge_coin']
        else:
            has_charge_coin = 0
        diff_charge_coin = charge_award_copy[gift_id]['charge_coin']-has_charge_coin
        need_charge_coin = max(0,diff_charge_coin)
        tmp_dic = {
                   'need_charge_coin':need_charge_coin,
                   'now_charge_coin':has_charge_coin,
                   'award':charge_award_copy[gift_id]['award'],
                   'desc':charge_award_copy[gift_id].get('desc',''),
                   'charge_coin':charge_award_copy[gift_id]['charge_coin'],
                   'name':charge_award_copy[gift_id].get('name',''),
                   }
        gift_list.append(tmp_dic)
    gift_list = sorted(gift_list,key=lambda x:x['charge_coin'])
    now_gift_id = len(gift_list)-1
    found = False
    for i in range(len(gift_list)):
        if not found and gift_list[i]['need_charge_coin']>0:
            now_gift_id = i
            found = True
        gift_list[i].pop('charge_coin')
    data={
          'gift_list':gift_list,
          'gift_index':now_gift_id,
          'end_time':end_time,
          }
    return 0,data


def recover_stamina(rk_user, params):
    """花费元宝回复体力
    
    每次回复的体力值是固定的，但消耗的元宝数
    是根据当天第几次回体配置的
    """
    user_property_obj = rk_user.user_property
    recover_stamina = game_config.system_config['coin_recover_stamina']
    has_recover_times = user_property_obj.property_info['recover_times']['recover_stamina']
    need_coin = game_config.system_config['recover_stamina_need'][has_recover_times + 1]
    

    # 检查用户体力是否已满
    if user_property_obj.max_recover():
        raise GameLogicError('user', 'max_recover')
    # 检查vip可以回复的次数到了没
    vip.check_limit_recover(rk_user, 'recover_stamina')

    # 检查用户coin是否足够 并扣钱
    if not user_property_obj.minus_coin(need_coin, 'recover_stamina'):
        raise GameLogicError('user', 'not_enough_coin')
    # 添加回复次数
    user_property_obj.add_recover_times('recover_stamina')
    user_property_obj.add_stamina(recover_stamina)
    return {}


def skip_tutorial(rk_user, params):
    """跳过新手引导

    Args:
        newbie_steps   要跳过几步新手引导
    """
    user = rk_user
    # 获取新手引导的额步骤
    max_steps_num = int(user.game_config.system_config.get('newbie_steps', 6))
    newbie_steps_num = params.get('newbie_steps') or max_steps_num
    # 要跳过那个哪步新手引导
    # 一键过新手引导
    if user.user_property.newbie:
        # user.user_property.property_info['newbie_steps'] = (1 << newbie_steps_num) - 1
        user.user_property.property_info['newbie_steps'] = newbie_steps_num
        user.user_property.set_newbie()
        user.user_property.do_put()
    return {}
