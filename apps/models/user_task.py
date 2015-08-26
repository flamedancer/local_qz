# encoding: utf-8
"""
file: apps/models/user_task.py
"""
import datetime
import time
import copy

from apps.common import utils
from apps.models import GameModel
from apps.models.user_mail import UserMail

from apps.config.game_config import game_config

class UserTask(GameModel):

    pk = 'uid'
    fields = ['uid', 'daily_info', 'main_task']
    def __init__(self):
        """初始化用户Login信息

        Args:
            uid: 用户游戏ID
            login_info:用户Login信息
        """
        self.uid = None
        self.daily_info = {}   # 每日任务信息
        self.main_task = {}

    @classmethod
    def create(cls,uid):
        ul = cls()
        ul.uid = uid
        # 每日任务信息
        ul.daily_info = {
            'today': '',
            'points': 0,  # 当日获得的积分
            'has_got': {  # 宝箱领取记录
                'copper': False,
                'silver': False,
                'gold': False,
            },
            'tasks': {}  # 记录每个任务的进度和是否已完成
               
        }
        # 结构图
        #ul.daily_info = {
        #    'today': '2015-01-12',
        #    'points': 0,  # 当日获得的积分
        #    'has_got': {  # 宝箱领取记录
        #        'copper': False,
        #        'silver': False,
        #        'gold': False,
        #    },
        #    'tasks': {  # 记录每个任务的进度和是否已完成
        #        '1':{
        #            'current': 0,
        #            'clear': False,
        #        },
        #        '2':{
        #            'current': 0,
        #            'clear': False,
        #        },
        #    }
        #}

        # 主线任务信息
        ul.main_task = {}
        # 结构图
        #ul.main_task = {
        #    'set_1':{           #  第一系列任务
        #        'step': 1,      #  任务进度(打完的)
        #        'got_award': 0, #  已领奖励个数
        #    }                   # setp > got_award 时才可领取奖励
        #}
        return ul

    @classmethod
    def get_instance(cls, uid):
        """ 获取一个当前的用户实例
        Args:
            uid: 用户游戏ID
        """
        obj = super(UserTask,cls).get(uid)
        if not obj:
            obj = cls.create(uid)
            obj.put()
        return obj

    @classmethod
    def get(cls, uid):
        """ 获取一个当前的用户实例
        Args:
            uid: 用户游戏ID
        """
        obj = super(UserTask,cls).get(uid)
        return obj
    
    def reset_daily_info(self):
        '''
        主要是判断日期，做一下重置
        '''
        data = {}
        daily_task = game_config.task_config['daily_task']
        today_str = utils.get_today_str()
        if today_str != self.daily_info['today']:  # 重置任务
            # 检查一下是否有未领取的宝箱，有的话发邮件
            self.__send_yesterday_mail()
            # 重置数据
            for k, v in daily_task.items():
                data[k] = {'current': 0, 'clear': False}
            self.daily_info['tasks'] = data
            self.daily_info['today'] = today_str
            self.daily_info['points'] = 0
            self.daily_info['has_got'] = {
                'copper': False,
                'silver': False,
                'gold': False,
            }
            
            self.put()
        else:
            data = self.daily_info['tasks']
        return data

    def do_daily_task(self, task_id, do_times=1):
        '''
        做每日任务
        do_times 说明  探索，武将升级，装备升级等有一键多次的功能
        '''
        if task_id not in self.daily_info['tasks'] or self.user_property.property_info['newbie'] or do_times <= 0:
            return
        task_conf = game_config.task_config['daily_task']
        self.reset_daily_info()
        clear_flag = self.daily_info['tasks'][task_id]['clear']
        if clear_flag == False:
            self.daily_info['tasks'][task_id]['current'] += do_times
            self.daily_info['tasks'][task_id]['current'] = min(self.daily_info['tasks'][task_id]['current'], task_conf[task_id]['count'])
        if self.daily_info['tasks'][task_id]['current']  >= task_conf[task_id]['count'] \
            and clear_flag == False:
            self.daily_info['tasks'][task_id]['clear'] = True
            self.daily_info['points'] += task_conf[task_id]['points']
        self.put()

    def __send_yesterday_mail(self):
        '''
        昨天没领的每日任务宝箱奖励以邮件形式补发
        '''
        my_points = self.daily_info['points']
        for box_type in ['copper', 'silver', 'gold']:
            box_conf = game_config.task_config['daily_task_box'][box_type]
            if my_points >= box_conf['need_point']:
                if self.daily_info['has_got'][box_type] == False:
                    sid = 'system_%s' % (utils.create_gen_id())
                    mailtype = 'system'
                    title = box_conf['mail_title']
                    content = box_conf['mail_content']
                    award = box_conf['award']
                    user_mail_obj = UserMail.hget(self.user_base.uid, sid)
                    user_mail_obj.set_mail(mailtype=mailtype, title=title, content=content, award=award)
               
            else: # 铜宝箱都不能领的话，其他不用看了
                break
            
    def today_can_get(self):
        '''
        判断当天是否有能领的每日任务宝箱
        '''
        self.reset_daily_info()
        for box_type, flag in self.daily_info['has_got'].items():
            box_conf = game_config.task_config['daily_task_box'][box_type]
            if flag == False and self.daily_info['points'] >= box_conf['need_point']:
                return True
        return False

    def check_main_tasks(self):
        '''
        监测是否有完成主线任务
        每一系任务的逻辑不同
        '''
        conf = game_config.task_config['main_task']
        # 第一系列任务检查  (通关第1大章第1大关第2小关)
        #---------------------------------------------------------------------------
        step = self.__get_step('set_1')
        if str(step+1) in conf['set_1']['value']:  # 做完这一系列任务就不需要处理了
            normal_current = self.user_dungeon.dungeon_info['normal_current']  #  游戏中显示 new 的那一关
            cur_floor = int(normal_current['floor_id'])
            cur_room = int(normal_current['room_id'])
            value = conf['set_1']['value'][str(step+1)]
            step_floor, step_room = map(str, value)
            # step_floor = self.__format_floor(value[0], value[1])
            # step_room = value[2]
    
            if cur_floor > step_floor or (cur_floor == step_floor and cur_room > step_room):

                self.__add_step('set_1')

        # 第2 系列任务检查  (获得第1大章第1大关所有星)
        #---------------------------------------------------------------------------
        step = self.__get_step('set_2')
        if str(step+1) in conf['set_2']['value']:  # 做完这一系列任务就不需要处理了
            floor = str(conf['set_2']['value'][str(step+1)])
            # floor = str(self.__format_floor(value[0], value[1]))
            print 'wzgdebug floor', floor
            #info = self.user_dungeon.has_played_info['normal'][str(floor)]
            #if info['cur_star'] >= info['floor_all_star']:
            #    self.__add_step('set_2')
            
            # 新玩家是没有这个记录的
            if floor in self.user_dungeon.has_played_info['normal']:
                info = self.user_dungeon.has_played_info['normal'][floor]
              
                if info['cur_star'] >= info['floor_all_star']:
                    self.__add_step('set_2')
            else:
             
                pass

        # 第3 系列任务检查  (战场总星数达到100颗)
        #---------------------------------------------------------------------------
        step = self.__get_step('set_3')
        if str(step+1) in conf['set_3']['value']:  # 做完这一系列任务就不需要处理了
            cur_star = self.user_dungeon.total_got_star
            conf_star = conf['set_3']['value'][str(step+1)]
            if cur_star >= conf_star:
                self.__add_step('set_3')

        # 第4 系列任务检查  (主角达到30级)
        #---------------------------------------------------------------------------
        step = self.__get_step('set_4')
        if str(step+1) in conf['set_4']['value']:  # 做完这一系列任务就不需要处理了
            cur_lv = self.user_property.lv
            conf_lv = conf['set_4']['value'][str(step+1)]
            if cur_lv >= conf_lv:
                self.__add_step('set_4')

    def __add_step(self, whichset):
        '''完成任务, 进度 +1'''
        if whichset in self.main_task:
            self.main_task[whichset]['step'] += 1
        else:
            # 完成第一个进度
            # 'step': 给1,
            self.main_task[whichset] = {
               'step': 1,
               'got_award': 0,
            }
        self.put()
        pass

    def __get_step(self, whichset):
        '''获得指定任务系列  的  当前已完成的进度'''
        # 如果还没记录过,当前完成进度返回0
        try:
            rtn =self.main_task[whichset]['step']  
        except: 
            rtn = 0
        #conf = game_config.task_config['main_task']
        max_step = self.max_step(whichset)
        if rtn >= max_step:
            rtn = 999
        return rtn

    # def __format_floor(self, dazhang, daguan):
    #     '''
    #     游戏中有大章(dazhang),大关(daguan),小关
    #     配置中只有 floor(大关), room(小关), 所以要转化成统一的格式
    #     大章,大关  转化成 floor
    #     '''
    #                           # 注意   一有变动就要改 ----------------------------------------------------------------------------
    #                           # 注意   一有变动就要改 ----------------------------------------------------------------------------
    #                           # 注意   一有变动就要改 ----------------------------------------------------------------------------
    #     floor_num = [7,3]     # 每个大章有几 floor, (不会经常改动,所以在这写死)
    #                           # 注意   一有变动就要改 ----------------------------------------------------------------------------
    #                           # 注意   一有变动就要改 ----------------------------------------------------------------------------
    #                           # 注意   一有变动就要改 ----------------------------------------------------------------------------

    #     floor = daguan
    #     if dazhang == 1:
    #         return floor
    #     elif dazhang > 1:
    #         for n in range(dazhang - 1):
    #             floor += floor_num[n]
    #     else:
    #         pass
    #     return floor

    def get_award(self, whichset):
        '''获得奖励后, 奖励计数+1'''
        if whichset not in self.main_task:
            return 1
        conf = game_config.task_config['main_task']
        max_award_cnt = max(conf[whichset]['award'])
        if self.main_task[whichset]['got_award'] >= max_award_cnt:
            return 2
        if self.main_task[whichset]['got_award'] >= self.main_task[whichset]['step']: # 还没打完的任务不能领
            return 3
        self.main_task[whichset]['got_award'] += 1
        self.put()
        return 0
        
    def max_step(self, whichset):
        '''一个任务系的最大进度'''
        conf = game_config.task_config['main_task']
        return len(conf[whichset]['value'])

    def can_get_award(self):
        '''
        是否有能领取的主线任务奖励
        '''
        for task in self.main_task:
            if self.main_task[task]['step'] > self.main_task[task]['got_award']:
                return True
        return False
