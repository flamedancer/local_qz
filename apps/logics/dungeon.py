#-*- coding: utf-8 -*-
'''
    该文件的主要功能函数就是战场的开始和结束的内容
    1  战场开始的函数
    2  战场结束的函数
    3  战场获得的星星开启的宝箱的函数
    4  战场重置的函数
'''
import copy
import datetime
import random
import time
from apps.models.user_property import UserProperty
from apps.models.user_cards import UserCards
from apps.models.user_dungeon import UserDungeon
from apps.models.user_pack import UserPack
from apps.models.user_souls import UserSouls
from apps.models.user_equips import UserEquips
from apps.common import utils
from apps.config.game_config import game_config
from apps.models.expect_users import ExceptUsers
from apps.models import data_log_mod
#from apps.models.virtual.card import Card as CardMod
from apps.logics.pack import set_item_deck
from apps.logics.main import __calculate_loopgap_dungeon_time
from apps.logics import vip

def start(rk_user,params):
    '''
    战场入口
    miaoyichao 
    '''
    #检查是否可以进入这个战场 
    user_dungeon_obj = UserDungeon.get_instance(rk_user.uid)
    #检查是否有重试请求，直接返回结果
    rty_fg = False
    last_info = user_dungeon_obj.dungeon_info.get('last',{})
    rty = params.get('rty','')
    if rty and 'enter_rty' in last_info:
        if rty == last_info['enter_rty']:
            last_info['enter_rty_count'] += 1
            rty_fg = True
        else:
            last_info['enter_rty'] = rty
            last_info['enter_rty_count'] = 0
    else:
        last_info['enter_rty'] = rty
        last_info['enter_rty_count'] = 0
    #如果在重试请求，直接返回给上次的结果
    if rty_fg is True:
        dungeon_data = last_info.get("dungeon_data", {})
        if dungeon_data != {}:
            return 0, dungeon_data

    #检查是否重新编队
    if params.get("new_deck"):
        from apps.logics import card
        rc, msg = card.set_decks(rk_user, params)
        if rc:
            return rc, msg

    rc,msg,conf = check_start(rk_user,params,user_dungeon_obj,rty_fg)
    if rc:
        return rc,{'msg':msg}
    #进入战场
    data = enter_dungeon(rk_user,params,user_dungeon_obj,conf,rty_fg)
    #记录日志信息
    log_data = {
        'statament': 'start',
        'dungeon_id': '%s_%s' % (params['floor_id'],params['room_id']),
        'dungeon_type': params['dungeon_type'],
        'card_deck': rk_user.user_cards.deck, 
        'lv': rk_user.user_property.lv
    }
    data_log_mod.set_log('DungeonRecord', rk_user, **log_data)
    return 0,data

def check_start(rk_user,params,user_dungeon_obj,rty_fg=False):
    """
    检查是否可以进入战场
    miaoyichao
    """
    if rty_fg:
        return 0,'',None
    #检查用户武将数量是否已经超过上限
    user_card_obj = UserCards.get(rk_user.uid)
    if user_card_obj.arrive_max_num():
        return 11,utils.get_msg('card','max_num'),None
    #获取战场的配置信息
    dungeon_type = params['dungeon_type']
    floor_id = params['floor_id']
    room_id = params['room_id']
    conf = get_conf(params, rk_user.uid, user_dungeon_obj)
    if not conf:
        return 11,utils.get_msg('dungeon','invalid_dungeon'),None
    #校验每日限次战场
    if user_dungeon_obj.check_limit_dungeon(rk_user,params) is False:
        return 11, utils.get_msg("dungeon", "invalid_limit_dungeon"),None
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    #活动迷宫时，检查迷宫是否开放状态
    if dungeon_type == 'special':
        if now_str > conf['end_time'] or \
        now_str < conf['start_time']:
            return 11,utils.get_msg('dungeon','not_open'),None
    # elif dungeon_type == 'daily':
    #     #每日活动副本 用户等级
    #     user_lv = rk_user.user_property.lv
    #     #开启战场的最小等级
    #     start_dungeon_lv = game_config.daily_dungeon_config.get(floor_id,{})['rooms'].get('room_id',{}).get('user_lv',1)
    #     #判断条件是否达到
    #     if start_dungeon_lv < user_lv:
    #         return 11,utils.get_msg('dungeon','not_open'),None
    else:
        #检查是否达到该战场  比如说以前打到11关  现在是15关则不能打
        if int(floor_id) > int(user_dungeon_obj.normal_current['floor_id']):
            return 11,utils.get_msg('dungeon','not_arrived'),None
        elif floor_id == user_dungeon_obj.normal_current['floor_id']:
            if int(room_id) > int(user_dungeon_obj.normal_current['room_id']):
                return 11,utils.get_msg('dungeon','not_arrived'),None
    last_info = user_dungeon_obj.dungeon_info['last']
    #检查用户体力是否足够
    need_stamina = int(conf['stamina'])
    if rk_user.user_property.stamina < need_stamina:
        return 11,utils.get_msg('user','not_enough_stamina'),None
    #检查药品编队
    rc,res = set_item_deck(rk_user,params)
    if rc:
        return 11,res.get('msg',''),None
    # 检查是否有 进入战场所需的 武将
    if not has_needed_cards(conf, user_card_obj):
        return 11, utils.get_msg('dungeon','needed_special_cards'), None

    return 0, "", conf

