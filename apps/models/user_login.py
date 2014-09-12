#!/usr/bin/env python
# encoding: utf-8
"""
filename:user_login.py
"""
import datetime,time
import copy

from apps.common import utils
from apps.models.user_base import UserBase
from apps.models.user_cards import UserCards
from apps.models.user_property import lv_top_model
from apps.models.user_gift import UserGift
from apps.models import GameModel

class UserLogin(GameModel):
    """
    用户Login信息
    """
    pk='uid'
    fields = ['uid','login_info']
    def __init__(self):
        """初始化用户Login信息

        Args:
            uid: 用户游戏ID
            data:用户Login信息
        """
        self.uid = None
        self.login_info = {}

    @classmethod
    def create(cls,uid):
        ul = cls()
        ul.uid = uid
        ul.login_info = {
                            'continuous_login_num':0,    # 连续Login的天数
                            'total_login_num':0,
                            'login_time':utils.datetime_toTimestamp(datetime.datetime.now()-datetime.timedelta(days=1)),   # 最后一次Login的时间
                            #'borrow_fids':[],#今天借别人卡的uid列表
                            'login_record':[],#登录记录
                            'send_weibo':0,
                            'send_weixin':0,
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
        #新手引导 直接跳过
        #obj.reset_newbie()

        return obj
    
    def reset_newbie(self):
        user = UserBase.get(self.uid)
        country = 1
        if user.user_property.newbie:
            user.user_property.set_country(str(country))
            user_card_obj = UserCards.get(user.uid)
            user_card_obj.init_cards(str(country))
            user.user_property.update_tutorial_step(10)
            #把主将设置为最高级
            leader_card_info = user_card_obj.cards[user_card_obj.leader_ucid]
            #leader_card_info['lv'] = Card.get(leader_card_info['cid']).max_lv
            user_card_obj.put()


    @classmethod
    def get(cls, uid):
        """ 获取一个当前的用户实例
        Args:
            uid: 用户游戏ID
        """
        obj = super(UserLogin,cls).get(uid)
#        if obj:
#            obj.refresh_daily_info()
        return obj
    
    @property
    def banquet_info(self):
        if 'banquet_info' not in self.login_info:
            self.login_info['banquet_info'] = {}
            self.put()
        return self.login_info.get('banquet_info',{})
    
    def refresh_daily_info(self):
        """
        每日根据当天日期，决定是否要刷新数据
        """
        today = utils.get_today_str()
        if today != self.login_info.get('today'):
            self.login_info['stamina_award'] = []
            self.login_info['today'] = today
            self.login_info['banquet_info']={}
            self.login_info['weibo_weixin_award']=[]
            self.put()
            
    def set_has_first_month_bonus(self):
        if not self.login_info.get('has_first_month_bonus',False):
            self.login_info['has_first_month_bonus']=True
            self.put()

    def login(self,params):
        """
        登录
        返回登录礼物的字符串
        """
        #获取用户的基本属性
        user_base_obj = UserBase.get(self.uid)
        #获取当天的字符串
        now = datetime.datetime.now()
        #获取注册时间
        add_date = utils.timestamp_toDatetime(user_base_obj.add_time).date()
        #获取双倍充值的时间
        charge_double_date = self.game_config.shop_config.get('charge_double_date','')
        data = {}
        #获取用户属性对象
        user_property_obj = user_base_obj.user_property

        if not user_property_obj.newbie and now.date() != utils.timestamp_toDatetime(self.login_info['login_time']).date():
            #领取体力的函数  以前是10-12点  12-13：30领取  现在改为美味大餐
            # if str(add_date) != str(now.date()):
            #     #
            #     self.refresh_daily_info()
            #     from apps.views.main import get_stamina_award
            #     get_stamina_award(userbase_obj,True)
            #记录用户自注册以来的登陆总天数
            self.login_info['total_login_num'] += 1
            #记录登陆的所有日期
            if self.login_info.get('login_record') is None:
                self.login_info['login_record'] = []
            self.login_info['login_record'].insert(0,str(now.date()))
            #获取最大的记录长度
            if len(self.login_info['login_record']) > self.game_config.system_config.get('login_record_length',30):
                self.login_info['login_record'].pop()
            #连续登录
            if now.date() == (utils.timestamp_toDatetime(self.login_info['login_time']) + datetime.timedelta(days=1)).date():
                self.login_info['continuous_login_num'] += 1
            #非连续登录
            else:
                self.login_info['continuous_login_num'] = 1
            #每日的借卡记录重置
            #self.login_info['borrow_fids'] = []
            
            #每日登录奖励
            data.update(self.get_daily_login_award())

            #判断有无系统奖励
            data.update(self.get_system_bonus())

            #临时的一个系统补偿
            data.update(self.get_system_compensates())
            
            #临时补偿
            data.update(self.get_temp_bonus())

            #发送微博数量重置
            self.login_info['send_weibo'] = 0
            self.login_info['send_weixin'] = 0
            #特定日期首次充值双倍再开放
            if not user_property_obj.double_charge and\
             str(add_date) != str(now.date()) and\
             str(now.date()) == charge_double_date:
                user_property_obj.property_info['double_charge'] = True

            #特定日期之后已充值过的用户首次充值双倍关闭
            if user_property_obj.double_charge and charge_double_date and \
            str(now.date()) > charge_double_date:
                user_property_obj.property_info['double_charge'] = False
            
            user_gift_obj = UserGift.get_instance(self.uid)
            if str(add_date) != str(now.date()):
                self.get_month_bonus_record(user_property_obj)
                self.get_continuous_login_award_record(str(self.login_info['continuous_login_num']))
                self.get_login_award_record(str(self.login_info['total_login_num']))
                self.get_upgrade_award_record(user_property_obj)
                self.set_has_first_month_bonus()
            else:
                #月份的累计登陆奖励
                #data.update(self.get_month_bonus(user_property_obj,version))
                #连续登录奖励
                continuous_award = self.get_continuous_login_award(str(self.login_info['continuous_login_num']))
                if continuous_award:
                    data['continuous'] = {
                        'days':self.login_info['continuous_login_num'],
                        'award':continuous_award,
                    }
                #累积登录奖励
                login_award = self.get_login_award(str(self.login_info['total_login_num']))
                if login_award:
                    data['total_login']={
                                    'days':self.login_info['total_login_num'],
                                    'award':login_award,
                                   }
                # 领取以前未领取的等级奖励
                user_gift_obj.get_lv_gift()
            # 领取绑定收集奖励
            user_gift_obj.get_bind_phone_gift()

            #月卡返还,当天注册的不返还
            if str(add_date) != str(now.date()):
                self.__refresh_month_card_info(user_property_obj)

        # 如果玩家没有成功通过新手引导- 战场1-1 则reset武将编队和物品编队以便继续新手引导
        if user_property_obj.property_info.get('newbie_steps', 0) == 15 and user_property_obj.newbie:
            user_property_obj.user_cards.reset_cards()
            user_property_obj.user_pack.clear_item_deck()

        if not user_property_obj.newbie:
            user_property_obj.property_info['login_time'] = int(time.time())
            #登录时间更新
            self.login_info['login_time'] = int(time.time())
            #版本更新奖励
            strVersion = params.get("version", "")
            if strVersion != "":
                update_version_award = self.get_update_version_bonus(strVersion)
                if update_version_award and strVersion not in user_property_obj.update_award:
                    data["update_version_award"] = {"award":update_version_award}
                    #user_property_obj.give_award(update_version_award)
                    user_property_obj.property_info["update_award"].append(strVersion)
            #判断有无绑定奖励
            if UserBase.get(self.uid).platform != 'oc' and \
            user_property_obj.property_info.get('bind_award'):
                data['bind_award'] = self.game_config.weibo_config['bind_award']
                user_property_obj.property_info['bind_award'] = False
        #将奖励放入礼包
        self.send_gift_award(data)
        self.popularize(user_property_obj)

        
        #当天注册用户判断是否有活动双倍
        if not self.login_info.get('set_newbie_double_charge',False) and\
         not user_property_obj.double_charge and\
         str(now.date()) == charge_double_date and\
         str(add_date) == str(now.date()):
            user_property_obj.property_info['double_charge'] = True
            self.login_info['set_newbie_double_charge'] = True
        #月份奖励
        if str(add_date) == str(now.date()) and not self.login_info.get('set_newbie_month_login_bonus',False):
            self.get_month_bonus_record(user_property_obj,1)
            self.get_continuous_login_award_record('1')
            self.get_login_award_record('1')
            self.login_info['set_newbie_month_login_bonus'] = True
            self.set_has_first_month_bonus()
        elif str(add_date) != str(now.date()) and \
        not self.login_info.get('has_first_month_bonus',False):
            self.get_month_bonus_record(user_property_obj)
            self.get_continuous_login_award_record(str(self.login_info['continuous_login_num']),today_has_got=True)
            self.get_login_award_record(str(self.login_info['total_login_num']),today_has_got=True)
            self.get_upgrade_award_record(user_property_obj)
            self.set_has_first_month_bonus()
        self.put()
        user_property_obj.put()

        #  若保底求将没开  清空保底求将元宝
        from apps.logics.gacha  import is_open_safty
        from apps.models.user_gacha import UserGacha
        if not is_open_safty():
            user_gacha_obj = UserGacha.get_instance(self.uid)
            user_gacha_obj.reset_cost_coin()
        
        return 'login_str'

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
            
    def send_gift_award(self,data):
        """
        奖励放礼包
        """
        user_gift_obj = UserGift.get_instance(self.uid)
        if 'continuous' in data:
            days = data['continuous']['days']
            award = data['continuous']['award']
            user_gift_obj.add_gift(award,utils.get_msg('login', 'continous_login_award', self) % days)
        if 'total_login' in data:
            days = data['total_login']['days']
            award = data['total_login']['award']
            user_gift_obj.add_gift(award,utils.get_msg('login', 'totoal_login_award', self) % days)
        if 'system' in data:
            content = data['system']['content']
            award = data['system']['award']
            user_gift_obj.add_gift(award,content)
        if 'compensates' in data:
            content = data['compensates']['content']
            award = data['compensates']['award']
            user_gift_obj.add_gift(award,content)
        if 'month_bonus' in data:
            content = data['month_bonus']['content']
            award = data['month_bonus']['award']
            user_gift_obj.add_gift(award,content)
        if 'bind_award' in data:
            content = utils.get_msg('user', 'bind_award', self)
            award = data['bind_award']
            user_gift_obj.add_gift(award,content)
        if 'update_version_award' in data:
            content = utils.get_msg('user', 'update_version_award', self)
            award = data['update_version_award']['award']
            user_gift_obj.add_gift(award,content)
        if 'daily_login' in data:
            content = data['daily_login']['content']
            award = data['daily_login']['award']
            user_gift_obj.add_gift(award,content)
        if 'temp_bonus' in data:
            content = data['temp_bonus']['content']
            award = data['temp_bonus']['award']
            user_gift_obj.add_gift(award,content)
        if 'month_daily_bonus' in data:
            for product_id in data['month_daily_bonus']:
                content = data['month_daily_bonus'][product_id]['content']
                award = data['month_daily_bonus'][product_id]['award']
                user_gift_obj.add_gift(award,content)
        if 'honor_award' in data:
            content = data['honor_award']['content']
            award = data['honor_award']['award']
            user_gift_obj.add_gift(award,content)
    
    def send_mails(self, awards):
        '''
        发得奖邮件
        '''
        if 'honor_award' in awards:
            content = awards['honor_award']['content']
            award = awards['honor_award']['award']
            sid = 'system_%s' % (utils.create_gen_id())
            user_mail = UserMail.hget(self.uid, sid)
            user_mail.set_awards_description(award)
            user_mail.set_mail(mailtype='system', content=content, award=award)

    def get_honor_award(self):
        data = {}
        user_real_pvp = UserRealPvp.get_instance(self.uid)
        r = user_real_pvp.yesterday_pvp_rank()   # 变量名r和配置里的一致.pk_config 'get_honor':'1400-4*(r-50)'
        rank_conf = user_real_pvp.get_pvp_rank_conf(r)
        if not rank_conf:
            return data
        get_honor = eval(str(rank_conf['get_honor']))
        # 时间处理
        now = datetime.datetime.now()
        now_date_str = now.strftime('%Y-%m-%d')
        next_refresh_time_str = '%s %s' % (now_date_str, '22:00:00')
        next_refresh_time = utils.string_toDatetime(next_refresh_time_str)
        last_refresh_time = next_refresh_time - datetime.timedelta(hours=24)
		
        next_refresh_timestamp = utils.datetime_toTimestamp(next_refresh_time)
        last_refresh_timestamp = utils.datetime_toTimestamp(last_refresh_time)
        now_timestamp = utils.datetime_toTimestamp(now)
        # 刷新时间并放入奖励
        if now_timestamp > user_real_pvp.pvp_info.get('last_refresh_time', last_refresh_timestamp):
            user_real_pvp.pvp_info['last_refresh_time'] = next_refresh_timestamp
            user_real_pvp.put()
            data['honor_award'] = {
                'content': u'功勋奖励',
                'award': {'honor': get_honor}
            }
        return data

    def popularize(self,user_property_obj):
        #运营活动，11.28 0:00~12.7 23:59:59 
        popularize_config = self.game_config.system_config.get('popularize')
        now_string = utils.datetime_toString(datetime.datetime.now())
        if popularize_config and popularize_config['start_time'] <= now_string and now_string <= popularize_config['end_time']:
            from apps.models.user_gift import UserGift
            user_gift_obj = UserGift.get_instance(self.uid)
            lv_rank = lv_top_model.rank(self.uid)
            if lv_rank == None:
                lv_top_model.set(self.uid,user_property_obj.lv)
                lv_rank = lv_top_model.rank(self.uid)
            lv_rank = lv_rank+1 if lv_rank != None else 0
            first_rank_user = lv_top_model.get(1)
            if first_rank_user:
                max_lv = int(first_rank_user[0][1])
                content = popularize_config['content'] % (lv_rank,max_lv)
                award = popularize_config['award']
                user_gift_obj.add_gift(award,content)

    def get_login_award(self,login_days):
        """
        """
        conf = self.game_config.loginbonus_config
        if login_days in conf['bonus']:
            return conf['bonus'][login_days]
        else:
            return {}
    
    @property
    def login_bonus_record(self):
        if 'login_bonus_record' not in self.login_info:
            self.login_info['login_bonus_record'] = {}
        return self.login_info['login_bonus_record'] 
    
    def get_login_award_record(self,login_days,today_has_got = False):
        """月份奖励-累积
        """
        bonus = copy.deepcopy(self.game_config.loginbonus_config['bonus'])
        for days in sorted([int(i) for i in bonus]):
            if days < int(login_days):
                continue
            days_str = str(days)
            if days_str in self.login_bonus_record:
                self.login_bonus_record[days_str]['login_days'] = login_days
                continue
            if days == int(login_days):
                self.login_bonus_record[days_str] = {}
                self.login_bonus_record[days_str]['award'] = bonus[days_str]
                self.login_bonus_record[days_str]['has_got'] = today_has_got
                self.login_bonus_record[days_str]['login_days'] = login_days
                self.login_bonus_record[days_str]['content'] = utils.get_msg('login','totoal_login_award', self) % str(days)
            if days > int(login_days):
                self.login_bonus_record[days_str] = {}
                self.login_bonus_record[days_str]['award'] = bonus[days_str]
                self.login_bonus_record[days_str]['has_got'] = False
                self.login_bonus_record[days_str]['login_days'] = login_days
                self.login_bonus_record[days_str]['content'] = utils.get_msg('login','totoal_login_award', self) % str(days)
                break
        self.put()

    def get_continuous_login_award(self,continuous_days):
        """
        获取连续登录的奖励
        输入 连续登录的天数
        输出 奖励内容
        """
        conf = self.game_config.loginbonus_config
        if continuous_days in conf['continuous_bonus']:
            #配置如果有的话直接去取配置里面的内容
            return conf['continuous_bonus'][continuous_days]
        else:
            #如果配置没有配的话就去取配置里面最大天数的那个奖励
            max_days = str(max([int(i) for i in conf['continuous_bonus']]))
            return conf['continuous_bonus'][max_days]

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
    def month_bonus_record(self):
        #每月的领取内容 登录的时候领取的内容
        if 'month_bonus_record' not in self.login_info:
            self.login_info['month_bonus_record'] = {}
        return self.login_info['month_bonus_record'] 
    
    def get_month_bonus_record(self,user_property_obj,month_total_login=None):
        """
        月份奖励-月份 一个月30天  30天每天的奖励
        """
        now = datetime.datetime.now()
        month_bonus_config = copy.deepcopy(self.game_config.loginbonus_config.get('month_bonus',{}))
        year_month = now.strftime('%Y-%m')
        now_month = str(int(now.strftime('%m')))
        is_put = False 
        if year_month not in self.month_bonus_record:
            self.login_info['month_bonus_record'][year_month] = {}
            is_put = True
        #当月总登录天数
        if not month_total_login:
            month_total_login = 0
            if True:#month_bonus_config.has_key(now_month):
                #计算当月累计登陆几天了
                for i in range(len(self.login_info['login_record'])):
                    if self.login_info['login_record'][i][:7] == year_month:
                        month_total_login += 1
                    else:
                        break
        cur_login = min(month_total_login,25)
        month_detail_bonus = month_bonus_config.get(now_month, {})
        self.month_bonus_record[year_month]['cur_login'] = cur_login
        if 'list' not in self.month_bonus_record[year_month]:
            self.month_bonus_record[year_month]['list'] = {}
            is_put = True
        for k in month_detail_bonus:
            if k not in self.month_bonus_record[year_month]['list'] or\
            not self.month_bonus_record[year_month]['list'][k]['has_got']:
                self.month_bonus_record[year_month]['list'][k] = {}
                self.month_bonus_record[year_month]['list'][k]['has_got'] = False
                self.month_bonus_record[year_month]['list'][k]['award'] = month_detail_bonus[k]
                is_put = True
            #发奖励
            if int(k) <= cur_login and not self.month_bonus_record[year_month]['list'][k]['has_got']:
                user_property_obj.give_award(month_detail_bonus[k],where='month_bonus')
                self.month_bonus_record[year_month]['list'][k]['has_got'] = True
                is_put = True
        if is_put is True:
            self.put()
    
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
            
    def get_continuous_login_award_record(self,continuous_days,today_has_got=False):
        """月份奖励-签到
        """
        continuous_bonus = copy.deepcopy(self.game_config.loginbonus_config['continuous_bonus'])
        if continuous_days in continuous_bonus:
            continuous_award = continuous_bonus[continuous_days]
        else:
            max_days = str(max([int(i) for i in continuous_bonus]))
            continuous_award =  continuous_bonus[max_days]
        now = datetime.datetime.now()
        #已经有这一天的就返回
        if str(now.date()) in self.continuous_bonus_record:
            return
        self.continuous_bonus_record[str(now.date())] = {
                                            'days':continuous_days,
                                            'award':continuous_award,
                                            'has_got':today_has_got,
                                            'content':utils.get_msg('login','continous_login_award', self) % continuous_days
                                            }

        #记录明天他可以领什么奖励
        tomorrow_days = int(continuous_days) + 1
        if str(tomorrow_days) in continuous_bonus:
            tomorrow_bonus = continuous_bonus[str(tomorrow_days)]
        else:
            max_days = str(max([int(i) for i in continuous_bonus]))
            tomorrow_bonus =  continuous_bonus[max_days]
        tomorrow_date = now + datetime.timedelta(days = 1)
        self.login_info['continuous_tomorrow_bonus'] = {
                                            'date':str(tomorrow_date.date()),
                                            'days':str(tomorrow_days),
                                            'award':tomorrow_bonus,
                                            'has_got':False,
                                            'content':utils.get_msg('login','continous_login_award', self) % str(tomorrow_days)
                                            }
        self.put()
    
    @property
    def upgrade_bonus_record(self):
        if 'upgrade_bonus_record' not in self.login_info:
            self.login_info['upgrade_bonus_record'] = {}
        return self.login_info['upgrade_bonus_record'] 
    
    def get_upgrade_award_record(self,user_property_obj):
        """刷新升级奖励的情况
        """
        first_upgrade = self.login_info.get('first_upgrade',False)
        upgrade_bonus_config = copy.deepcopy(self.game_config.operat_config.get('lv_up_award', {}))
        for lv in upgrade_bonus_config:
            if lv in self.upgrade_bonus_record:
                continue
            lv_award = upgrade_bonus_config[lv]
            self.upgrade_bonus_record[lv] = {}
            if not first_upgrade and int(lv) <= user_property_obj.lv:
                self.upgrade_bonus_record[lv]['has_got'] = True
            else:
                self.upgrade_bonus_record[lv]['has_got'] = False
            self.upgrade_bonus_record[lv]['award'] = lv_award
            self.upgrade_bonus_record[lv]['content'] = utils.get_msg('user','lv_up_award', self) % int(lv)
        if not first_upgrade:
            self.login_info['first_upgrade'] = True
        self.put()
        
    def get_system_compensates(self):
        data = {}
        now = datetime.datetime.now()
        system_compensates_conf = copy.deepcopy(self.game_config.loginbonus_config.get('system_compensates',{}))
        #当天注册不给予补偿
        add_date = utils.timestamp_toDatetime(UserBase.get(self.uid).add_time).date()
        if str(add_date) != str(now.date()):
            if str(now.date()) in system_compensates_conf:#兼容旧配置
                data['compensates'] = {
                    'content':system_compensates_conf[str(now.date())].pop('content'),
                    'award':system_compensates_conf[str(now.date())]
                }
            else:#新配置支持区间奖励
                for k in system_compensates_conf:
                    if isinstance(k,(list,tuple))==False:
                        continue

                    login_count = 0#累积登录天数
                    if len(k)==2:
                        date_start = k[0]
                        date_end = k[1]
                        today_time = str(now.date())
                        if  today_time < date_start or today_time > date_end:
                            continue
                        #计算活动区间累积登录天数
                        lg_record = self.login_info.get('login_record',[])
                        login_count = len([x for x in lg_record if date_start<=x<=date_end])

                    if str(login_count) in system_compensates_conf[k]:
                        data['compensates'] = {
                            'content':system_compensates_conf[k][str(login_count)].pop('content'),
                            'award':system_compensates_conf[k][str(login_count)]
                        }
                        break
        return data
    
    def get_temp_bonus(self):
        """
        临时补偿，分安卓和ios
        """
        data = {}
        now = datetime.datetime.now()
        temp_bonus_conf = copy.deepcopy(self.game_config.loginbonus_config.get('temp_bonus',{}))
        #当天注册不给予补偿
        user_base_obj = UserBase.get(self.uid)
        add_date = utils.timestamp_toDatetime(user_base_obj.add_time).date()
        if str(add_date) != str(now.date()):
            for k in temp_bonus_conf:
                if isinstance(k,(list,tuple))==False:
                    continue
                if len(k)==2:
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
                        }
                    break
        return data
        
    def get_system_bonus(self):
        data = {}
        now = datetime.datetime.now()
        system_bonus_conf = copy.deepcopy(self.game_config.loginbonus_config.get('system_bonus',{}))
        if str(now.date()) in system_bonus_conf:#兼容旧配置
            data['system'] = {
                'content':system_bonus_conf[str(now.date())].pop('content'),
                'award':system_bonus_conf[str(now.date())]
            }
        else:#新配置支持区间奖励
            for k in system_bonus_conf:
                if isinstance(k,(list,tuple))==False:
                    continue

                login_count = 0#累积登录天数
                if len(k)==2:
                    date_start = k[0]
                    date_end = k[1]
                    today_time = str(now.date())
                    if  today_time < date_start or today_time > date_end:
                        continue
                    #计算活动区间累积登录天数
                    lg_record = self.login_info.get('login_record',[])
                    login_count = len([x for x in lg_record if date_start<=x<=date_end])

                if str(login_count) in system_bonus_conf[k]:
                    data['system'] = {
                        'content':system_bonus_conf[k][str(login_count)].pop('content'),
                        'award':system_bonus_conf[k][str(login_count)]
                    }
                    break
        return data
    
    def get_daily_login_award(self):
        data = {}
        now = datetime.datetime.now()
        daily_bonus_conf = copy.deepcopy(self.game_config.loginbonus_config.get('daily_bonus',{}))
        for k in daily_bonus_conf:
            if isinstance(k,(list,tuple))==False:
                continue
            if len(k)==2:
                date_start = k[0]
                date_end = k[1]
                today_time = str(now.date())
                if  date_start<=today_time<=date_end and daily_bonus_conf[k]:
                    data['daily_login'] = {
                        'content':daily_bonus_conf[k].pop('content'),
                        'award':daily_bonus_conf[k],
                    }
                    break
        return data
     
    # def get_daily_login_award(self):
    #     '''
    #     获取每日登陆的礼包
    #     '''
    #     data = {}
    #     #获取当前时间
    #     now = datetime.datetime.now()
    #     #获取每日登陆的配置
    #     daily_bonus_conf = copy.deepcopy(self.game_config.loginbonus_config.get('daily_bonus',{}))
    #     if daily_bonus_conf:
    #         #如果存在配置 就取配置 拂去领取时间范围
    #         start_time = daily_bonus_conf.get('start_time','2115-03-08')
    #         end_time = daily_bonus_conf.get('end_time','2115-03-08')
    #         today_time = str(now.date())
    #         award = daily_bonus_conf.get('award',{})
    #         if  date_start<=today_time<=date_end and award:
    #             #时间范围正确  并且奖励内容不为空的时候 格式化领取的内容
    #             format_award = utils.format_award(award)
    #             data['daily_login'] = {
    #                 'content':daily_bonus_conf.pop('desc'),
    #                 'award':format_award,
    #             }
    #     return data

    def set_borrow_user(self,fid):
        """写入被借卡人id
        """
        self.login_info['borrow_fids'].append(fid)
        self.put()

    def send_weibo(self):
        """
        发送微博记录
        """
        if 'send_weibo' in self.login_info:
            self.login_info['send_weibo'] += 1
        else:
            self.login_info['send_weibo'] = 1
        today_str = str(datetime.date.today())
        if 'weibo_record' not in self.login_info:
            self.login_info['weibo_record'] = {today_str:1}
        else:
            if today_str in self.login_info['weibo_record']:
                self.login_info['weibo_record'][today_str] += 1
            else:
                self.login_info['weibo_record'][today_str] = 1
            if len(self.login_info['weibo_record']) > 15:
                latest_key = min(self.login_info['weibo_record'].keys())
                self.login_info['weibo_record'].pop(latest_key)
        self.put()

    def send_weixin(self):
        """发微信记录
        """
        if 'send_weixin' in self.login_info:
            self.login_info['send_weixin'] += 1
        else:
            self.login_info['send_weixin'] = 1
        today_str = str(datetime.date.today())
        if 'weixin_record' not in self.login_info:
            self.login_info['weixin_record'] = {today_str:1}
        else:
            if today_str in self.login_info['weixin_record']:
                self.login_info['weixin_record'][today_str] += 1
            else:
                self.login_info['weixin_record'][today_str] = 1
            if len(self.login_info['weixin_record']) > 15:
                latest_key = min(self.login_info['weixin_record'].keys())
                self.login_info['weixin_record'].pop(latest_key)
        self.put()

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

