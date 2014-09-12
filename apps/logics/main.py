#-*- coding: utf-8 -*-
""" filename:main.py

"""
import copy
import datetime
import random
import traceback

from apps.models.user_cards import UserCards
from apps.models.user_equips import UserEquips
from apps.models.user_lend import UserLend
from apps.models.user_login import UserLogin
from apps.models.user_dungeon import UserDungeon
from apps.common import utils
from apps.config.game_config import game_config
from apps.models.user_gift import UserGift
from apps.logics.card import get_card_soul_drop_info 
from apps.logics.equip import get_equip_drop_info
from apps.models.gift_code import GiftCode
from apps.models import data_log_mod
from apps.models.random_name import Random_Names
from django.conf import settings
from apps.logics import vip


def index(rk_user,params):
    data = {}
    #登录奖励
    UserLogin.get_instance(rk_user.uid).login(params)

    #借卡信息
    UserLend.get_instance(rk_user.uid).read_info(params)

    #邀请奖励信息
    #data['invited_award'] = rk_user.user_property.read_invite_award(params)

    #用户卡片信息
    card_obj = UserCards.get_instance(rk_user.uid)
    data['user_cards'] = card_obj.cards
    data['user_decks'] = card_obj.decks
    data['deck_index'] = card_obj.cur_deck_index
    #获取用户的装备信息
    user_equips_obj = rk_user.user_equips
    data['user_equips'] = user_equips_obj.equips
    #获取战场信息
    #data['weekly_info'] = UserDungeon.get_instance(rk_user.uid).get_weekly_info()
    data['daily_info'] = UserDungeon.get_instance(rk_user.uid).get_daily_info()
    data['user_dungeon_info'] = UserDungeon.get_instance(rk_user.uid).get_dungeon_info()
    return 0,data