def has_needed_cards(conf, user_card_obj):
    #判断进入战场是否需要特定的武将
    if "needed_cards" not in conf:
        return True
    needed_cards = conf["needed_cards"]
    return user_card_obj.has_cards_in_cur_deck(needed_cards)

def get_conf(params, uid = None, user_dungeon_obj = None):
    """
    取得相应的战场配置
    miaoyichao
    """
    #获取战场类型  目前来说只有普通战场 每日战场 限时活动战场
    dungeon_type = params['dungeon_type']
    floor_id = params['floor_id']
    room_id = params['room_id']
    #判断战场类型是否符合要求
    if dungeon_type not in ['normal','special','daily']:
        return None
    #直接深度 copy 需要的部分即可  不需要全部 copy
    if dungeon_type == 'normal':
        #普通战场配置
        floor_conf = copy.deepcopy(game_config.normal_dungeon_config[floor_id])
    elif dungeon_type == 'special':
        #特殊活动战场配置
        floor_conf = copy.deepcopy(game_config.special_dungeon_config[floor_id])
    else:
        #每日活动战场配置
        floor_conf = copy.deepcopy(game_config.daily_dungeon_config[floor_id])
    #获取该room的配置信息
    return_conf = floor_conf['rooms'][room_id]
    #判断是否需要特殊武将
    if "needed_cards" in floor_conf:
        return_conf["needed_cards"] = floor_conf["needed_cards"]
    return return_conf

def enter_dungeon(rk_user,params,user_dungeon_obj,conf,rty_fg=False):
    """
    进入战场
    miaoyichao
    """
    dungeon_type = params['dungeon_type']
    floor_id = params['floor_id']
    room_id = params['room_id']
    #增加进入战场打印
    print 'start_dun_%s:%s_%s_%s' % (str(rk_user.uid),dungeon_type,floor_id,room_id)

    last_info = user_dungeon_obj.dungeon_info['last']

    data = {}
    if not rty_fg:
        #清空last_info里面的内容
        if 'revive_coin' in last_info:
            last_info.pop('revive_coin')
        if 'need_stamina' in last_info:
            last_info.pop('need_stamina')
        if 'dungeon_stamina' in last_info:
            last_info.pop('dungeon_stamina')
        #记录战斗的唯一标识
        dungeon_uid = utils.create_gen_id()
        data['dungeon_uid'] = dungeon_uid
        last_info['dungeon_uid'] = dungeon_uid
        #新用户前7天失败不扣体力 付费用户失败不扣体力
        need_stamina = int(conf['stamina'])
        last_info['dungeon_stamina'] = need_stamina
        #新手用户可以几天不用体力
        # if datetime.datetime.now() < \
        # utils.timestamp_toDatetime(rk_user.add_time) + datetime.timedelta(days=game_config.system_config.get('newbie_days',0)):
        #     last_info['need_stamina'] = need_stamina
        # elif rk_user.user_property.charged_user and user_dungeon_obj.can_free_stamina():
        #     #付费用户每天可以有多少次可以不扣体力
        #     last_info['need_stamina'] = need_stamina
        #     user_dungeon_obj.add_free_stamina_cnt()
        # else:
        #其余情况需要扣除体力
        rk_user.user_property.minus_stamina(need_stamina)
    #计算每一个小节的敌将和掉落信息
    steps_res = calculate_steps(params, conf,rk_user)
    #格式化返回的数据
    data['all_drop_info'] = steps_res['all_drop_info']
    data['steps_info'] = steps_res['steps_info']
    data['dungeon_uid'] = last_info['dungeon_uid']
    data['exp_point'] = conf.get('exp_point',0)
    #将本次计算的信息作为历史信息保存
    last_info['floor_id'] = floor_id
    last_info['room_id'] = room_id
    last_info['dungeon_type'] = dungeon_type
    last_info['all_drop_info'] = steps_res.get('all_drop_info',{})
    #######################################################################################
    last_info['total_gold'] = steps_res['total_gold']
    last_info['dungeon_gold'] = steps_res['dungeon_gold']
    last_info['exp_point'] = conf.get('exp_point',0)
    #######################################################################################
    last_info["dungeon_data"] = data
    now = datetime.datetime.now()
    today_str = now.strftime('%Y-%m-%d')
    last_info["limit_time"] = today_str
    last_info['exp'] = steps_res['exp']
    '''
    这里添加try是为了防止进入战场的时候判断不成功
    因为每日战场和普通战场的每日可打次数的计算是不同的   所以在这里要分开处理  
    普通战场要精确到每一个 room 但是每日活动战场则是精确到 floor 
    '''
    ################################战场次数处理###########################################
    if dungeon_type == 'normal':
        #进入普通战场就减少当天进入的次数
        try:
            user_dungeon_obj.dungeon_repeat_info[dungeon_type][floor_id][room_id] +=1
        except :
            if dungeon_type not in user_dungeon_obj.dungeon_repeat_info:
                user_dungeon_obj.dungeon_repeat_info[dungeon_type]={}
            if floor_id not in user_dungeon_obj.dungeon_repeat_info[dungeon_type]:
                user_dungeon_obj.dungeon_repeat_info[dungeon_type][floor_id] = {}
            if room_id not in user_dungeon_obj.dungeon_repeat_info[dungeon_type][floor_id]:
                user_dungeon_obj.dungeon_repeat_info[dungeon_type][floor_id][room_id] = 0
            user_dungeon_obj.dungeon_repeat_info[dungeon_type][floor_id][room_id] +=1
    elif dungeon_type == 'daily':
        #进入每日战场就减少当天进入的次数  
        try:
            user_dungeon_obj.dungeon_repeat_info[dungeon_type][floor_id] +=1
        except :
            if dungeon_type not in user_dungeon_obj.dungeon_repeat_info:
                user_dungeon_obj.dungeon_repeat_info[dungeon_type]={}
            if floor_id not in user_dungeon_obj.dungeon_repeat_info[dungeon_type]:
                user_dungeon_obj.dungeon_repeat_info[dungeon_type][floor_id] = 0
            user_dungeon_obj.dungeon_repeat_info[dungeon_type][floor_id] +=1
    user_dungeon_obj.put()
    #统计当日可以打多少次
    if dungeon_type == 'normal':
        #获取该战场的今日次数
        data['copy_times'] = user_dungeon_obj.get_today_copy_info(dungeon_type,floor_id,room_id)
        data['copy_times']['floor_id'] = floor_id
        data['copy_times']['room_id'] = room_id
    elif dungeon_type == 'daily':
        data['daily_info'] = user_dungeon_obj.get_daily_info()
        #获取该战场的今日次数
        data['copy_times'] = user_dungeon_obj.get_today_copy_info(dungeon_type,floor_id,room_id)
        data['copy_times']['floor_id'] = floor_id
    #将结果返回给前端
    return data

