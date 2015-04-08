# encoding: utf-8
"""
file: apps/models/user_character.py
start: 2015-03-01
"""
import datetime
import time
import copy
from apps.common import utils
from apps.models import GameModel
from operator import itemgetter
import json

class UserCharacter(GameModel):
    pk = 'uid'
    fields = ['uid', 'talent_info']

    def __init__(self):
        self.uid = None
        self.talent_info = None

    # 天赋树 字典结构  lv 表示状态 -1:还没开启(还没解锁),0:可以学习(领悟),正数:已经学习,数字表示等级
    # __talent_tree = {
    #     '1': {
    #         'lv': -1
    #     },
    #     '2': {
    #         'lv': -1,
    #         'jin': 0,   # 0 关   1 开
    #         'mu': 0,
    #         'shui': 0,
    #         'huo': 0,
    #         'tu': 0,
    #     },
    # talent tree 只表示天赋的状态,
    __init_talent_tree = {
        '1': {
            'lv':-1
        },
        '2': {
            'lv':-1,
            'jin':0,
            'mu':0,
            'shui':0,
            'huo':0,
            'tu':0,
        },
        '3': {
            'lv':-1
        },
        '4': {
            'lv':-1,
            'jin':0,
            'mu':0,
            'shui':0,
            'huo':0,
            'tu':0,
        },
        '5': {
            'lv':-1
        },
        '6': {
            'lv':-1,
            'jin':0,
            'mu':0,
            'shui':0,
            'huo':0,
            'tu':0,
        },
    }


    @classmethod
    def create(cls,uid):
        uc = cls()
        uc.uid = uid
        uc.talent_info = {
            'cur_talent_index': 0,
            'talent_page': [copy.deepcopy(cls.__init_talent_tree)],        # 天赋，以后可能有几套天赋
            'costed_star': 0,               # 学习天赋消耗的星数
            'costed_gold': 0,               # 学习天赋消耗的铜钱
            'refresh_times': 0,             # 重洗天赋的次数
        }

        return uc

    @classmethod
    def get_instance(cls, uid):
        """ 获取一个当前的用户实例
        Args:
            uid: 用户游戏ID
        """
        obj = super(UserCharacter,cls).get(uid)
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
        obj = super(UserCharacter,cls).get(uid)
        return obj

    @property
    def cur_talent_index(self):
        return self.talent_info['cur_talent_index']

    @property
    def cur_talent(self):
        return self.talent_info['talent_page'][self.cur_talent_index]

    @property
    def star_num(self):
        '''可用的星数'''
        num = self.user_dungeon.total_got_star - self.talent_info['costed_star']
        return num

    @property
    def refresh_times(self):
        return self.talent_info['refresh_times']

    def consume_star(self, num):
        self.talent_info['costed_star'] += num
        self.put()

    def consume_gold(self, num):
        self.talent_info['costed_gold'] += num
        self.put()

    def is_star_enough(self, num):
        if self.star_num - num >= 0:
            return True
        return False

    def learn_talent(self, new_talent):
        '''
        学习天赋 成功返回 0 
        '''
        max_lv = self.game_config.character_talent_config['max_lv']
        new_talent = json.loads(new_talent)
        print 'new_talent', new_talent
        for layer in new_talent:
            if layer not in self.cur_talent:
                return 1
            # 还没开启
            if new_talent[layer]['lv'] != self.cur_talent[layer]['lv'] and self.cur_talent[layer]['lv'] < 0:
                return 2
            # 等级不能倒退
            if new_talent[layer]['lv'] < self.cur_talent[layer]['lv']:
                return 3
            if new_talent[layer]['lv'] > max_lv:
                return 4

            if len(new_talent[layer]) == 6:
                try:
                    # 已开启的属性珠子不能关闭
                    if new_talent[layer]['jin'] < self.cur_talent[layer]['jin']:
                        return 5
                
                    if new_talent[layer]['mu'] < self.cur_talent[layer]['mu']:
                        return 6
               
                    if new_talent[layer]['shui'] < self.cur_talent[layer]['shui']:
                        return 7
               
                    if new_talent[layer]['huo'] < self.cur_talent[layer]['huo']:
                        return 8
               
                    if new_talent[layer]['tu'] < self.cur_talent[layer]['tu']:
                        return 9
                except:
                    # 天赋树结构不对
                    return 10
                # 属性天赋有升级时,一定要开启至少一个属性
                if new_talent[layer]['lv'] > 0:
                    if new_talent[layer]['jin'] + new_talent[layer]['mu'] + new_talent[layer]['shui'] + new_talent[layer]['huo'] + new_talent[layer]['tu'] == 0:
                        return 11
                else:
                # 属性天赋没开启或还没学习时, 不能开启任何一个属性
                    if new_talent[layer]['jin'] + new_talent[layer]['mu'] + new_talent[layer]['shui'] + new_talent[layer]['huo'] + new_talent[layer]['tu'] > 0:
                        return 12
            elif len(new_talent[layer]) == 1:
                pass
            else:
                # 天赋树结构不对
                return 10

            # 上一级还没学习,所以本级天赋不能学
            #if new_talent[layer]['lv'] > self.cur_talent[layer]['lv']:
            #    last_layer = self.__get_last_layer(layer)
            #    if last_layer:
            #        if last_layer['lv'] <= 0:
            #            return 13


        self.cur_talent.update(new_talent)
        self.check_open_talent()
        self.put()
        return 0

    def __get_last_layer(self, cur_layer):
        '''获得上一层天赋'''
        if cur_layer == '1':
            return None
        last_layer = str(int(cur_layer) - 1)
        return self.cur_talent[last_layer]


    def refresh_talent(self):
        '''重洗天赋'''
        for layer in self.cur_talent:
            if self.cur_talent[layer]['lv'] > 0:
                self.cur_talent[layer]['lv'] = 0
            if len(self.cur_talent[layer]) == 6:
                for shuxing in ['jin', 'mu','shui','huo','tu']:
                    self.cur_talent[layer][shuxing] = 0
        self.talent_info['costed_star'] = 0          # 返还 已消耗的星数
        self.user_property.add_gold(self.talent_info['costed_gold'])
        self.talent_info['costed_gold'] = 0          # 返还 已消耗的铜钱
        self.talent_info['refresh_times'] += 1
        self.put()

    def check_open_talent(self):
        '''检查是否有新天赋能开启,有则开启新天赋'''
        conf = self.game_config.character_talent_config['open_lv']
        user_lv = self.user_property.lv

        #fb_star = self.user_dungeon.total_got_star
        #print 'wzgdb ',user_lv, fb_star
        #for t in conf: 
        #    if user_lv == t[0]:
        #        if fb_star >= t[1]: 
        #            self.__open_talent(conf[t])    ##  t[0] 等级,  t[1] 星数
        for lv in conf: 
            if user_lv >= int(lv):
                self.__open_talent(conf[lv])

    def __open_talent(self, layer):
        ''' 上一层学过才能开启这一层'''
        
        #if self.cur_talent[layer]['lv'] == -1:
        #    self.cur_talent[layer]['lv'] = 0
        if self.cur_talent[layer]['lv'] == -1:
            last_layer = self.__get_last_layer(layer)
            if last_layer:
                if last_layer['lv'] > 0:
                    self.cur_talent[layer]['lv'] = 0
            else:
                self.cur_talent[layer]['lv'] = 0

        self.put()

    def zhuzi_damage(self):
        return self.game_config.user_level_config[str(self.user_property.lv)]['zhuzi_damage']
