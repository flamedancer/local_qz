#-*- coding: utf-8 -*-

import copy
import datetime
import hashlib
import hmac
import json
import md5
import os
import time
import traceback
import urllib
import urllib2
from base64 import b64decode

from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
# from M2Crypto import RSA as M2Crypto_RSA
from django.conf import settings
from django.http import HttpResponse

from apps.common.decorators import maintenance_auth
from apps.common.decorators import set_user
from apps.common.decorators import session_auth
from apps.common.decorators import signature_auth
from apps.common.decorators import verify_key
from apps.common.utils import print_err
from apps.common.utils import send_exception_mail
from apps.models import data_log_mod
from apps.models.account_mapping import AccountMapping
from apps.config.game_config import game_config
from apps.models.user_base import UserBase
from apps.oclib import app
from apps.common.utils import get_msg
from apps.common.utils import transtr2datetime
from apps.common.utils import datetime_toString
from apps.common.utils import string_toDatetime
from apps.models.user_mail import UserMail
from apps.common import utils
from apps.common import tools

ChargeRecord = data_log_mod.get_log_model("ChargeRecord")
OrderRecord = data_log_mod.get_log_model("OrderRecord")


g_rsa_pp = None
pp_pem_file = settings.BASE_ROOT+'/apps/config/public_pp.pem'

google_publicKey = 'MIIBIjANBgkqhkiG9w0BA\
            QEFAAOCAQ8AMIIBCgKCAQE\
            AsiFdMOKhlSzMD+5uuFny7\
            3lipBwo22+YxOBg+K4KK53\
            h9bsUaQTjIx/GDjDrcKylL\
            HVK3So06Jtbtxj3m177ozc\
            zPN/DNHhdDhYhkAEZASTTE\
            WS8XfoAT+YoCmIXhTL8RB4\
            IMPJwyTgkPYIp8bvoapAYf\
            fdm2zuBGVTaMtGgmBzoXf8\
            IKRlgJXSk2Jz+O2KJQXPTE\
            knJGSxCj4HIblFgsH38zWv\
            y00UGTfM1w0uEScnGidHBh\
            4HW1MXoyvENb+Ln3pHTcW7\
            XBpQ31YF+znrBIoVyVWO2z\
            Roq4NSSjACpw36lJzsPiDC\
            UJ62D0WhpbcWGTE3w6PV5p\
            C9gY+Pag+ipWwIDAQAB'


def charge_api(user_base_obj, oid, item_id, platform='', res_dict={},
               request=None, charge_way='', more_msg={}, charge_money=None):
    """充值通用函数


    Args:
        oid:   订单号，唯一标示
        item_id:   虚拟产品ID
        user_base_obj:  UserBase对象
        platform:   平台  例如：  qq, 360 , sina
    """
    data = {
        'rc': 0,
        'result': '',
        'data': {
            'msg': get_msg('charge','success'),
        }
    }

    if ChargeRecord.find({'oid':oid}):
        data['result'] = u'fail_订单重复' 
        return data

    rk_user = user_base_obj
    user_property_obj = rk_user.user_property
    property_info = user_property_obj.property_info
            
    try:
        shop_config = game_config.shop_config
        sale_conf = shop_config['sale']
        monthCard_sale_conf = shop_config.get('monthCard', {})
        item_info = sale_conf.get(item_id) or monthCard_sale_conf.get(item_id)
        if not item_info:
            data['rc'] = 12
            data['result'] = u'fail_无此商品' 
            data['data']['msg'] = 'item_id not exist:  ' + item_id
            return data
            

        # all_sale_type = ['sale']
        # for sale_type in all_sale_type:
        #     sale_items.update(shop_config.get(sale_type, {}))

        
        # 检查金额是否对
        if charge_money and not settings.DEBUG and float(charge_money) != float(item_info['price']):
            data['rc'] = 12
            data['result'] = u"充值金额不正确:%f" % float(charge_money)
            data['data']['msg'] = get_msg('charge','charge_money_invalid')
            return data
        before_coin = user_property_obj.coin
        # 分为月卡购买和  普通元宝购买
        free_coin = 0
        if item_id in sale_conf:
            # 计算此次购买可以买到的sale_coin 和额外赠送的 free_coin
            this_item_has_bought_times = property_info["charge_item_bought_times"].get(item_id, 0)
            if this_item_has_bought_times < item_info['extreme_cheap_time']:
                free_coin = item_info['extreme_free_coin']
            else:
                free_coin = item_info['free_coin']
            all_get_coin = item_info['sale_coin'] + free_coin
            # 记录此商品已购买次数
            property_info['charge_item_bought_times'].setdefault(item_id, 0)
            property_info['charge_item_bought_times'][item_id] += 1

        else:
            monthCard_remain_days = property_info.get('monthCard_remain_days', {})
            monthCard_remain_days.setdefault(item_id, 0)
            monthCard_remain_days[item_id] += 29
            property_info['monthCard_remain_days'] = monthCard_remain_days
            all_get_coin = item_info['sale_coin']

        # 记录总充值金额和元宝数
        property_info["charge_coins"] += all_get_coin
        property_info["charge_money"] += item_info['price']
        # 加元宝
        user_property_obj.property_info["coin"] += all_get_coin

        after_coin = user_property_obj.coin

        #作记录
        record_data = {
                        'oid': oid,
                        'platform': rk_user.platform,
                        'lv': user_property_obj.lv,
                        'price': item_info['price'],
                        'item_id': item_id,
                        'sale_coin': item_info['sale_coin'],
                        'free_coin': free_coin,
                        'createtime': datetime_toString(datetime.datetime.now()),
                        'before_coin': before_coin,
                        'after_coin': after_coin,
                        'client_type':rk_user.client_type,
                        'charge_way': charge_way,
                      }
        if more_msg:
            record_data.update(more_msg)
        ChargeRecord.set_log(rk_user, record_data)

        data['result'] = 'success'
        # 判断是否首次充值，若是，给首充奖励
        if (property_info["charge_money"] - item_info['price']) <= 0:
            __give_first_charge_award(rk_user)

        # （运营活动）充值满多少原价元宝给奖励
        __give_charge_award(rk_user, item_info['sale_coin'])        
        # 月卡处理
        # if item_id in month_items:
        #     __record_month_item(rk_user, item_id, item_info)
        user_property_obj.property_info = property_info
        user_property_obj.put()
    except:
        print_err()
        send_exception_mail(request)
        #清空storage
        app.pier.clear()
        data['rc'] = 12
        data['result'] = 'fail_' + traceback.format_exc()
        data['data']['msg'] = get_msg('charge','invalid')
    return data