def calculate_steps(params, conf,rk_user = None,self_leader_skill='',helper_leader_skill=''):
    """
    计算本次进入战场的每步数据
    miaoyichao
    """
    data = {}
    #获取每一步的信息
    all_points_info = []
    #获取每一小节的敌将信息
    steps_info = copy.deepcopy(conf['steps_info'])
    #获取到每一小节 并排序
    step_key = sorted(steps_info.keys())
    user_dungeon_obj = UserDungeon.get_instance(rk_user.uid)
    normal_current = user_dungeon_obj.normal_current
    return_step = []
    max_gold = 0
    for step in step_key:
        #遍历每一小节
        cur_step_info = []
        for monster_info in steps_info[step]:
            monster_list = {}
            #获取金币配置区间
            gold_config = monster_info[1]
            #设置id
            monster_list['monster_id'] = monster_info[0]
            monster_list['gold'] = random.randint(gold_config[0],gold_config[1])
            #统计总的金币掉落
            max_gold += monster_list['gold']
            #将敌将信息给当前小节
            cur_step_info.append(monster_list)
        #将每一步的信息赋值到要返回的信息中
        return_step.append(cur_step_info)
    all_drop_info = {}
    #计算掉落的信息
    dungeon_type = params['dungeon_type']
    if dungeon_type == 'normal':
        dungeon_drop_config  = game_config.drop_info_config.get('normal_dungeon',{})
    elif dungeon_type == 'daily':
        dungeon_drop_config  = game_config.drop_info_config.get('daily_dungeon',{})
    room_drop_config = conf.get('drop_info',{})
    invisible_drop = conf.get('invisible_drop',{})
    all_drop = {'visible_drop':room_drop_config,'invisible_drop':invisible_drop}
    #第一次进入1-1的时候强制给一个装备
    if dungeon_type == 'normal' and params['room_id'] != '0' and normal_current['floor_id'] == '1' and normal_current['room_id'] == '1':
        all_drop_info['equip'] = {}
        all_drop_info['equip']['12002_equip'] = 1
    #获取掉落的你内容
    for visible in all_drop:
        if visible == 'visible_drop':
            visible_type = 'visible'
        elif visible == 'invisible_drop':
            visible_type = 'invisible'
        cur_drop_conf = all_drop[visible]
        for drop_type in cur_drop_conf:
            if drop_type != 'soul':
                #不是碎片的处理
                cur_drop_type_info = cur_drop_conf[drop_type]
                #遍历内容 获取可能掉落的内容
                for drop_info in cur_drop_type_info:
                    #获取掉落的配置信息
                    drop_config = dungeon_drop_config[drop_info]
                    #获取掉落的概率
                    drop_rate = drop_config.get(visible_type,[[0,0],0])[1]
                    #判断掉落是否发生
                    if utils.is_happen(drop_rate):
                        num = random.randint(drop_config[visible_type][0][0],drop_config[visible_type][0][1])
                        #判断掉落的类型是否在返回的内容中
                        '''
                        在这里面赋值而不在for外面赋值的原因是不确定是否掉落
                        '''
                        if drop_type not in all_drop_info:
                            all_drop_info[drop_type] = {}
                        #判断掉落的内容是否在类型中
                        if drop_info not in all_drop_info[drop_type]:
                            all_drop_info[drop_type][drop_info] = 0
                        #赋值掉落的数目
                        all_drop_info[drop_type][drop_info] += num
            else:
                cur_soul_info = cur_drop_conf[drop_type]
                for drop_info in cur_soul_info:
                    if 'card' in drop_info:
                        soul_type = 'card'
                    elif 'equip' in drop_info:
                        soul_type = 'equip'
                    else:
                        break
                    drop_config = dungeon_drop_config[drop_type][drop_info]
                    #获取掉落的概率
                    drop_rate = drop_config[visible_type][1]
                    #判断掉落是否发生
                    if utils.is_happen(drop_rate):
                        num = random.randint(drop_config[visible_type][0][0],drop_config[visible_type][0][1])
                        '''
                        在这里面赋值而不在for外面赋值的原因是不确定是否掉落
                        '''
                        #判断掉落的类型是否在返回的内容中
                        if drop_type not in all_drop_info:
                            all_drop_info[drop_type] = {}
                        #判断掉落的类型是否在返回的内容中
                        if soul_type not in all_drop_info[drop_type]:
                            all_drop_info[drop_type][soul_type] = {}
                        #判断掉落的内容是否在类型中
                        if drop_info not in all_drop_info[drop_type][soul_type]:
                            all_drop_info[drop_type][soul_type][drop_info] = 0
                        #赋值掉落的数目
                        all_drop_info[drop_type][soul_type][drop_info] += num
    #将素材道具随机分配到敌将身上
    steps_info = random_monster_info(conf['boss'],return_step,all_drop_info)
    #结果返回
    data['dungeon_gold'] = conf.get('gold',0)
    data['exp'] = int(conf.get('exp',0))
    data['steps_info'] = steps_info
    data['all_drop_info'] = all_drop_info
    data['total_gold'] = max_gold
    return data

