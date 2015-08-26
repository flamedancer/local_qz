# encoding: utf-8
"""
file: apps/logics/task.py
"""
#import sys

import copy
from apps.common import tools
from apps.config.game_config import game_config
from apps.common.exceptions import GameLogicError


def show_daily_task(rk_user, params):
    '''
    获取玩家 每日任务信息
    '''
    task_conf = game_config.task_config['daily_task']
    ut = rk_user.user_task
    user_daily_info = ut.reset_daily_info()
    #reload(sys)
    #sys.setdefaultencoding('utf-8')
    data = {'tasks': {}}
    for task_id, task_info in task_conf.items():
        if task_info['open'] and task_id in user_daily_info:
            data['tasks'][task_id] = copy.deepcopy(task_info)
            data['tasks'][task_id].update(user_daily_info[task_id])
            data['tasks'][task_id]['desc'] = task_info['desc'] % task_info['count']
            data['tasks'][task_id].pop('open')

    data['points'] = ut.daily_info['points']

    box = copy.deepcopy(game_config.task_config['daily_task_box'])
    for box_type, box_info in box.items():
        box_info.pop('mail_title')
        box_info.pop('mail_content')
        box_info['has_got'] = ut.daily_info['has_got'][box_type]
    data['box'] = box

    ut.put()
    return 0, data


def get_box(rk_user, params):
    '''
    领取每日任务的宝箱
    '''
    box_type = params['box_type']
    ut = rk_user.user_task

    points = ut.daily_info['points']
    box_conf = game_config.task_config['daily_task_box'][box_type]
    if points < box_conf['need_point']:
        raise GameLogicError('task','not_enough_points')
    if ut.daily_info['has_got'][box_type] == True:
        raise GameLogicError('task','box_has_got')
    award = box_conf['award']
    data = tools.add_things(
        rk_user,
        [{"_id": goods, "num": award[goods]} for goods in award if goods],
        where="daily_task_award"
    )
    ut.daily_info['has_got'][box_type] = True
    ut.put()
    return 0, data


def do_daily_task(func):
    '''
    做每日任务
    '''
    def wrap_func(request, *args, **kwargs):
        rc, data = func(request, *args, **kwargs)
        if rc != 0:
            return rc, data
        
        # 任务调用的接口，
        # value为任务id，对应task_config['daily_task']的key
        method_list = {
            'dungeon.end': ['task_1', 'task_4', 'task_13'],   # 完成普通副本， 完成试炼, 大扫荡
            #'gift.get_sign_in_gift': 'task_2',
            'mystery_store.buy_store_goods': 'task_3',
            'equip.update': ['task_5', 'task_7'],   # 装备升级  宝物升级
            'card.card_update': 'task_6',
            'activity.explore': 'task_9',
            'pack.buy_props': 'task_10',    # 商城购买物品（道具）
            #'vip.buy_vip_gift': 'task_10', # 商城购买物品（礼包）
            'activity.get_banquet_stamina': 'task_11', # 吃包子
            'gacha.charge': 'task_12',          # 招募
            'gacha.charge_multi': 'task_12',    # 招募
            'dungeon.wipe_out': 'task_13',       # 扫荡
        }

        method = request.REQUEST.get('method', '')

        if method in method_list:
            ut = request.rk_user.user_task
            if method == 'dungeon.end':
                if data.get('dungeon_fail'):  # 战斗失败
                    return rc, data
                if request.REQUEST.get('dungeon_type', '') == 'daily':
                    ut.do_daily_task(method_list[method][1])
                elif request.REQUEST.get('dungeon_type', '') == 'normal':
                    ut.do_daily_task(method_list[method][0])
                    ut.do_daily_task(method_list[method][2])
            elif method == 'equip.update':
                equip_type = request.REQUEST.get('base_type', '')
                # 装备升级
                if equip_type in ['1', '2', '3', '4']:
                    do_times = max(data['up_lv']) - min(data['up_lv']) + 1
                    ut.do_daily_task(method_list[method][0], do_times)
                # 宝物升级
                elif equip_type in ['5', '6']:  
                    ut.do_daily_task(method_list[method][1])
            elif method == 'card.card_update':
                do_times = data['up_lv']
                ut.do_daily_task(method_list[method], do_times)
            elif method == 'activity.explore':
                do_times = int(request.REQUEST.get('times', '1'))
                ut.do_daily_task(method_list[method], do_times)
            elif method == 'dungeon.wipe_out':
                do_times = int(request.REQUEST.get('do_times', '1'))
                ut.do_daily_task(method_list[method], do_times)
            else:
                ut.do_daily_task(method_list[method])
        # 是否有可领取的每日任务宝箱
        # 没写在 wrap_info 里  是因为只有调用了任务的接口才有必要去判断这个字段
        #data['user_info']['task_box_can_get'] = request.rk_user.user_task.today_can_get()
        return rc, data
    return wrap_func


