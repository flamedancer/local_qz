#!/usr/bin/env python
# encoding: utf-8
""" filename user_dungeon.py
"""
import datetime
import copy
import traceback
from apps.models.user_property import UserProperty
from apps.models.user_gift import UserGift
from apps.common import utils
from apps.models import GameModel


class UserDungeon(GameModel):
    """ classname:UserDungeon
    用户的战场信息
    """
    pk = 'uid'
    fields = ['uid','dungeon_info','dungeon_fail_list','dungeon_repeat_info','has_played_info']
    def __init__(self):
        """类初期化函数
        Args:
            uid: string 用户ID
        return:
             无返回值
        """
        self.uid = ''
        self.dungeon_info = {}
        #记录失败获取的信息,失败会触发送相应礼物
        self.dungeon_fail_list = []
        #记录用户当天的战场重复进入次数的信息
        self.dungeon_repeat_info = {
                            'today_str':utils.get_today_str(),
                            'special':{},
                            'weekly':{},
                            'daily':{},
                            'normal':{},
        }
        #记录用户已经打过的战场信息
        self.has_played_info = {
            'normal':{},
            'special':{},
            'weekly':{},
            'daily':{},
        }

    @classmethod
    def get(cls, uid):
        """获取类对象
        Args:
            uid: string 用户ID
        return:
            UserDungeon：类对象
        """
        obj = super(UserDungeon, cls).get(uid)
        if obj is not None:
            #检查是否有新战场配置
            obj.check_new_dungeon()
            obj.refresh_daily_info()
            #增加记录
            if 'record' not in obj.dungeon_info:
                obj.dungeon_info['record'] = {
                    'special':{},
                }
        return obj

    @classmethod
    def get_instance(cls, uid):
        """获取类对象
        Args:
            uid: string 用户ID
        return:
            UserDungeon：类对象
        """
        obj = super(UserDungeon,cls).get(uid)
        if obj is None:
            obj = cls._install(uid)
        #检查是否有新战场配置
        obj.check_new_dungeon()
        obj.refresh_daily_info()
        return obj
    
    @classmethod
    def get_Ex(cls, uid):
        """获取类对象
        Args:
            uid: string 用户ID
        return:
            UserDungeon：类对象
        """
        obj = super(UserDungeon,cls).get(uid)
        return obj

    @classmethod
    def _install(cls, uid):
        """生成类对象
        Args:
            uid: string 用户ID
        return:
            UserDungeon：类对象
        """
        obj = cls()
        obj.uid = uid
        #根据配置生成用户的战场信息
        obj.dungeon_info = {
            'today':utils.get_today_str(),
            'free_stamina_cnt':0,
            'normal_current':{
                'floor_id':'1',
                'room_id':'1',
                'status':0,
            },
            'last':{},
        }
        # #每周的活动战场数据
        # weekly_dungeon = {}
        # weekly_dungeon_conf = obj.game_config.weekly_dungeon_config
        # for week_key,week_value in weekly_dungeon_conf.iteritems():
        #     week_temp = {
        #         'status':0,
        #         'rooms':{},
        #     }
        #     for room_id in week_value['rooms']:
        #         week_temp['rooms'][room_id] = 0
        #     weekly_dungeon[week_key] = week_temp
        # obj.dungeon_info['weekly'] = weekly_dungeon
        #每日的活动战场数据
        daily_dungeon = {}
        daily_dungeon_conf = obj.game_config.daily_dungeon_config
        for daily_key,daily_value in daily_dungeon_conf.iteritems():
            daily_temp = {
                'status':0,
                'rooms':{},
            }
            for room_id in daily_value['rooms']:
                daily_temp['rooms'][room_id] = 0
            daily_dungeon[daily_key] = daily_temp
        obj.dungeon_info['daily'] = daily_dungeon
        #特殊活动的战场数据
        # special_dungeon_conf = obj.game_config.special_dungeon_config
        # special_dungeon = {}
        # now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # for special_key,special_value in special_dungeon_conf.iteritems():
        #     if (now_str > special_value['end_time'] or now_str < special_value['start_time']):
        #         continue
        #     special_temp = {
        #         'status':0,
        #         'rooms':{},
        #     }
        #     for room_id in special_value['rooms']:
        #         special_temp['rooms'][room_id] = 0
        #     special_dungeon[special_key] = special_temp
        # obj.dungeon_info['special'] = special_dungeon
        # obj.dungeon_info['record'] = {
        #     'special':{},
        # }
        obj.put()
        return obj
    
    def refresh_daily_info(self):
        """
        每日根据当天日期，决定是否要刷新数据
        """
        today = utils.get_today_str()
        if today != self.dungeon_info.get('today'):
            self.__reset_once_daily_and_open_special()
            self.dungeon_info['free_stamina_cnt'] = 0
            self.dungeon_info['today'] = today
            self.put()
            
    def can_free_stamina(self):
        """
        是否可以失败免体力消耗
        """
        return self.dungeon_info.get('free_stamina_cnt',0)<self.game_config.system_config.get('free_stamina_cnt',0)
    
    def add_free_stamina_cnt(self):
        """
        记录失败未消耗体力次数
        """
        if 'free_stamina_cnt' not in self.dungeon_info:
            self.dungeon_info['free_stamina_cnt'] = 1
        else:
            self.dungeon_info['free_stamina_cnt'] += 1
        self.put()
    
    def minus_free_stamina_cnt(self):
        """
        记录失败未消耗体力次数
        """
        if 'free_stamina_cnt' in self.dungeon_info and self.dungeon_info['free_stamina_cnt']>0:
            self.dungeon_info['free_stamina_cnt'] -= 1
            self.put()

    @property
    def normal_current(self):
        return self.dungeon_info['normal_current']

        
    def get_dungeon_info(self):
        """
        获取用户的战场信息
        """
        dungeon_info_copy = self.dungeon_info
        # has_played_info_copy = copy.deepcopy(self.has_played_info)
        dungeon_info = {
            'normal_current':dungeon_info_copy['normal_current'],
            # 'special':dungeon_info_copy['special'],
            # 'weekly':dungeon_info_copy.get('weekly',{}),
            'daily':dungeon_info_copy.get('daily',{}),
        }
        return dungeon_info
    
    def get_weekly_info(self):
        '''
        * 初始化周战场信息
        '''
        floor_data = {}
        #获取每周活动副本配置信息
        # dungeon_config_conf = self.game_config.weekly_dungeon_config
        # for floor_id in dungeon_config_conf:
        #     floor_data[floor_id] = {}
        #     for room_id in dungeon_config_conf[floor_id]['rooms']:
        #         floor_data[floor_id][room_id] = self.get_today_copy_info('weekly',floor_id,room_id)
        #获取已经打过的战场的信息
        #has_played_weekly_info = copy.deepcopy(self.has_played_info.get('weekly',{}))
        #floor_data.update(has_played_weekly_info)
        return floor_data

    def get_daily_info(self):
        '''
        * 初始化每日战场信息
        '''
        floor_data = {}
        #获取每日活动副本配置信息
        dungeon_config_conf = self.game_config.daily_dungeon_config
        for floor_id in dungeon_config_conf:
            # 因为每日战场的次数是和 floor_id 走的所以只需要一个 floor_id 即可
            floor_data[floor_id] = self.get_today_copy_info('daily',floor_id,None)
        return floor_data

    def get_all_floor_info(self):
        '''
        * 初始化所有战场的信息
        * miaoyichao
        '''
        floor_data = {}
        #获取普通战场配置信息
        dungeon_config_conf = self.game_config.normal_dungeon_config
        #循环
        for floor_id in dungeon_config_conf:
            floor_init_data = self.get_floor_init_info(floor_id)
            floor_data.update(floor_init_data)
        floor_data = self.get_update_floor_info(floor_data)
        #踢出没用的信息
        for floor_id in floor_data:
            floor_info = floor_data[floor_id]
            for room_id in floor_info['rooms']:
                floor_info['rooms'][room_id]['copy_times'] = self.get_today_copy_info('normal',floor_id,room_id)
        return floor_data
    
    def get_update_floor_info(self,floor_data):
        '''
        获取完整的 floor 信息
        '''
        has_played_info = self.has_played_info.get('normal',{})
        hard_ratio = ['normal']
        for floor_id in has_played_info:
            #获取金银铜宝箱是否存在
            floor_data[floor_id]['gold_box'] = has_played_info.get(floor_id,{}).get('gold_box',False)
            floor_data[floor_id]['silver_box'] = has_played_info.get(floor_id,{}).get('silver_box',False)
            floor_data[floor_id]['bronze_box'] = has_played_info.get(floor_id,{}).get('bronze_box',False)
            #获取当前floor的获得的星数
            floor_data[floor_id]['cur_star'] = has_played_info.get(floor_id,{}).get('cur_star',False)
            init_rooms_info = floor_data[floor_id]['rooms']
            played_rooms_info = has_played_info.get(floor_id,{}).get('rooms',{})
            for room_id in played_rooms_info:
                if room_id not in init_rooms_info:
                    continue
                init_rooms_info[room_id]['perfect'] = played_rooms_info.get(room_id,{}).get('perfect',False)
                for hard in hard_ratio:
                    if hard in played_rooms_info.get(room_id,{}):
                        init_rooms_info[room_id][hard]['get_star'] = played_rooms_info[room_id][hard].get('get_star',0)
        return floor_data

    def get_floor_init_info(self,floor_id):
        '''
        * 获取该floor的信息
        * miaoyichao
        * 返回该floor的初始化信息
        '''
        floor_data = {}
        #获取普通战场配置信息
        dungeon_config_conf = self.game_config.normal_dungeon_config
        #获取系数配置表
        dungeon_world_config = self.game_config.dungeon_world_config
        box_info_config = dungeon_world_config.get('box_info',{}).get(str(floor_id),{})
        floor_info = dungeon_config_conf[floor_id]
        #格式化 floor 里面的信息
        floor_data[floor_id] = {}

        for box_type in ["gold", "silver", "bronze"]:
            box_name = box_type + "_box"
            judges_name = 'has_{}_box'.format(box_type)
            if box_name in box_info_config:
                floor_data[floor_id][judges_name] = True
                box_star_name = box_name + '_star'
                floor_data[floor_id][box_star_name] = box_info_config[box_star_name]
            else:
                floor_data[floor_id][judges_name] = False

        floor_data[floor_id]['floor_all_star'] = self.__get_floor_all_star('normal',floor_id)
        floor_data[floor_id]['cur_star'] = 0
        #格式化 floor 里面的 room 的所有的信息
        floor_data[floor_id]['rooms'] = {}
        for room_id in floor_info['rooms']:
            if room_id =='0':
                pass
            else:
                room_info = floor_info['rooms'][room_id]
                base_gold = room_info.get('gold',100)
                base_exp  = room_info.get('exp',100)
                room_star = 0
                floor_data[floor_id]['rooms'][room_id] = {}
                #初始化普通战场信息
                floor_data[floor_id]['rooms'][room_id]['star_evaluation'] = room_info.get('star_evaluation',{})
                floor_data[floor_id]['rooms'][room_id]['normal'] = {}
                floor_data[floor_id]['rooms'][room_id]['normal']['total_star'] = room_info.get('normal',3)
                floor_data[floor_id]['rooms'][room_id]['normal']['get_star'] = 0
                floor_data[floor_id]['rooms'][room_id]['normal']['gold'] = base_gold
                floor_data[floor_id]['rooms'][room_id]['normal']['exp'] = base_exp
                floor_data[floor_id]['rooms'][room_id]['perfect'] = False
                floor_data[floor_id]['rooms'][room_id]['drop_info'] = room_info.get('drop_info',{})
        return floor_data

    def get_played_floor_info(self,floor_id):
        """
        * 获取用户已经打过的战场的star信息
        * 包括简单 困难 和 炼狱
        * miaoyichao
        """
        #获取一份已经打过的战场信息
        has_played_info_copy = self.has_played_info
        #获取里面的各种战场信息
        dungeon_info = has_played_info_copy.get('normal',{})
        #将里面的room_get_star和room_star 进行pop
        for floor_id in dungeon_info:
            floor_info = dungeon_info[floor_id]
            rooms_info = floor_info['rooms']
            for room_id in rooms_info:
                room_info = rooms_info[room_id]
                if 'room_get_star' in room_info:
                    room_info.pop('room_get_star')
                if 'room_star' in room_info:
                    room_info.pop('room_star')
                room_info['copy_times'] = self.get_today_copy_info('normal',floor_id,room_id)
        #初始化该类型的战场
        floordata = {}
        floordata[floor_id] = dungeon_info.get(floor_id,{})
        #结果返回
        return floordata

    def get_today_copy_info(self,dungeon_type,floor_id,room_id):
        '''
        * miaoyichao
        * 获取今日可打副本的次数和总共打的次数
        '''

        #real_config实际的配置信息
        # if dungeon_type == 'special':
        #     real_config = self.game_config.special_dungeon_config
        if dungeon_type == 'daily':
            real_config = self.game_config.daily_dungeon_config
        else:
            real_config = self.game_config.normal_dungeon_config
        #判断战场类型 计算正常情况下可以打多少次 默认10次
        if dungeon_type == 'daily':
            #每日战场是根据 floor 信息进行确认打多少次的
            cur_can_in = real_config[floor_id].get('can_make_copy_cn',10)
        else:
            cur_can_in = real_config[floor_id]['rooms'][room_id].get('can_make_copy_cn',10)

        #获取战场当前已经打的信息
        dungeon_repeat_info = self.dungeon_repeat_info
        #获取当天信息
        today_str = utils.get_today_str()
        if today_str == dungeon_repeat_info['today_str']:
            if dungeon_type == 'daily':
                try:
                    #去找该floor已经打过多少次
                    has_repeat_times = dungeon_repeat_info[dungeon_type][floor_id]
                except:
                    #没有找到的时候就知道该战场没有被打过 那么就直接返回0即可
                    has_repeat_times = 0
            elif dungeon_type == 'normal':
                try:
                    #去找该room已经打过多少次
                    has_repeat_times = dungeon_repeat_info[dungeon_type][floor_id][room_id]
                except:
                    #没有找到的时候就知道该战场没有被打过 那么就直接返回0即可
                    has_repeat_times = 0
        else:
            #日期过期重置
            dungeon_repeat_info = {
                'today_str':utils.get_today_str(),
            }
            self.put()
            has_repeat_times = 0
        #格式化要返回的参数
        all_times = cur_can_in
        left_times = all_times - has_repeat_times
        data = {}
        data['all_times'] = all_times
        data['left_times'] = left_times
        return data

    def update_dungeon_info(self,dungeon_type,floor_id,room_id, once_daily = False):
        """
        更新用户的战场信息
        """
        #通关奖励
        clear_floor_coin = 0
        #如果是普通战场
        if dungeon_type == 'normal':
            #所完成战场是该用户当前的最新战场时，更新最新战场信息
            normal_current = self.dungeon_info['normal_current']
            if floor_id == normal_current['floor_id'] and \
            room_id == normal_current['room_id'] and normal_current['status'] != 2:
                conf = self.game_config.normal_dungeon_config
                #有下一局时,更新为下一局
                if str(int(room_id) + 1) in conf[floor_id]['rooms']:
                    #更新当前最新战场为下一局
                    self.dungeon_info['normal_current']['room_id'] = str(int(room_id) + 1)
                #没有下一局时，当前场clear
                else:
                    #有下一场时，更新为下一场,局数从1开始
                    if str(int(floor_id) + 1) in conf:
                        self.dungeon_info['normal_current']['floor_id'] = str(int(floor_id) + 1)
                        self.dungeon_info['normal_current']['room_id'] = '1'
                    else:
                        #没有下一场时，只标识当前场clear
                        self.dungeon_info['normal_current']['status'] = 2
                    #赠送元宝
                    clear_floor_coin = UserProperty.get(self.uid).dungeon_clear()
                    self.clear_normal_dungeon(str(floor_id))
        elif dungeon_type == 'special' or dungeon_type == 'weekly' or dungeon_type == 'daily':
            self.__resolve_once_daily(floor_id, room_id, dungeon_type, once_daily)
            #活动战场时，更新最短通关时间
            if self.dungeon_info[dungeon_type][floor_id]['rooms'].get(room_id,0) != 2:
                self.dungeon_info[dungeon_type][floor_id]['rooms'][room_id] = 2
                #全部小关卡clear并且该战场没有clear时
                if self.dungeon_info[dungeon_type][floor_id]['status'] != 2:
                    clear_fg = True
                    for rmid in self.dungeon_info[dungeon_type][floor_id]['rooms']:
                        if self.dungeon_info[dungeon_type][floor_id]['rooms'][rmid] != 2:
                            clear_fg = False
                            break
                    if clear_fg:
                        self.dungeon_info[dungeon_type][floor_id]['status'] = 2
                        #赠送元宝
                        clear_floor_coin = UserProperty.get(self.uid).dungeon_clear()
        #清除未完成的迷宫信息
        self.dungeon_info['last'] = {}
        self.put()
        data = {
            'normal_current':self.dungeon_info['normal_current'],
            # 'special':self.dungeon_info['special'],
            # 'weekly':self.dungeon_info.get('weekly',{}),
            'daily':self.dungeon_info.get('daily',{}),
        }
        if clear_floor_coin:
            data['clear_floor_coin'] = clear_floor_coin
        return data

    def __resolve_once_daily(self,floor_id, room_id, dungeon_type, once_daily):
        #战场只能打一次，所以标志能否打
        if once_daily and self.dungeon_info[dungeon_type][floor_id].get('once_daily',{}):
            self.dungeon_info[dungeon_type][floor_id]['once_daily']['rooms'][room_id] = False
            clear_all = True
            for rmid in self.dungeon_info[dungeon_type][floor_id]['rooms']:
                if self.dungeon_info[dungeon_type][floor_id]['once_daily']['rooms'][rmid]:
                    clear_all = False
                    break
            if clear_all:
                self.dungeon_info[dungeon_type][floor_id]['once_daily']['can_fight'] = False
            self.put()
            
    def __reset_once_daily_and_open_special(self):
        """
        重置每天只能打一次战场关卡状态
        """
        pt_fg = False
        # for floor_id in self.dungeon_info['special']:
        #     open_special_coin = self.game_config.dungeon_world_config.get('open_special_coin',[])
        #     if open_special_coin and 'open_dungeon_info' in self.dungeon_info['special'][floor_id]:
        #         open_coin = open_special_coin[0]
        #         self.dungeon_info['special'][floor_id]['open_dungeon_info'] = {
        #                                                                           'open_cnt':0,
        #                                                                           'open_coin':open_coin,
        #                                                                           'expire_time':0,
        #                                                                           }
        #         pt_fg = True
        #     if not self.dungeon_info['special'][floor_id].get('once_daily',{}):
        #         continue
        #     self.dungeon_info['special'][floor_id]['once_daily']['can_fight'] = True
        #     for rmid in self.dungeon_info['special'][floor_id]['once_daily']['rooms']:
        #         self.dungeon_info['special'][floor_id]['once_daily']['rooms'][rmid] = True
        #     pt_fg = True
        if pt_fg:
            self.put()
        
    def clear_normal_dungeon(self,floor):
        """
        普通战场通关额外奖励
        """
        dungeon_clear_award = self.game_config.dungeon_world_config.get('dungeon_clear_award',{})
        if floor in dungeon_clear_award:
            award = dungeon_clear_award[floor]
            user_gift_obj = UserGift.get_instance(self.uid)
            user_gift_obj.add_gift(award, utils.get_msg('dungeon','clear_dungeon', self))
            

    def check_new_dungeon(self):
        """检查是否有新战场配置，主要是普通战场和活动特殊战场
        """
        #普通战场当前最新任务已经完成时，检查是否有新战场
        put_fg = False
        normal_conf = self.game_config.normal_dungeon_config
        if self.dungeon_info['normal_current']['status'] == 2 and \
        str(int(self.dungeon_info['normal_current']['floor_id']) + 1) in normal_conf:
            self.dungeon_info['normal_current'] = {
                'floor_id':str(int(self.dungeon_info['normal_current']['floor_id']) + 1),
                'room_id':'1',
                'status':0,
            }
            put_fg = True
        #检查是否有新的战场
        #特殊战场
        # special_conf = self.game_config.special_dungeon_config
        # open_special_coin = self.game_config.dungeon_world_config.get('open_special_coin',[])
        # for special_key,special_value in special_conf.iteritems():
        #     if 'loop_gap' not in special_value and\
        #      'special_key' in self.dungeon_info['special'] and\
        #      'open_dungeon_info' in self.dungeon_info['special'][special_key]:
        #         self.dungeon_info['special'][special_key].pop('open_dungeon_info')
        #         put_fg = True
        #     tag,return_start_time,return_end_time = utils.in_speacial_time(special_conf[special_key],False)
        #     if not tag and 'loop_gap' not in special_value:
        #         continue
        #     if special_key in self.dungeon_info['special']:
        #         #如果有新追加的关卡，加入进去，并设置为未通关状态
        #         once_daily_conf = special_value.get('once_daily',False)
        #         once_daily = self.dungeon_info['special'][special_key].get('once_daily',{})
        #         new_once_daily_room = False
        #         if once_daily_conf and not once_daily:
        #             self.dungeon_info['special'][special_key]['once_daily'] = {'rooms':{},'can_fight':True}
        #             put_fg = True
        #         elif not once_daily_conf and once_daily:
        #             self.dungeon_info['special'][special_key].pop('once_daily')
        #             put_fg = True
        #         for room_id in special_value['rooms']:
        #             if room_id not in self.dungeon_info['special'][special_key]['rooms']:
        #                 self.dungeon_info['special'][special_key]['rooms'][room_id] = 0
        #                 self.dungeon_info['special'][special_key]['status'] = 0
        #                 if once_daily_conf:
        #                     self.dungeon_info['special'][special_key]['once_daily']['rooms'][room_id] = True
        #                     new_once_daily_room = True
        #                 put_fg = True
        #             elif once_daily_conf and room_id not in self.dungeon_info['special'][special_key]['once_daily']['rooms']:
        #                 self.dungeon_info['special'][special_key]['once_daily']['rooms'][room_id] = True
        #                 put_fg = True
        #         if once_daily_conf and \
        #         new_once_daily_room and not self.dungeon_info['special'][special_key]['once_daily']['can_fight']:
        #             self.dungeon_info['special'][special_key]['once_daily']['can_fight'] = True
        #             put_fg = True
        #     else:
        #         special_temp = {
        #             'status':0,
        #             'rooms':{},
        #         }
        #         once_daily_conf = special_value.get('once_daily',False)
        #         if once_daily_conf:
        #             special_temp['once_daily'] = {'rooms':{},'can_fight':True}
        #         for room_id in special_value['rooms']:
        #             special_temp['rooms'][room_id] = 0
        #             if once_daily_conf:
        #                 special_temp['once_daily']['rooms'][room_id] = True
        #         self.dungeon_info['special'][special_key] = special_temp
        #         put_fg = True
        #     #加入提前开启活动战场信息
        #     #循环战场加一项提前开启信息
        #     if 'loop_gap' in special_value and 'open_dungeon_info' not in self.dungeon_info['special'][special_key]:
        #         if open_special_coin:
        #             open_coin = open_special_coin[0]
        #             self.dungeon_info['special'][special_key]['open_dungeon_info'] = {
        #                                                                               'open_cnt':0,
        #                                                                               'open_coin':open_coin,
        #                                                                               'expire_time':0,
        #                                                                               }
        #             put_fg = True
        # #每天限时战场
        # weekly_conf = self.game_config.weekly_dungeon_config
        # for weekly_key,weekly_value in weekly_conf.iteritems():
        #     if 'weekly' not in self.dungeon_info:
        #         self.dungeon_info['weekly'] = {}
        #         put_fg = True
        #     if weekly_key not in self.dungeon_info['weekly']:
        #         week_temp = {
        #             'status':0,
        #             'rooms':{},
        #         }
        #         for room_id in weekly_value['rooms']:
        #             week_temp['rooms'][room_id] = 0

        #         self.dungeon_info['weekly'][weekly_key] = week_temp
        #         put_fg = True
        #     else:
        #         #如果有新追加的关卡，加入进去，并设置为未通关状态
        #         for room_id in weekly_value['rooms']:
        #             if room_id not in self.dungeon_info['weekly'][weekly_key]['rooms']:
        #                 self.dungeon_info['weekly'][weekly_key]['rooms'][room_id] = 0
        #                 self.dungeon_info['weekly'][weekly_key]['status'] = 0
        #                 put_fg = True
        # #room已经失效时
        # for dungeon_type in ['special','weekly']:
        #     if dungeon_type == 'special':
        #         dungeon_conf = special_conf
        #     elif dungeon_type == 'weekly':
        #         dungeon_conf = weekly_conf
        #     for floor_id in self.dungeon_info[dungeon_type]:
        #         if floor_id not in dungeon_conf:
        #             continue
        #         for rmid in copy.deepcopy(self.dungeon_info[dungeon_type][floor_id]['rooms']):
        #             if rmid not in dungeon_conf[floor_id]['rooms']:
        #                 self.dungeon_info[dungeon_type][floor_id]['rooms'].pop(rmid)
        #                 put_fg = True
        if put_fg:
            self.put()
            
    def can_once_daily(self,dungeon_type,floor_id,room_id):
        """
        检查每天一次战场现在是否可以打
        """
        if 'once_daily' not in self.dungeon_info[dungeon_type][floor_id]:
            return True
        return self.dungeon_info[dungeon_type][floor_id]['once_daily']['rooms'].get(room_id,True)


    def check_limit_dungeon(self,rk_user,params):
        """
        * 检查每天战场可以打多少次
        * miaoyichao
        * 2014-03-27
        * ture can fight  flase can not fight 
        """
        dungeon_type = params['dungeon_type']
        floor_id = params['floor_id']
        room_id = params['room_id']
        dungeon_repeat_info_obj = copy.deepcopy(self.dungeon_repeat_info)
        today_str = utils.get_today_str()
        if today_str == dungeon_repeat_info_obj['today_str']:
            #获取今日战场的类型信息
            try:
                #获取征战多少次
                #获取战场类型
                db_dungeon_type = dungeon_repeat_info_obj.get(dungeon_type,{})

                if dungeon_type == 'normal':
                    #获取floor的id
                    db_floor_id = db_dungeon_type.get(floor_id,{})
                    if not len(db_floor_id):
                        db_dungeon_type[floor_id] = {}
                    #获取房间id
                    db_room_id = db_dungeon_type[floor_id].get(room_id,0)
                    if not db_room_id:
                        db_dungeon_type[floor_id][room_id] = 0
                #因为每日战场的可打次数是整个 floor 的不是每个 room 的 所以要区别对待
                if dungeon_type == 'daily':
                    if floor_id not in db_dungeon_type:
                        db_dungeon_type[floor_id] = 0
                    has_already_conquer = db_dungeon_type[floor_id]
                else:
                    has_already_conquer = db_dungeon_type[floor_id][room_id]
                if has_already_conquer:
                    #有征战过该战场
                    '''
                    * 根据不同的战场获取不同战场的配置信息中的可以打的次数
                    * miaoyichao
                    '''
                    if dungeon_type == 'normal':
                        cur_can_in = self.game_config.normal_dungeon_config[floor_id]['rooms'][room_id].get('can_make_copy_cn',10)
                    elif dungeon_type == 'daily':
                        cur_can_in = self.game_config.daily_dungeon_config[floor_id].get('can_make_copy_cn',10)
                    elif dungeon_type == 'weekly':
                        cur_can_in = self.game_config.weekly_dungeon_config[floor_id]['rooms'][room_id].get('can_make_copy_cn',10)
                    # elif dungeon_type == 'special':
                    #     cur_can_in = self.game_config.special_dungeon_config[floor_id]['rooms'][room_id].get('can_make_copy_cn',10)
                    else:
                        cur_can_in = 10
                    max_repeat = cur_can_in
                    if has_already_conquer>=max_repeat:
                        return False
                    else:
                        return True
                else:
                    #没有征战过该战场
                    if dungeon_type == 'daily':
                        #处理每日战场
                        try:
                            dungeon_repeat_info_obj[dungeon_type][floor_id] = 0
                        except:
                            dungeon_repeat_info_obj[dungeon_type] = {}
                            dungeon_repeat_info_obj[dungeon_type][floor_id] = 0
                    else:
                        #处理普通战场
                        try:
                            dungeon_repeat_info_obj[dungeon_type][floor_id][room_id] = 0
                        except:
                            dungeon_repeat_info_obj[dungeon_type] = {}
                            dungeon_repeat_info_obj[dungeon_type][floor_id] = {}
                            dungeon_repeat_info_obj[dungeon_type][floor_id][room_id] = 0
                        
            except :
                traceback.print_exc()
                return False
            #更新该次操作的信息
            self.dungeon_repeat_info.update(dungeon_repeat_info_obj)
            #保存
            self.put()
            return True
        else:
            #战场信息过期 重置战场信息
            self.dungeon_repeat_info = {
                'today_str':utils.get_today_str(),
                'special':{},
                'daily':{},
                'normal':{},
            }
            self.put()
            return True
        
    def update_has_played_info(self,dungeon_type,floor_id,room_id,hard_ratio,star_ratio):
        '''
        * miaoyichao
        * 更新战场完结的信息
        '''
        # 如果是新手战场跳过
        if floor_id == '1' and room_id == '0':
            return
        put_fg = False
        #目前再是只有一个难度  如果有其他难度的话只需要修改hard_list即可
        hard_list = ['normal']
        global game_config
        game_config = self.game_config
        conf_dict = {
            'normal': game_config.normal_dungeon_config,
            'daily': game_config.daily_dungeon_config
        }
        dungeon_config = conf_dict[dungeon_type]
        if floor_id in self.has_played_info[dungeon_type]:
            floor_info = self.has_played_info[dungeon_type][floor_id]
            if room_id in floor_info['rooms']:
                #已经有该room的信息
                room_info = floor_info['rooms'][room_id]
                if hard_ratio in room_info:
                    #该难度玩家以前玩过 只需要判断星级和完美标志即可
                    if room_info[hard_ratio]['get_star'] < int(star_ratio):
                        #玩家这次打的结果比较好 更新信息
                        #更新floor的cur_star 信息
                        floor_info['cur_star'] += int(star_ratio) - room_info[hard_ratio]['get_star']
                        #更新room中获取的星
                        room_info['room_get_star'] += int(star_ratio) - room_info[hard_ratio]['get_star']
                        #更新该难度的星
                        room_info[hard_ratio]['get_star'] = int(star_ratio)
                        #计算整个room一共有多少星
                        room_total_star = 0
                        #取得该room的配置信息
                        room_conf_info = dungeon_config[floor_id]['rooms'][room_id]
                        for hard in hard_list:
                            if hard == 'normal':
                                room_total_star += 3
                            else:
                                room_total_star += room_conf_info.get(hard,0)
                        #查看是否需要更新room完美标志信息
                        if room_info['room_get_star'] >= room_total_star:
                            room_info['perfect'] = True
                        put_fg = True
                else:
                    #该难度不在记录中 初始化该难度的信息
                    room_info[hard_ratio] = {}
                    #记录该次的星信息
                    room_info[hard_ratio]['get_star'] = int(star_ratio)
                    #更新room中获取的星
                    room_info['room_get_star'] += int(star_ratio)
                    #更新floor的cur_star 信息
                    floor_info['cur_star'] += int(star_ratio)
                    #计算整个room一共有多少星
                    room_total_star = 0
                    #取得该room的配置信息
                    room_conf_info = dungeon_config[floor_id]['rooms'][room_id]
                    for hard in hard_list:
                        if hard == 'normal':
                            room_total_star += 3
                        else:
                            room_total_star += room_conf_info.get(hard,0)
                    #查看是否需要更新room完美标志信息
                    if room_info['room_get_star'] == room_total_star:
                        room_info['perfect'] = True
                    put_fg = True
            else:
                #没有这个room的信息
                floor_info['rooms'][room_id] = {}
                floor_info['rooms'][room_id][hard_ratio] = {}
                room_info = floor_info['rooms'][room_id]
                #记录这次打的信息
                room_info[hard_ratio]['get_star'] = int(star_ratio)
                #计算整个room一共有多少星
                room_total_star = 0
                #取得该room的配置信息
                room_conf_info = dungeon_config[floor_id]['rooms'][room_id]
                for hard in hard_list:
                    if hard == 'normal':
                        room_total_star += 3
                    else:
                        room_total_star += room_conf_info.get(hard,0)
                #设置该room的所取得的star信息
                room_info['room_get_star'] = int(star_ratio)
                #设置该room的完美标志
                if room_total_star>int(star_ratio):
                    floor_info['rooms'][room_id]['perfect'] = False
                else:
                    floor_info['rooms'][room_id]['perfect'] = True
                #更新floor的cur_star 信息
                floor_info['cur_star'] += int(star_ratio)
                put_fg = True
        else:
            #没有这一个floor的信息 需要重新构建该floor的信息
            has_played_info = self.has_played_info
            has_played_info[dungeon_type][floor_id] = {}
            has_played_info[dungeon_type][floor_id]['rooms'] = {}
            has_played_info[dungeon_type][floor_id]['rooms'][room_id] = {}
            floor_info = has_played_info[dungeon_type][floor_id]
            #计算该floor的所有的星
            floor_all_star = self.__get_floor_all_star(dungeon_type,floor_id)
            floor_info['floor_all_star'] = floor_all_star
            #因为该floor是最新的所以当前所打的星就是当前floor所获得最大的星
            floor_info['cur_star'] = int(star_ratio)
            #初始化宝箱信息
            floor_info['gold_box'] = False
            floor_info['silver_box'] = False
            floor_info['bronze_box'] = False
            #记录信息
            floor_info['rooms'][room_id][hard_ratio]={}
            floor_info['rooms'][room_id][hard_ratio]['get_star'] = int(star_ratio)
            #取得该room的配置信息
            room_conf_info = dungeon_config[floor_id]['rooms'][room_id]
            #计算整个room一共有多少星
            room_total_star = 0
            for hard in hard_list:
                if hard == 'normal':
                    room_total_star += 3
                else:
                    room_total_star += room_conf_info.get(hard,0)
            #设置该room的所取得的star信息
            floor_info['rooms'][room_id]['room_get_star'] = int(star_ratio)
            #设置该room的完美标志
            if room_total_star > int(star_ratio):
                floor_info['rooms'][room_id]['perfect'] = False
            else:
                floor_info['rooms'][room_id]['perfect'] = True
            put_fg = True
        if put_fg:
            self.put()

    def __get_floor_all_star(self,dungeon_type,floor_id):
        '''
        * miaoyichao
        * 获取该floorid的星级 
        * 遍历每一个room获取星级
        '''
        #计算基础数据
        config_info = self.game_config.normal_dungeon_config
        #因为每一个room有三种难度
        rooms = config_info[floor_id].get('rooms',{})
        all_star = 0
        #计算该floor的star总数
        for room in rooms:
            if room == '0':
                pass
            else:
                all_star += rooms[room].get('normal',3)
        return all_star

    def recover_copy(self,dungeon_type,floor_id,room_id):
        """重置战场已打次数信息
        若为普通战场，则直接将已打次数置为  0
        若为每日试炼战场则，将已打次数减一
        """
        if dungeon_type == 'normal':
            self.dungeon_repeat_info[dungeon_type][floor_id][room_id] = 0
        elif dungeon_type == 'daily':
            self.dungeon_repeat_info[dungeon_type][floor_id] -= 1
        self.put()

    def add_repeat_cnt(self, dungeon_type, floor_id, room_id, cnt=1):
        if dungeon_type == 'normal':
            self.dungeon_repeat_info[dungeon_type][floor_id][room_id] += cnt
        elif dungeon_type == 'daily':
            self.dungeon_repeat_info[dungeon_type][floor_id] += cnt
        self.put()