def get_config(rk_user, params):
    config_info = {}
    #一些系统配置
    config_info['common'] = {
        'stamina_recover_time':game_config.system_config['stamina_recover_time'],
        'max_gacha_point':game_config.system_config['max_gacha_point'],
        'revive_coin':game_config.system_config['revive_coin'],
        'recover_stamina_coin':game_config.system_config['recover_stamina_coin'],
        'dungeon_clear_coin':game_config.system_config['dungeon_clear_coin'],
        'card_extend_coin':game_config.system_config['card_extend_coin'],
        'card_extend_num':game_config.system_config['card_extend_num'],
        'gacha_cost_gold':game_config.gacha_config['cost_gacha_gold'],
        'gacha_cost_coin':game_config.gacha_config['cost_coin'],
        'gacha_notice':game_config.gacha_config['notice'],
        'agreement':game_config.system_config.get('agreement',''),
        'help_links':game_config.system_config.get('help_links',[]),
        'aboutus':game_config.system_config['aboutus'],
        'praise':utils.get_msg('login','praise'),
        'weixin_voice_fg':game_config.weibo_config.get('weixin_voice_fg', False),
        'app_url':game_config.system_config['app_url'],
        'tapjoy_fg':game_config.system_config.get('tapjoy_fg',False),
        'admob_fg':game_config.system_config.get('admob_fg',False),
        'bbs_url': game_config.system_config.get('bbs_url',''),
        'bg_change':game_config.system_config.get('bg_change', '1'),
        'special_bg':game_config.system_config.get('special_bg',''),
        'card_update_conf':game_config.card_update_config,
        #商店充值活动
        "charge_url":game_config.shop_config.get("charge_award",{}).get("charge_url", ''),
        #微信分享类型1:到个人,2:朋友圈
        "weixin_share_type":game_config.weibo_config.get('weixin_share_type', 1),
        'notice':game_config.system_config['notice'],
        'pvp_recover_inter_time':game_config.pvp_config['pvp_recover_inter_time'],
        'recover_pvp_stamina_coin':game_config.pvp_config['recove_pvp_stamina_coin'],
        'multi_gacha_cnt':game_config.gacha_config.get('multi_gacha_cnt',0), #连抽次数
        'gift_code_fg':game_config.gift_config.get('is_open',False),
        'invite_fg':game_config.invite_config.get('open_invite',False),
        'app_comment_url':game_config.system_config.get('app_comment_url',''),
        'contact_us':game_config.system_config.get('contact_us',''),
        'free_gacha_notice':game_config.system_config.get('free_gacha_notice',''),

        'weixin_fg':game_config.weibo_config.get('weixin_fg',False),

        'auto_fight_is_open':game_config.system_config.get('auto_fight_is_open',False),#自动战斗总开关
        'month_item_is_open':game_config.shop_config.get('month_item_is_open',False),#月卡开关
        'stamina_conf':game_config.operat_config.get('stamina_conf',{}),#领取体力配置
        'stamina_award_is_open':game_config.operat_config.get('stamina_award_is_open',False),#领取体力配置开关
        'open_special_is_open':game_config.dungeon_world_config.get('open_special_is_open',False),#花费元宝开启loopgap战场开关
        'mycard_is_open':game_config.shop_config.get('mycard_is_open',False),#mycard 开关
        'mystery_store_is_open':game_config.mystery_store.get('mystery_store_is_open', False),# 神秘商店开关
    }

    version = float(params['version'])
    tut_open_lv = game_config.user_init_config.get('tut_open_lv',{})

    config_info['common']['card_update_open_lv'] = tut_open_lv.get('card_update_open_lv',3)

    config_info['common']['card_upgrade_open_lv'] = tut_open_lv.get('card_upgrade_open_lv',5)
    config_info['common']['equip_house_open_lv'] = tut_open_lv.get('equip_house_open_lv',6)
    config_info['common']['special_dungeon_open_lv'] = tut_open_lv.get('special_dungeon_open_lv',6)
    config_info['gacha_card_up'] = game_config.gacha_config.get('gacha_card_up',[])
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
        if 'free_gacha_notice' in game_config.android_config:
            config_info['common']['free_gacha_notice'] = game_config.android_config['free_gacha_notice']
        if 'auto_fight_is_open' in game_config.android_config:
            config_info['common']['auto_fight_is_open'] = game_config.android_config['auto_fight_is_open']
    #ios审核特殊处理
    if rk_user.client_type not in settings.ANDROID_CLIENT_TYPE and \
        version>float(game_config.system_config['version']) and \
        game_config.system_config.get('in_review',False):
            config_info['common']['invite_fg'] = False
            config_info['common']['gift_code_fg'] = False
            config_info['common']['gacha_notice'] = game_config.system_config.get('gacha_notice_in_review','')
            config_info['common']['notice'] = game_config.system_config.get('notice_in_review','')
            config_info['common']['free_gacha_notice'] = game_config.system_config.get('free_gacha_notice_in_review','')
            config_info['common']['auto_fight_is_open'] = False
            config_info['common']['stamina_award_is_open'] = False
            config_info['common']['open_special_is_open'] = False
            config_info['common']['month_item_is_open'] = False
            config_info['common']['card_update_open_lv'] = 5
            config_info['common']['mystery_store_is_open'] = False
            if 'gacha_card_up_in_review' in game_config.gacha_config:
                config_info['gacha_card_up'] = game_config.gacha_config['gacha_card_up_in_review']
    else:
        #定时公告
        if rk_user.client_type in settings.ANDROID_CLIENT_TYPE and 'timing_notice_conf' in game_config.android_config:
            timing_notice_conf = game_config.android_config.get('timing_notice_conf',{})
        else:
            timing_notice_conf = game_config.system_config.get('timing_notice_conf',{})
        now_str = utils.datetime_toString(datetime.datetime.now())
        for notice_type in ['notice','gacha_notice','free_gacha_notice']:
            if notice_type not in timing_notice_conf:
                continue
            notice_conf = timing_notice_conf[notice_type]
            for k in notice_conf:
                if now_str>k[0] and now_str<k[1]:
                    config_info['common'][notice_type] = notice_conf[k]
                    break
        #gacha_card_up取定时求将
        gacha_timing_config = game_config.gacha_timing_config
        for time_tuple in gacha_timing_config:
            if isinstance(time_tuple, (list,tuple)) is True and len(time_tuple) == 2:
                start = time_tuple[0]
                end = time_tuple[1]
                if now_str > start and now_str < end and gacha_timing_config[time_tuple].get('gacha_card_up'):
                    config_info['gacha_card_up'] = gacha_timing_config[time_tuple]['gacha_card_up']
                    break

    #武将等级配置
    config_info['card_level'] = game_config.card_level_config
    #好友送礼配置
    config_info['friend_gift_conf'] = game_config.invite_config['friend_gift_conf']
    #武将品质配置
    config_info['card_quality_conf'] = game_config.card_update_config['card_quality']
    #战场配置
    rc,config_info['dungeon'] = get_dungeon_config(rk_user,params)
    config_info['dungeon_world'] = game_config.dungeon_world_config['world']

    config_info['pvp_level'] = game_config.pvp_config['pvp_level_config']
    config_info['init_leader_card'] = game_config.user_init_config['init_leader_card']

    # mycard 商品配置
    config_info['mycard_sale'] = game_config.shop_config.get('mycard_sale', {})
    
    # sale 商品配置
    shop_config = copy.deepcopy(game_config.shop_config)
    sale_conf = shop_config.get('sale', {})
    sale_conf.update(shop_config.get('google_sale',{}))
    config_info['sale_conf'] = sale_conf
    config_info['props_sale'] = shop_config.get('props_sale',{})
    config_info['vip_gift_sale'] = vip.vip_gift_sale_list(rk_user.uid)

    #指定floor里面的内容信息
    config_info['all_floor_info'] = UserDungeon.get_instance(rk_user.uid).get_all_floor_info()
    #获取显示关卡的星配置信息
    config_info['message_tip'] = game_config.pack_config.get('message',{})
    config_info['common']['sell_base_gold'] = game_config.card_update_config['sell_base_gold']
    config_info['common']['exp_gold_rate'] = game_config.card_update_config['exp_gold_rate']
    #战斗参数配置
    config_info['fight_params_conf'] = {
                        'hc_drop_rate':game_config.skill_params_config.get('hc_drop_rate',0.1),
                        'bc_drop_rate':game_config.skill_params_config.get('bc_drop_rate',0.1),
                    }
    return 0,config_info