def __give_first_charge_award(rk_user):
    """首次充值奖励
    """
    first_charge_award = rk_user.game_config.operat_config.get('first_charge_award', {})
    tools.add_things(rk_user, [{'_id': thing_id, 'num': num}
                     for thing_id, num in first_charge_award.items()], where='first_charge_award')

def __give_charge_award(rk_user, coin):
    """运营活动）充值奖励
    """
    if rk_user.client_type in settings.ANDROID_CLIENT_TYPE and 'charge_award' in game_config.android_config:
        charge_award = rk_user.game_config.android_config['charge_award']
    else:
        charge_award = rk_user.game_config.operat_config.get('charge_award',{})
    if not charge_award:
        return
    charge_award_info = rk_user.user_property.charge_award_info

    for gift_id in charge_award:
        gift_conf = charge_award[gift_id]
        start_time = gift_conf.get('start_time')
        end_time = gift_conf.get('end_time','2111-11-11 11:11:11')
        now_str = datetime_toString(datetime.datetime.now())
        # 未开放或已过期的礼包
        if now_str > end_time or now_str < start_time:
            continue
        
        if gift_id not in charge_award_info:
            charge_award_info[gift_id] = {'charge_coin': coin}
        else:
            # 已经领取过的礼包
            if charge_award_info[gift_id].get('has_got', False):
                continue
            charge_award_info[gift_id]['charge_coin'] += coin
        # 金额未达到
        if charge_award_info[gift_id]['charge_coin'] < gift_conf.get('charge_coin',0):
            continue
        # 满足条件，发奖励
        charge_award_info[gift_id]['has_got'] = True
        msg = get_msg('charge', 'charge_award') % gift_conf.get('charge_coin',0)
        sid = 'system_%s' % (utils.create_gen_id())
        mail_title = msg
        mail_content = gift_conf.get('desc', '')
        user_mail_obj = UserMail.hget(rk_user.uid, sid)
        user_mail_obj.set_mail(mailtype='system', title=mail_title, content=mail_content, award=gift_conf['award'])

    rk_user.user_property.put()



def __check_can_buy_month_item(rk_user, item_id):
    """
    检查是否能买月卡
    """
    month_item_info = rk_user.user_property.month_item_info
    product_id = item_id.split('.')[-1]
    if product_id in month_item_info and not month_item_info[product_id]['can_buy']:
        return False
    else:
        return True
    
def __record_month_item(rk_user,item_id,item_info):
    """
    记录月卡信息        
    """
    today = datetime.date.today()
    product_id = item_id.split('.')[-1]
    today_str = datetime_toString(today,'%Y-%m-%d')
    month_item_info = rk_user.user_property.month_item_info
    should_end_time = datetime_toString(today + datetime.timedelta(days=29),'%Y-%m-%d')
    if product_id not in month_item_info:
        month_item_info[product_id] = {
                                        'can_buy':False,#可以购买
                                        'charge_date':[today_str],#购买日期
                                        'can_get_today': False,#领奖开始时间
                                        'start_time':today_str,#领奖开始时间
                                        'end_time':should_end_time,#领奖结束时间
                                       }
    else:
        month_item_info[product_id]['charge_date'].insert(0,today_str)
        month_item_info[product_id]['charge_date'] = month_item_info[product_id]['charge_date'][:5]
        month_item_info[product_id]['can_buy'] = False
        #第一次买或者领奖期限已过
        if not month_item_info[product_id]['end_time'] or today_str >= month_item_info[product_id]['end_time']:
            month_item_info[product_id]['start_time'] = today_str
            month_item_info[product_id]['end_time'] = should_end_time
        else:
            end_time_date = string_toDatetime(month_item_info[product_id]['end_time'],'%Y-%m-%d')
            month_item_info[product_id]['end_time'] = datetime_toString(end_time_date + datetime.timedelta(days=30),'%Y-%m-%d')
    #发首日奖励
    first_day_bonus = item_info.get('first_day_bonus',{})
    if first_day_bonus:
        month_card_award = get_msg('operat', 'month_card_award')
        if month_card_award and product_id in month_card_award:
            content = month_card_award[product_id].get('month_today_award','')
        else:
            content = ''
        rk_user.user_gift.add_gift(first_day_bonus,content)
    rk_user.user_property.put()


@signature_auth
@session_auth
@set_user
def charge_result(request):
    """ 苹果AppStore充值回调
    """
    
    #审核期间用沙箱url
    now_version = request.REQUEST.get('version','')
    platform = request.REQUEST.get('platform','')
    review_version = game_config.system_config.get('review_version','')
    sandbox = 0
    if review_version and float(now_version) == float(review_version):
        apple_url = 'https://sandbox.itunes.apple.com/verifyReceipt'
        sandbox = 1
    else:
        apple_url = 'https://buy.itunes.apple.com/verifyReceipt'
    #解析参数
    receipt_data = request.REQUEST.get('receipt')
    #客户端传来的+变空格了
    receipt_data = receipt_data.replace(" ", "+")
    #向Apple验证
    data = {
        "receipt-data":receipt_data,
    }
    try:
        req = urllib2.Request(apple_url, urllib.urlencode(data))
        url_request = urllib2.urlopen(req, timeout=12)
        code,res = url_request.code, url_request.read()
    except:
        data = {
            'rc':7,
            'data':{
                  'msg':get_msg('login','refresh'),
                  'server_now':int(time.time()),
            },
        }
        data_log_mod.set_log('ChargeResultLog', **{'uid':request.rk_user.uid,'charge_way':'apple',\
                                              'result':u'fail_请求超时','subarea': request.rk_user.subarea, })
        return HttpResponse(
                    json.dumps(data, indent=1),
                    content_type='application/x-javascript',
                )
    data = {
        'rc':12,
        'result':u'fail_验证失败code:%s'%code,
        'data':{'msg':get_msg('charge','fail')}
    }
    oid = ''
    item_id = ''
    #验证成功发给用户商品
    if code == 200:
        res_dict = json.loads(res)
        rc = res_dict["status"]
        data['result'] = u'fail_status:%s'%rc
        if rc == 0:
            oid = res_dict["receipt"]["transaction_id"]
            item_id = res_dict["receipt"]["product_id"]
            if sandbox==1:
                more_msg = {'sandbox':sandbox}
            else:
                more_msg = {}
            data = charge_api(request.rk_user, oid, item_id, platform = platform,\
                              res_dict=res_dict,request = request,more_msg = more_msg)
    data['data']['user_info'] = request.rk_user.wrapper_info()
    data['data']['server_now'] = int(time.time())
    data_log_mod.set_log('ChargeResultLog', **{'uid':request.rk_user.uid,'charge_way':'apple',\
                                              'result':data['result'],'oid':oid,'item_id':item_id,'subarea': request.rk_user.subarea,})
    data.pop("result")
    return HttpResponse(
                json.dumps(data, indent=1),
                content_type='application/x-javascript',
            )
    

