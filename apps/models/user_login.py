# encoding: utf-8
"""
filename:user_login.py
"""
import datetime
import time
import copy

from apps.common import utils
from apps.models.user_base import UserBase
from apps.models.user_gift import UserGift
from apps.models import GameModel
from apps.models.user_mail import UserMail
from apps.models.user_real_pvp import UserRealPvp

class UserLogin(GameModel):
    """
    用户Login信息
    """
    pk = 'uid'
    fields = ['uid', 'login_info']
    def __init__(self):
        """初始化用户Login信息

        Args:
            uid: 用户游戏ID
            login_info:用户Login信息
        """
        self.uid = None
        self.login_info = {}

    @classmethod
    def create(cls,uid):
        ul = cls()
        ul.uid = uid
        ul.login_info = {
            'continuous_login_num': 0,    # 连续Login的天数
            'total_login_num': 0,
            'login_time': 0,   # 最后一次Login的时间戳
            'login_record': [],#登录记录  每天第一次登陆的日期
            'login_record_new': [],  # 记录每次登陆时间，与login_record不同
        }
        return ul

    @classmethod
    def get_instance(cls, uid):
        """ 获取一个当前的用户实例
        Args:
            uid: 用户游戏ID
        """
        obj = super(UserLogin,cls).get(uid)
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
        obj = super(UserLogin,cls).get(uid)
        return obj
    
    @property
    def total_login_num(self):
        return self.login_info['total_login_num']

    def login(self, params):
        """登录
        发送登录奖励邮件
        """
        user_base_obj = self.user_base
        user_property_obj = self.user_property
        game_config = self.game_config
        # 获取当天的字符串
        now = datetime.datetime.now()
        # 获取注册时间
        add_date = utils.timestamp_toDatetime(user_base_obj.add_time).date()
        # 获取双倍充值的时间
        # charge_double_date = game_config.shop_config.get('charge_double_date', '')
        mail_awards = {}
        
        now_str = utils.datetime_toString(now)
        self.login_info.setdefault('login_record_new', []).insert(0, now_str)
        if len(self.login_info['login_record_new']) > 5:
                self.login_info['login_record_new'].pop()
        last_login_time = self.login_info['login_time']
        # 新安装用户，或玩家每天首次登入
        if not last_login_time or now.date() != utils.timestamp_toDatetime(last_login_time).date():
            self.login_info['total_login_num'] += 1
            self.login_info['login_record'].insert(0, str(now.date()))
            # 获取最大的记录长度
            if len(self.login_info['login_record']) > game_config.system_config.get('login_record_length', 30):
                self.login_info['login_record'].pop()
            # 连续登录
            if now.date() == (utils.timestamp_toDatetime(last_login_time) + datetime.timedelta(days=1)).date():
                self.login_info['continuous_login_num'] += 1
            # 非连续登录
            else:
                self.login_info['continuous_login_num'] = 1
            
            # 每日登录奖励
            mail_awards.update(self.get_daily_login_award())

            # 判断有无系统奖励
            mail_awards.update(self.get_system_bonus())

            #临时的一个系统补偿
            mail_awards.update(self.get_system_compensates())
            
            #临时补偿
            mail_awards.update(self.get_temp_bonus())

            # # 特定日期首次充值双倍再开放
            # if not user_property_obj.double_charge and (
            # str(add_date) != str(now.date()) and
            # str(now.date()) == charge_double_date):
            #     user_property_obj.property_info['double_charge'] = True

            # # 特定日期之后已充值过的用户首次充值双倍关闭
            # if user_property_obj.double_charge and charge_double_date and (
            # str(now.date()) > charge_double_date):
            #     user_property_obj.property_info['double_charge'] = False
            
            user_gift_obj = UserGift.get_instance(self.uid)

            #连续登录奖励
            mail_awards.update(self.get_continuous_login_award())

            #累积登录奖励
            mail_awards.update(self.get_login_award())

            # 领取以前未领取的等级奖励
            user_gift_obj.get_lv_gift()

            # 月卡返还,当天注册的不返还
            if str(add_date) != str(now.date()):
                self.__refresh_month_card_info(user_property_obj)

            # 重置道具商店购买次数
            self.user_pack.reset_store_has_bought_cnt()

            # vip 玩家 每日奖励  通过邮件发放
            mail_awards.update(self.get_vip_daily_bonus())

        # 如果玩家没有成功通过新手引导- 战场1-1 则reset武将编队以便继续新手引导
        if user_property_obj.property_info.get('newbie_steps', 0) == 15 and user_property_obj.newbie:
            user_property_obj.user_cards.reset_cards()

        rtn_data = {}

        user_property_obj.property_info['login_time'] = int(time.time())

        #版本更新奖励
        strVersion = params.get("version", "")
        if last_login_time and strVersion != "":
            update_version_award = self.get_update_version_bonus(strVersion)
            if update_version_award and strVersion not in user_property_obj.update_award:
                mail_awards["update_version_award"] = {"award":update_version_award}
                #user_property_obj.give_award(update_version_award)
                user_property_obj.property_info["update_award"].append(strVersion)
        #判断有无绑定奖励
        if UserBase.get(self.uid).platform != 'oc' and \
        user_property_obj.property_info.get('bind_award'):
            mail_awards['bind_award'] = self.game_config.weibo_config['bind_award']
            user_property_obj.property_info['bind_award'] = False
            
        rtn_data = self.new_login_bonus(now, user_property_obj)

        # 根据上一次22:00的pvp排名给予相应的功勋奖励
        mail_awards.update(self.get_honor_award())
        # 发得奖邮件
        self.send_mails(mail_awards)
        
        #当天注册用户判断是否有活动双倍
        # if not self.login_info.get('set_newbie_double_charge',False) and\
        #  not user_property_obj.double_charge and\
        #  str(now.date()) == charge_double_date and\
        #  str(add_date) == str(now.date()):
        #     user_property_obj.property_info['double_charge'] = True
        #     self.login_info['set_newbie_double_charge'] = True

        #  若保底求将没开  清空保底求将元宝
        from apps.logics.gacha import is_open_safty
        self.user_gacha.reset_cost_coin()
        if not is_open_safty():
            self.user_gacha.reset_cost_coin()

        # 登录时间更新
        self.login_info['login_time'] = int(time.time())

        self.put()
        user_property_obj.put()
        
        return rtn_data

    def new_login_bonus(self, now, user_property):
        '''
        新版本-登录收益
        '''
        data = {}
        # login_record_new sample  [u'2014-11-21 16:42:04', u'2014-11-21 10:40:22', u'2014-11-19 15:40:22']
        if len(self.login_info['login_record_new']) <= 1:
            return data
        last_login_time = utils.string_toDatetime(self.login_info['login_record_new'][1])
        delta = now - last_login_time
        
        conf = self.game_config.user_level_config[str(user_property.lv)]['outline_permin_award']
        minutes = min(delta.days*1440 + delta.seconds/60, 1440)
        gold = int(round(conf['gold'] * minutes))
        exp_point = int(round(conf['card_exp_point'] * minutes))
        user_property.add_gold(gold)
        user_property.add_card_exp_point(exp_point)
        data['gold'] = gold
        data['exp_point'] = exp_point
        # 离线的分钟和小时
        data['mm'] = delta.seconds % 3600 / 60
        data['hh'] = delta.days * 24 + delta.seconds / 3600
        return data

    def __refresh_month_card_info(self,user_property_obj):
        """
        刷新 月卡信息
        """
        today = datetime.date.today()

        month_item_info = user_property_obj.month_item_info

        for product_id in month_item_info:
            #月卡标志重新判断
            charge_date = month_item_info[product_id]['charge_date']
            if charge_date and not month_item_info[product_id]['can_buy']:
                last_charge_month = utils.string_toDatetime(charge_date[0],'%Y-%m-%d').month
                if today.month != last_charge_month:
                    month_item_info[product_id]['can_buy'] = True
        user_property_obj.put()

    def __get_month_daily_coin(self,user_property_obj):
        """
        领取月卡元宝
        """
        #检查本月是否可以购买月卡
        today = datetime.date.today()
        today_str = utils.datetime_toString(today,'%Y-%m-%d')
        data = {'month_daily_bonus':{}}
        month_item_info = user_property_obj.month_item_info
        pt_fg = False
        shop_config = copy.deepcopy(self.game_config.shop_config)
        sale_conf = shop_config.get('sale',{})
        sale_conf.update(shop_config.get('new_sale',{}))
        sale_conf.update(shop_config.get('google_sale',{}))
        # month_item_is_open = shop_config.get('month_item_is_open',False)
        # month_card_award = utils.get_msg('operat', 'month_card_award', self)
        for product_id in month_item_info:
            
            start_time = month_item_info[product_id]['start_time']
            end_time = month_item_info[product_id]['end_time']
            if start_time and end_time and today_str>=start_time and today_str<=end_time:
                month_item_info[product_id]['can_get_today'] = True

            #月卡标志重新判断
            charge_date = month_item_info[product_id]['charge_date']
            if charge_date and not month_item_info[product_id]['can_buy']:
                last_charge_month = utils.string_toDatetime(charge_date[0],'%Y-%m-%d').month
                if today.month != last_charge_month:
                    month_item_info[product_id]['can_buy'] = True
                    pt_fg = True
        if pt_fg:
            user_property_obj.put()
        if not data['month_daily_bonus']:
            data.pop('month_daily_bonus')
        return data
            
    def send_mails(self, awards):
        """将奖励于邮件形式发送"""
        for award_type, award_info in awards.items():
            title = award_info.get('title', '')
            content = award_info.get('content', '')
            award = award_info.get('award', {})
            sid = 'system_%s' % (utils.create_gen_id())
            user_mail = UserMail.hget(self.uid, sid)
            user_mail.set_mail(mailtype=award_type, title=title, content=content, award=award)

    def get_honor_award(self):
        data = {}
        user_real_pvp = UserRealPvp.get_instance(self.uid)
        r = user_real_pvp.yesterday_pvp_rank()   # 变量名r和配置里的一致.pk_config 'get_honor':'1400-4*(r-50)'
        rank_conf = user_real_pvp.get_pvp_rank_conf(r)
        if not rank_conf:
            return data
        get_honor = eval(str(rank_conf['get_honor']))
        now = datetime.datetime.now()
        now_timestamp = utils.datetime_toTimestamp(now)
        # 能够得到功勋奖励,刷新时间并放入奖励
        if now_timestamp > user_real_pvp.pvp_info.get('next_refresh_time', 0):
            now_date = now.strftime('%Y-%m-%d')
            now_time = now.strftime('%H:%M:%S')
            tomorrow_now = now + datetime.timedelta(days=1)
            tomorrow_date = tomorrow_now.strftime('%Y-%m-%d')
            refresh_time = self.game_config.pk_store_config.get('auto_refresh_time', '22:00:00')
            if now_time > refresh_time:
                next_refresh_time_str = '%s %s' % (tomorrow_date, refresh_time)
            else:
                next_refresh_time_str = '%s %s' % (now_date, refresh_time)
            next_refresh_time = utils.string_toTimestamp(next_refresh_time_str)
            user_real_pvp.pvp_info['next_refresh_time'] = next_refresh_time
            user_real_pvp.put()
            data['honor_award'] = {
                'title': u'pvp奖励',
                'content': u'功勋奖励',
                'award': {'honor': get_honor}
            }
        return data

    def get_login_award(self):
        """累积登入天数奖励"""
        login_days = str(self.login_info['total_login_num'])
        conf = self.game_config.loginbonus_config['bonus']

        title = conf.get('title', '')
        content = conf.get('content', '') % login_days
        data = {
            'total_login' : {
                'title': title,
                'content': content,
                'award': {},
            }
        }
        if login_days in conf['awards']:
            data['total_login']['award'] = conf['awards'][login_days]
            return data
        else:
            return {}
    
    @property
    def login_bonus_record(self):
        if 'login_bonus_record' not in self.login_info:
            self.login_info['login_bonus_record'] = {}
        return self.login_info['login_bonus_record'] 
    
    def get_continuous_login_award(self):
        """
            获取连续登录的奖励
            输入 连续登录的天数
            输出 奖励内容
        """
        # continuous_award = self.get_continuous_login_award(str(self.login_info['continuous_login_num']))
        # if continuous_award:
        #     award_info['continuous'] = {
        #         'days':self.login_info['continuous_login_num'],
        #         'award':continuous_award,
        #     }
        continuous_days = str(self.login_info['continuous_login_num'])
        conf = self.game_config.loginbonus_config['continuous_bonus']

        title = conf.get('title', '')
        content = conf.get('content', '') % continuous_days

        data = {
            'continuous' : {
                'title': title,
                'content': content,
                'award': {},
            }
        }
        if continuous_days in conf['awards']:
            #配置如果有的话直接去取配置里面的内容
            award = conf['awards'][continuous_days]
        else:
            #如果配置没有配的话就去取配置里面最大天数的那个奖励
            max_days = str(max([int(i) for i in conf['awards']]))
            award = conf['awards'][max_days]
        data['continuous']['award'] = award
        return data

    def get_update_version_bonus(self, version):
        #"""获得版本更新奖励
        #"""
        conf = self.game_config.loginbonus_config
        updae_version_bonus = conf.get("update_vesion_bonus", {})
        if version not in updae_version_bonus:
            return {}
        else:
            return updae_version_bonus[version]
    
