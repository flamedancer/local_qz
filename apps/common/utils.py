# encoding: utf-8

import urllib2
import datetime,time
import os
import random
import sys
import traceback
import string
from hashlib import md5
import copy
from django.conf import settings
from django.core.mail import send_mail
from apps.models.redis_tool import RedisTool
from apps.config.game_config import game_config
import sms_config
import socket

UUID_STR = 'fWv3wFvwSIJ0RuNthkCBeRXnfk5635kufiD5G84MCRcDydAmpD0zxE8QsPjGsAsI'
UPWD_STR = 'JpHot0lcJascWXF5lGP5YNTiKvEEf6RUfrCQI95R7QMIEJQej73CaWMNFgsrm0Ho'

def print_err():
    sys.stderr.write('=='*30+os.linesep)
    sys.stderr.write('err time: '+str(datetime.datetime.now())+os.linesep)
    sys.stderr.write('--'*30+os.linesep)
    traceback.print_exc(file=sys.stderr)
    sys.stderr.write('=='*30+os.linesep)

def debug_print(content):
    if settings.DEBUG:
        print content
        
def create_gen_id():
    """根据时间生成一个id """
    gen_id = str(datetime.datetime.now()).replace(' ', '').replace('-','').replace(':', '').replace('.', '')
    gen_id += str(random.randint(0,9))
    return gen_id


def get_msg(category_key, msg_key, user_model=None):
    """获取提示信息 """
    if user_model:
        global game_config
        game_config = user_model.game_config
    return game_config.msg_config.get(category_key,{}).get(msg_key,'')

def get_today_str():
    """取得今天的日期字符串"""
    return datetime.date.today().strftime('%Y-%m-%d')

#def utc_to_tz(utc_dt_str, utc_fmt='%Y-%m-%dT%H:%M:%SZ', tz=None):
#    """
#        将UTC时区的时间转换为当前时区的时间
#        当前时区取django settings.py 中设置的时区
#        如：在settings.py文件中的设置
#        TIME_ZONE = 'Asia/Tokyo'
#
#        PARAMS:
#            * utc_dt_str - utc时区时间，字符串类型。如：2010-01-14T07:00:20Z
#            * utc_fmt - utc时区时间格式。如：%Y-%m-%dT%H:%M:%SZ
#            * tz - 当前时区，如：Asia/Tokyo
#
#        RETURNS: tz_dt
#    """
#    if tz is None:
#        tz = os.environ['TZ']
#
#    utc_fmt_dt = datetime.datetime.strptime(utc_dt_str, utc_fmt)
#    utc_dt = datetime.datetime(utc_fmt_dt.year, utc_fmt_dt.month, utc_fmt_dt.day, utc_fmt_dt.hour, utc_fmt_dt.minute, utc_fmt_dt.second, tzinfo=pytz.utc)
#    tz_dt = utc_dt.astimezone(pytz.timezone(tz))
#
#    return tz_dt

def get_index_by_random(weight_list):
    """ 根据权重数组中设定的各权重值随机返回该权重数组的下标
        args:
            * weight_list - 权重数组

        returns: int 权重数组的下标
    """

    total_weight = 0
    weight_list_temp = []

    #计算总权重
    for weight in weight_list:
        total_weight = total_weight + weight
        weight_list_temp.append(total_weight)

    #在总权重数中产生随机数
    random_value = random.randint(1, total_weight)

    #根据产生的随机数判断权重数组的下标
    list_index = 0
    for weight_temp in weight_list_temp:
        if random_value <= weight_temp:
            break
        list_index = list_index + 1

    return list_index

def get_item_by_random(item_list, weight_list = []):
    """ 根据权重数组中设定的各权重值随机返回item列表中的item
        args:
            * item_list - item数组
            * weight_list - 权重数组

        returns: 随机指定的item
    """

    if ((item_list is None) or (len(item_list) == 0)):
        return None

    if ((weight_list is None) or (len(weight_list) == 0)):
        random_index = random.randint(0, len(item_list)-1)
    else:
        if (len(item_list) != len(weight_list)):
            return None
        else:
            random_index = get_index_by_random(weight_list)

    return item_list[random_index]

