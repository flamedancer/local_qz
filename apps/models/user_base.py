#!/usr/bin/env python
# encoding: utf-8
"""
user_base.py

"""
import datetime,time,copy,traceback
from apps.common import utils
from apps.models.user_marquee import UserMarquee
from apps.models.account_mapping import AccountMapping
from apps.common.utils import get_msg
from apps.models.user_name import UserName
from apps.models.user_gacha import UserGacha
from django.conf import settings

from apps.models import GameModel


class UserBase(GameModel):
    """用户基本信息

    Attributes:
        uid: 用户ID str
        username: 名称 str
        gender: 性别 str
        icons: 头像 str
        add_time: 添加应用时间 datetime
    """
    pk = 'uid'
    fields = ['uid','baseinfo']
    def __init__(self):
        """初始化用户基本信息

        Args:
            uid: 用户游戏ID
        """
        self.uid = None
        self.baseinfo = {}
        self.is_new = False
        self._friend = None  # 用户好友
        self._account = None

    @property
    def username(self):
        """用户好友
        """
        return self.baseinfo['username']

    @property
    def signature(self):
        """用户签名
        """
        return self.baseinfo.get('signature','')

    @property
    def frozen(self):
        """用户账号状态
        """
        return self.baseinfo['frozen']

    @property
    def in_frozen(self):
        """是否处于冻结期
        """
        if self.frozen:
            return True
        now = int(time.time())
        if self.baseinfo.get('unfroze_time') and self.baseinfo.get('unfroze_time') > now:
            return True
        return False

    @property
    def stop(self):
        """账户是否停用
        """
        return self.baseinfo.get('stop')

    @property
    def subarea(self):
        """分区号
        """
        return str(self.baseinfo.get('subarea', '1'))