def get_equip_config(rk_user, params):
    """获得装备的配置
    """
    data = {}
    #获取装备配置信息
    equip_config = copy.deepcopy(game_config.equip_config)
    for eid in equip_config:
        unlock_skill = equip_config[eid].get('unlock_skill',{})
        if unlock_skill:
            #如果有解锁技能的话 就格式化解锁技能
            all_keys = sorted(unlock_skill.keys())
            tmp = []
            for lv in all_keys:
                info = unlock_skill[str(lv)]
                info['lv'] = str(lv)
                tmp.append(info)
            equip_config[eid]['unlock_skill'] = tmp

    data['equip_conf'] = equip_config
    #获取装备等级经验配置信息
    data['equip_exp_conf'] = game_config.equip_exp_conf
    #获取装备强化配置信息
    data['equip_update_config'] = game_config.equip_update_config
    #获取套装配置信息
    data['suit_type_conf'] = game_config.suit_type_conf
    #获取武器的碎片掉落信息
    data['equip_drop_info']  = get_equip_drop_info()
    return 0,data

def get_yuan_fen(rk_user,params):
    '''
    * miaoyichao
    * 获取缘分系统的配置信息
    '''
    return 0,{'fate_conf':game_config.fate_conf}


def get_item_config(rk_user, params):
    """获得药品的配置
    """
    data = {'item_conf':game_config.item_config}
    data.update(game_config.skill_params_config)
    return 0, data

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
    data['soul_drop_info'] = get_card_soul_drop_info()
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
    for conf_type in ['normal','special','daily','weekly']:

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
                if 'drop_info' in local_copy[floor_key]['rooms'][room_key]:
                    local_copy[floor_key]['rooms'][room_key].pop('drop_info')
                #去除不可见掉落信息
                if 'invisible_drop' in local_copy[floor_key]['rooms'][room_key]:
                    local_copy[floor_key]['rooms'][room_key].pop('invisible_drop')
                #去除通关经验
                if 'exp' in local_copy[floor_key]['rooms'][room_key]:
                    local_copy[floor_key]['rooms'][room_key].pop('exp')
                #去除通关金币
                if 'gold' in local_copy[floor_key]['rooms'][room_key]:
                    local_copy[floor_key]['rooms'][room_key].pop('gold')
                #去除可打次数信息
                if 'can_make_copy_cn' in local_copy[floor_key]['rooms'][room_key]:
                    local_copy[floor_key]['rooms'][room_key].pop('can_make_copy_cn')
                #去除通关经验点信息
                if 'exp_point' in local_copy[floor_key]['rooms'][room_key]:
                    local_copy[floor_key]['rooms'][room_key].pop('exp_point')

            data[conf_type] = local_copy

    return 0,data