@verify_key
@session_auth
@set_user
def ali_charge_result(request):
    """支付宝充值回调
    """
    #验证成功发给用户商品
    
    print 'ali_charge_result: ', request
    oid = request.REQUEST['oid']
    item_id = request.REQUEST['item_id']
    item_info = game_config.shop_config['sale'][item_id]
    total_price = float(request.REQUEST.get('total_price', '1'))
    if float(item_info['price']) != total_price:
        return HttpResponse(
               json.dumps({'rc': 3}, indent=1),
               content_type='application/x-javascript',)

    data = charge_api(request.rk_user, oid, item_id,platform='',res_dict={},request=request,charge_way='alipay')
    data['data']['user_info'] = request.rk_user.wrapper_info()
    data['data']['server_now'] = int(time.time())
    data_log_mod.set_log('ChargeResultLog', **{'uid':request.rk_user.uid,'charge_way':'ali',\
                                              'result':data['result'],'oid':oid,'item_id':item_id,'subarea': request.rk_user.subarea,})
    data.pop("result")
    return HttpResponse(
                json.dumps(data, indent=1),
                content_type='application/x-javascript',
            )



@signature_auth
@session_auth
@set_user
def google_charge_result(request):
    
    signedData = request.REQUEST['signedData']
    signature = request.REQUEST['signature'].replace(' ','+')
    purchaseState =  json.loads(signedData)['purchaseState']
    item_id = request.REQUEST['item_id']
    oid = request.REQUEST['oid']
    data = {
        'rc':12,
        'result':u'fail_验证失败',
        'data':{'msg':get_msg('charge','fail'),'server_now':int(time.time())},
    }
    try:
        gvpfg = google_validate_purchase(signedData,signature)
    except:
        gvpfg = False
        print request
        print traceback.format_exc()
        return HttpResponse(
            json.dumps(data, indent=1),
            content_type='application/x-javascript',
        )
    if purchaseState==0 and gvpfg:
        data = charge_api(request.rk_user, oid, item_id,platform='gp',res_dict={},request=request,charge_way='googleplay')
        data['data']['user_info'] = request.rk_user.wrapper_info()
        data['data']['server_now'] = int(time.time())
    data_log_mod.set_log('ChargeResultLog', **{'uid':request.rk_user.uid,'charge_way':'gp',\
                                          'result':data['result'],'oid':oid,'item_id':item_id,'subarea': request.rk_user.subarea,})
    data.pop("result")
    return HttpResponse(
                json.dumps(data, indent=1),
                content_type='application/x-javascript',
            )


def charge_result_360(request):
    """充值回调
    """
    
    pay_dict = {}
    pay_dict['app_uid'] = str(request.REQUEST['app_uid'])#应用内用户ID
    pay_dict['order_id'] = str(request.REQUEST['order_id'])#360支付订单号
    pay_dict['app_key'] = str(request.REQUEST['app_key'])#应用app key
    pay_dict['product_id'] = str(request.REQUEST['product_id'])#所购商品id
    pay_dict['amount'] = str(request.REQUEST['amount'])#总价，单价，分
    pay_dict['app_order_id'] = str(request.REQUEST.get('app_order_id', ''))#应用订单号
    pay_dict['sign_type'] = str(request.REQUEST['sign_type'])#应用传给订单核实接口的参数
    pay_dict['sign_return'] = str(request.REQUEST['sign_return'])#应用传给订单核实接口的参数sign_type
    pay_dict['client_id'] = settings.APP_KEY_360#应用app key
    pay_dict['client_secret'] = settings.APP_SECRET_KEY_360#应用app_secret
    data = {
        'rc':12,
        'result':u'fail_验证失败',
        'data':{'msg':get_msg('charge','fail'),'server_now':int(time.time())},
    }
    rk_user = UserBase.get(pay_dict['app_uid'])
    pay_dict['gateway_flag'] = str(request.REQUEST.get('gateway_flag', ''))
    if pay_dict['gateway_flag'] != 'success':
        data_log_mod.set_log('ChargeResultLog', **{'uid':rk_user.uid,'charge_way':'360',\
                                              'result':u'fail_gateway_flag','oid':pay_dict['order_id'],\
                                              'item_id':pay_dict['product_id'],'price':pay_dict['amount'], 'subarea': rk_user.subarea,})
        return HttpResponse('ok')
    pay_url = "https://openapi.360.cn/pay/verify_mobile_notification.json?app_key=%(app_key)s&product_id=%(product_id)s&amount=%(amount)s&app_uid=%(app_uid)s&order_id=%(order_id)s&app_order_id=%(app_order_id)s&sign_type=%(sign_type)s&sign_return=%(sign_return)s&client_id=%(client_id)s&client_secret=%(client_secret)s" % pay_dict
    try:
        url_request = urllib2.urlopen(pay_url, timeout=12)
        code, res = url_request.code, url_request.read()
    except:
        data = {
            'rc':7,
            'data':{
                  'msg':get_msg('login','refresh'),
                  'server_now':int(time.time()),
            },
        }
        data_log_mod.set_log('ChargeResultLog', **{'uid':rk_user.uid,'charge_way':'360',\
                                              'result':u'fail_请求超时','oid':pay_dict['order_id'],\
                                              'item_id':pay_dict['product_id'],'price':pay_dict['amount'],'subarea': rk_user.subarea,})
        return HttpResponse('ok')
    oid = pay_dict["order_id"]
    item_id = pay_dict["product_id"]
    if code == 200:
        res_dict = json.loads(res)
        ret = res_dict.get('ret', '')
        if ret == 'verified':
            data = charge_api(rk_user, oid, item_id, platform = '360',res_dict={},request = request)
    data_log_mod.set_log('ChargeResultLog', **{'uid':rk_user.uid,'charge_way':'360',\
                                              'result':data['result'],'oid':oid,'item_id':item_id,'price':pay_dict['amount'],'subarea': rk_user.subarea,})
    return HttpResponse('ok')