#    @property
#    def client_macaddr(self):
#        if "client_macaddr" not in self.baseinfo:
#            self.baseinfo["client_macaddr"] = []
#        return self.baseinfo["client_macaddr"]
#    
#    @property
#    def mktids(self):
#        if "mktids" not in self.baseinfo:
#            self.baseinfo["mktids"] = []
#        return self.baseinfo["mktids"]

    @property
    def pid(self):
        """用户平台id
        """
        return self.baseinfo['pid']

    @property
    def platform(self):
        return self.baseinfo.get('platform','oc')

    @property
    def headurl(self):
        """用户好友
        """
        return self.baseinfo['headurl']

    @property
    def sex(self):
        """用户好友
        """
        return self.baseinfo['sex']


    @property
    def friend(self):
        """用户好友
        """
        if not self._friend:
            from apps.models.friend import Friend

            self._friend = Friend.get(self.uid)
            if not self._friend:
                self._friend = Friend._install(self.uid)

        return self._friend


    @property
    def account(self):
        """用户账户信息
        """
        if not self._account:
            self._account = AccountMapping.get(self.pid)
        return self._account

    @property
    def add_time(self):
        """注册时间
        """
        return self.baseinfo.get("add_time", int(time.time()))

    @classmethod
    def get(cls,uid):

        obj = super(UserBase,cls).get(uid)
        return obj

    @classmethod
    def get_uid(cls,pid,platform, subarea):
        '''
        PIDより、UIDを取得
        '''
        # 默认分区为 1 区

        rk_uid = AccountMapping.get_user_id(pid, subarea)
        return rk_uid


    @classmethod
    def get_exist_user(cls, pid, subarea='1'):
        '''
        用已存在的PID  取得 userbase 实例
        '''
        account = AccountMapping.get(pid)
        return cls.get(account.get_subarea_uid(subarea)) if account else None

    @classmethod
    def _install(cls,pid,platform='oc',uuid='', mktid='', version=1.0, client_type='', macaddr='',idfa='',ios_ver='', subarea=''):
        """检测安装用户

        Args:
            pid,platform
        """
        if subarea is '':
            subarea = '1'
        uid = cls.get_uid(pid, platform, subarea)
        rk_user = cls.get(uid)
        if rk_user is None:
            rk_user = cls._install_new_user(uid,pid,platform,uuid, mktid, version,client_type,macaddr,idfa,ios_ver, subarea=subarea)
        return rk_user

    @classmethod
    def create(cls,uid):
        ub = cls()
        ub.uid = uid
        ub.baseinfo = {
                            'pid':'',#内部32位的唯一id
                            'username':'',# 用户姓名
                            'subarea': '',  # 分区号
                            'sex':'' ,# 性别
                            'birthday':int(time.time()),
                            'mainurl':'',#
                            "headurl":'',# 头像
                            'add_time':int(time.time()),# 安装时间
                            'frozen':False,
                            'frozen_count':0,#已冻结次数
                            'unfroze_time':None,#解冻时间
                            'stop':False,
                            'openid':'',#开放平台有openid
                            'platform':'oc',#开放平台
                            'signature':'',
                            'marquee_rtime': time.time(),#跑马灯刷新时间，每10分钟一次
                            'install_version': '', # 安装时版本号

                        }

        return ub

    @classmethod
    def _install_new_user(cls,uid,pid,platform, uuid='', mktid='', version=1.0,client_type='',macaddr='',idfa='',ios_ver='', subarea='1'):
        """安装新用户，初始化用户及游戏数据

        Args:
            uid: 用户ID
        """
        now = int(time.time())

        rk_user = cls.create(uid)
        rk_user.baseinfo["pid"] = pid
        rk_user.baseinfo["add_time"] = now
        rk_user.baseinfo["platform"] = platform
        rk_user.baseinfo["client_type"] = client_type
        rk_user.baseinfo["subarea"] = subarea
        rk_user.baseinfo["install_version"] = float(version)
        if platform != 'oc':
            rk_user.baseinfo['bind_time'] = now
        if macaddr != '':
            rk_user.baseinfo['macaddr'] = macaddr
        if mktid != '':
            rk_user.baseinfo['mktid'] = mktid
        if uuid != '':
            rk_user.baseinfo['uuid'] = uuid
        if idfa != '':
            rk_user.baseinfo['idfa'] = idfa
        if ios_ver != '':
            rk_user.baseinfo['ios_ver'] = ios_ver
        rk_user.put()

        rk_user.is_new = True

        return rk_user

    def update_user_from_qq(self,base_data):
        """ 更新用户平台数据"""
        #self.baseinfo["username"] = base_data['data'].get('nick').decode('utf-8')
        self.baseinfo["sex"] = 1 if base_data['data'].get('sex') == 1 else 0
        self.baseinfo["platform"] = 'qq'
        self.baseinfo["openid"] = base_data['data'].get('openid')
        self.put()

    def update_user_from_sina(self,base_data):
        """ 更新用户平台数据"""
        #self.baseinfo["username"] = base_data.get('name').decode('utf-8')
        self.baseinfo["sex"] = 1 if base_data.get('gender', '').decode('utf-8') == u'm' else 0
        self.baseinfo["platform"] = 'sina'
        self.baseinfo["openid"] = base_data.get('id')
        self.put()

    def has_friend(self,fid):
        """检查用户是否有该好友
        """
        from apps.models.friend import Friend
        user_friend_obj = Friend.get(self.uid)
        return fid in user_friend_obj.friends
    
    @property
    def client_type(self):
        return self.baseinfo.get('client_type','')
    
    @property
    def install_version(self):
        return self.baseinfo.get('install_version',1.0)

    def wrapper_info(self):
        """将自己的信息打包成字典
        * modify by miaoyichao
        * 2014-03-26  add vip 字段
        """
        data = {
            'pid':self.pid,
            'platform':self.baseinfo.get('platform'),
            'username':self.username,
            'sex':self.sex,
            'max_stamina':self.user_property.max_stamina,
            'vip_cur_level':self.user_property.vip_cur_level,
            'vip_next_level':self.user_property.vip_next_level,
            'vip_charge_money':self.user_property.charge_sumcoin,
            'vip_next_lv_need_money':self.user_property.next_lv_need_coin,
            'uid':self.uid,
            'signature':self.baseinfo.get('signature',''),
            'max_friend_num':self.user_property.max_friend_num,
        }

        data.update(self.user_property.property_info)
        if 'get_card' in data:
            data.pop('get_card')
        if 'invite_info' in data:
            data.pop('invite_info')
        if 'bind_award' in data:
            data.pop('bind_award')
        if 'tapjoy' in data:
            data.pop('tapjoy')
        if 'bind_award' in data:
            data.pop('bind_award')
        if 'charge_sumcoin' in data:
            data.pop('charge_sumcoin')
        if 'update_award' in data:
            data.pop('update_award')
        if 'charge_sum_money' in data:
            data.pop('charge_sum_money')
        if 'double_charge_date' in data:
            data.pop('double_charge_date')
        if 'system_award_time' in data:
            data.pop('system_award_time')
        if 'bind_phone_number_info' in data and 'validate_code' in data['bind_phone_number_info']:
            data['bind_phone_number_info'].pop('validate_code')
        #data['cost'] = self.user_property.cost
        data['this_lv_now_exp'] = self.user_property.this_lv_now_exp
        data['next_lv_need_exp'] = self.user_property.next_lv_need_exp
        data['invite_code'] = self.user_property.invite_code
        #也许Friend不存在
        from apps.models.friend import Friend
        objFriend = Friend.get_instance(self.uid)
        data["friend_request_num"] = len(objFriend.get_request_ids())
        data['friend_gift_num'] = objFriend.get_gift_num()

        # #pvp
        # user_pvp_obj = self.user_pvp.get(self.uid)
        # pvp_baseinfo_copy = copy.deepcopy(user_pvp_obj.pvp_info['base_info'])
        # pvp_baseinfo_copy.update(user_pvp_obj.next_level_pt())
        # pvp_baseinfo_copy['max_pvp_stamina'] = user_pvp_obj.max_pvp_stamina
        # if 'last' in pvp_baseinfo_copy:
        #     pvp_baseinfo_copy.pop('last')
        # if 'pt_user_lv' in pvp_baseinfo_copy:
        #     pvp_baseinfo_copy.pop('pt_user_lv')
        # data['pvp'] = pvp_baseinfo_copy
        # 实时pvp相关
        data['real_pvp_title'] = self.user_real_pvp.pvp_title
        data['honor'] = self.user_real_pvp.honor

        #新礼包数
        from apps.models.user_gift import UserGift
        user_gift_obj = UserGift.get(self.uid)
        data['new_gift_num'] = user_gift_obj.get_new_gift_num(self.user_property)

        #pvp新手标志
        data['pvp_newbie'] = self.user_property.pvp_newbie
        #首冲标志
        data['first_charge'] = self.user_property.double_charge or self.user_property.first_charge
        #月卡信息
        data['month_item_info'] = copy.deepcopy(self.user_property.month_item_info)
        for product_id in data['month_item_info']:
            if 'charge_date' in data['month_item_info'][product_id]:
                data['month_item_info'][product_id].pop('charge_date')
            if data['month_item_info'][product_id]['start_time']:
                data['month_item_info'][product_id]['start_time'] += ' 00:00:00'
            if data['month_item_info'][product_id]['end_time']:
                data['month_item_info'][product_id]['end_time'] += ' 00:00:00'
        #自动战斗开关,只对付费用户开启
        data['auto_fight_is_open'] = False
        #倒计时求将时间
        data['next_free_gacha_time'] = UserGacha.get_instance(self.uid).next_free_gacha_time

        #跑马灯信息，每隔10分钟返回一次
        data['marquee_info'] = self.marquee_info()
        #推送信息
        data['push_info'] = utils.get_push_info(self)
        data['push_open'] = self.game_config.system_config.get('push_open',False)
        #花费元宝重置次数
        data['recover_times'] = self.user_property.get_recover_times()
        return data

    def old_set_name(self,country):
        """设置初始用户名
        1:曹魏雄才
        2:蜀汉俊士
        3:东吴英杰
        """
        name = {
            '1':u'曹魏雄才',
            '2':u'蜀汉俊士',
            '3':u'东吴英杰',
        }
        self.baseinfo['username'] = name[country]
        self.put()

    def set_name(self,name):
        """设置初始用户名
        """
        if UserName.get(name):
            return False

        if 'npc' in name:
            return False

        try:
            UserName.set_name(self.uid, name)
        except:
            return False
        self.baseinfo['username'] = name
        self.put()
        return True

    def set_sex(self, sex):
        """设置初始用户名
        """

        self.baseinfo['sex'] = sex
        self.put()
        return True


    def rename(self,name):
        '''
        重命名
        '''
        self.baseinfo['username'] = name
        self.put()
        return True


    def froze(self):
        """冻结账户，前两次按时间，累计三次之后永久
        """
        msg = ''
        if self.in_frozen:
            return ''
        frozen_count = self.baseinfo.get('frozen_count',0)
        if frozen_count:
            self.baseinfo['frozen_count'] += 1
        else:
            self.baseinfo['frozen_count'] = 1
        #首次冻结2天，再次7天，3次永久
        now = datetime.datetime.now()
        if self.baseinfo['frozen_count'] == 1:
            frozen_days = 2
            self.baseinfo['unfroze_time'] = utils.datetime_toTimestamp(now + datetime.timedelta(days=frozen_days))
            msg = get_msg('login','frozen_time', self)
            msg = msg % (frozen_days,utils.timestamp_toString(self.baseinfo['unfroze_time'],'%m.%d %H:%M'),self.uid)
        elif self.baseinfo['frozen_count'] == 2:
            frozen_days = 7
            self.baseinfo['unfroze_time'] = utils.datetime_toTimestamp(now + datetime.timedelta(days=frozen_days))
            msg = get_msg('login','frozen_time', self)
            msg = msg % (frozen_days,utils.timestamp_toString(self.baseinfo['unfroze_time'],'%m.%d %H:%M'),self.uid)
        else:
            self.baseinfo['frozen'] = True
            self.baseinfo['username'] = u'(已冻结)' + self.baseinfo['username']
            msg = get_msg('login','frozen', self) % self.uid
        self.put()
        return msg

    def unfroze(self):
        """解冻
        """
        if self.in_frozen:
            if self.frozen:
                self.baseinfo['frozen'] = False
                if u'(已冻结)' in self.username:
                    self.baseinfo['username'] = self.username[5:]
            else:
                self.baseinfo['unfroze_time'] = None
            self.put()
        return