def set_country(rk_user,params):
    """用户选择国家
    """
    country = params['country']
    rk_user.user_property.set_country(country)
    return 0,{}

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
    返回：man_names:['xxx','yyy'] female_names:['xxx','yyy']
    """
    rand_num = random.random()
    data = {}
    #男名
    random_list_man = Random_Names.find({'random' : { '$gte' : rand_num }},limit=20)
    if not random_list_man:
        random_list_man = Random_Names.find({'random' : { '$lte' : rand_num }},limit=20)
    data['man_names'] = []
    if random_list_man:
        for random_name_obj in random_list_man:
            data['man_names'].append(random_name_obj.name)
    else:
        data['man_names'] = [u'历史大轮回哦',u'千年等一回哦哦']
    #女名
    rand_num = random.random()
    random_list_female = Random_Names.find({'random' : { '$gte' : rand_num }},limit=20)
    if not random_list_female:
        random_list_female = Random_Names.find({'random' : { '$lte' : rand_num }},limit=20)
    data['female_names'] = []
    if random_list_female:
        for random_name_obj in random_list_female:
            data['female_names'].append(random_name_obj.name)
    else:
        data['female_names'] = [u'你是风儿',u'我是沙']
    return 0,data

def __remove_random_name(name):
    """
    删除随机名字
    """
    try:
        random_name_obj = Random_Names.get(name)
        if random_name_obj:
            random_name_obj.delete()
    except:
        utils.debug_print(traceback.format_exc())
        utils.send_exception_mailEx()
        
def set_name(rk_user,params):
    '''
    新手引导设置名称和性别
    name   名字
    sex    性别 man  / woman

    '''
    name = params.get('name','')
    
    step = int(params.get('step',0))
    #如果有用户名的话就不做处理
    if not rk_user.username:
        if len(name.strip())<=0:
            return 11,{'msg':utils.get_msg('user', 'name_cannot_null')}
        if utils.is_sense_word(name):
            return 11,{'msg':utils.get_msg('user', 'wrong_words')}
        if not rk_user.set_name(name):
            __remove_random_name(name)
            return 11,{'msg':utils.get_msg('user', 'name_exist')}
        __remove_random_name(name)
    if step:
        #设置新手引导的步骤
        rk_user.user_property.set_newbie_steps(step)
        sex = params.get('sex' , 'man')
        rk_user.set_sex(sex)
    return 0,{}

def show_vedio(rk_user,params):
    '''
    新手引导片头动画
    '''
    #获取新手引导的额步骤
    step = params.get('step',0)
    if step:
        #设置新手引导的步骤
        rk_user.user_property.set_newbie_steps(step)
        return 0,{}
    else:
        #参数错误
        return 11,{'msg':utils.get_msg('card','params_wrong')}

def __get_weibo_weixin_award(ul,user_gift_obj):
    """
    微博微信分享发奖励
    """
    if 'weibo_weixin_award' not in ul.login_info:
        ul.login_info['weibo_weixin_award'] = []
    now = datetime.datetime.now()
    hour_str = str(now.hour)
    #在本时间段没领过奖励，则发奖
    if hour_str not in ul.login_info['weibo_weixin_award']:
        ul.login_info['weibo_weixin_award'].append(hour_str)
        award_cnt_once = game_config.weibo_config.get('award_cnt_once',1)
        weibo_weixin_award = game_config.weibo_config['weibo_weixin_award']
        random_share_award_msg = utils.get_msg('weibo', 'random_share_award')
        for i in range(award_cnt_once):
            award = utils.get_item_by_random_simple(weibo_weixin_award)
            user_gift_obj.add_gift_by_dict(award,random_share_award_msg)
        ul.put()

def weibo_back(rk_user,params):
    """
    发微博回调
    """
    #如果当天发微博在5次以内，则给予奖励
    ul = UserLogin.get(rk_user.uid)
    rc = 0
    send_type = params.get('send_type','0')
    user_gift_obj = UserGift.get_instance(rk_user.uid)
    max_send_weibo = game_config.weibo_config.get('max_send_weibo',5)
    max_send_weixin = game_config.weibo_config.get('max_send_weixin',5)
    weibo_weixin_award = game_config.weibo_config.get('weibo_weixin_award',[])
    if send_type == '0':
        msg = utils.get_msg('weibo','sina_share')
        if weibo_weixin_award:
            __get_weibo_weixin_award(ul,user_gift_obj)
        elif ul.login_info.get('send_weibo',0) < max_send_weibo:
            ul.send_weibo()
            award = game_config.weibo_config.get('weibo_award_sina',{})
            user_gift_obj.add_gift(award,msg)

    elif send_type == '1':
        msg = utils.get_msg('weibo','qq_share')
        if weibo_weixin_award:
            __get_weibo_weixin_award(ul,user_gift_obj)
        elif ul.login_info.get('send_weibo',0) < max_send_weibo:
            ul.send_weibo()
            award = game_config.weibo_config.get('weibo_award_qq',{})
            user_gift_obj.add_gift(award,msg)
    elif send_type == '2':
        msg = utils.get_msg('weibo','fb_share')
        if weibo_weixin_award:
            __get_weibo_weixin_award(ul,user_gift_obj)
        elif ul.login_info.get('send_weibo',0) < max_send_weibo:
            ul.send_weibo()
            award = game_config.weibo_config.get('weibo_award_fb',{})
            user_gift_obj.add_gift(award,msg)
    else:
        msg = utils.get_msg('weibo','weixin_share')
        if weibo_weixin_award:
            __get_weibo_weixin_award(ul,user_gift_obj)
        elif ul.login_info.get('send_weixin',0) < max_send_weixin:
            ul.send_weixin()
            award = game_config.weibo_config.get('weixin_award',{})
            user_gift_obj.add_gift(award,msg)
    if send_type == '3':
        tmp_type = 'weixin'
    else:
        tmp_type = 'weibo'

    data_log_mod.set_log('Feed', rk_user,
                    lv=rk_user.user_property.lv,
                    feed_style=tmp_type,
                    platform=rk_user.platform
    )
    return rc,{'msg':msg}

def set_signature(rk_user,params):
    """
    设置签名
    """

    words = params.get('words','')
    if words:
        if utils.is_sense_word(words):
            return 11,{'msg':utils.get_msg('user','wrong_words')}
        if len(words) > 15:
            return 11 ,{'msg':utils.get_msg('user','too_long_signature')}
    rk_user.set_signature(words)
    return 0,{}

def get_gift(rk_user,params):
    #"""兑换礼品码
    #"""
    gift_keys = game_config.gift_config.get("gift_config", {})
    if rk_user.client_type in settings.ANDROID_CLIENT_TYPE and 'is_open' in game_config.android_config:
        is_open = game_config.android_config.get('is_open',True)
    else:
        is_open = game_config.gift_config.get('is_open',True)
    if not is_open:
        msg = utils.get_msg("gift", "gift_not_open")
        return 11, {"msg":msg}
    #校验礼品码
    gift_code = params["gift_code"]
    gift_code = gift_code.strip()
    gift_id = gift_code[:-5]
    if gift_id not in gift_keys:
        msg = utils.get_msg("gift", "gift_code_not_exist")
        return 11, {"msg":msg}
    gift = game_config.gift_config['gift_config'][gift_id]
    start_time = utils.string_toDatetime(gift.get('start_time','2013-05-29 00:00:00'))
    end_time = utils.string_toDatetime(gift.get('end_time','2913-05-29 00:00:00'))
    now_time = datetime.datetime.now()
    if now_time < start_time or now_time > end_time:
        return 11 ,{'msg':utils.get_msg('gift',"gift_not_in_right_time")}

    gift_code_obj = GiftCode.get(gift_id)
    user_gift_obj = UserGift.get_instance(rk_user.uid)
    if gift['type'] in user_gift_obj.gift_code_type:
        return 11,{'msg':utils.get_msg('gift','this_type_already_get')}
    if not gift_code_obj:
        return 11 ,{'msg':utils.get_msg('gift','gift_code_not_exist')}
    if gift_code not in gift_code_obj.codes:
        return 11,{'msg':utils.get_msg('gift','gift_code_error')}

    recycling = gift.get('recycling', False)
    if not recycling:
        if gift_code_obj.codes[gift_code]:
            return 11,{'msg':utils.get_msg('gift','gift_code_gived')}

    if not user_gift_obj.add_has_got_gift_code(gift_code):
        return 11,{'msg':utils.get_msg('gift','gift_code_gived')}

    #发礼品
    gift_code_obj.codes[gift_code] = rk_user.uid
    gift_code_obj.put()
    if gift.get('gift',{}):
        user_gift_obj.add_gift(gift['gift'],content=utils.get_msg('gift','exchange_gift_award'))
    #对于可以升级获得的奖励
    if gift.get('lv_up_gift',{}):
        user_gift_obj.add_lv_up_giftcode(gift_id)
        user_gift_obj.get_giftcode_lv_up_award(gift_id)
    user_gift_obj.gift_code_type.append(gift['type'])
    user_gift_obj.put()
    return 0,{}

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

def get_user_info(rk_user,params):
    """
    返回用户信息
    """
    return 0,{}