#@set_user
#def verify_ali_charge_result(request):
#    """验证支付宝充值订单
#    """
#    #验证订单是否存在
#    oid = request.REQUEST['oid']
#    data = {'data':{}, 'rc':12 }
#    charge_res = ChargeRecord.find({'oid':oid})
#    if not charge_res:
#        return HttpResponse(
#                json.dumps(data, indent=1),
#                content_type='application/x-javascript',
#            )
#    rk_user = request.rk_user
#    charge_record_obj = charge_res[0]
#    if rk_user.uid != charge_record_obj.uid:
#        return HttpResponse(
#                json.dumps(data, indent=1),
#                content_type='application/x-javascript',
#            )
#    data['data']['get_coin'] = charge_record_obj.after_coin - charge_record_obj.before_coin
#    data['data']['user_info'] = request.rk_user.wrapper_info()
#    data['data']['server_now'] = int(time.time())
#    data['rc'] = 0
#    return HttpResponse(
#                json.dumps(data, indent=1),
#                content_type='application/x-javascript',
#            )


def chunks(s, n):
    for start in range(0, len(s), n):
        yield s[start:start+n]


def pem_format(key):
    return '\n'.join([
        '-----BEGIN PUBLIC KEY-----',
        '\n'.join(chunks(key, 64)),
        '-----END PUBLIC KEY-----'
    ])


def google_validate_purchase(signedData, signature):
    global google_publicKey
    publicKey = google_publicKey
    key = RSA.importKey(pem_format(publicKey))
    verifier = PKCS1_v1_5.new(key)
    data = SHA.new(signedData)
    sig = b64decode(signature)
    return verifier.verify(data, sig)




@signature_auth
@maintenance_auth
@session_auth
@set_user
def has_oid(request):
    """
    给前端调用，用来确认oid是否是成功充值
    """
    oid = request.REQUEST['oid']
    match_query = {'oid': oid}
    charge_log = ChargeRecord.find(match_query)

    data = {}
    if charge_log:
        data['item_id'] = charge_log[0].item_id
    return HttpResponse(
        json.dumps({'rc': 0, 'data': data}, indent=1),
        content_type='application/x-javascript',
    )


# ＃＃＃＃＃＃＃ mycard  点卡支付逻辑
FACID = settings.MYCARD_FACID
KEY1 = settings.MYCARD_KEY1
KEY2 = settings.MYCARD_KEY2
host_auth_code = "http://test.b2b.mycard520.com.tw/MyCardIngameService/Auth"
host_web = "http://test.mycard520.com.tw/MyCardIngame/"
host_serve = "http://test.b2b.mycard520.com.tw/MyCardIngameService/Confirm"
host_confirm_oid = "http://test.b2b.mycard520.com.tw/MyCardIngameService/CheckTradeStatus"
if settings.DEBUG is False:
    host_auth_code = "https://b2b.mycard520.com.tw/MyCardIngameService/Auth"
    host_web = "https://redeem.mycard520.com/"
    host_serve = "https://b2b.mycard520.com.tw/MyCardIngameService/Confirm"
    host_confirm_oid = "https://b2b.mycard520.com.tw/MyCardIngameService/CheckTradeStatus"
@signature_auth
@maintenance_auth
@session_auth
@set_user
def mycard_get_authcode(request):
    """
    進行交易起始取得授權碼
    """
    #  支付方式  ingame  （先实现ingame的方式）
    if request.REQUEST['type'] != 'ingame':
        return
    rk_user = request.rk_user

    facTradeSeq = "mycard" + rk_user.uid + str(time.time())
    hash_str = hashlib.sha256(KEY1 + FACID + facTradeSeq + KEY2).hexdigest()
    request_data = dict(
        facId = FACID,
        facTradeSeq = facTradeSeq,
        hash = hash_str,
    )

    pairs = urllib.urlencode(request_data)
    fullurl = host_auth_code + '?' + pairs

    data = {
          'msg':get_msg('login','refresh'),
          'server_now':int(time.time()),
    }

    try:
        url_request = urllib2.urlopen(fullurl, timeout=12)
        code, res = url_request.code, url_request.read()
    #  请求 authcode 超时
    except:
        return HttpResponse(
            json.dumps({'rc': 7, 'data': data}, indent=1),
            content_type='application/x-javascript',
        )

    result_auth_code = json.loads(res)
    if code == 200 and result_auth_code["ReturnMsgNo"] == 1:
        data = {
              'server_now':int(time.time()),
              'facTradeSeq': facTradeSeq,
              'TradeType': result_auth_code['TradeType'],
              'AuthCode': result_auth_code['AuthCode'],
        }

        #  走 mycard web 的支付方式  要返回 支付网页地址
        if result_auth_code['TradeType'] == 2:
            authCode = result_auth_code['AuthCode']
            facMemId = rk_user.pid
            hash_str = hashlib.sha256(KEY1 + authCode + FACID + facMemId + KEY2).hexdigest()
            data_web = dict(
                facId = FACID,
                authCode = authCode,
                facMemId = facMemId,
                hash = hash_str,
            )
            pairs = urllib.urlencode(data_web)
            fullurl_web = host_web + '?' + pairs
            data = {
                  'server_now':int(time.time()),
                  'TradeType': result_auth_code['TradeType'],
                  'mycard_url': fullurl_web,
            }
        return HttpResponse(
            json.dumps({'rc': 0, 'data': data}, indent=1),
            content_type='application/x-javascript',
        )
    return HttpResponse(
        json.dumps({'rc': 12, 'data': data}, indent=1),
        content_type='application/x-javascript',
    )


