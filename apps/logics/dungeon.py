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
from apps.logics.main import __calculate_loopgap_dungeon_time
from apps.logics import vip
from apps.common.exceptions import GameLogicError
from apps.logics import card
from apps.logics import activity
from apps.logics.activity import multiply_income
from apps.models.user_task import UserTask

def start(rk_user, params):
    """战场入口"""

    # 检查是否可以进入这个战场 
    user_dungeon_obj = rk_user.user_dungeon

    # 检查是否重新编队
    if params.get("new_deck"):
        card.set_decks(rk_user, params)

    conf = check_start(rk_user, params, user_dungeon_obj)

    #进入战场
    data = enter_dungeon(rk_user, params, user_dungeon_obj, conf)
    #记录日志信息
    log_data = {
        'statament': 'start',
        'dungeon_id': '%s_%s' % (params['floor_id'],params['room_id']),
        'dungeon_type': params['dungeon_type'],
        'card_deck': rk_user.user_cards.deck, 
        'lv': rk_user.user_property.lv
    }
    data_log_mod.set_log('DungeonRecord', rk_user, **log_data)
    return data

def check_start(rk_user,params,user_dungeon_obj):
    """检查是否可以进入战场"""

    user_card_obj = UserCards.get(rk_user.uid)
    user_lv = rk_user.user_property.lv
    #获取战场的配置信息
    dungeon_type = params['dungeon_type']
    floor_id = params['floor_id']
    room_id = params['room_id']
    conf = get_conf(params, rk_user.uid, user_dungeon_obj)
    if not conf:
        raise GameLogicError('dungeon', 'invalid_dungeon')
    #校验每日限次战场
    if user_dungeon_obj.check_limit_dungeon(rk_user,params) is False:
        raise GameLogicError('dungeon', 'invalid_limit_dungeon')
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    #活动迷宫时，检查迷宫是否开放状态
    if dungeon_type == 'special':
        if now_str > conf['end_time'] or now_str < conf['start_time']:
            raise GameLogicError('dungeon', 'not_open')
    elif dungeon_type == 'daily':
        #每日活动副本 用户等级
        
        #开启战场的最小等级
        start_dungeon_lv = game_config.daily_dungeon_config.get(floor_id,{})['rooms'].get(room_id,{}).get('user_lv',1)
        #判断条件是否达到
        if user_lv < start_dungeon_lv:
            raise GameLogicError('dungeon', 'not_arrived_lv')
    else:
        # 开启战场的最小等级
        start_dungeon_lv = game_config.normal_dungeon_config[floor_id]['rooms'][room_id].get('need_lv',1)
        #判断条件是否达到
        if user_lv < start_dungeon_lv:
            raise GameLogicError('dungeon', 'not_arrived_lv')
        #检查是否达到该战场  比如说以前打到11关  现在是15关则不能打
        if int(floor_id) > int(user_dungeon_obj.normal_current['floor_id']):
            raise GameLogicError('dungeon', 'not_arrived')
        elif floor_id == user_dungeon_obj.normal_current['floor_id']:
            if int(room_id) > int(user_dungeon_obj.normal_current['room_id']):
                raise GameLogicError('dungeon', 'not_arrived')

    #检查用户体力是否足够
    need_stamina = int(conf['stamina'])
    if rk_user.user_property.stamina < need_stamina:
        raise GameLogicError('user','not_enough_stamina')

    # 检查是否有 进入战场所需的 武将
    if not has_needed_cards(conf, user_card_obj):
        raise GameLogicError('dungeon','needed_special_cards')

    # 进入战场要扣一点体力
    rk_user.user_property.minus_stamina(1 if need_stamina > 0 else 0)

    return conf

def has_needed_cards(conf, user_card_obj):
    #判断进入战场是否需要特定的武将
    if "needed_cards" not in conf:
        return True
    needed_cards = conf["needed_cards"]
    return user_card_obj.has_cards_in_cur_deck(needed_cards)