def get_item_by_random_simple(item_weight_list):
    """ 根据权重数组中设定的各权重值随机返回item列表中的item
        args:
            * item_weight_list - item,权重数组

        returns: 随机指定的item
    """

    if ((item_weight_list is None) or (len(item_weight_list) == 0)):
        return None

    item_list = []
    weight_list = []

    for item_weight in item_weight_list:
        item_list.append(item_weight[0])
        weight_list.append(item_weight[1])

    return get_item_by_random(item_list, weight_list)


def get_items_by_weight_dict(item_weight_dict, num):
    item_weight_list = []
    for item_dict in copy.deepcopy(item_weight_dict).values():
        if "weight" in item_dict:
            item_weight_list.append([item_dict, item_dict['weight']])
    return get_items_by_random_simple(item_weight_list, num)


def get_items_by_random_simple(item_weight_list, num):
    """ 根据权重数组中设定的各权重值随机指定个数item列表中的item 
        注： 个数不足返回全部！
        args:
            * item_weight_list - item,权重数组
            * num  返回个数

        returns: 随机的items  
    """
    selected_items = []
    item_weight_list_copy = copy.deepcopy(item_weight_list)

    all_items = [simple[0] for simple in item_weight_list_copy]

    if len(all_items) <= num:
        return all_items
    for cnt in range(0, num):
        item = get_item_by_random_simple(item_weight_list_copy)
        selected_items.append(item)
        pop_index = all_items.index(item)
        item_weight_list_copy.pop(pop_index)
        all_items.pop(pop_index)
    return selected_items

def get_items_by_random_simple_repeat(item_weight_list, num):
    """ 根据权重数组中设定的各权重值随机指定个数item列表中的item 
        注： 个数不足返回全部！
        args:
            * item_weight_list - item,权重数组
            * num  返回个数

        returns: 随机的items  
    """
    selected_items = []
    item_weight_list_copy = copy.deepcopy(item_weight_list)

    all_items = [simple[0] for simple in item_weight_list_copy]

    if len(all_items) <= num:
        return all_items
    for cnt in range(0, num):
        item = get_item_by_random_simple(item_weight_list_copy)
        selected_items.append(item)
    return selected_items
    

def get_item_by_random_simpleEx(item_weight_list):
    """ 根据权重数组中设定的各权重值随机返回item列表中的item
        args:
            * item_weight_list - item,权重数组('1','2',10)

        returns: 随机指定的item
    """

    if ((item_weight_list is None) or (len(item_weight_list) == 0)):
        return None

    item_list = []
    weight_list = []

    for item_weight in item_weight_list:
        item_list.append((item_weight[0],item_weight[1]))
        weight_list.append(item_weight[2])

    return get_item_by_random(item_list, weight_list)

def random_choice(alist, num):
    """ 随机从列表中选择指定数量的元素
    """
    if num <= 0:
        return []
    list_len = len(alist)
    key_len = list_len if list_len < num else num
    return random.sample(alist, key_len)

def is_happen_new(rate, unit=100):
    """根据概率判断事件是否发生
    args:
        rate:概率。可以为小数，也可以为整数。为整数时，总和为unit参数
        unit:当rate为整数时，表示总和
    return:
        bool,是否发生
    """
    happend = False
    if isinstance(rate, int):
        random_value = random.randint(1, unit)
        if rate >= random_value:
            happend = True
    elif isinstance(rate, float):
        random_value = random.random()
        if rate >= random_value:
            happend = True
    return happend

def is_happen(rate):
    """根据概率判断事件是否发生
    args:
        rate:概率。小数
    return:
        bool,是否发生
    """
    happend = False
    random_value = random.random()
    if float(rate) >= random_value:
        happend = True
    return happend

def cul_items_num(item_dict):
    """计算字典中项目的总个数
    Args:
        item_dict: dict 项目的字典，例：item_dict = {"aaa":12,"bbb":5,"ccc":8}
    return:
        int 字典中项目的总个数 items_num = 12+5+8 = 25
    """
    items_num = 0
    if item_dict is not None:
        for (k,v) in item_dict.items():
            items_num = items_num + v
    return items_num