def show_main_task(rk_user, params):
    '''
    获取玩家 主线任务信息
    '''
    conf = game_config.task_config['main_task']
    dungeon_conf = game_config.normal_dungeon_config
    ut = rk_user.user_task
    udungeon = rk_user.user_dungeon
    data = {'tasks': {}}
    for task in conf:
        data['tasks'][task] = {}

        #step = ut.main_task[task]['step']
        #if step >= ut.max_step(task):
        #    current_step = str(ut.max_step(task))
        #else:
        #    current_step = str(step + 1)

        got_award = ut.main_task.get(task, {}).get('got_award', 0)
        if got_award >= ut.max_step(task):  # 最大进度数和最大奖励个数是一样的
            current_step = str(ut.max_step(task))
            data['tasks'][task]['all_finished'] = True
        else:
            current_step = str(got_award + 1)
            data['tasks'][task]['all_finished'] = False

        data['tasks'][task]['title'] = conf[task]['title']
        
        data['tasks'][task]['can_award'] = ut.main_task.get(task, {}).get('step', 0) > ut.main_task.get(task, {}).get(
                'got_award', 0)
        data['tasks'][task]['award'] = conf[task]['award'][current_step]
        # data['tasks'][task]['total_steps'] = len(conf[task]['value'])
        # data['tasks'][task]['finished_step'] = ut.main_task[task]['step']
        data['tasks'][task]['got_award'] = ut.main_task.get(task, {}).get('got_award', 0)   # 已领取的奖励个数

        # 根据不同的任务，显示不同的进度
        # 第一系列任务进度显示  (通关第1大章第1大关第2小关)  始终显示 0/1  或 1/1
        if task == 'set_1':
            step_floor, step_room = map(str, conf['set_1']['value'][current_step])
            data['tasks'][task]['desc'] = conf[task]['desc'] % dungeon_conf[step_floor]['rooms'][step_room]['name']
            data['tasks'][task]['total_steps'] = 1
            data['tasks'][task]['finished_step'] = 1 if  data['tasks'][task]['can_award'] else 0
        # 第2 系列任务  (获得第1大章第1大关所有星)  显示当前获得星 / 此关所有星
        elif task == 'set_2':
            step_floor = str(conf['set_2']['value'][current_step])
            data['tasks'][task]['desc'] = conf[task]['desc'] % dungeon_conf[step_floor]['name']
            data['tasks'][task]['total_steps'] = udungeon.get_floor_all_star('normal', step_floor)
            data['tasks'][task]['finished_step'] = udungeon.has_played_info['normal'].get(step_floor, {}).get('cur_star', 0)
        # 第3 系列任务检查  (战场总星数达到x颗 )  当前获得总星/条件星数
        elif task == 'set_3':
            data['tasks'][task]['desc'] = conf[task]['desc'] % conf['set_3']['value'][current_step]
            data['tasks'][task]['finished_step'] = udungeon.total_got_star
            data['tasks'][task]['total_steps'] = conf['set_3']['value'][current_step]
        # 第4 系列任务检查  (主角达到30级)  当前等级 / 条件等级
        elif task == 'set_4':
            data['tasks'][task]['desc'] = conf[task]['desc'] % conf['set_4']['value'][current_step]
            data['tasks'][task]['finished_step'] = rk_user.user_property.lv
            data['tasks'][task]['total_steps'] = conf['set_4']['value'][current_step]
    return 0, data


def get_award(rk_user, params):
    '''领取主线任务奖励'''
    task_set = params['task']
    award_result = rk_user.user_task.get_award(task_set)  # 已做领奖次数+1的处理
    print 'award_result', award_result
    if award_result != 0 :
        raise GameLogicError('task','cant_get_award')
    conf = game_config.task_config['main_task']
    current_award = str(rk_user.user_task.main_task[task_set]['got_award'])
    print 'current_award',current_award
    award = conf[task_set]['award'][current_award]
    print 'awardinfo', [{"_id": goods, "num": award[goods]} for goods in award if goods]
    data = {}
    data['get_things'] = tools.add_things(
        rk_user,
        [{"_id": goods, "num": award[goods]} for goods in award if goods],
        where="main_task_award"
    )
    data.update(show_main_task(rk_user, params)[1])
    return 0, data


# ----------------------------- test ---------------------------
def test_check_main_tasks(rk_user, params):
    rk_user.user_task.check_main_tasks()
    return show_main_task(rk_user, params)
