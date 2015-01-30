# encoding: utf-8
"""
file: apps/models/user_task.py
"""
import datetime
import time
import copy

from apps.common import utils
from apps.models.user_base import UserBase
from apps.models.user_gift import UserGift
from apps.models import GameModel
from apps.models.user_mail import UserMail

from apps.config.game_config import game_config

class UserTask(GameModel):

    pk = 'uid'
    fields = ['uid', 'daily_info']
    def __init__(self):
        """初始化用户Login信息

        Args:
            uid: 用户游戏ID
            login_info:用户Login信息
        """
        self.uid = None
        self.daily_info = {}   # 每日任务信息

    @classmethod
    def create(cls,uid):
        ul = cls()
        ul.uid = uid
        ul.daily_info = {
            'today': '',
            'points': 0,  # 当日获得的积分
            'has_got': {  # 包厢领取记录
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