def send_exception_mail(request):
    """ 发送异常信息的mail
    """
    error_msg = traceback.format_exc()
    #过滤掉无效充值error
    if error_msg.find('com.zeptolab.ctrbonus') >= 0:
        return
    msg = '=='*30+'\n'
    msg += 'err time: '+str(datetime.datetime.now())+'\n'
    msg += '--'*30+'\n'
    msg += error_msg +'\n'
    msg += '--'*30+'\n'
    msg += str(request)
    error_path = request.path
    error_ml = __get_admin_mail_list()
    send_mail('[%s]: Django Error (EXTERNAL IP):' % settings.EMAIL_TITLE+error_path, msg, 
        settings.EMAIL_ACCOUNT, error_ml, fail_silently=False,\
        auth_user=settings.EMAIL_ACCOUNT.split('@')[0],
        auth_password=settings.EMAIL_PASSWORD )

    if not settings.DEBUG:
        send_mobile_message()

def send_exception_mailEx():
    """ 发送异常信息的mail
    """
    msg = '=='*30+'\n'
    msg += 'err time: '+str(datetime.datetime.now())+'\n'
    msg += '--'*30+'\n'
    msg += traceback.format_exc() +'\n'
    msg += '--'*30+'\n'
    error_ml = __get_admin_mail_list()
    send_mail('[%s]: Django Error (EXTERNAL IP):' % settings.EMAIL_TITLE+'fatal error', msg, 
        settings.EMAIL_ACCOUNT, error_ml, fail_silently=False,\
        auth_user=settings.EMAIL_ACCOUNT.split('@')[0],
        auth_password=settings.EMAIL_PASSWORD )

    if not settings.DEBUG:
        send_mobile_message()
    
def send_mobile_message():
    #"""发送手机短信
    #"""
    try:
        if sms_config.SEND_MOBILE_MESSAGE is False:
            return 
        error_msg = traceback.format_exc()
        if error_msg.find('com.zeptolab.ctrbonus') >= 0:
            return
        if error_msg.find('IndexError') < 0 and \
         error_msg.find('KeyError') < 0 and \
         error_msg.find('Mongo') < 0 and \
         error_msg.find('mongo') < 0 and \
         error_msg.find('redis') < 0 and \
         error_msg.find('Redis') < 0 and \
         error_msg.find('AttributeError') < 0:
            return
        last_time = RedisTool.get(settings.CACHE_PRE+'mobile_time', None)
        error_num = RedisTool.get(settings.CACHE_PRE+'mobile_error_num', 0)
        error_time = RedisTool.get(settings.CACHE_PRE+'mobile_error_time', None)
        now = int(time.time())
        if error_time is None:
            error_num = 0
            RedisTool.set(settings.CACHE_PRE+'mobile_error_time', now, 0)
        else:
            total_second = now - error_time
            if total_second > 65:
                error_num = 0
                RedisTool.set(settings.CACHE_PRE+'mobile_error_time', now, 0)
                return
        #错误15条以上才开始发
        error_num += 1
        if error_num < 30:
            RedisTool.set(settings.CACHE_PRE+'mobile_error_num', error_num, 0) 
            return  
        if last_time is not None:
            total_second = now - last_time
            if total_second < 60 * 3:
                return 

        urllib2.urlopen(sms_config.MOBILE_URL + socket.gethostname(), 
                timeout=12)
        RedisTool.set(settings.CACHE_PRE+'mobile_time', now, 0) 
        RedisTool.set(settings.CACHE_PRE+'mobile_error_num', 0, 0)
        RedisTool.set(settings.CACHE_PRE+'mobile_error_time', now, 0)
    except:
        print 'send_mobile_message error'
        print_err()
    