#    def add_client_macaddr(self, mac_addr):
#        #"""增加mac地址
#        #"""
#        if "client_macaddr" not in self.baseinfo:
#            self.baseinfo["client_macaddr"] = []
#        if mac_addr not in self.baseinfo["client_macaddr"]:
#            self.baseinfo["client_macaddr"].append(mac_addr)
#            self.put()
#    
#    def add_mktid(self, mktid):
#        #"""增加下载渠道标识
#        #"""
#        if "mktids" not in self.baseinfo:
#            self.baseinfo["mktids"] = []
#        if mktid not in self.baseinfo["mktids"]:
#            self.baseinfo["mktids"].append(mktid)
#            self.put()

    def set_signature(self,words):
        self.baseinfo['signature'] = words
        self.put()
        
    def update_user_from_fb(self,base_data):
        """ 更新用户平台数据"""
        if base_data.get('gender'):
            self.baseinfo["sex"] = 1 if base_data.get('gender').decode('utf-8') == u'male' else 0
        else:
            self.baseinfo["sex"] = 0
        self.baseinfo["platform"] = 'fb'
        self.baseinfo["openid"] = base_data.get('id')
        self.put()
        
    def update_user_from_360(self,res_dict):
        self.baseinfo["platform"] = '360'
        self.baseinfo["openid"] = str(res_dict.get('id'))
        self.put()


    def update_user_from_mi(self,res_dict):
        self.baseinfo["platform"] = 'mi'
        self.baseinfo["openid"] = str(res_dict.get('openid'))
        self.put()
    
    def update_user_from_91(self,openid):
        self.baseinfo["platform"] = '91'
        self.baseinfo["openid"] = str(openid)
        self.put()
    
    def update_user_from_pp(self,openid):
        self.baseinfo["platform"] = 'pp'
        self.baseinfo["openid"] = str(openid)
        self.put()

    def marquee_info(self):
        """获得跑马灯的信息, 每隔10分钟返回一次"""
        if time.time() - self.baseinfo.get('marquee_rtime', 1) >= 10 * 60:
        #if time.time() - self.baseinfo.get('marquee_rtime', time.time()) >= 10:
            user_marquee_obj = UserMarquee.get(self.subarea)
            dmarquee = user_marquee_obj.marquee_info
            mlen = len(dmarquee)
            self.baseinfo['marquee_rtime'] = time.time()
            self.put()
            return {'info': dmarquee, 'mlen': mlen } 
        else:
            return {'mlen': 0}