def random_monster_info(boss_id,return_step,all_drop_info):
    '''
    将素材道具  药品  卡牌  碎片随机分配到敌将身上
    miaoyichao
    '''
    for drop_type in all_drop_info:
        if drop_type != 'soul':
            drop_info = all_drop_info.get(drop_type,{})
            for drop_id in drop_info:
                for num in xrange(int(drop_info[drop_id])):
                    step = random.randint(0,len(return_step)-1)
                    location = random.randint(0,len(return_step[step])-1)
                    #素材掉落
                    if drop_type == 'mat':
                        if 'mat_drop_kind' not in return_step[step][location]:
                            return_step[step][location]['mat_drop_kind'] =[]
                        return_step[step][location]['mat_drop_kind'].append(drop_id)
                    #药品掉落
                    elif drop_type == 'item':
                        if 'item_drop_kind' not in return_step[step][location]:
                            return_step[step][location]['item_drop_kind'] =[]
                        return_step[step][location]['item_drop_kind'].append(drop_id)
                    #道具掉落
                    elif drop_type == 'props':
                        if 'props_drop_kind' not in return_step[step][location]:
                            return_step[step][location]['props_drop_kind'] =[]
                        return_step[step][location]['props_drop_kind'].append(drop_id)
                    #武器掉落
                    elif drop_type == 'equip':
                        if 'equip_drop_kind' not in return_step[step][location]:
                            return_step[step][location]['equip_drop_kind'] =[]
                        return_step[step][location]['equip_drop_kind'].append(drop_id)
                    #武将掉落
                    if drop_type == 'card':
                        if 'card' not in return_step[step][location]:
                            return_step[step][location]['card'] =[]
                        return_step[step][location]['card'].append(drop_id)
        elif drop_type == 'soul':
            #获取所有的碎片信息
            all_soul_info = all_drop_info.get(drop_type,{})
            for soul_type in all_soul_info:
                '''
                这里将card和equip分开的主要原因是因为武将碎片只能有boss掉落  其他不掉落
                所以才进行区分
                '''
                #处理是武将碎片的信息
                if soul_type == 'card':
                    #遍历武将碎片
                    for card_soul_id in all_soul_info[soul_type]:
                        #获取武将碎片的数量
                        monster_num = int(all_soul_info[soul_type][card_soul_id])
                        for monster in return_step[-1]:
                            #获取敌将的 id
                            monster_id = monster['monster_id']
                            #将武将碎片放在最后一关的boss身上
                            if monster_id in boss_id:
                                monster_card_id = game_config.monster_config.get(monster_id,'')
                                if monster_card_id == card_soul_id:
                                    #如果敌将id和bossid一样的话 证明可以从该敌将上掉落该碎片
                                    for num in xrange(monster_num):
                                        #添加武将碎片
                                        if 'card_soul' not in monster:
                                            monster['card_soul'] =[]
                                        monster['card_soul'].append(card_soul_id)
                elif soul_type == 'equip':
                    for equip_soul_id in all_soul_info[soul_type]:
                        for num in xrange(int(all_soul_info[soul_type][equip_soul_id])):
                            step = random.randint(0,len(return_step)-1)
                            location = random.randint(0,len(return_step[step])-1)
                            #武器掉落
                            if 'equip_soul_drop_kind' not in return_step[step][location]:
                                return_step[step][location]['equip_soul_drop_kind'] =[]
                            return_step[step][location]['equip_soul_drop_kind'].append(equip_soul_id)
                else:
                    pass
        else:
            pass
    return return_step