def send_middlewares_exception_mail(request, exception_info):
    """ 发送异常信息的mail
    """
    msg = '=='*30+'\n'
    msg += 'err time: '+str(datetime.datetime.now())+'\n'
    msg += 'exception_info: ' + exception_info + '\n'
    msg += '--'*30+'\n'
    msg += traceback.format_exc() +'\n'
    msg += '--'*30+'\n'
    msg += str(request)
    error_path = request.path
    error_ml = __get_admin_mail_list()
    send_mail('[MiddleWares %s]: Django MiddleWares Error (EXTERNAL IP):' % settings.EMAIL_TITLE+error_path, msg,
        settings.EMAIL_ACCOUNT, error_ml, fail_silently=False,\
        auth_user=settings.EMAIL_ACCOUNT.split('@')[0],
        auth_password=settings.EMAIL_PASSWORD )

def __get_admin_mail_list():
    mail_list = [a[1] for a in settings.ADMINS]
    return mail_list

def get_uuid():
    """生成一个唯一的用户id
    """
    return md5(create_gen_id() + UUID_STR).hexdigest()

def get_upwd():
    """生成一个唯一的用户密码
    """
    return md5(create_gen_id() + UPWD_STR).hexdigest()

def check_openid(openid):
    openid = str(openid)
    if len(openid) != 32:
        return False
    all_chars = list(string.ascii_lowercase + string.digits)
    for o_str in openid:
        if o_str not in all_chars:
            return False
    return True

def format_award(award, user_model=None):
    """
    生成奖励描述
    """
    res = []
    from apps.models.virtual.card import Card as CardMod
    if 'coin' in award:
        res.append(u'元宝%d个' % award['coin'])
    if 'gacha_pt' in award:
        res.append(u'援军点数%d点' % award['gacha_pt'])
    if 'gold' in award:
        res.append(u'铜钱%d枚' % award['gold'])
    if 'card' in award:
        card_res = []
        for cid in award['card']:
            this_card = CardMod.get(cid)
            clv = min(award['card'][cid].get('lv',1),this_card.max_lv)
            if user_model:
                global game_config
                game_config = user_model.game_config
            card_name = game_config.card_config[cid]['name']
            card_star = u'★' * int(this_card.star)
            card_lv = u'Lv.最大' if clv == this_card.max_lv else u'Lv.%d' % clv
            card_str = card_star + card_lv + card_name
            card_res.append(card_str)
        res.append(u'獲得%s' % (u'、'.join(card_res)))
    res_str = u'，'.join(res)
    res_str += u'!'
    return res_str

def create_sig(timestamp, user_model=None):
    """生成服务器端签名
    """
    timestamp_str = str(timestamp)
    signature = md5(timestamp_str + settings.SIG_SECRET_KEY).hexdigest()[:7]
    gap_length = random.choice(range(10,22))
    if user_model:
        global game_config
        game_config = user_model.game_config
    server_sig = game_config.system_config.get('server_sig',True)
    if server_sig:
        padding = md5(timestamp_str + 'oc_random_key').hexdigest()[:gap_length]
    else:
        padding_old = md5(timestamp_str + 'oc_random_key').hexdigest()[:gap_length-1]
        padding_list = list(padding_old)
        replace_index = random.choice(range(gap_length - 1))
        padding_list[replace_index] = '0'
        now_sum = sum(map(lambda x:int(x,16),padding_list))
        add_num_str = str(4 - now_sum % 4)
        padding_list[replace_index] = add_num_str
        padding = ''.join(padding_list)
    return signature + padding

def transtr2datetime(value):
    #"""转换字符串成日期型
    #"""
    try:
        lstdatetime = value.split(" ")
        year, month, day = lstdatetime[0].split("-")
        hour, m, second = lstdatetime[1].split(":")
        return datetime.datetime(int(year), int(month), int(day),
                                 int(hour), int(m), int(second))
    except:
        return None

#把datetime转成字符串
def datetime_toString(dt,strformat='%Y-%m-%d %H:%M:%S'):
    return dt.strftime(strformat)

#把字符串转成datetime
def string_toDatetime(string,strformat='%Y-%m-%d %H:%M:%S'):
    return datetime.datetime.strptime(string, strformat)

#把字符串转成时间戳形式
def string_toTimestamp(strTime):
    return int(time.mktime(string_toDatetime(strTime).timetuple()))

