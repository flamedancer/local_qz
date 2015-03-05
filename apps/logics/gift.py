#-*- coding: utf-8 -*-
""" filename:gift.py
"""
import copy
from apps.common import utils
from apps.common import tools
from apps.models.user_gift import UserGift
from apps.models.user_login import UserLogin
from apps.config.game_config import game_config
from apps.models.user_property import UserProperty
from apps.models.user_equips import UserEquips
from apps.models.user_cards import UserCards
from apps.models.user_souls import UserSouls
from apps.models.user_pack import UserPack
from apps.models.user_task import UserTask
from apps.logics import vip
import datetime
import time

user_gift_record = {}

def new_gift_list(rk_user,params):
    '''
    获取该用户的可领取的礼包内容
    '''
    user_gift_obj = UserGift.get(rk_user.uid)
    data = {}
    data['new_gifts'] = user_gift_obj.new_gift_to_client(float(params['version']))
    data.update(UserLogin.get(rk_user.uid).get_award_info(rk_user.user_property))
    return 0,data


def get_gift(rk_user,params):
    gift_ids = params.get('gift_ids','')
    user_gift_obj = UserGift.get(rk_user.uid)
    if not gift_ids:
        return 11,{'msg':utils.get_msg('gift','invalid_gift')}
    if gift_ids == 'all':
        gift_ids_list = user_gift_obj.gift_list.keys()
    else:
        gift_ids_list = [ i for i in gift_ids.split('_') if i]
    award_return = {'stamina':0,'gold':0,'coin':0,'gacha_pt':0,'item':{}, 'material':{},'props':{},'card':{},'equip':{}, 'normal_soul': {},}
    for gift_id in gift_ids_list:
        tmp = user_gift_obj.get_gift(gift_id)
        for _k in tmp:
            if _k in ['gold','coin','gacha_pt','stamina']:
                award_return[_k] = award_return.get(_k,0) + tmp.get(_k,0)
            elif _k in ['item','material','props','normal_soul']:
                for __kk in tmp[_k]:
                    award_return[_k][__kk] = award_return[_k].get(__kk,0) + tmp[_k][__kk]
            elif _k in ['card','equip']:
                award_return[_k].update(tmp[_k])
    data = {i:award_return[i] for i in award_return if award_return[i]}
    return 0,{'get_info':data}

def __get_old_gift(rk_user,gift_ids,award_return):
    user_gift_obj = UserGift.get(rk_user.uid)
    if not gift_ids:
        return 11,utils.get_msg('gift','invalid_gift')
    if gift_ids == 'all':
        gift_ids_list = user_gift_obj.gift_list.keys()
    else:
        gift_ids_list = [ i for i in gift_ids.split('_') if i]
    for gift_id in gift_ids_list:
        tmp = user_gift_obj.get_gift(gift_id)
        __format_award(tmp,award_return)
    return 0,''

def __format_award(tmp,award_return):
    """
    格式化奖励,将tmp的奖励合入award_return
    """
    for _k in tmp:
        if _k in ['gold','coin','gacha_pt','stamina']:
            award_return[_k] = award_return.get(_k,0) + tmp.get(_k,0)
        elif _k in ['item','material','props','normal_soul']:
            for __kk in tmp[_k]:
                award_return[_k][__kk] = award_return[_k].get(__kk,0) + tmp[_k][__kk]
        elif _k in ['card','equip']:
            award_return[_k].update(tmp[_k])
                