def mycard_return_charge_result(request):
    """
    將使用者導到 MyCard 特定網站入口并充值后， mycard调用此接口通知我们给玩家发商品
    """
    facId = request.REQUEST['facId']
    facMemId = request.REQUEST['facMemId']
    facTradeSeq = request.REQUEST['facTradeSeq']
    tradeSeq = request.REQUEST['tradeSeq']
    CardId = request.REQUEST['CardId']
    oProjNo = request.REQUEST['oProjNo']
    CardKind = request.REQUEST['CardKind']
    CardPoint = request.REQUEST['CardPoint']
    ReturnMsgNo = request.REQUEST['ReturnMsgNo']
    ErrorMsgNo = request.REQUEST['ErrorMsgNo']
    ErrorMsg = request.REQUEST['ErrorMsg']
    if ErrorMsg:
        import sys
        reload(sys) 
        sys.setdefaultencoding('utf-8') 
        ErrorMsg = ErrorMsg.decode('utf-8')
        return HttpResponse(ErrorMsg)
    hash_str = request.REQUEST['hash']
    hash_items = map(str, [KEY1, facId, facMemId, facTradeSeq, tradeSeq,
                  CardId, oProjNo, CardKind, CardPoint, ReturnMsgNo,
                  ErrorMsgNo, ErrorMsg, KEY2])
    if hash_str != hashlib.sha256(''.join(hash_items)).hexdigest():
        return HttpResponse("hash erro")
    hash_str = hashlib.sha256(KEY1 + FACID + facTradeSeq + KEY2).hexdigest()
    data_comfirm = dict(
        facId = FACID,
        facTradeSeq = facTradeSeq,
        hash = hash_str,
    )

    pairs = urllib.urlencode(data_comfirm)
    fullurl = host_confirm_oid + '?' + pairs
    try:
        url_request = urllib2.urlopen(fullurl, timeout=12)
        code, res = url_request.code, url_request.read()
    except:
        return HttpResponse("mycard confirm serve out of time")
    confirm_result = json.loads(res)
    #  通过  facMemId（pid） 获得 user_base
    rk_user = UserBase.get_exist_user(facMemId)

    if not rk_user:
        return  HttpResponse(u"user not exist ")
    if code == 200 and confirm_result['ReturnMsgNo'] == 1 and \
    confirm_result['TradeStatus'] == 3 and\
    confirm_result['MyCardId'] == CardId and\
    confirm_result['Save_Seq'] == tradeSeq and\
    confirm_result['CardPoint'] == CardPoint:

        mycard_shop = game_config.shop_config['mycard_sale']
        # mycard_pt_item = {mycard_shop[item]['mycard_pt']: item for item in mycard_shop}
        mycard_pt_item = {}
        for item in mycard_shop:
            mycard_pt_item[mycard_shop[item]['mycard_pt']] = item
        import bisect
        all_pt = sorted(mycard_pt_item.keys())
        index = bisect.bisect(all_pt, int(CardPoint)) - 1
        if index < 0:
            return  HttpResponse("CardPoint not enough!")
        pt = all_pt[index]
        data = {'result': u'fail_验证失败',}
        item_id = mycard_pt_item[pt]
        more_msg = dict(
                MyCard_ID = CardId,   # MyCard 卡號
                Cust_ID = facMemId,   # 玩家pid
                TRADE_NO = tradeSeq,  # MyCard 交易序號
                GAME_TNO = facTradeSeq,  # oc产生的 交易序號
                CardKind = confirm_result['CardKind'],
                oProjNo = confirm_result['oProjNo']
            )
        data = charge_api(rk_user, facTradeSeq, item_id, platform='', res_dict={}, request=request, charge_way='mycard', more_msg=more_msg)
        data_log_mod.set_log('ChargeResultLog', **{'uid':rk_user.uid,'charge_way':'mycard',\
                                              'result':data['result'],'oid':facTradeSeq,'item_id':item_id,'subarea': rk_user.subarea,})
        if data['rc'] != 0 or data['result'] == u'fail_订单重复':
            return  HttpResponse(data['result'])
        return  HttpResponse("charge success! " + rk_user.uid)
    return HttpResponse("parameter difference!")


def mycard_sync_report(request):
    StartDate = request.REQUEST.get('StartDate', '').replace("/", "-")
    EndDate = request.REQUEST.get('EndDate', '').replace("/", "-")
    MyCardID = request.REQUEST.get('MyCardID', '')

    inquiry = {'charge_way': "mycard"}
    if MyCardID:
        inquiry['MyCard_ID'] = MyCardID
    elif StartDate and EndDate:
        inquiry['createtime'] = {}
        inquiry['createtime']['$gte'] = '%s 00:00:00' % StartDate
        inquiry['createtime']['$lte'] = '%s 23:59:59' % EndDate
    else:
        return HttpResponse("")

    result = ChargeRecord.find(inquiry)
    return_str = ""
    for item in result:
        need_columns = [item.MyCard_ID, item.Cust_ID, item.TRADE_NO, item.GAME_TNO, item.createtime]
        return_str = return_str + ",".join(need_columns) + "<BR>" + os.linesep
    return HttpResponse(return_str)