def end(rk_user,params):
    """
    离开战场请求
    """
    data = {}
    user_dungeon_obj = UserDungeon.get(rk_user.uid)
    #记录中如果没有未完成的战场，则返回
    if not user_dungeon_obj.dungeon_info['last'].get('floor_id'):
        return 11,{'msg':utils.get_msg('dungeon','already_end')}
    #给用户奖励
    last_info = user_dungeon_obj.dungeon_info['last']
    floor_id = last_info['floor_id']
    room_id = last_info['room_id']
    dungeon_type = last_info['dungeon_type']
    #检查场和局
    para_floor_id = params['floor_id']
    para_room_id = params['room_id']
    para_dungeon_type = params['dungeon_type']

    where = 'dungeon_%s_%s_%s' % (para_dungeon_type[0], para_floor_id, para_room_id)

    if floor_id != para_floor_id or room_id != para_room_id or dungeon_type != para_dungeon_type:
        return 11,{'msg':utils.get_msg('dungeon','unsame_dungeon')}

    #检查战场唯一标识
    para_dungeon_uid = params.get('dungeon_uid','')
    if para_dungeon_uid and para_dungeon_uid != last_info['dungeon_uid']:
        return 11,{'msg':utils.get_msg('dungeon','unsame_dungeon')}
    #判断战场是否是完成的
    if params.get('result','1') == '0':
        data = {}#__resolve_fail(rk_user,user_dungeon_obj,ver=float(params['version']))
        return 0,data
    #获取获得的金币
    user_gold = int(params['user_gold'])
    #扣除药水
    use_items = params.get('use_items','')
    if use_items:
        rc,res_dic = use_item(rk_user,{'items':use_items})
        if rc:
            return rc,res_dic
    #胜利扣除复活的元宝
    if 'revive_coin' in last_info:
        if rk_user.user_property.minus_coin(last_info['revive_coin'],\
                'revive_%s_%s_%s'%(last_info.get("floor_id"),last_info.get("room_id"),last_info.get("dungeon_type"))):
                data_log_mod.set_log("ConsumeRecord", rk_user, 
                                    lv=rk_user.user_property.lv,
                                    num=last_info['revive_coin'],
                                    consume_type='revive',
                                    before_coin=rk_user.user_property.coin + last_info['revive_coin'],
                                    after_coin=rk_user.user_property.coin,
                )
        else:
            return 11,{'msg':utils.get_msg('dungeon','revive_err')}
    #金币 打怪掉的
    get_gold = min(user_gold,last_info['total_gold'])
    #获取打怪掉的和通关奖励的金币之和
    get_gold = int((get_gold + last_info['dungeon_gold']))
    if get_gold:
        rk_user.user_property.add_gold(get_gold,where)
    data['get_gold'] = get_gold
    ####异常记录####
    if user_gold > last_info['total_gold']:
        dungeon_except = ExceptUsers.get_instance('normal_dungeon')
        dungeon_except.set_users('%s_%s'%(floor_id,room_id),rk_user.uid)
    # all_drop_info mat item props   添加背包里面的掉落信息
    all_drop_info = last_info['all_drop_info']
    user_pack_obj = UserPack.get(rk_user.uid)
    data['get_material'] = {}
    data['get_item'] = {}
    data['get_props'] = {}
    pack_list = ['mat','item','props']
    for drop_type in pack_list:
        drop_info = all_drop_info.get(drop_type,{})
        for drop_id in drop_info:
            num = int(drop_info[drop_id])
            if drop_type == 'mat':
                #添加素材
                user_pack_obj.add_material(drop_id,num)
                data['get_material'][drop_id] = num
            elif drop_type == 'item':
                #添加药品
                user_pack_obj.add_item(drop_id,num)
                data['get_item'][drop_id] = num
            elif drop_type == 'props':
                #添加道具
                user_pack_obj.add_props(drop_id,num)
                data['get_props'][drop_id] = num
            else:
                pass
    #重新整理药品编队的信息 因为药品内容可能变动  这时候编队信息也可能变动  获取最新的即可
    data['item_deck'] = user_pack_obj.item_deck
    #加碎片
    data['get_souls'] = {}
    if last_info['all_drop_info'].get('soul'):
        user_souls_obj = UserSouls.get_instance(rk_user.uid)
        soul =  last_info['all_drop_info']['soul']
        for soul_type in soul:
            data['get_souls'][soul_type] = {}
            if soul_type == 'equip':
                #如果碎片是普通装备的话的处理逻辑
                drop_soul_info = soul[soul_type]
                for drop_id in drop_soul_info:
                    num = int(drop_soul_info[drop_id])
                    #装备的添加
                    user_souls_obj.add_equip_soul(drop_id,num,where=where)
                    data['get_souls'][soul_type][drop_id] = num
            elif soul_type == 'card':
                #如果碎片类型是武将的话
                drop_card_soul_info = soul[soul_type]
                for drop_id in drop_card_soul_info:
                    num = int(drop_card_soul_info[drop_id])
                    user_souls_obj.add_normal_soul(drop_id,num,where=where)
                    data['get_souls'][soul_type][drop_id] = num
            else:
                pass

    #处理装备掉落返回值
    user_equip_obj = UserEquips.get(rk_user.uid)
    get_equips = []
    for eid in last_info['all_drop_info'].get('equip',{}):
        num = int(last_info['all_drop_info']['equip'][eid])
        for i in xrange(num):
            fg, all_equips_num, ueid, is_first = user_equip_obj.add_equip(eid, 'dungeon_drop')
            temp = {
                    'ueid':ueid,
            }
            temp.update(user_equip_obj.equips[ueid])
            get_equips.append(temp)
    data['get_equip'] = get_equips
    user_card_obj = UserCards.get(rk_user.uid)
    #图鉴更新列表
    get_cards = []
    for cid in last_info['all_drop_info'].get('card',{}):
        num = int(last_info['all_drop_info']['card'][cid])
        for i in xrange(num):
            card_lv = 1
            success_fg,all_cards_num,ucid,is_first = user_card_obj.add_card(cid,card_lv,where=where)
            temp = {
                    'ucid':ucid,
            }
            temp.update(user_card_obj.cards[ucid])
            get_cards.append(temp)
    #处理新手引导的内容
    #data_tmp = sepcial_treat_dungen(rk_user,user_dungeon_obj,dungeon_type,floor_id,room_id,params['version'])
    #get_cards += data_tmp.get('get_upd_cards',[])
    #加经验
    lv_up,get_upg_data = rk_user.user_property.add_exp(last_info['exp'],where)
    data['get_exp'] = last_info['exp']
    get_cards.extend(get_upg_data.get('get_card',[]))
    #添加经验点
    get_exp_point = last_info['exp_point']
    if get_exp_point:
        rk_user.user_property.add_card_exp_point(get_exp_point)
    data['get_exp_point'] = get_exp_point
    data['get_card'] = get_cards
    #if 'get_material' in data_tmp:
    #    for mat_id in data_tmp['get_material']:
    #        if mat_id in data['get_material']:
    #            data['get_material'][mat_id] += data_tmp['get_material'][mat_id]
    #        else:
    #            data['get_material'][mat_id] = data_tmp['get_material'][mat_id]
    #用户升级的用于引导奖励 
    if 'get_material' in get_upg_data:
        for mat_id in get_upg_data['get_material']:
            if mat_id in data['get_material']:
                data['get_material'][mat_id] += get_upg_data['get_material'][mat_id]
            else:
                data['get_material'][mat_id] = get_upg_data['get_material'][mat_id]
    #判断新手引导
    newbie_step = int(params.get('newbie_step',0))
    if newbie_step:
        rk_user.user_property.set_newbie_steps(newbie_step)
    #更新用户的迷宫状态
    data['dungeon_info'] = user_dungeon_obj.update_dungeon_info(dungeon_type,floor_id,room_id,once_daily = last_info.get('once_daily',False))
    if 'clear_floor_coin' in data['dungeon_info']:
        data['clear_floor_coin'] = data['dungeon_info'].pop('clear_floor_coin')
    log_data = {
        'statament': 'end',
        'dungeon_id': '%s_%s' % (para_floor_id,para_room_id),
        'dungeon_type': para_dungeon_type,
        'card_deck': user_card_obj.deck,
        'exp_point': get_exp_point,
        'lv': rk_user.user_property.lv,
    }

    #记录该次战场的星级
    if dungeon_type == 'normal':
        #获取难度系数
        hard_ratio = params.get('hard_ratio', 'normal')         # 中等难度
        #获取星级系数
        star_ratio = int(params['star_ratio'])
        data['star_ratio'] = star_ratio
        user_dungeon_obj.update_has_played_info(dungeon_type,floor_id,room_id,hard_ratio,star_ratio)

        has_played_floor_info = user_dungeon_obj.has_played_info['normal'].get(floor_id)
        
        if has_played_floor_info:
            #格式化要返回的部分数据
            tmpdata = {}
            tmpdata['floor_id'] = floor_id
            tmpdata['rooms_id'] = room_id
            tmpdata['floor_get_star'] = has_played_floor_info['cur_star']
            tmpdata['hard'] = hard_ratio
            tmpdata['room_get_star'] = has_played_floor_info['rooms'][room_id][hard_ratio]['get_star']
            tmpdata['room_perfect'] = has_played_floor_info['rooms'][room_id]['perfect']
            data['floor_info'] = tmpdata
        
    elif dungeon_type == 'daily':
        pass
    user_dungeon_obj.put()
    
    data_log_mod.set_log('DungeonRecord', rk_user, **log_data)
    return 0,data
            