def get_conf(params, uid=None, user_dungeon_obj=None):
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
        floor_conf = game_config.normal_dungeon_config[floor_id]
    # elif dungeon_type == 'special':
    #     #特殊活动战场配置
    #     floor_conf = game_config.special_dungeon_config[floor_id]
    else:
        #每日活动战场配置
        floor_conf = game_config.daily_dungeon_config[floor_id]
    #获取该room的配置信息
    return_conf = copy.deepcopy(floor_conf['rooms'][room_id])
    #判断是否需要特殊武将
    if "needed_cards" in floor_conf:
        return_conf["needed_cards"] = floor_conf["needed_cards"]
    return return_conf

def enter_dungeon(rk_user, params, user_dungeon_obj, conf):
    """进入战场"""
    
    dungeon_type = params['dungeon_type']
    floor_id = params['floor_id']
    room_id = params['room_id']
    #增加进入战场打印
    print 'start_dun_%s:%s_%s_%s' % (str(rk_user.uid),dungeon_type,floor_id,room_id)

    ########  运营活动  特定时间内收益翻倍
    multiply = 1
    if dungeon_type == 'daily':
        multiply_income_conf = rk_user.game_config.operat_config.get("multiply_income", {}
        ).get("daily_dungeon", {}).get(floor_id)
        multiply = multiply_income(multiply_income_conf)
    ########  

    last_info = {}

    data = {}
    #记录战斗的唯一标识
    dungeon_uid = utils.create_gen_id()
    data['dungeon_uid'] = dungeon_uid
    last_info['dungeon_uid'] = dungeon_uid
    #新用户前7天失败不扣体力 付费用户失败不扣体力
    need_stamina = int(conf['stamina'])
    last_info['dungeon_stamina'] = need_stamina
    #计算每一个小节的敌将和掉落信息
    steps_res = calculate_steps(params, conf, rk_user, multiply)

    ########  运营活动 特定时间额外掉落物品 扫荡时也有类似逻辑  万恶的代码
    more_drop = activity.more_dungeon_drop(dungeon_type, floor_id, room_id, times=1)
    if more_drop:
        all_drop_info = steps_res['all_drop_info']
        for thing_type, things_id_num in more_drop.items():
            if thing_type == 'gold':
                steps_res['dungeon_gold'] = steps_res['dungeon_gold'] + more_drop['gold']['num']
                continue
            all_drop_info.setdefault(thing_type, {})
            for thing_id, num in things_id_num.items():
                if thing_type == 'soul':
                    if 'card' in thing_id:
                        soul_type = 'card'
                    elif 'equip' in thing_id:
                        soul_type = 'equip'
                    all_drop_info[thing_type].setdefault(soul_type, {})
                    all_drop_info[thing_type][soul_type][thing_id] = all_drop_info[thing_type][soul_type].get(thing_id, 0) + num
                else:
                    all_drop_info[thing_type][thing_id] = all_drop_info[thing_type].get(thing_id, 0) + num
    ###################  

    #格式化返回的数据
    data['all_drop_info'] = steps_res['all_drop_info']
    data['steps_info'] = steps_res['steps_info']
    data['dungeon_uid'] = last_info['dungeon_uid']
    data['exp_point'] = steps_res['exp_point']
    data['boss_id'] = conf['boss'][0]
    #将本次计算的信息作为历史信息保存
    last_info['floor_id'] = floor_id
    last_info['room_id'] = room_id
    last_info['dungeon_type'] = dungeon_type
    last_info['all_drop_info'] = steps_res['all_drop_info']
    #######################################################################################
    last_info['total_gold'] = steps_res['total_gold']
    last_info['dungeon_gold'] = steps_res['dungeon_gold']
    last_info['exp_point'] = steps_res['exp_point']
    #######################################################################################
    last_info["dungeon_data"] = data
    now = datetime.datetime.now()
    today_str = now.strftime('%Y-%m-%d')
    last_info["limit_time"] = today_str
    last_info['exp'] = steps_res['exp']

    user_dungeon_obj.dungeon_info['last'] = last_info
    user_dungeon_obj.put()
    #将结果返回给前端
    return data