@signature_auth
@maintenance_auth
@session_auth
@set_user
def  mycard_serve_side_charge(request):
    """
    在遊戲中呈現「卡號」、「密碼」的輸入介面供使用者進行儲值
    """
    rk_user = request.rk_user

    facId = FACID
    authCode = request.REQUEST['authCode']
    facMemId = rk_user.pid
    cardId = request.REQUEST['cardId']
    cardPwd = request.REQUEST['cardPwd']
    data = {
      'msg':get_msg('login','refresh'),
      'server_now':int(time.time()),
    }
    try:
        hash_items = map(str, [KEY1, facId, authCode, facMemId,cardId, cardPwd, KEY2])
    except:
        print request
        print traceback.format_exc()
        return HttpResponse(
            json.dumps({'rc': 7, 'data': data}, indent=1),
            content_type='application/x-javascript',
        )

    hash_str = hashlib.sha256(''.join(hash_items)).hexdigest()

    charge_data = dict(
            facId = facId,
            authCode = authCode,
            facMemId = facMemId,
            cardId = cardId,
            cardPwd = cardPwd,
            hash = hash_str,
        )

    pairs = urllib.urlencode(charge_data)
    fullurl = host_serve + '?' + pairs

    data = {
      'msg':get_msg('login','refresh'),
      'server_now':int(time.time()),
    }
    try:
        url_request = urllib2.urlopen(fullurl, timeout=12)
        code, res = url_request.code, url_request.read()
    #  请求 authcode 超时
    except:
        return HttpResponse(
            json.dumps({'rc': 7, 'data': data}, indent=1),
            content_type='application/x-javascript',
        )
    charge_result = json.loads(res)

    if code == 200 and charge_result['ReturnMsgNo'] == 1:
        facTradeSeq = charge_result['facTradeSeq']
        CardPoint = charge_result['CardPoint']
        hash_str = hashlib.sha256(KEY1 + FACID + facTradeSeq + KEY2).hexdigest()
        data_comfirm = dict(
            facId = FACID,
            facTradeSeq = facTradeSeq,
            hash = hash_str,
        )

        pairs = urllib.urlencode(data_comfirm)
        fullurl = host_confirm_oid + '?' + pairs
        try:
            url_request = urllib2.urlopen(fullurl, timeout=12)
            code, res = url_request.code, url_request.read()
        except:
            data = {
              'msg': "mycard confirm serve out of time",
              'server_now':int(time.time()),
            }
            return HttpResponse(
                json.dumps({'rc': 12, 'data': data}, indent=1),
                content_type='application/x-javascript',
            )
        confirm_result = json.loads(res)
        if code == 200 and confirm_result['ReturnMsgNo'] == 1 and \
        confirm_result['TradeStatus'] == 3 and\
        confirm_result['MyCardId'] == cardId and\
        confirm_result['Save_Seq'] == charge_result['SaveSeq'] and\
        int(confirm_result['CardPoint']) == CardPoint:
            mycard_shop = game_config.shop_config['mycard_sale']
            # mycard_pt_item = {mycard_shop[item]['mycard_pt']: item for item in mycard_shop}
            mycard_pt_item = {}
            for item in mycard_shop:
                mycard_pt_item[mycard_shop[item]['mycard_pt']] = item
            import bisect
            all_pt = sorted(mycard_pt_item.keys())
            index = bisect.bisect(all_pt, int(CardPoint)) - 1
            if index < 0:
                return  HttpResponse("CardPoint not enough!")
            pt = all_pt[index]
            data = {'result': u'fail_验证失败',}
            item_id = mycard_pt_item[pt]
            more_msg = dict(
                MyCard_ID = cardId,   # MyCard 卡號
                Cust_ID = facMemId,   # 玩家pid
                TRADE_NO = confirm_result['Save_Seq'],  # MyCard 交易序號
                GAME_TNO = facTradeSeq,  # oc产生的 交易序號
                CardKind = confirm_result['CardKind'],
                oProjNo = confirm_result['oProjNo']
            )
            data = charge_api(rk_user, facTradeSeq, item_id, platform='', res_dict={}, request=request, charge_way='mycard', more_msg=more_msg)
            data_log_mod.set_log('ChargeResultLog', **{'uid':rk_user.uid,'charge_way':'mycard',\
                                                  'result':data['result'],'oid':facTradeSeq,'item_id':item_id,'subarea': rk_user.subarea,})

            data['data']['user_info'] = request.rk_user.wrapper_info()
            data['data'].pop('msg')
            return HttpResponse(
                json.dumps(data, indent=1),
                content_type='application/x-javascript',
            )
        data = {
          'msg': "argv different  ",
          'server_now':int(time.time()),
        }
        return HttpResponse(
            json.dumps({'rc': 12, 'data': data}, indent=1),
            content_type='application/x-javascript',
        )
    data = {
      'msg': charge_result['ReturnMsg'],
      'server_now':int(time.time()),
    }
    return HttpResponse(
        json.dumps({'rc': 12, 'data': data}, indent=1),
        content_type='application/x-javascript',
    )



################## mi (小米)支付逻辑##########
@signature_auth
@maintenance_auth
@session_auth
@set_user
def mi_create_orderid(request):
    """
    给前段返回一个唯一的小米订单号，并记录在 OrderRecord 表
    """
    rk_user = request.rk_user
    item_id = request.REQUEST.get('item_id', None)
    if not item_id:
        data = {
            'rc':12,
            'result':u'没有物品id',
            'data':{'msg':get_msg('charge','fail'),'server_now':int(time.time())},
        }
        return HttpResponse(
            json.dumps(data, indent=1),
            content_type='application/x-javascript',
        )
    oid = "mi" + rk_user.uid + str(time.time())

    #作记录
    record_data = {
                    "oid":oid,
                    "uid":rk_user.uid,
                    "item_id":item_id,
                    "createtime":datetime_toString(datetime.datetime.now()),
                  }
    data_log_mod.set_log('OrderRecord', rk_user, **record_data)
    data = {
        'rc': 0,
        'data': {'oid': oid, 'server_now': int(time.time())},
    }
    return HttpResponse(
        json.dumps(data, indent=1),
        content_type='application/x-javascript',
    )