#把时间戳转成字符串形式
def timestamp_toString(stamp,strformat='%Y-%m-%d %H:%M:%S'):
    return time.strftime(strformat, time.localtime(stamp))

#把datetime类型转外时间戳形式
def datetime_toTimestamp(dateTim):
    return int(time.mktime(dateTim.timetuple()))

#把datetime类型转外时间戳形式
def timestamp_toDatetime(stamp,strformat='%Y-%m-%d %H:%M:%S'):
    strTime = timestamp_toString(stamp,strformat)
    return string_toDatetime(strTime,strformat)

def is_sense_word(words, user_model=None):
    """
    检查是否是敏感词
    """
    if user_model:
        global game_config
        game_config = user_model.game_config
    sensitive_words = game_config.maskword_config.get('sensitive_words',[])
    _name = words.lower()
    special_words = ['%','$','#','@','&','*','^','~','`','|']
    for w in special_words:
        if w in _name:
            return True
    for sense_word in sensitive_words:
        if _name.find(sense_word) >= 0:
            return True
    return False

def award_return_form(award):

    award_return = {'get_gold':0,'get_coin':0,'get_gacha_pt':0,'get_stone':0,\
                    'get_item':{},'get_material':{},'get_card':[],'get_equip':{},\
                    'get_super_soul':0,'get_normal_soul':{}}
    # award = {1:{'coin':1,},2:{'gold':2}}
    for award_id in award:
        tmp = award[award_id]
        for _k in award[award_id]:
            if not _k.startswith('get_'):
                change_k = 'get_%s' % _k
            else:
                change_k = _k
            if change_k in ['get_gold','get_coin','get_gacha_pt','get_stone','get_super_soul']:
                award_return[change_k] = award_return.get(change_k,0) + tmp.get(_k,0)
            elif change_k in ['get_item','get_material','get_normal_soul']:
                for __kk in tmp[_k]:
                    award_return[change_k][__kk] = award_return[change_k].get(__kk,0) + tmp[_k][__kk]
            elif change_k == 'get_equip':
                award_return[change_k].update(tmp[_k])
            elif change_k == 'get_card':  #这地方的card是 {ucid:{'':'','':''},ucid:{'':'','':''}}
                for ucid in tmp[_k]:
                    tmp_tmp = {
                    'ucid':ucid,
                            }
                    tmp_tmp.update(tmp[_k][ucid])
                    award_return[change_k].append(tmp_tmp)
    award_return_final = {key : award_return[key] for key in award_return if award_return[key] } 
    return award_return_final

def in_speacial_time(floor_conf,include_taday=True):
    # 多少天一个轮回
    tag = False
    time_now = datetime.datetime.now()
    time_now_str = datetime_toString(time_now)
    return_start_time = floor_conf['start_time']
    return_end_time = floor_conf['end_time']
    loop_gap = floor_conf.get('loop_gap')
    if loop_gap:
        if return_start_time[:10] > time_now_str[:10]:
            return False ,return_start_time,return_end_time
        return_start_time = time_now_str[:10] + floor_conf['start_time'][10:] 
        return_end_time = time_now_str[:10] + floor_conf['end_time'][10:] 
    if (time_now_str >= return_start_time and return_end_time >= time_now_str) or \
        ( time_now_str[:10] == return_start_time[:10] and include_taday\
         and time_now_str < return_start_time):
        if loop_gap:
            temp_today = string_toDatetime(time_now_str[:10] + ' 0:0:0')
            temp_start = string_toDatetime(floor_conf['start_time'][:10] + ' 0:0:0')
            if not (temp_today - temp_start).days % int(loop_gap):
                tag = True
        else:
            tag = True
    return tag , return_start_time ,return_end_time


def get_marquee_config(user_model=None):
    """获得跑马灯配置"""
    if user_model:
        global game_config
        game_config = user_model.game_config
    marquee_config = copy.deepcopy(game_config.marquee_config)
    return marquee_config
    