def calculate_steps(params, conf, rk_user, multiply=1):
    """
    计算本次进入战场的每步数据
    Arges:
        multiply  活动收益翻倍翻得倍数
    """
    data = {}
    #获取每一小节的敌将信息
    steps_info = copy.deepcopy(conf['steps_info'])
    #获取到每一小节 并排序
    step_key = sorted(steps_info.keys())
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
            max_gold += monster_list['gold'] * multiply
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
        dungeon_drop_config = game_config.drop_info_config.get('daily_dungeon',{})
    room_drop_config = conf.get('drop_info',{})
    invisible_drop = conf.get('invisible_drop',{})
    all_drop = {'visible_drop':room_drop_config,'invisible_drop':invisible_drop}
    # 添加必掉的物品
    if 'must_drop' in conf:
        all_drop_info.update(conf['must_drop'])
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
                        num = random.randint(drop_config[visible_type][0][0],drop_config[visible_type][0][1]) * multiply
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
                        num = random.randint(drop_config[visible_type][0][0],drop_config[visible_type][0][1]) * multiply
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

    data['dungeon_gold'] = conf.get('gold',0) * multiply
    data['exp'] = int(conf.get('exp',0))
    data['steps_info'] = steps_info
    data['all_drop_info'] = all_drop_info
    data['total_gold'] = max_gold * multiply
    data['exp_point'] = conf.get('exp_point',0) * multiply

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

    where = 'dungeon_%s_%s_%s' % (para_dungeon_type, para_floor_id, para_room_id)

    if floor_id != para_floor_id or room_id != para_room_id or dungeon_type != para_dungeon_type:
        return 11,{'msg':utils.get_msg('dungeon','unsame_dungeon')}

    #检查战场唯一标识
    para_dungeon_uid = params.get('dungeon_uid','')
    if para_dungeon_uid and para_dungeon_uid != last_info['dungeon_uid']:
        return 11,{'msg':utils.get_msg('dungeon','unsame_dungeon')}
    #判断战场是否是完成的
    if params.get('result','1') == '0':
        data = {'dungeon_fail': True}#__resolve_fail(rk_user,user_dungeon_obj,ver=float(params['version']))
        return 0,data
    #获取获得的金币
    user_gold = int(params['user_gold'])

    #胜利扣除复活的元宝
    if 'revive_coin' in last_info:
        if not rk_user.user_property.minus_coin(last_info['revive_coin'],
                'revive_%s_%s_%s'%(last_info.get("floor_id"),last_info.get("room_id"),last_info.get("dungeon_type"))):
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
    # data['get_item'] = {}
    data['get_props'] = {}
    pack_list = ['mat','item','props']
    for drop_type in pack_list:
        drop_info = all_drop_info.get(drop_type,{})
        for drop_id in drop_info:
            num = int(drop_info[drop_id])
            if drop_type == 'mat':
                #添加素材
                user_pack_obj.add_material(drop_id, num, where=where)
                data['get_material'][drop_id] = num
            elif drop_type == 'props':
                #添加道具
                user_pack_obj.add_props(drop_id, num, where=where)
                data['get_props'][drop_id] = num
            else:
                pass

    #  成功打完战场才扣体力
    need_stamina = last_info['dungeon_stamina']
    #新手用户可以几天不用体力
    # if datetime.datetime.now() < \
    # utils.timestamp_toDatetime(rk_user.add_time) + datetime.timedelta(days=game_config.system_config.get('newbie_days',0)):
    #     last_info['need_stamina'] = need_stamina
    # elif rk_user.user_property.charged_user and user_dungeon_obj.can_free_stamina():
    #     #付费用户每天可以有多少次可以不扣体力
    #     last_info['need_stamina'] = need_stamina
    #     user_dungeon_obj.add_free_stamina_cnt()
    # else:
    # 需要扣除体力  进战场时已经扣一点  这里只扣剩下的
    rk_user.user_property.minus_stamina(max(need_stamina - 1, 0))

    #加碎片
    data['get_souls'] = {}
    if last_info['all_drop_info'].get('soul'):
        user_souls_obj = UserSouls.get_instance(rk_user.uid)
        soul = last_info['all_drop_info']['soul']
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
            fg, all_equips_num, ueid, is_first = user_equip_obj.add_equip(eid, where=where)
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
    #加经验
    lv_up,get_upg_data = rk_user.user_property.add_exp(last_info['exp'],where)
    data['get_exp'] = last_info['exp']
    get_cards.extend(get_upg_data.get('get_card',[]))
    #添加经验点
    get_exp_point = last_info['exp_point']
    if get_exp_point:
        rk_user.user_property.add_card_exp_point(get_exp_point, where)
    data['get_exp_point'] = get_exp_point
    data['get_card'] = get_cards
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
        rk_user.user_property.set_newbie_steps(newbie_step, where)
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
    if dungeon_type in ['normal', 'daily']:
        #获取难度系数
        hard_ratio = params.get('hard_ratio', 'normal')         # 中等难度
        #获取星级系数
        star_ratio = int(params['star_ratio'])
        data['star_ratio'] = star_ratio
        user_dungeon_obj.update_has_played_info(dungeon_type,floor_id,room_id,hard_ratio,star_ratio)

        has_played_floor_info = user_dungeon_obj.has_played_info[dungeon_type].get(floor_id)
        
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
    else:
        pass

    # 战场次数处理 因为每日战场和普通战场的每日可打次数的计算是不同的 
    # 普通战场要精确到每一个 room 但是每日活动战场则是精确到 floor 
    dungeon_repeat_info = user_dungeon_obj.dungeon_repeat_info
    dungeon_repeat_info.setdefault(dungeon_type, {})
    if dungeon_type == 'normal':
        #进入普通战场就减少当天进入的次数
        dungeon_repeat_info[dungeon_type].setdefault(floor_id, {})
        dungeon_repeat_info[dungeon_type][floor_id].setdefault(room_id, 0)
        dungeon_repeat_info[dungeon_type][floor_id][room_id] +=1
    elif dungeon_type == 'daily':
        #进入每日战场就减少当天进入的次数  
        dungeon_repeat_info[dungeon_type].setdefault(floor_id, 0)
        dungeon_repeat_info[dungeon_type][floor_id] +=1

    # #统计当日可以打多少次
    # if dungeon_type == 'normal':
    #     #获取该战场的今日次数
    #     data['copy_times'] = user_dungeon_obj.get_today_copy_info(dungeon_type,floor_id,room_id)
    #     data['copy_times']['floor_id'] = floor_id
    #     data['copy_times']['room_id'] = room_id
    # elif dungeon_type == 'daily':
    #     data['daily_info'] = user_dungeon_obj.get_daily_info()
    #     #获取该战场的今日次数
    #     data['copy_times'] = user_dungeon_obj.get_today_copy_info(dungeon_type,floor_id,room_id)
    #     data['copy_times']['floor_id'] = floor_id

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