def mi_sync_report(request):
    """
    mi获得玩家的充值行为后，用此api通知我们
    第一步  验证mi 的请求参数
    第二步  主动查询 mi，进一步确认订单状态
    第三步  给玩家充值
    """
    request_data = dict(
        appId = request.REQUEST.get('appId', None),
        cpOrderId = request.REQUEST.get('cpOrderId', None),
        cpUserInfo = request.REQUEST.get('cpUserInfo', None),
        uid = request.REQUEST.get('uid', None),
        orderId = request.REQUEST.get('orderId', None),
        orderStatus = request.REQUEST.get('orderStatus', None),
        payFee = request.REQUEST.get('payFee', None),
        productCode = request.REQUEST.get('productCode', None),
        productName = request.REQUEST.get('productName', None),
        productCount = request.REQUEST.get('productCount', None),
        payTime = request.REQUEST.get('payTime', None),
        orderConsumeType = request.REQUEST.get('orderConsumeType', None),
        signature = request.REQUEST.get('signature', None),
    )

    #### 验证mi 的传参
    # errcode 含义
    # 状态码,200 成功
    # 1506 cpOrderId 错误
    # 1515 appId 错误
    # 1516 uid 错误  （mi 的uid）
    # 1525 signature 错误 
    # 3515 订单信息  不一致,用于和 CP 的订单校验
    #￼3502 订单处理超时￼￼￼
    #￼1511 支付结果错误￼￼￼￼￼￼￼￼￼￼￼￼￼￼
    errcode = {'errcode': 200}
    if request_data['appId'] != settings.MI_APP_ID:
        errcode['errcode'] = 1515
        return HttpResponse(
                json.dumps(errcode, indent=1),
                content_type='application/x-javascript',
        ) 

    signature_params = sorted([key for key in request_data.keys() if request_data[key] and key != 'signature'])
    ready_signature = "&".join(['{}={}'.format(key, request_data[key].encode('utf-8')) for key in signature_params])
    if request_data['signature'] != hmac.new(settings.MI_SECRET_KEY, ready_signature, hashlib.sha1).hexdigest():
        errcode['errcode'] = 1525
        return HttpResponse(
            json.dumps(errcode, indent=1),
            content_type='application/x-javascript',
        ) 

    oid = request_data['cpOrderId']

    mi_record = OrderRecord.find({'oid':oid})
    if not mi_record:
        errcode['errcode'] = 1506
        return HttpResponse(
                json.dumps(errcode, indent=1),
                content_type='application/x-javascript',
        )
    item_id = mi_record[0].item_id
    oc_uid = mi_record[0].uid


    #### 我们 主动查询mi的订单支付状态接口  加强验证
    mi_url = "http://mis.migc.xiaomi.com/api/biz/service/queryOrder.do"
    ready_signature = 'appId=%s&cpOrderId=%s&uid=%s' % (settings.MI_APP_ID, oid, request_data['uid'])
    signature = hmac.new(settings.MI_SECRET_KEY, ready_signature, hashlib.sha1).hexdigest()
    confirm_data = dict(
        appId = settings.MI_APP_ID,
        cpOrderId = oid,
        uid = request_data['uid'],
        signature = signature,
    )
    pairs = urllib.urlencode(confirm_data)
    fullurl = mi_url + '?' + pairs
    url_request = urllib2.urlopen(fullurl, timeout=12)
    code, res = url_request.code, url_request.read()
    res_dict = json.loads(res)

    rk_user = UserBase.get(oc_uid)
    if not rk_user:
        errcode['errcode'] = 1506
        return HttpResponse(
            json.dumps(errcode, indent=1),
            content_type='application/x-javascript',
        ) 

    if code != 200:
        errcode['errcode'] = 3502
        data_log_mod.set_log('ChargeResultLog', **{'uid':rk_user.uid,'charge_way':'mi',\
                                              'result': u'订单处理超时' + str(code),'oid':oid,'item_id':item_id,'subarea': rk_user.subarea,})
        return HttpResponse(
            json.dumps(errcode, indent=1),
            content_type='application/x-javascript',
        ) 
    if 'errcode' in res_dict:
        errcode['errcode'] = res_dict['errcode']
        data_log_mod.set_log('ChargeResultLog', **{'uid':rk_user.uid,'charge_way':'mi',\
                                      'result': u'小米验证支付状态不通过' + errcode['errcode'],'oid':oid,'item_id':item_id,'subarea': rk_user.subarea,})
        return HttpResponse(
            json.dumps(errcode, indent=1),
            content_type='application/x-javascript',
        ) 
    if res_dict['cpOrderId'] != oid or res_dict['orderStatus'] != 'TRADE_SUCCESS':
        errcode['errcode'] = 1511
        data_log_mod.set_log('ChargeResultLog', **{'uid':rk_user.uid,'charge_way':'mi',\
                              'result': u'小米返回：支付结果错误'+ res_dict['orderStatus'],'oid':oid,'item_id':item_id,'subarea': rk_user.subarea,})
        return HttpResponse(
                json.dumps(errcode, indent=1),
                content_type='application/x-javascript',
        )


    # 和前端约定cpUserInfo  存的是 item_id
    if item_id != res_dict['cpUserInfo']:
        errcode['errcode'] = 3515
        data_log_mod.set_log('ChargeResultLog', **{'uid':rk_user.uid,'charge_way':'mi',\
                      'result': u'物品不一致','oid':oid,'item_id':item_id,'subarea': rk_user.subarea,})
        return HttpResponse(
                json.dumps(errcode, indent=1),
                content_type='application/x-javascript',
        )

    ###  给玩家充值
    
    data = charge_api(rk_user, oid, item_id, platform = 'mi',res_dict={},request = request, charge_way='mi')
    data_log_mod.set_log('ChargeResultLog', **{'uid':rk_user.uid,'charge_way':'mi',\
                                              'result':data['result'],'oid':oid,'item_id':item_id,'subarea': rk_user.subarea,})
    if data['result'] == u'fail_订单重复':
        errcode['errcode'] = 2004
    elif data['rc'] != 0:
        errcode['errcode'] = 1506
    return HttpResponse(
        json.dumps(errcode, indent=1),
        content_type='application/x-javascript',
    )

################## 91支付逻辑##########
@signature_auth
@maintenance_auth
@session_auth
@set_user
def create_orderid_91(request):
    """
    给前段返回一个唯一的91充值订单号，并记录在 OrderRecord 表
    """
    rk_user = request.rk_user
    item_id = request.REQUEST.get('item_id', None)
    if not item_id:
        data = {
            'rc':12,
            'result':u'没有物品id',
            'data':{'msg':get_msg('charge','fail'),'server_now':int(time.time())},
        }
        return HttpResponse(
            json.dumps(data, indent=1),
            content_type='application/x-javascript',
        )
    oid = "91" + rk_user.uid + str(time.time())
    oid = oid.replace('.','_')

    #作记录
    record_data = {
                    "oid":oid,
                    "uid":rk_user.uid,
                    "item_id":item_id,
                    "createtime":datetime_toString(datetime.datetime.now()),
                  }
    data_log_mod.set_log('OrderRecord', rk_user, **record_data)
    data = {
        'rc': 0,
        'data': {'oid': oid, 'server_now': int(time.time())},
    }
    return HttpResponse(
        json.dumps(data, indent=1),
        content_type='application/x-javascript',
    )
    