def get_push_info(user_model=None):
    """获得推送信息"""
    if user_model:
        global game_config
        game_config = user_model.game_config
    push_info = copy.deepcopy(game_config.system_config.get('push_info', {}))
    tdate = str(datetime.datetime.now().date())
    data = {}
    klist = push_info.keys()
    klist.sort()
    for i, t in enumerate(klist):
        at = tdate + ' ' + t
        ptime = time.mktime(time.strptime('%s' %(at), '%Y-%m-%d %H:%M'))
        data[str(i + 1)] = {}
        data[str(i + 1)]['ptime'] = int(ptime)
        data[str(i + 1)]['info'] = push_info[t]
    data['popen'] = copy.deepcopy(game_config.system_config.get('popen', False))
    return data


def windex(lst): 
    '''
    * 有权重的随机选择
    * input [[value,weight],[value,weight],[value,weight],[value,weight]]
    * output value 
    * miaoyichao
    '''
    wtotal = sum([x[1] for x in lst]) 
    n = random.uniform(0, wtotal) 
    for item, weight in lst: 
        if n < weight: 
            break 
        n = n - weight 
    return item

def format_award(award):
    '''
    * 格式化礼包内容
    input : {
        id:num,
        id:num,
        soul:{
            id:num,
            id:num
        }
    }
    out_put: data = {
        'card':{
            'card_id':num,
            'card_id':num,
        },
        'soul':{
            'equip':{
                'equip_id':num,
            }
            'card':{
                'card_id':num,
            },
        }, 
    }
    '''
    data = {}
    for award_id in award:
        #获取奖励的数量
        if award_id == 'soul':
            soul_info = award[award_id]
            if 'soul' not in data:
                data['soul'] = {}
            for soul_id in soul_info:
                if 'card' in soul_id:
                    #处理武将碎片的内容
                    if 'card' not in data['soul']:
                        data['soul']['card'] = {}
                    if soul_id not in data['soul']['card']:
                        data['soul']['card'][soul_id] = 0
                    data['soul']['card'][soul_id] += int(soul_info[soul_id])
                elif 'equip' in soul_id:
                    #处理装备碎片的内容
                    if 'equip' not in data['soul']:
                        data['soul']['equip'] = {}
                    if soul_id not in data['soul']['equip']:
                        data['soul']['equip'][soul_id] = 0
                    data['soul']['equip'][soul_id] += int(soul_info[soul_id])
                else:
                    pass
        elif 'card' in award_id:
            #处理武将奖励
            if 'card' not in data:
                data['card'] = {}
            if award_id not in data['card']:
                data['card'][award_id] = 0
            data['card'][award_id] += int(award[award_id])
        elif 'equip' in award_id:
            #处理装备奖励
            if 'equip' not in data:
                data['equip'] = {}
            if award_id not in data['equip']:
                data['equip'][award_id] = 0
            data['equip'][award_id] = int(award[award_id])
        elif 'mat' in award_id:
            #处理素材奖励
            if 'mat' not in data:
                data['mat'] = {}
            if award_id not in data['mat']:
                data['mat'][award_id] = 0
            data['mat'][award_id] = int(award[award_id])
        elif 'item' in award_id:
            #处理药品奖励
            if 'item' not in data:
                data['item'] = {}
            if award_id not in data['item']:
                data['item'][award_id] = 0
            data['item'][award_id] = int(award[award_id])
        elif 'props' in award_id:
            #处理道具奖励
            if 'props' not in data:
                data['props'] = {}
            if award_id not in data['props']:
                data['props'][award_id] = 0
            data['props'][award_id] = int(award[award_id])
        elif 'coin' in award_id:
            #处理元宝奖励
            if 'coin' not in data:
                data['coin'] = 0
            data['coin'] += int(award[award_id])
        elif 'gold' in award_id:
            #处理金币奖励
            if 'gold' not in data:
                data['gold'] = 0
            data['gold'] += int(award[award_id])
        elif 'stamina' in award_id:
            #处理金币奖励
            if 'stamina' not in data:
                data['stamina'] = 0
            data['stamina'] += int(award[award_id])
        else:
            pass
    #结果返回
    return data
                    
def remove_null(_list):
    """
    去空
    """
    return [ i for i in _list if i ]

def between_gap(value, gaps):
    for gap in gaps:
        if gap[0] <= value <= gap[1]:
            return gap
