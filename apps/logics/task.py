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
            'gacha.multi_charge': 'task_12',    # 招募
            'dungeon.wipe_out': 'task13',       # 扫荡
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
            else:
                ut.do_daily_task(method_list[method])
        # 是否有可领取的每日任务宝箱
        data['user_info']['task_box_can_get'] = request.rk_user.user_task.today_can_get()
        return rc, data
    return wrap_func