def revive(rk_user,params):
    """复活
    """
    user_dungeon_obj = UserDungeon.get(rk_user.uid)
    last_info = user_dungeon_obj.dungeon_info['last']
    revive_coin = game_config.system_config['revive_coin']
    #检查是否有重试请求，重试时，直接返回结果
    #检查用户coin是否足够
    last_revive_coin = last_info.get('revive_coin',0)
    if rk_user.user_property.coin < revive_coin+last_revive_coin:
        return 11,{'msg':utils.get_msg('user','not_enough_coin')}
    last_info['revive_coin'] = last_revive_coin + revive_coin
    user_dungeon_obj.put()
    return 0,{}

def recover_stamina(rk_user,params):
    """
    回复体力
    miaoyichao
    """
    recover_stamina_coin = game_config.system_config['recover_stamina_coin']
    #检查用户体力是否已满
    if rk_user.user_property.max_recover():
        return 11,{'msg':utils.get_msg('user','max_recover')}
    #检查vip可以回复的次数到了没
    if not vip.check_limit_recover(rk_user,'recover_stamina'):
        return 11,{'msg':utils.get_msg('user','max_times')}
    else:
        #检查用户coin是否足够 并扣钱
        if not rk_user.user_property.minus_coin(recover_stamina_coin,'recover_stamina'):
            return 11,{'msg':utils.get_msg('user','not_enough_coin')}
        #添加回复次数
        rk_user.user_property.add_recover_times('recover_stamina')
        rk_user.user_property.recover_stamina()
        data_log_mod.set_log("ConsumeRecord", rk_user, 
                    lv=rk_user.user_property.lv,
                    num=recover_stamina_coin,
                    consume_type='recover_stamina',
                    before_coin=rk_user.user_property.coin + recover_stamina_coin,
                    after_coin=rk_user.user_property.coin,
        )

        return 0,{}

