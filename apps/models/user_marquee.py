#!/usr/bin/env python
# encoding: utf-8

from apps.oclib.model import BaseModel
from apps.models.virtual.card import Card as CardMod
from apps.config.game_config import game_config
import time
from apps.common import utils

class UserMarquee(BaseModel):
    """公用的跑马灯信息纪录
    Attributes:
        uid   : 用户分区标示
        marquee_info: 跑马灯信息
    """
    pk = 'uid'
    fields = ['uid', 'marquee_info', 'marquee_index', 'ex']

    def __init__(self):
        """初始化用户基本信息
        """
        self.uid = '1' #用户分区标示
        self.marquee_info = {}   #跑马灯信息
        self.marquee_index = 0#上一次存入的位置
        self.ex = 1              #时间戳，每10分钟纪录一次

    @classmethod
    def get(cls,subarea):
        obj = super(UserMarquee, cls).get(subarea)
        if not obj:
            obj = cls()
            obj.uid = subarea
            obj.marquee_info = {}
            obj.ex = 1
            obj.marquee_index = 0#上一次存入的位置
            obj.put()
        return obj

    @property
    def game_config(self):
        game_config.set_subarea(self.uid)
        return game_config
    
    def record(self, marquee_params):
        """纪录跑马灯信息, 30条"""
        ex = time.time()
        #时间戳，每10分钟纪录一次
        if ex - self.ex > 10 * 60:
        #if ex - self.ex > 10:
            params_type = marquee_params.get('type', '')
            if params_type in ['gacha_gold', 'gacha_charge']:#招募的跑马灯纪录
                cid = marquee_params['cid']
                if 'gacha_gold' == params_type:
                    if not cid in utils.get_marquee_config().get('gacha_gold', []):
                        return False
                description = u'%s成功招募到“%s星%s”，实力更进一步！'
                username = marquee_params['username']
                star = str(self.game_config.card_config.get(cid,{}).get('star',4))
                name = self.game_config.card_config.get(cid,{}).get('name','')
                dstr = description % (username, star, name)
            elif params_type == 'card_upgrade':#武将进化纪录跑马灯
                username = marquee_params['username']
                base_card = marquee_params['base_card']
                description = u'%s成功进化出“%s星%s”，实力更进一步！'
                new_cardmod = CardMod.get(base_card.upg_target)
                name = new_cardmod.name
                star = new_cardmod.star
                dstr = description % (username, star, name)
            elif params_type == 'pvp_end':#
                username = marquee_params['username']
                pvp_title = marquee_params['pvp_title']
                description = u'%s军衔成功升至“%s”，排名进一步上升！'
                dstr = description % (username, pvp_title)
            else:
                return False
            next_index = (self.marquee_index % 30) + 1
            self.marquee_info[str(next_index)] = dstr
            self.marquee_index = next_index
            self.ex = time.time()
            self.put()
            return True
        else:
            return False