def charge_result_91(request):
    """
    91获得玩家的充值行为后，用此api通知我们
    第一步  验证91 的请求参数
    第二步  给玩家充值
    """
    request_data = dict(
        AppId = request.REQUEST.get('AppId', None),
        Act = request.REQUEST.get('Act', None),
        ProductName = request.REQUEST.get('ProductName', None),
        ConsumeStreamId = request.REQUEST.get('ConsumeStreamId', None),
        CooOrderSerial = request.REQUEST.get('CooOrderSerial', None),
        Uin = request.REQUEST.get('Uin', None),
        GoodsId = request.REQUEST.get('GoodsId', None),
        GoodsInfo = request.REQUEST.get('GoodsInfo', None),
        GoodsCount = request.REQUEST.get('GoodsCount', None),
        OriginalMoney = request.REQUEST.get('OriginalMoney', None),
        OrderMoney = request.REQUEST.get('OrderMoney', None),
        Note = request.REQUEST.get('Note', None),
        PayStatus = request.REQUEST.get('PayStatus', None),
        CreateTime = request.REQUEST.get('CreateTime', None),
        Sign = request.REQUEST.get('Sign', None),
    )

    #### 验证91 的传参
    # ErrorCode 含义
    # 状态码,1 成功
    # 0 失败
    # 2 AppId无效
    # 3 Act无效
    # 4 参数无效 
    # 5 Sign错误
    errcode = {'ErrorCode': 1,'ErrorDesc':u'接收成功'}
    if None in request_data.values():
        errcode = {'ErrorCode': 4,'ErrorDesc':u'参数无效'}
        return HttpResponse(
                json.dumps(errcode, indent=1),
                content_type='application/x-javascript',
        ) 
    if request_data['AppId'] != settings.APP_ID_91:
        errcode['ErrorCode'] = 2
        errcode['ErrorDesc'] = u'AppId无效'
        return HttpResponse(
                json.dumps(errcode, indent=1),
                content_type='application/x-javascript',
        ) 
    if request_data['Act'] != '1':
        errcode['ErrorCode'] = 3
        errcode['ErrorDesc'] = u'Act无效'
        return HttpResponse(
                json.dumps(errcode, indent=1),
                content_type='application/x-javascript',
        ) 
    if request_data['PayStatus'] != '1':
        errcode['ErrorCode'] = 0
        errcode['ErrorDesc'] = u'接收失败'
        return HttpResponse(
                json.dumps(errcode, indent=1),
                content_type='application/x-javascript',
        )

    signature_params = u"{0}{1}{2}{3}{4}{5}{6}{7}{8}{9:.2f}{10:.2f}{11}{12}{13}{14}".format(\
                     request_data['AppId'],request_data['Act'],request_data['ProductName'],request_data['ConsumeStreamId'],\
                     request_data['CooOrderSerial'],request_data['Uin'],request_data['GoodsId'],request_data['GoodsInfo'],\
                     request_data['GoodsCount'],float(request_data['OriginalMoney']),float(request_data['OrderMoney']),\
                     request_data['Note'],request_data['PayStatus'],request_data['CreateTime'],settings.APP_KEY_91)
    signature = md5.new(signature_params.encode('utf-8')).hexdigest()
    if request_data['Sign'] != signature:
        errcode['ErrorCode'] = 5
        errcode['ErrorDesc'] = u'Sign无效'
        return HttpResponse(
            json.dumps(errcode, indent=1),
            content_type='application/x-javascript',
        ) 

    oid = request_data['CooOrderSerial']
    pid = md5.md5('91'+str(request_data['Uin'])).hexdigest()
    acc_obj = AccountMapping.get(pid)
    if not acc_obj:
        errcode['ErrorCode'] = 0
        errcode['ErrorDesc'] = u'接收失败'
        return HttpResponse(
                json.dumps(errcode, indent=1),
                content_type='application/x-javascript',
        )
    oc_uid = acc_obj.uid
    item_id = request_data['GoodsId']
    mi_record = OrderRecord.find({'oid':oid})
    if not mi_record:
        errcode['ErrorCode'] = 0
        errcode['ErrorDesc'] = u'接收失败'
        return HttpResponse(
                json.dumps(errcode, indent=1),
                content_type='application/x-javascript',
        )
    get_item_id = mi_record[0].item_id
    get_oc_uid = mi_record[0].uid
    if get_item_id != item_id or oc_uid != get_oc_uid:
        errcode['ErrorCode'] = 0
        errcode['ErrorDesc'] = u'接收失败'
        return HttpResponse(
                json.dumps(errcode, indent=1),
                content_type='application/x-javascript',
        )
    rk_user = UserBase.get(oc_uid)
    ###  给玩家充值
    OrderMoney = float(request_data['OrderMoney'])
    data = charge_api(rk_user, oid, item_id, platform = '91',res_dict={},request = request, charge_way='91',charge_money=OrderMoney)
    data_log_mod.set_log('ChargeResultLog', **{'uid':rk_user.uid,'charge_way':'91',\
                                              'result':data['result'],'oid':oid,'item_id':item_id,'subarea': rk_user.subarea,})
    if data['rc'] != 0:
        errcode['ErrorCode'] = 0
        errcode['ErrorDesc'] = u'接收失败'
    return HttpResponse(
        json.dumps(errcode, indent=1),
        content_type='application/x-javascript',
    )
    
################## pp支付逻辑##########
@signature_auth
@maintenance_auth
@session_auth
@set_user
def pp_create_orderid(request):
    """
    给前段返回一个唯一的pp充值订单号，并记录在 OrderRecord 表
    """
    rk_user = request.rk_user
    item_id = request.REQUEST.get('item_id', None)
    if not item_id:
        data = {
            'rc':12,
            'result':u'没有物品id',
            'data':{'msg':get_msg('charge','fail'),'server_now':int(time.time())},
        }
        return HttpResponse(
            json.dumps(data, indent=1),
            content_type='application/x-javascript',
        )
    oid = "pp" + rk_user.uid + str(time.time())
    oid = oid.replace('.','_')

    #作记录
    record_data = {
                    "oid":oid,
                    "uid":rk_user.uid,
                    "item_id":item_id,
                    "createtime":datetime_toString(datetime.datetime.now()),
                  }
    data_log_mod.set_log('OrderRecord', rk_user, **record_data)
    data = {
        'rc': 0,
        'data': {'oid': oid, 'server_now': int(time.time())},
    }
    return HttpResponse(
        json.dumps(data, indent=1),
        content_type='application/x-javascript',
    )

def decode_pp_callback(data):
    global g_rsa_pp
    try:
        b64string = b64decode(data)
        if not g_rsa_pp:
            g_rsa_pp = M2Crypto_RSA.load_pub_key(pp_pem_file)
            
        ctxt = g_rsa_pp.public_decrypt(b64string, M2Crypto_RSA.pkcs1_padding)
        return 0,json.loads(ctxt)
    except:
        return 1,{}

def charge_result_pp(request):
    """
    pp获得玩家的充值行为后，用此api通知我们
    第一步  验证pp 的请求参数
    第二步  给玩家充值
    """
    status = int(request.REQUEST['status'])
    #已经兑现过了
    if status == 1:
        return HttpResponse('success')
    
    #订单验证失败
    sign = request.REQUEST['sign']
    rc, pp_sign = decode_pp_callback(sign) 
    if rc or pp_sign == {}:
        return HttpResponse('fail')
    
    #订单是否处理过
    billno = pp_sign['billno']
    billno_req = request.REQUEST['billno']
    if billno_req != billno:
        return HttpResponse('fail')
    #是否是正确的玩家
    uid = pp_sign['roleid']
    
    mi_record = data_log_mod.get_log_model("OrderRecord").find({'oid':billno})
    if not mi_record:
        return HttpResponse('fail')
    item_id = mi_record[0].item_id
    oc_uid = mi_record[0].uid
    if oc_uid != uid:
        return HttpResponse('fail')

    rk_user = UserBase.get(oc_uid)
    if not rk_user:
        return HttpResponse('fail')
    
    data = charge_api(rk_user, billno, item_id, platform = 'pp',res_dict={},request = request, charge_way='pp')
    data_log_mod.set_log('ChargeResultLog', rk_user, **{'charge_way':'pp',
                                              'result':data['result'],'oid':billno,'item_id':item_id})
    if data['rc'] != 0:
        return HttpResponse('fail')
    return HttpResponse('success') 