# def open_special_dungeon(rk_user,params):
#     """提前开启限时战场，需要花费元宝
#        params:
#            floor_id:战场id
#     """
#     floor_id = params['floor_id']
#     floor_conf = game_config.special_dungeon_config.get(floor_id,{})
#     if 'loop_gap' in floor_conf and game_config.dungeon_world_config.get('open_special_is_open',False):
#         loop_dungeon_time = __calculate_loopgap_dungeon_time(floor_conf)
#         now_str = utils.datetime_toString(datetime.datetime.now())
#         #已经开启的不用花元宝
#         if (now_str>=loop_dungeon_time[0][0] and now_str<=loop_dungeon_time[0][1]) or\
#         (now_str>=loop_dungeon_time[1][0] and now_str<=loop_dungeon_time[1][1]):
#             return 0,{'msg':utils.get_msg('dungeon','already_open')}
#         user_dungeon_obj = UserDungeon.get(rk_user.uid)
#         if floor_id in user_dungeon_obj.dungeon_info['special'] and 'open_dungeon_info' in user_dungeon_obj.dungeon_info['special'][floor_id]:
#             open_dungeon_info = user_dungeon_obj.dungeon_info['special'][floor_id]['open_dungeon_info']
#             open_coin = open_dungeon_info['open_coin']
#             if not rk_user.user_property.minus_coin(open_coin,
#                 'open_special_dungeon_%s' % floor_id):
#                 return 11,{'msg':utils.get_msg('user','not_enough_coin')}
#             else:
#                 open_dungeon_info['expire_time'] = int(time.time()) + game_config.dungeon_world_config.get('open_special_time',3600)
#                 open_dungeon_info['open_cnt'] += 1
#                 open_special_coin = game_config.dungeon_world_config.get('open_special_coin',[])
#                 if open_special_coin:
#                     if open_dungeon_info['open_cnt']+1<=len(open_special_coin):
#                         next_open_coin = open_special_coin[open_dungeon_info['open_cnt']]
#                     else:
#                         next_open_coin = open_special_coin[-1]
#                     open_dungeon_info['open_coin'] = next_open_coin
#                 user_dungeon_obj.put()
#                 return 0,{
#                           'dungeon_info':{
#                                 'normal_current':user_dungeon_obj.dungeon_info['normal_current'],
#                                 'special':user_dungeon_obj.dungeon_info['special'],
#                                 'weekly':user_dungeon_obj.dungeon_info.get('weekly',{}),
#                                 }
#                           }
#         else:
#             return 11,{'msg':utils.get_msg('dungeon','can_not_open_now')}
#     else:
#         return 11,{'msg':utils.get_msg('dungeon','can_not_open_now')}
    
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
    if not box_type in floor_conf:
        return 11,{'msg':utils.get_msg('dungeon', 'no_box_config')}
    box_info = floor_conf[box_type]
    if get_step == '0':
        #处理前端要显示的宝箱的内容
        data['box_info'] = utils.format_award(box_info)
        data['box_star'] = int(floor_conf[box_type+'_star'])
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
                newbie_step = int(params.get('newbie_step', 0))
                if newbie_step:
                    rk_user.user_property.set_newbie_steps(newbie_step, "get_box_gift")
                #结果返回
                return 0,data
        else:
            return 11,{'msg':utils.get_msg('dungeon', 'invalid_dungeon_info')}
    else:
        #未识别的内容
        return 11,{'msg':utils.get_msg('dungeon', 'invalid_dungeon_info')}