def new_get_gift(rk_user,params):
    """
    新领奖接口
    params:
      type:
          login_bonus_record-累积登录
          continuous_bonus_record-连续登录
          upgrade_bonus_record-升级奖励
          old_gift-老奖励方式
      value: days,coin
             date,gold
             lv,card:171_card
             giftid
             all-全部收取
    """
    params_type = params.get('type','').strip()
    if params_type not in ['login_bonus_record','continuous_bonus_record','upgrade_bonus_record','old_gift']:
        return 11,{'msg':utils.get_msg('gift','gift_type_error')}
    params_value = params.get('value','')
    val_ls = params_value.split(',')
    k = val_ls[0].strip()
    if len(val_ls)>=2:
        v = val_ls[1].strip()
    award_return = {'stamina':0,'gold':0,'coin':0,'gacha_pt':0,'stone':0,'item':{}, 'super_soul': 0, 'material':{},'card':{},'equip':{}, 'normal_soul': {},}
    ul = UserLogin.get(rk_user.uid)
    if k != 'all':
        if params_type == 'old_gift':
            rc,msg = __get_old_gift(rk_user,k,award_return)
            if rc != 0:
                return rc,{'msg':msg}
            else:
                data = {i:award_return[i] for i in award_return if award_return[i]}
                return rc,{'get_info':data}
        bonus = ul.login_info.get(params_type,{})
        if not bonus or k not in bonus or bonus[k].get('has_got',False):
            return 11,{'msg':utils.get_msg('gift','gift_not_exist')}
        if params_type == 'login_bonus_record' and\
         (int(bonus[k]['login_days']) < int(k) or not bonus[k].get('award',{})):
            return 11,{'msg':utils.get_msg('gift','gift_not_exist')}
        if params_type == 'upgrade_bonus_record' and\
         (rk_user.user_property.lv < int(k) or not bonus[k].get('award',{})):
            return 11,{'msg':utils.get_msg('gift','gift_not_exist')}
        award = bonus[k]['award']
        v_ls = v.split(':')
        if len(v_ls)>=2:
            v1 = v_ls[0]
            v2 = v_ls[1]
        else:
            v1 = v_ls[0]
            v2 = ''
        if v1 not in award or (v2 and v2 not in award[v1]):
            return 11,{'msg':utils.get_msg('gift','gift_not_exist')}
        if not v2:
            tmp = rk_user.user_property.give_award({v1:award[v1]},where = params_type)
            __format_award(tmp,award_return)
            award.pop(v1)
        else:
            if isinstance(award[v1][v2],dict):
                award_copy = copy.deepcopy(award[v1][v2])
                tmp = rk_user.user_property.give_award({v1:{v2:award_copy}},where = params_type)
                __format_award(tmp,award_return)
                award[v1].pop(v2)
                if not award[v1]:
                    award.pop(v1)
            else:
                tmp = rk_user.user_property.give_award({v1:{v2:award[v1][v2]}},where = params_type)
                __format_award(tmp,award_return)
                award[v1].pop(v2)
                if not award[v1]:
                    award.pop(v1)
        if not award:
            bonus[k]['has_got'] = True
            bonus[k].pop('award')
    else:
        #一键领取
        if params_type == 'old_gift':
            __get_old_gift(rk_user,'all',award_return)
        else:
            bonus = ul.login_info.get(params_type,{})
            for k in bonus:
                if bonus[k].get('has_got',False) or not bonus[k].get('award',{}):
                    continue
                if params_type == 'login_bonus_record' and int(bonus[k]['login_days']) < int(k):
                    continue
                if params_type == 'upgrade_bonus_record' and rk_user.user_property.lv < int(k):
                    continue
                award = bonus[k]['award']
                tmp = rk_user.user_property.give_award(award,where = params_type)
                __format_award(tmp,award_return)
                bonus[k]['has_got'] = True
    ul.put()
    data = {i:award_return[i] for i in award_return if award_return[i]}
    return 0,{'get_info':data}


# def get_month_card_award(rk_user, params):
#         """
#         领取月卡元宝
#         """
#         card_type = params['type']
#         user_property_obj = rk_user.user_property

#         sale_conf = copy.deepcopy(game_config.shop_config).get('sale',{})
#         sale_conf.update(game_config.shop_config.get('new_sale',{}))
#         sale_conf.update(game_config.shop_config.get('google_sale',{}))