def use_item(rk_user,params):
    """消耗药品
       params:
           items:药品id:数量,药品id:数量,药品id:数量
    """
    user_pack_obj = UserPack.get_instance(rk_user.uid)
    item_deck = user_pack_obj.item_deck
    items = params['items'].split(',')
    new_items = utils.remove_null(items)
    for item in new_items:
        item_id,num = item.split(':')
        num = int(num)
        found = False
        for i in item_deck:
            if item_id in i and i[item_id] < num:
                return 11,{'msg':utils.get_msg('pack', 'not_enough_item')}
            elif item_id in i and i[item_id] >= num:
                #item deck中减去相应数量的药品
                i[item_id] -= num
                # if i[item_id] == 0:
                #     i.pop(item_id)
                #背包中减去相应的物品
                if not user_pack_obj.minus_item(item_id,num,'dungeon_use'):
                    return 11,{'msg':utils.get_msg('pack', 'not_enough_item')}
                found = True
                break
        if not found:
            return 11,{'msg':utils.get_msg('pack', 'not_enough_item')}
    user_pack_obj.put()
    return 0,{}

#當第一次過1-1的時候，根據主將給素材卡
def sepcial_treat_dungen(rk_user,user_dungeon_obj,dungeon_type,floor_id,room_id,version=None):
    date_temp = {}
    normal_current = user_dungeon_obj.dungeon_info['normal_current']
    if floor_id == normal_current['floor_id'] and \
        room_id == normal_current['room_id']:
        user_property_obj = rk_user.user_property
        if floor_id == '1' and room_id == '1':
            user_country = user_property_obj.country
            card_cid = game_config.user_init_config['init_leader_card'][str(user_country)]
            cid_config = CardMod.get(card_cid)
            if cid_config and cid_config.upg_target:
                max_lv = cid_config.max_lv
                upg_gold = cid_config.upg_gold
                upg_need = cid_config.upg_need
                if upg_gold:
                    user_property_obj.add_gold(upg_gold,where='dungen_n_1_1_upgrate')
                if upg_need:
                    user_cards_obj = UserCards.get(user_dungeon_obj.uid)
                    suit_ucids = [ ucid for ucid in user_cards_obj.cards \
                                    if user_cards_obj.cards[ucid]['cid'] == card_cid \
                                    and user_cards_obj.cards[ucid]['lv'] == max_lv
                                ]
                    if suit_ucids:
                        user_property_obj.set_upgrade_tutorial(True,suit_ucids[0])
                        get_upd_cards = []
                        for cid in upg_need:
                            success_fg,all_cards_num,ucid,is_first = user_cards_obj.add_card(cid,where='dungen_n_1_1_upgrate')
                            temp = {'ucid':ucid}
                            temp.update(user_cards_obj.cards[ucid])
                            get_upd_cards.append(temp)
                        date_temp['get_upd_cards'] = get_upd_cards
    return date_temp

def open_special_dungeon(rk_user,params):
    """提前开启限时战场，需要花费元宝
       params:
           floor_id:战场id
    """
    floor_id = params['floor_id']
    floor_conf = game_config.special_dungeon_config.get(floor_id,{})
    if 'loop_gap' in floor_conf and game_config.dungeon_world_config.get('open_special_is_open',False):
        loop_dungeon_time = __calculate_loopgap_dungeon_time(floor_conf)
        now_str = utils.datetime_toString(datetime.datetime.now())
        #已经开启的不用花元宝
        if (now_str>=loop_dungeon_time[0][0] and now_str<=loop_dungeon_time[0][1]) or\
        (now_str>=loop_dungeon_time[1][0] and now_str<=loop_dungeon_time[1][1]):
            return 0,{'msg':utils.get_msg('dungeon','already_open')}
        user_dungeon_obj = UserDungeon.get(rk_user.uid)
        if floor_id in user_dungeon_obj.dungeon_info['special'] and 'open_dungeon_info' in user_dungeon_obj.dungeon_info['special'][floor_id]:
            open_dungeon_info = user_dungeon_obj.dungeon_info['special'][floor_id]['open_dungeon_info']
            open_coin = open_dungeon_info['open_coin']
            if not rk_user.user_property.minus_coin(open_coin,\
                'open_special_dungeon_%s' % floor_id):
                return 11,{'msg':utils.get_msg('user','not_enough_coin')}
            else:
                data_log_mod.set_log("ConsumeRecord", rk_user, 
                                    lv=rk_user.user_property.lv,
                                    num=open_coin,
                                    consume_type='open_special_dungeon',
                                    before_coin=rk_user.user_property.coin + open_coin,
                                    after_coin=rk_user.user_property.coin
                )

                open_dungeon_info['expire_time'] = int(time.time()) + game_config.dungeon_world_config.get('open_special_time',3600)
                open_dungeon_info['open_cnt'] += 1
                open_special_coin = game_config.dungeon_world_config.get('open_special_coin',[])
                if open_special_coin:
                    if open_dungeon_info['open_cnt']+1<=len(open_special_coin):
                        next_open_coin = open_special_coin[open_dungeon_info['open_cnt']]
                    else:
                        next_open_coin = open_special_coin[-1]
                    open_dungeon_info['open_coin'] = next_open_coin
                user_dungeon_obj.put()
                return 0,{
                          'dungeon_info':{
                                'normal_current':user_dungeon_obj.dungeon_info['normal_current'],
                                'special':user_dungeon_obj.dungeon_info['special'],
                                'weekly':user_dungeon_obj.dungeon_info.get('weekly',{}),
                                }
                          }
        else:
            return 11,{'msg':utils.get_msg('dungeon','can_not_open_now')}
    else:
        return 11,{'msg':utils.get_msg('dungeon','can_not_open_now')}
    