def recover_copy(rk_user, params):
    """重置副本可挑战次数
    
    Args:
        dungeon_type: 战场类型 (normal 普通战场/ daily试炼)  
        floor_id
        room_id   (试炼可无)
    """
    #检测参数是否合法
    dungeon_type = params['dungeon_type']
    floor_id = params['floor_id']
    room_id  = params.get('room_id', '')
    if room_id:
        where = 'recover_copy_' + "_".join([dungeon_type, floor_id, room_id])
    else:
        where = 'recover_copy_' + "_".join([dungeon_type, floor_id])

    # 检查vip可以回复的次数到了没
    has_recover_times = vip.check_limit_recover(rk_user,'recover_copy', dungeon_type, floor_id)
    next_recover_times = has_recover_times + 1
    if dungeon_type == 'normal':
        recover_conf = game_config.system_config['recover_normal_copy_need']
    elif dungeon_type == 'daily':
        recover_conf = game_config.system_config['recover_daily_copy_need']
    # 检查重置次数是否达到上限
    if next_recover_times not in recover_conf:
        raise GameLogicError('dungeon', 'reach_max_recover_%s' % dungeon_type)

    #检查用户coin是否足够
    recover_need_coin = recover_conf[next_recover_times]
    if not rk_user.user_property.minus_coin(recover_need_coin, where):
        return 11,{'msg':utils.get_msg('user', 'not_enough_coin')}
    #添加回复次数
    rk_user.user_property.add_recover_times('recover_copy', dungeon_type, floor_id)
    user_dungeon_obj = UserDungeon.get(rk_user.uid)
    user_dungeon_obj.recover_copy(dungeon_type,floor_id,room_id)

    return {}