#         today = datetime.date.today()
#         today_str = utils.datetime_toString(today,'%Y-%m-%d')

#         this_month_item_info = user_property_obj.month_item_info.get(card_type)

#         item_info = {}
#         for item_id in sale_conf:
#             if card_type == item_id.split('.')[-1]:
#                 item_info = sale_conf[item_id]
#                 break
#         if not item_info or not item_info.get('daily_bonus',{}):
#             return 0, {}

#         start_time = this_month_item_info.get('start_time')
#         last_got_date = this_month_item_info.get('last_got_date')
#         end_time = this_month_item_info.get('end_time')

#         if this_month_item_info and this_month_item_info['can_get_today'] \
#         and today_str>last_got_date and today_str<=end_time:
#             card_award = {}

#             if card_type == "coin001":
#                 start_date = utils.string_toDatetime(start_time,'%Y-%m-%d') + datetime.timedelta(days=1)
#                 award_index = (utils.string_toDatetime(today_str,'%Y-%m-%d') - start_date).days % len(item_info['daily_bonus']['card'])
#                 card_award['card'] = item_info['daily_bonus']['card'][award_index]
#             else:
#                 card_award = item_info['daily_bonus']
#             user_property_obj.give_award(card_award, where='month_card_award {}'.format(card_type))
#             this_month_item_info['can_get_today'] = False
#             user_property_obj.month_item_info[card_type] = this_month_item_info
#             user_property_obj.put()
#             return 0, {}
#         return 11,{'msg': utils.get_msg('gift','gift_not_exist')}

# ----------------------------------- new version ⥥ -----------------------------------

def show_open_server_gift(rk_user, params):
    '''
    返回开服奖励的礼包
    '''
    ug = rk_user.user_gift
    ul = rk_user.user_login
    add_time = utils.timestamp_toDatetime(rk_user.add_time)
    now = datetime.datetime.now()
    today = utils.get_today_str()
    # 初始化
    if not ug.open_server_record['gifts']:
        # 'gifts'按领取天数记录奖励是否领取，比如登录过10天，但只领过一次，这时gifts记录的是['1']['has_got']=True ,其他为False
        # 因为每天只能领取一次，'date_info'用来按日期记录哪天是否已领过一次
        #ug.open_server_record = {'gifts': {}, 'date_info': {}}
        for day in range(1, 32):
            ug.open_server_record['gifts'].setdefault(str(day), {})['has_got'] = False
        ug.put()
    data = {'gifts': {}}
    # 账号注册已达45天（包括注册当天），或者全部领取了，则清空全部开服礼包
    if (now - add_time).days + 1 > 45 or ug.has_got_all_open_server_gifts():
        return 0, data
    awards = game_config.loginbonus_config['open_server_gift'].get('awards', {})
    
    for days, award in awards.items():
        data['gifts'].setdefault(days, {})['awards'] = award
        data['gifts'][days]['has_got'] = ug.open_server_record['gifts'][days]['has_got']
        # 给前端现实能否领取，不需存在model中

        if int(days) == ug.total_open_days+1 and not ug.open_server_record['date_info'].get(today, False):
            data['gifts'][days]['can_get'] = True
        else:
            data['gifts'][days]['can_get'] = False

    return 0, data


