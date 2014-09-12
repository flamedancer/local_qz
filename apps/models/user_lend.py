#!/usr/bin/env python
# encoding: utf-8
"""
user_lend.py

"""
from apps.models.user_property import UserProperty as UserPropertyMod
from apps.common import utils
from apps.models import GameModel


class UserLend(GameModel):
    """
    用户被借卡的信息
    """
    pk = 'uid'
    fields = ['uid','lend_info']
    def __init__(self):
        """初始化用户游戏内部基本信息

        Args:
            uid: 用户游戏ID
            data:游戏内部基本信息
        """
        self.uid = None
        self.lend_info = {}


    @classmethod
    def get_instance(cls,uid):
        obj = super(UserLend,cls).get(uid)

        if obj is None:
            obj = cls._install(uid)
        obj.refresh_daily_info()

        return obj

    @classmethod
    def _install(cls,uid):
        obj = cls()
        obj.uid = uid
        obj.lend_info = {
            'friend':0,
            'other':0,
            'gacha_pt':0,
        }
        obj.put()
        return obj

    def refresh_daily_info(self):
        """
        每日根据当天日期，决定是否要刷新数据
        """
        today = utils.get_today_str()
        if today != self.lend_info.get('today'):
            self.lend_info['today'] = today
            self.lend_info['helper_ids'] = []
            self.put()
            
    def read_info(self,params):
        """
        用户登录时，显示被借卡信息，并且提取其中的积分
        """
        #device_type = params.get('device_type','1')
        if self.lend_info['gacha_pt']:
            userproperty_obj = UserPropertyMod.get(self.uid)
            userproperty_obj.add_gacha_pt(self.lend_info['gacha_pt'])
            #lend_temp = copy.deepcopy(self.lend_info)
            #lend_temp['now_gacha_pt'] = userproperty_obj.gacha_pt
#            from apps.models.user_gift import UserGift
#            user_gift_obj = UserGift.get_instance(self.uid)
#            user_gift_obj.add_gift({'gacha_pt':self.lend_info['gacha_pt']},u'帮助了友军获得:')
            self.lend_info['friend'] = 0
            self.lend_info['other'] = 0
            self.lend_info['gacha_pt'] = 0
            self.put()
            return u''
        else:
            return u''

    def add_lend_info(self,lend_type,gacha_pt,uid=''):
        """增加
        """
        self.lend_info[lend_type] += 1
        if uid:
            if 'helper_ids' not in self.lend_info:
                self.lend_info['helper_ids'] = [uid]
                self.lend_info['gacha_pt'] += gacha_pt
            elif uid not in self.lend_info['helper_ids']:
                self.lend_info['helper_ids'].append(uid)
                self.lend_info['gacha_pt'] += gacha_pt
        self.put()

    def format_lendinfo(self,lend_info,device_type):
        """
        """
        if device_type == '0':
            res = u'<span style="font-size:30px">'
        else:
            res = u'<span style="font-size:16px">'
        res += u'<p align="center"><font>幫助了<font color="#9900FF">%d</font>支友軍和<font color="#9900FF">%d</font>支義軍！</font></p>' % (lend_info['friend'],lend_info['other'])
        res += u'<p align="center"><font>作為幫助回禮獲得了援軍點數<font color="#9900FF">%d</font>點</font></p>' % lend_info['gacha_pt']
        res += u'<p align="center"><font>現在擁有<font color="#9900FF">%d</font>點援軍點數</font></p>' % lend_info['now_gacha_pt']
        gacha_pt_cost = self.game_config.gacha_config['cost_gacha_pt']
        if lend_info['now_gacha_pt'] >= gacha_pt_cost:
            can_gacha_num = lend_info['now_gacha_pt'] / gacha_pt_cost
            res += u'<p align="center"><font>可以求良將<font color="#9900FF">%d</font>次</font></p>' % can_gacha_num
        else:
            need_gacha_pt = gacha_pt_cost - lend_info['now_gacha_pt']
            res += u'<p align="center"><font>還需要<font color="#FF0000">%d</font>點援軍點數才可以求良將</font></p>' % need_gacha_pt
        res += u'</span>'
        return res