def wipe_out(rk_user, params):
    '''
    扫荡
        玩家能够在已经完美过关的关卡上使用扫荡功能，扫荡不用进入战斗画面，直接返回关卡奖励
        与普通战斗不同的是扫荡并不需要更新战场的关卡信息，
    params: 
        dungeon_type:'normal'  战场类型，有普通战场 normal , 试炼 daily
        floor_id:'1'
        room_id:'1'
        do_times: '1'  扫荡次数
    '''     

    # ------------------------------参数check start-------------------------
    d_type = params.get('dungeon_type')
    floor_id = params.get('floor_id')
    room_id  = params.get('room_id')
    do_times = params.get('do_times')
    if d_type not in ['normal', 'daily'] or not floor_id or not room_id:
        return 6, {'msg':utils.get_msg('dungeon', 'invalid_params')}
    try:
        do_times = int(do_times)
    except ValueError:
        return 6, {'msg':utils.get_msg('dungeon', 'invalid_params')}
    if do_times < 1 or do_times > 10:
        return 6, {'msg':utils.get_msg('dungeon', 'invalid_params')}

    # 读配置
    conf_dict = {
        'normal': game_config.normal_dungeon_config,
        'daily': game_config.daily_dungeon_config
    }
    dungeon_config = conf_dict[d_type]

    # 战场不存在 
    try:
        dungeon_config[floor_id]['rooms'][room_id]
    except KeyError:
        return 6,{'msg':utils.get_msg('dungeon', 'invalid_dungeon')}
    # ------------------------------参数check end----------------------------

    # ------------------------------扫荡逻辑check start----------------
    user_dungeon = rk_user.user_dungeon
    has_played_info = user_dungeon.has_played_info
    user_property = rk_user.user_property
    # 玩家未达到15级，不开启扫荡
    open_lv = game_config.user_init_config['open_lv'].get('wipe_out', 0)
    if user_property.lv < open_lv:
        return 11,{'msg':utils.get_msg('dungeon', 'wipe_out_open_lv') % open_lv}
    # vip未达到4级，不开启多次扫荡
    open_lv = game_config.user_init_config['open_lv'].get('vip_multi_wipe_out', 0)
    if do_times > 1 and user_property.vip_cur_level < open_lv:
        return 11,{'msg':utils.get_msg('dungeon', 'vip_wipe_out') % open_lv}
    # 未达到此战场
    try:
        has_played_info[d_type][floor_id]['rooms'][room_id]
    except KeyError:
        return 11,{'msg':utils.get_msg('dungeon', 'not_arrived')}
    # 没达到3星
    if not has_played_info[d_type][floor_id]['rooms'][room_id]['perfect']:
        return 11,{'msg':utils.get_msg('dungeon', 'not_three_star')}
    # 当前扫荡券不足
    user_pack = rk_user.user_pack
    if not user_pack.is_props_enough('24_props', do_times):
        return 11,{'msg':utils.get_msg('dungeon', 'wipe_out_not_enough')}
    floor_config = dungeon_config[floor_id]
    room_config = dungeon_config[floor_id]['rooms'][room_id]
    # 检查用户体力是否足够
    need_stamina = int(room_config['stamina']) * do_times
    if user_property.stamina < need_stamina:
        raise GameLogicError('user','not_enough_stamina')
    
    # 进入战场次数用完，不能扫荡,  或者更新repeat_info的当天日期
    if user_dungeon.check_limit_dungeon(rk_user,params) is False:
        raise GameLogicError('dungeon', 'invalid_limit_dungeon')
    # 计算能够扫荡次数
    
    if d_type == 'normal':
        try:  #  判断dungeon_repeat_info中有无此关卡记录
            user_dungeon.dungeon_repeat_info[d_type][floor_id][room_id]
        except KeyError:
            # 无此关卡记录时，把此关卡今日完成次数置零
            user_dungeon.dungeon_repeat_info      \
                .setdefault(d_type, {})           \
                .setdefault(floor_id, {})         \
                .setdefault(room_id, 0)
            user_dungeon.put()
        can_make_copy_cnt = room_config['can_make_copy_cn']
        has_played_cnt = user_dungeon.dungeon_repeat_info[d_type][floor_id][room_id]
    elif d_type == 'daily':
        try:  #  判断dungeon_repeat_info中有无此关卡记录
            user_dungeon.dungeon_repeat_info[d_type][floor_id]
        except KeyError:
            # 无此关卡记录时，把此关卡今日完成次数置零
            user_dungeon.dungeon_repeat_info      \
                .setdefault(d_type, {})           \
                .setdefault(floor_id, 0)
            user_dungeon.put()
        can_make_copy_cnt = floor_config['can_make_copy_cn']
        has_played_cnt = user_dungeon.dungeon_repeat_info[d_type][floor_id]

    can_wipe_out_cnt = can_make_copy_cnt - has_played_cnt

    data = {}
    # 剩余战场次数不够扫荡n次
    if can_wipe_out_cnt < do_times:
        return 11,{'msg':utils.get_msg('dungeon', 'cant_do_multi_times') % do_times}
    data['can_wipe_out_cnt'] = can_wipe_out_cnt
    # ------------------------------扫荡逻辑check end----------------

    # 能扫荡次数和vip等级有关
    #if utils.get_today_str() == user_property.property_info['recover_times']['today_str']:
    #    wipe_out_times = user_property.property_info.get('wipe_out_times', 0)
    #    vip_lv = user_property.vip_cur_level
    #    can_wipe_out_cnt = game_config.user_vip_config[str(vip_lv)]['can_wipe_out_cnt']
    #    if can_wipe_out_cnt - wipe_out_times < do_times:
    #        return 11,{'msg':utils.get_msg('dungeon', 'vip_wipe_out')}
    #    user_property.property_info['wipe_out_times'] += do_times
    #else:
    #    user_property.property_info['wipe_out_times'] = do_times
    #    vip.check_limit_recover(rk_user, 'wipe_out')  # 更新一下，防止出错
    #user_property.put()

    # ------------------------------添加扫荡物品 start----------------
    # 扫荡战利品
    get_goods = {
        'exp': 0,
        'exp_point': 0,
        'gold': 0,
        'card': {},
        'equip': {},
        'soul':{
            'card': {},
            'equip': {},
        },
        'mat': {},
        'props': {},
    }
    # 扫荡一次能够得到的经验，卡经验点，和钱币
    get_goods['exp'] += room_config.get('exp', 0) * do_times
    get_goods['exp_point'] += room_config.get('exp_point', 0) * do_times
    get_goods['gold'] += room_config.get('gold', 0) * do_times
    
    ########  运营活动 特定时间额外掉落物品   万恶的代码
    more_drop = activity.more_dungeon_drop(d_type, floor_id, room_id, times=do_times)
    if more_drop:
        for thing_type, things_id_num in more_drop.items():
            if thing_type == 'gold':
                get_goods['gold'] += more_drop['gold']['num']
                continue
            for thing_id, num in things_id_num.items():
                if thing_type == 'soul':
                    if 'card' in thing_id:
                        soul_type = 'card'
                    elif 'equip' in thing_id:
                        soul_type = 'equip'
                    get_goods[thing_type][soul_type][thing_id] = get_goods[thing_type][soul_type].get(thing_id, 0) + num
                else:
                    get_goods[thing_type][thing_id] = get_goods[thing_type].get(thing_id, 0) + num
    ################### ############
    
    # 扫荡能够得到的物品
    drop_info = _pack_drop_info(room_config.get('drop_info', {}))
    invisible_drop = _pack_drop_info(room_config.get('invisible_drop', {}))
    drop_info.extend(invisible_drop)
    # 有掉落物品（包括可见和不可见）时计算掉落, 不用战斗所以不区分可见不可见
    if drop_info: # sample  ['12002_equip', '5_card_soul', '53001_equip_1_soul', '6_card', '23_props', '8_props']
        drop_info = list(set(drop_info))  # list去重
        drop_info_config = game_config.drop_info_config['normal_dungeon']
        # 检查战场掉落配置中是否有此物品
        for goods_id in drop_info:
            if 'soul' in goods_id:
                if goods_id[:-5] not in drop_info_config['soul']:
                    return 11,{'msg':utils.get_msg('dungeon', 'no_this_goods')}
            else:
                if goods_id not in drop_info_config:
                    return 11,{'msg':utils.get_msg('dungeon', 'no_this_goods')}
        # 计算掉落数量
        for n in range(do_times):
            for goods_id in drop_info:
                if 'soul' in goods_id:
                    goods_id = goods_id[:-5]  # 去掉'_soul'后缀
                    value_config = drop_info_config['soul'][goods_id].get('visible', drop_info_config['soul'][goods_id].get('invisible', 0))
                    # 根据配置概率判断是否得到
                    if utils.is_happen(value_config[1]):
                        num = random.randint(value_config[0][0], value_config[0][1])
                        if 'card' in goods_id:
                            soul_type = 'card'
                        elif 'equip' in goods_id:
                            soul_type = 'equip'
                        else:
                            continue
                        if goods_id not in get_goods['soul'][soul_type]:
                            get_goods['soul'][soul_type][goods_id] = num
                        else:
                            get_goods['soul'][soul_type][goods_id] += num
                    else:
                        continue
                else:
                    value_config = drop_info_config[goods_id].get('visible', drop_info_config[goods_id].get('invisible', 0))
                    # 根据配置概率判断是否得到
                    if utils.is_happen(value_config[1]):
                        num = random.randint(value_config[0][0], value_config[0][1])
                        for t in ['card', 'equip', 'props', 'mat']:
                            if t in goods_id:
                                get_type = t
                        if goods_id not in get_goods[get_type]:
                            get_goods[get_type][goods_id] = num
                        else:
                            get_goods[get_type][goods_id] += num
                    else:
                        continue

    # 添加must_drop必掉物品
    md = room_config.get('must_drop', {})
    for goods_type in md:
        if goods_type == 'soul':
            for key in md[goods_type]:
                if 'card' in key:
                    soul_type = 'card'
                elif 'equip' in key:
                    soul_type = 'equip'
                else:
                    continue
                if key in get_goods[goods_type][soul_type]:
                    get_goods[goods_type][soul_type][key] += md[goods_type][key]
                else:
                    get_goods[goods_type][soul_type][key] = md[goods_type][key]
        else:
            for key in md[goods_type]:
                if key in get_goods[goods_type]:
                    get_goods[goods_type][key] += md[goods_type][key]
                else:
                    get_goods[goods_type][key] = md[goods_type][key]

    # ------------------------------添加扫荡物品 end----------------

    # 添加扫荡获得物品
    tmpdata = user_property.test_give_award(get_goods, where='wipe_out')
    # 减扫荡券
    user_pack.minus_props('24_props', do_times, 'wipe_out')
    # 扣体力
    user_property.minus_stamina(need_stamina)
    # 记录repeat info
    user_dungeon.add_repeat_cnt(d_type, floor_id, room_id, do_times)

    # 给前端
    data['get_exp'] = tmpdata['exp']
    data['get_exp_point'] = tmpdata['exp_point']
    data['get_gold'] = tmpdata['gold']
    data['get_card'] = tmpdata['card']
    data['get_equip'] = tmpdata['equip']
    data['get_souls'] = tmpdata['soul']
    data['get_material'] = tmpdata['mat']
    data['get_props'] = tmpdata['props']

    return 0, data


def _pack_drop_info(drop_info):
    '''
    把drop_info转换成一个list
    '''
    rtn_list = []
    for goods_type in drop_info:
        if goods_type == 'soul':
            # 如果是碎片，后缀'_soul'以示区别
            rtn_list.extend([goods_id+'_soul' for goods_id in drop_info[goods_type]])
        else:
            rtn_list.extend(drop_info[goods_type])
    return rtn_list