def get_open_server_gift(rk_user, params):
    '''
    领取开服礼包中的奖励
    参数
        params['day'] 第几次领
    '''
    day = params['day']
    ug = rk_user.user_gift
    ul = rk_user.user_login
    awards = game_config.loginbonus_config['open_server_gift'].get('awards', {})
    if day not in awards.keys():
        return 11, {'msg': utils.get_msg('gift', 'gift_not_exist')}
    the_gift = ug.open_server_record['gifts'][day]
    if the_gift['has_got']:
        return 11, {'msg': utils.get_msg('gift', 'gift_has_got')}
    # 一天只能领一次
    today = utils.get_today_str()
    if ug.open_server_record['date_info'].get(today, False):
        return 11, {'msg': utils.get_msg('gift', 'today_has_signed_in')}
    # 按顺序领取
    if int(day) != ug.total_open_days+1:
        return 11, {'msg': utils.get_msg('gift', 'signin_in_turn')}
    this_award = awards[day]
    data = tools.add_things(
        rk_user, 
        [{"_id": goods, "num": this_award[goods]} for goods in this_award if goods],
        where="open_server_gift"
    )
    
    the_gift['has_got'] = True
    # 因为每天只能领取一次，'date_info'用来按日期记录哪天是否已领过一次
    ug.open_server_record['date_info'][today] = True 
    ug.put()
    return 0, data


def show_sign_in_gift(rk_user, params):
    '''
    返回前端当月签到奖励信息
    '''
    now = datetime.datetime.now()
    month = str(now.month)
    today = str(now.day)
    conf = game_config.loginbonus_config['sign_in_bonus']
    awards = conf.get(month, conf[conf.keys()[0]]) # 容错处理，没配置当月的话取配置里的第一个

    if not awards:
        return 11, {'msg': utils.get_msg('gift', 'no_sign_in_gift')}
    data = {'gifts': {}}
    ug = rk_user.user_gift

    # 当月总登陆天数
    month_login_days = rk_user.user_login.month_total_login
    # 下一个月，签到信息重置
    if str(now.month) != str(ug.sign_month):
        for n in range(1, 32):
            ug.sign_in_record.setdefault(str(n), {})['has_got'] = False
            ug.sign_in_record[str(n)]['today_has_signed_in'] = False
        ug.sign_month = month
        ug.put()

    for day, award in awards.items():
        data['gifts'].setdefault(day, {})['awards'] = award
        data['gifts'][day]['has_got'] = ug.sign_in_record[day].setdefault('has_got', False)

        #  每天只能签到一次
        if int(day) == ug.total_sign_days+1 and not ug.sign_in_record[today].setdefault('today_has_signed_in', False):
            data['gifts'][day]['can_get'] = True
        else:
            data['gifts'][day]['can_get'] = False
    ug.put()

    data['total_sign_in_days'] = ug.total_sign_days
    data['month_login_days'] = month_login_days
    return 0, data


def get_sign_in_gift(rk_user, params):
    '''
    领取签到奖励
    params['day'] 代表第几次签到，如果当月已签到3次则day应该是4
    '''
    day = params['day']
    ug = rk_user.user_gift
    now = datetime.datetime.now()
    month = str(now.month)
    today = str(now.day)
    
    if ug.sign_in_record[day]['has_got']:
        return 11, {'msg': utils.get_msg('gift', 'gift_has_got')}
    # 一天只能领一次
    if ug.sign_in_record[today].get('today_has_signed_in', False):
        return 11, {'msg': utils.get_msg('gift', 'today_has_signed_in')}
    # 不能跳领，必须一天一个按顺序领
    if day != str(ug.total_sign_days + 1):
        return 11, {'msg': utils.get_msg('gift', 'signin_in_turn')}
    # 添加奖励
    conf = game_config.loginbonus_config['sign_in_bonus']
    award = conf.get(month, conf[conf.keys()[0]]).get(day, {})  # 容错处理，没配置当月的话取配置里的第一个

    data = tools.add_things(
        rk_user, 
        [{"_id": goods, "num": award[goods]} for goods in award if goods],
        where="sign_in_gift"
    )
    #  用来给前端显示是否已领取,这时sign_in_record的下一层字段代表签到天数
    ug.sign_in_record[day]['has_got'] = True
    #  每天只能签到一次，此字段用来后端判断当天是否已签到过，这时sign_in_record的下一层字段代表日期
    ug.sign_in_record[today]['today_has_signed_in'] = True
    ug.put()

    return 0, data