#    def get_month_bonus(self,user_property_obj,version):
#        now = datetime.datetime.now()
#        year_month = now.strftime('%Y-%m')
#        now_month = str(int(now.strftime('%m')))
#        month_bonus = copy.deepcopy(self.game_config.loginbonus_config.get('month_bonus',{}))
#        data = {}
#        if month_bonus.has_key(now_month):
#            #计算当月累计登陆几天了
#            month_total_login = 0
#
#            for i in range(len(self.login_info['login_record'])):
#                if self.login_info['login_record'][i][:7] == year_month:
#                    month_total_login += 1
#                else:
#                    break
#            if month_bonus[now_month].has_key(str(month_total_login)):
#                data['month_bonus'] = {'content':month_bonus[now_month][str(month_total_login)].pop('content'),
#                                           'award': month_bonus[now_month][str(month_total_login)]}
#        return data
    
    @property
    def continuous_bonus_record(self):
        if 'continuous_bonus_record' not in self.login_info:
            self.login_info['continuous_bonus_record'] = {}
        return self.login_info['continuous_bonus_record'] 
    
    @property
    def continuous_tomorrow_bonus(self):
        if 'continuous_tomorrow_bonus' not in self.login_info:
            self.login_info['continuous_tomorrow_bonus'] = {}
        return self.login_info['continuous_tomorrow_bonus']
    
    @property
    def upgrade_bonus_record(self):
        if 'upgrade_bonus_record' not in self.login_info:
            self.login_info['upgrade_bonus_record'] = {}
        return self.login_info['upgrade_bonus_record'] 
    
    def get_system_compensates(self):
        data = {}
        now = datetime.datetime.now()
        system_compensates_conf = self.game_config.loginbonus_config.get('system_compensates', {})
        title = system_compensates_conf.get('title', '')
        # 当天注册不给予补偿
        add_date = utils.timestamp_toDatetime(self.user_base.add_time).date()
        if str(add_date) != str(now.date()):
            if str(now.date()) in system_compensates_conf['awards']: # 兼容旧配置
                data['compensates'] = {
                    'content':system_compensates_conf[str(now.date())].get('content', ''),
                    'award':system_compensates_conf[str(now.date())],
                    'title': title,
                }
            else:#新配置支持区间奖励
                for k in system_compensates_conf['awards']:
                    if not isinstance(k, (list, tuple)):
                        continue
                    login_count = 0 # 累积登录天数
                    if len(k) == 2:
                        date_start = k[0]
                        date_end = k[1]
                        today_time = str(now.date())
                        if  today_time < date_start or today_time > date_end:
                            continue
                        # 计算活动区间累积登录天数
                        lg_record = self.login_info.get('login_record',[])
                        login_count = len([x for x in lg_record if date_start <= x <= date_end])

                    if str(login_count) in system_compensates_conf[k]:
                        data['compensates'] = {
                            'content':system_compensates_conf[k][str(login_count)].get('content', ''),
                            'award':system_compensates_conf[k][str(login_count)],
                            'title': title,
                        }
                        break
        return data
    
    def get_temp_bonus(self):
        """
        临时补偿，分安卓和ios
        """
        data = {}
        now = datetime.datetime.now()
        temp_bonus_conf = self.game_config.loginbonus_config.get('temp_bonus', {})
        title = temp_bonus_conf.get('title', '')
        # 当天注册不给予补偿
        user_base_obj = self.user_base
        add_date = utils.timestamp_toDatetime(user_base_obj.add_time).date()
        if str(add_date) != str(now.date()):
            for k in temp_bonus_conf['awards']:
                if not isinstance(k, (list, tuple)):
                    continue
                if len(k) == 2:
                    date_start = k[0]
                    date_end = k[1]
                    today_time = str(now.date())
                    if  today_time < date_start or today_time > date_end:
                        continue
                    #ios
                    if not user_base_obj.client_type:
                        award = temp_bonus_conf[k].get('ios',{})
                    else:
                        award = temp_bonus_conf[k].get('android',{})
                    if award:
                        data['temp_bonus'] = {
                            'content':temp_bonus_conf[k].pop('content'),
                            'award':award,
                            'title': title,
                        }
                    break
        return data
        
    def get_system_bonus(self):
        data = {}
        now = datetime.datetime.now()
        system_bonus_conf = self.game_config.loginbonus_config.get('system_bonus', {})
        title = system_bonus_conf.get('title', '')

        for k in system_bonus_conf['awards']:
            if not isinstance(k, (list, tuple)):
                continue
            login_count = 0 #累积登录天数
            if len(k)==2:
                date_start = k[0]
                date_end = k[1]
                today_time = str(now.date())
                if  today_time < date_start or today_time > date_end:
                    continue
                #计算活动区间累积登录天数
                lg_record = self.login_info.get('login_record',[])
                login_count = len([x for x in lg_record if date_start <= x <=date_end])

            if str(login_count) in system_bonus_conf[k]:
                data['system'] = {
                    'title': title,
                    'content':system_bonus_conf[k][str(login_count)].get('content', ''),
                    'award':system_bonus_conf[k][str(login_count)]
                }
                break
        return data
    
    def get_daily_login_award(self):
        data = {}
        now = datetime.datetime.now()
        daily_bonus_conf = self.game_config.loginbonus_config.get('daily_bonus',{})
        for k in daily_bonus_conf:
            if not isinstance(k, (list, tuple)):
                continue
            if len(k) == 2:
                date_start = k[0]
                date_end = k[1]
                today_time = str(now.date())
                if  date_start <= today_time <= date_end and daily_bonus_conf[k]:
                    data['daily_login'] = {
                        'title': daily_bonus_conf[k].get('title', ''),
                        'content': daily_bonus_conf[k].get('content', ''),
                        'award': daily_bonus_conf[k]['awards'],
                    }
                    break
        return data

    def get_award_info(self,user_property_obj):
        """得到 月份奖励的信息返回给前端
        """
        data = {}
        data['month_bonus_record'] = copy.deepcopy(self.month_bonus_record)
        if data['month_bonus_record']:
            year_month_ls = sorted(data['month_bonus_record'].keys())
            data['month_bonus_record'] = {year_month_ls[-1]:data['month_bonus_record'][year_month_ls[-1]]}
        data['continuous_tomorrow_bonus'] = copy.deepcopy(self.continuous_tomorrow_bonus)
        data['login_bonus_record'] = {}
        data['continuous_bonus_record'] = {}
        data['upgrade_bonus_record'] = {}
        #连续登录
        continuous_bonus_record = copy.deepcopy(self.continuous_bonus_record)
        for k in continuous_bonus_record:
            has_got = continuous_bonus_record[k]['has_got']
            if not has_got:
                data['continuous_bonus_record'][k] = continuous_bonus_record[k]
        #累积登录
        login_bonus_record = copy.deepcopy(self.login_bonus_record)
        for k in login_bonus_record:
            has_got = login_bonus_record[k]['has_got']
            if not has_got:
                data['login_bonus_record'][k] = login_bonus_record[k]
        #升级奖励
        upgrade_bonus_record = copy.deepcopy(self.upgrade_bonus_record)
        for k in sorted([int(i) for i in upgrade_bonus_record]):
            has_got = upgrade_bonus_record[str(k)]['has_got']
            if not has_got and k<=user_property_obj.lv:
                data['upgrade_bonus_record'][str(k)] = upgrade_bonus_record[str(k)]
            if k>user_property_obj.lv:
                data['upgrade_bonus_record'][str(k)] = upgrade_bonus_record[str(k)]
                break
        #格式转化方便前端
        for year_month in data['month_bonus_record']:
            if 'list' in data['month_bonus_record'][year_month]:
                for k in data['month_bonus_record'][year_month]['list']:
                    self.transform_award(data['month_bonus_record'][year_month]['list'][k]['award'])
        self.transform_award(data['continuous_tomorrow_bonus'].get('award',{}))
        for days in data['login_bonus_record']:
            self.transform_award(data['login_bonus_record'][days]['award'])
        for date_str in data['continuous_bonus_record']:
            self.transform_award(data['continuous_bonus_record'][date_str]['award'])
        for lv in data['upgrade_bonus_record']:
            self.transform_award(data['upgrade_bonus_record'][lv]['award'])
        return data
    
    def get_bonus_num(self,user_property_obj):
        """
        获取未领奖励总数
        """
        total_cnt = 0
        #连续登录
        continuous_bonus_record = self.continuous_bonus_record
        for k in continuous_bonus_record:
            if not continuous_bonus_record[k]['has_got']:
                total_cnt += len(continuous_bonus_record[k].get('award',{}).keys())
        #累积登录
        login_bonus_record = self.login_bonus_record
        for k in login_bonus_record:
            if not login_bonus_record[k]['has_got'] and\
             int(login_bonus_record[k]['login_days'])>=int(k):
                total_cnt += len(login_bonus_record[k].get('award',{}).keys())
        #升级奖励
        upgrade_bonus_record = self.upgrade_bonus_record
        for k in upgrade_bonus_record:
            has_got = upgrade_bonus_record[k]['has_got']
            if not has_got and int(k)<=user_property_obj.lv:
                total_cnt += len(upgrade_bonus_record[k].get('award',{}).keys())
        return total_cnt

    def transform_award(self,award):
        """
        奖励格式转化
        """
        for k,v in award.items():
            if isinstance(v,dict):
                for kk,vv in v.items():
                    if isinstance(vv,dict):
                        award[k][kk] = vv.get('num',1)

    def get_vip_daily_bonus(self):
        info = {}
        vip_lv = str(self.user_property.vip_cur_level)
        vip_daily_conf = self.game_config.loginbonus_config['vip_daily_bonus']
        if vip_lv not in vip_daily_conf['awards'] or not vip_daily_conf['awards'][vip_lv]:
            return info
        award = vip_daily_conf['awards'][vip_lv]
        info['vip_daily_bonus'] = {
            'title': vip_daily_conf.get('title', 'vip_daily_bonus'),
            'content': vip_daily_conf.get('content', 'vip_daily_bonus') % vip_lv,
            'award':award,
        }
        return info