def get_box_gift(rk_user,params):
    '''
    * 领取宝箱奖励
    '''
    data = {}
    get_step = params.get('step','0')
    floor_id = params.get('floor_id')
    box_type = params.get('box_type')
    dungeon_config = game_config.dungeon_world_config.get('box_info',{})
    floor_conf = dungeon_config.get(floor_id,{})
    box_info = floor_conf[box_type]
    if get_step == '0':
        #处理前端要现实的宝箱的内容
        if box_type in floor_conf:
            data['box_info'] = utils.format_award(box_info)
            data['box_star'] = int(floor_conf[box_type+'_star'])
        else:
            return 11,{'msg':utils.get_msg('dungeon', 'no_box_config')}
        return 0,data
    elif get_step == '1':
        #处理前端要领取的宝箱信息
        user_dungeon_obj = UserDungeon.get(rk_user.uid)
        has_played_info_copy = copy.deepcopy(user_dungeon_obj.has_played_info)
        if floor_id in has_played_info_copy.get('normal',{}):
            floor_info = has_played_info_copy['normal'][floor_id]
            #查看领取条件是否合适
            floor_get_star = floor_info['cur_star']
            if floor_get_star < int(floor_conf[box_type+'_star']):
                return 11,{'msg':utils.get_msg('dungeon', 'box_can_not_open')}
            if floor_info[box_type]:
                #宝箱已领取情况
               return 11,{'msg':utils.get_msg('dungeon', 'has_got_box_award')}
            else:
                #领取宝箱逻辑 格式化内容
                award = utils.format_award(box_info)
                user_property_obj = UserProperty.get(rk_user.uid)
                #将宝箱里面的内容添加到用户信息里面
                award_info = user_property_obj.test_give_award(award,where='get_'+box_type)
                #格式化要返回的内容
                data['award_info'] = award_info
                data['floor_info'] = {}
                data['floor_info']['floor_id'] = floor_id
                data['floor_info']['box_type'] = box_type
                data['floor_info']['box_flag'] = True
                #重置标志位
                user_dungeon_obj.has_played_info['normal'][floor_id][box_type] = True
                user_dungeon_obj.put()
                #判断新手引导
                newbie_step = int(params.get('newbie_step',0))
                if newbie_step:
                    rk_user.user_property.set_newbie_steps(newbie_step)
                #结果返回
                return 0,data
        else:
            return 11,{'msg':utils.get_msg('dungeon', 'invalid_dungeon_info')}
    else:
        #未识别的内容
        return 11,{'msg':utils.get_msg('dungeon', 'invalid_dungeon_info')}


def recover_copy(rk_user,params):
    """
    * 重置副本次数
    * miaoyichao
    """
    recover_copy_coin = game_config.system_config['recover_copy_coin']
    #检查vip可以回复的次数到了没
    if not vip.check_limit_recover(rk_user,'recover_copy'):
        return 11,{'msg':utils.get_msg('user','max_recover_copy_times')}
    else:
        try:
            #检测参数是否合法
            dungeon_type = params['dungeon_type']
            floor_id = params['floor_id']
            room_id  = params['room_id']
        except:
            return 11,{'msg':utils.get_msg('dungeon','invalid_dungeon_info')}
        #检查用户coin是否足够
        if not rk_user.user_property.minus_coin(recover_copy_coin,'recover_copy'):
            return 11,{'msg':utils.get_msg('user','not_enough_coin')}
        #添加回复次数
        rk_user.user_property.add_recover_times('recover_copy',dungeon_type)
        user_dungeon_obj = UserDungeon.get(rk_user.uid)
        user_dungeon_obj.recover_copy(dungeon_type,floor_id,room_id)
        data_log_mod.set_log("ConsumeRecord", rk_user, 
                            lv=rk_user.user_property.lv,
                            num=recover_copy_coin,
                            consume_type='recover_copy',
                            before_coin=rk_user.user_property.coin + recover_copy_coin,
                            after_coin=rk_user.user_property.coin
        )
        return 0,{}
