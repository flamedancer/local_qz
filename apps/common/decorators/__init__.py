#-*- coding: utf-8 -*-

import md5
import time
import os
from django.http import HttpResponse
from django.conf import settings
from apps.common.utils import print_err,debug_print
from apps.oclib.utils import rkjson as json
from apps.models.user_base import UserBase
from apps.models.account_mapping import AccountMapping
from apps.models.session import Session
from apps.common.utils import send_exception_mail
from apps.common.utils import get_msg,timestamp_toString
from apps.common.utils import get_uuid, check_openid
from apps.config.game_config import game_config
from apps.oclib import app
from apps.logics.gift import user_gift_record
import traceback
from apps.common.utils import get_upwd
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from base64 import b64decode
from Crypto.Hash import SHA
import hmac, hashlib
import urllib
import urllib2

_pub_rsa_key = open(settings.BASE_ROOT+'/apps/config/public.pem', "r").read()


def platform_auth(func):
    """ 修饰器，进行基于平台的账号校验

    根据参数中指定的平台，去相应的开放平台进行身份验证
    主要验证access_token以及openid
    """

    def new_func(request, *args, **argw):
        access_token = request.REQUEST.get('access_token', '')
        openid = request.REQUEST.get('openid', '')
        platform = request.REQUEST.get('platform', '')
        uuid = request.REQUEST.get("uuid", "")
        mktid = request.REQUEST.get("mktid", "")
        version = request.REQUEST.get("version", "1.0")
        client_type = request.REQUEST.get("client_type", "")
        # ios5以前用mac地址，ios6以后的用idfa
        macaddr = request.REQUEST.get("macaddr", "")
        idfa = request.REQUEST.get("idfa", "")
        ios_ver = request.REQUEST.get("ios_ver", "")

        if platform == 'oc':
            result,pid,msg = auth_token_for_oc(request, access_token, openid, uuid,
                                               mktid, version, client_type,macaddr,
                                               idfa, ios_ver)
            if not result:
                #print '##### failed to auth_token_for_oc, result, pid, msg=', result, pid, msg
                data = {
                    'rc': 3,
                    'data': {
                        'msg': msg,
                        'server_now': int(time.time())
                    }
                }
                return HttpResponse(
                    json.dumps(data, indent=1),
                    content_type='application/x-javascript',
                )
        else:
            result = False

            # 除360外， 必须需要 access_token, openid, platform
            # 2014/10/22: 现在 360, 只给 access_token ?
            if platform != '360' and (not access_token or not openid or not platform):
                #print '#### platform_auth, rc: 6'
                data = {
                    'rc': 6,    #缺参数
                    'data': {
                        'msg': get_msg('login', 'platform_overdue'),
                        'server_now': int(time.time())
                    }
                }
                return HttpResponse(
                    json.dumps(data, indent=1),
                    content_type='application/x-javascript',
                )
            
            auth_function = globals().get("auth_token_for_" + platform)

            if auth_function:
                result,pid = auth_function(request, access_token, openid, uuid,
                                           mktid, version, client_type,
                                           macaddr, idfa, ios_ver)

        if not result:
            #print '##### failed to auth_function, result, pid=', result, pid
            data = {
                'rc': 3,
                'data': {
                    'msg': get_msg('login', 'platform_overdue'),
                    'server_now': int(time.time())
                }
            }
            return HttpResponse(
                json.dumps(data, indent=1),
                content_type='application/x-javascript',
            )
        # 验证成功
        else:
            #检查用户是否处于冻结状态
            frozen_msg = get_frozen_msg(request.rk_user)
            if frozen_msg:
                data = {
                    'rc': 10,
                    'data': {
                        'msg': frozen_msg,
                        'server_now': int(time.time())
                    }
                }
                return HttpResponse(
                    json.dumps(data, indent=1),
                    content_type='application/x-javascript',
                )

            if platform != '360':
                Session.set(platform, pid)

        result = func(request, *args, **argw)
        return result
    return new_func


def platform_bind(func):
    """ 接口加上这个修饰将进行session验证"""
    def new_func(request,*args,**argw):
        # 用户在进行账号绑定时,需要与开放平台进行验证，主要验证access_token以及openid
        access_token = request.REQUEST.get('access_token','')
        openid = request.REQUEST.get('openid','')
        platform = request.REQUEST.get('platform','')
        bind_access_token = request.REQUEST.get('bind_access_token','')
        bind_openid = request.REQUEST.get('bind_openid','')

        if not access_token or not openid or not platform or not bind_access_token or not bind_openid:
            data = {'rc':6,'data':{'msg':get_msg('login','platform_overdue'),'server_now':int(time.time())}}
            return HttpResponse(
                json.dumps(data, indent=1),
                content_type='application/x-javascript',
            )
        if platform == 'qq':
            result,pid,msg = auth_bind_for_qq(request,access_token,openid,bind_access_token,bind_openid)
        elif platform == 'fb':
            result,pid,msg = auth_bind_for_fb(request,access_token,openid,bind_access_token,bind_openid)
        else:
            result,pid,msg = auth_bind_for_sina(request,access_token,openid,bind_access_token,bind_openid)
        if not result:
            data = {'rc':11,'data':{'msg':msg,'server_now':int(time.time())}}
            return HttpResponse(
                json.dumps(data, indent=1),
                content_type='application/x-javascript',
            )
        else:
            Session.set(platform, pid)
        result = func(request,*args,**argw)
        return result
    return new_func


def session_auth(func):
    """ 修饰器，session超时验证
    
    为防止玩家长时间没有进行平台验证，而此时玩家的账号口令
    可能已过期而导致的安全隐患。对每个玩家设置session，若
    session太过旧，需重新进行平台验证
    """

    def new_func(request, *args, **argw):
        para_pid = request.REQUEST.get('pid', None)
        para_platform = request.REQUEST.get('platform', None)

        session_overdue = False
        if para_platform is None or para_pid is None:
            session_overdue = True
        else:
            platform, pid = Session.get("{}:{}".format(para_platform, para_pid))
            if not platform or not pid or platform != para_platform or para_pid != pid:
                session_overdue = True

        #session过期
        if session_overdue:
            data = {
                'rc': 8,
                'data': {
                    'msg': get_msg('login', 'server_exception'),
                    'server_now': int(time.time())
                }
            }
            return HttpResponse(
                json.dumps(data, indent=1),
                content_type='application/x-javascript',
            )
        result = func(request, *args, **argw)
        return result
    return new_func


def signature_auth(func):
    """ 修饰器，进行request参数校验

    主要校验request的时间戳是否过旧
    参数的验证码是否正确
    """

    def new_func(request, *args, **argw):
        try:
            timestamp = request.REQUEST.get('timestamp')
            if not timestamp:
                data = {
                    'rc':6,
                    'data': {
                        'msg': get_msg('login', 'refresh'),
                        'server_now': int(time.time()),
                    }
                }
                return HttpResponse(
                    json.dumps(data, indent=1),
                    content_type='application/x-javascript',
                )
            # all_post_data  是 QueryDict 类型，详见：https://docs.djangoproject.com/en/1.4/ref/request-response/#django.http.QueryDict
            all_post_data = request.POST.copy()
            if 'signature' in all_post_data:
                all_post_data['signature'] = all_post_data['signature'].replace(' ', '+')

            debug_print('all_post_datas>>>>>>>>>>>>>>' + str(all_post_data))
            
            # 检查时间  时间戳超过一定时间后，视为过期请求
            if (time.time() - int(timestamp)) > settings.AUTH_AGE:
                data = {
                    'rc':1,
                    'data': {
                        'msg': get_msg('login', 'refresh'),
                        'server_now': int(time.time()),
                    }
                }
                print 'timestamp auth failed!', request.REQUEST.get('pid', 'none')
                return HttpResponse(
                    json.dumps(data, indent=1),
                    content_type='application/x-javascript',
                )

            # 检查验证码
            arg = all_post_data.pop('arg')[0]
            all_string = ''
            all_args = []
            for key, value in sorted(all_post_data.items()):
                all_args.append('%s=%s&' % (key, value))
            all_string = ''.join(all_args)

            local_arg = md5.md5(all_string.encode('utf-8') + settings.SIG_SECRET_KEY).hexdigest()[:10]
            # 签名认证不通过
            if False: #local_arg != arg:
                signature_fail = True
                if 'method' in request.REQUEST and request.REQUEST['method'] in ['main.set_name', 'pack.rename']:
                    signature_fail = False
                if signature_fail:
                    print 'signature auth failed!', request.REQUEST.get('pid', 'none')
                    data = {
                        'rc':1,
                        'data': {
                            'msg': get_msg('login', 'refresh'),
                            'server_now': int(time.time())
                        }
                    }
                    return HttpResponse(
                        json.dumps(data, indent=1),
                        content_type='application/x-javascript',
                    )
            # 认证通过
            result = func(request, *args, **argw)
            return result
        except:
            print_err()
            # 清空storage
            app.pier.clear()
            # send mail
            send_exception_mail(request)

            data = {
                'rc': 8,
                'data': {
                    'msg': get_msg('login', 'server_exception'),
                    'server_now': int(time.time())
                }
            }
            return HttpResponse(
                json.dumps(data, indent=1),
                content_type='application/x-javascript',
            )
    return new_func


def __get_uid(platform, openid, pid, subarea):
    """取得uid

    根据平台、openid等信息取得对应的uid

    Returns:
        玩家uid, 若没有符合条件的uid则返回空字符串
    """

    if not pid:
        if platform == 'oc':
            pid = openid
        else:
            pid = md5.md5(platform + str(openid)).hexdigest()
    ac = AccountMapping.get(pid)
    return ac.get_subarea_uid(subarea) if ac else ''


def maintenance_auth(func):
    """ 修饰器，维护期校验

    若游戏处于维护期，则只有指定的uid才可以登入
    """

    def new_func(request, *args, **argw):
        try:
            if game_config.system_config['maintenance']:
                pid = request.REQUEST.get('pid', '')
                platform = request.REQUEST.get('platform', '')
                openid = request.REQUEST.get('openid', '')
                subarea = request.REQUEST.get('subarea', '1')
                allow = False
                if platform and (pid or openid):
                    uid = __get_uid(platform, openid, pid, subarea)
                    if uid and uid in game_config.system_config.get('allow_uids', []):
                        allow = True
                if not allow:
                    data = {
                        'rc': 9,
                        'data': {
                            'msg': get_msg('login', 'maintenance'),
                            'server_now': int(time.time()),
                        }
                    }
                    return HttpResponse(
                        json.dumps(data, indent=1),
                        content_type='application/x-javascript',
                    )
            result = func(request, *args, **argw)
            return result
        except:
            print_err()
            app.pier.clear()
            #send mail
            send_exception_mail(request)
            data = {
                'rc': 8,
                'data': {
                    'msg': get_msg('login', 'server_exception'),
                    'server_now': int(time.time())
                }
            }
            return HttpResponse(
                json.dumps(data, indent=1),
                content_type='application/x-javascript',
            )
    return new_func


def set_user(func):
    """ 修饰器，取得并设置此次请求的发起者(userbase实例)

    通过参数中pid、subarea等获得UserBase实例代表
    此次请求的发起者，并加入到request实例中。
    若没有符合条件的UserBase，则代表是新手玩家，需新建userbase实例
    """

    def new_func(request,*args,**argw):
        pid = request.REQUEST.get("pid")
        platform = request.REQUEST.get("platform")
        subarea = request.REQUEST.get("subarea", "1")

        if pid and platform:
            request.rk_user = UserBase._install(pid, platform, subarea=subarea)
            frozen_msg = get_frozen_msg(request.rk_user)
            if frozen_msg:
                data = {
                    'rc': 10,
                    'data': {
                        'msg': frozen_msg,
                        'server_now': int(time.time())
                    }
                }
                return HttpResponse(
                    json.dumps(data, indent=1),
                    content_type='application/x-javascript',
                )
        else:
            #print '#### set_user, rc: 6'
            data = {
                'rc': 6,
                'data': {
                    'msg': get_msg('login', 'platform_overdue'),
                    'server_now': int(time.time())
                }
            }
            return HttpResponse(
                json.dumps(data, indent=1),
                content_type='application/x-javascript',
            )
        return func(request, *args, **argw)
    return new_func

def _bind_new_platform(request, platform_name, platform_openId, old_account, result):
    subarea = request.REQUEST.get("subarea", "1")
    fg = False
    msg = ''
    pid = md5.md5(platform_name + str(platform_openId)).hexdigest()
    #检查新账户是否已经被关联
    account_mapping_obj = AccountMapping.get(pid)
    if account_mapping_obj:
        msg = get_msg('login', 'already_bind')
        return fg, pid, msg
    #检查被绑定用户类型是否是oc
    old_user_obj = UserBase.get(old_account.get_subarea_uid(subarea))
    if old_user_obj.baseinfo['platform'] != 'oc':
        msg = get_msg('login', 'already_bind')
        return fg, pid, msg
    fg = True
    #创建新账户，将旧账户uid关联到新账户后，删除旧账户
    account_mapping_obj = AccountMapping.create(pid)
    account_mapping_obj.subarea_uids = old_account.subarea_uids
    account_mapping_obj.put()
    #删除oc账户
    old_account.delete()
    #给request安装用户
    request.rk_user = UserBase._install(pid, platform_name, subarea=subarea)
    request.rk_user.baseinfo['pid'] = pid
    request.rk_user.baseinfo['platform'] = platform_name
    request.rk_user.baseinfo['bind_time'] = int(time.time())
    request.rk_user.put()
    update_function = request.rk_user.update_platform_openid(platform_name, platform_openId)
    if update_function:
        update_function(result)
    return fg, pid, msg

def auth_token_for_qq(request,access_token,openid,uuid,mktid,version,client_type,macaddr,idfa,ios_ver):
    """论证qq开放平台
    """
    fg = False
    pid = ''
    subarea = request.REQUEST.get("subarea", "1")
    user_info_url = 'https://open.t.qq.com/api/user/info?format=json&oauth_consumer_key=%s&access_token=%s&openid=%s&oauth_version=2.a&scope=all' % (settings.QQ_APP_ID,access_token,openid)
    url_request = urllib2.urlopen(str(user_info_url), timeout=12)
    rc = url_request.code
    res  = url_request.read()

    if rc == 200:
        res = res.strip()
        res = res.replace('false','False')
        res = res.replace('true','True')
        res = res.replace('null','None')
        exec('result = %s' % res)
        if not result['ret']:
            get_openid = str(result['data']['openid'])
            if get_openid == openid:
                fg = True
                pid = md5.md5('qq' + str(openid)).hexdigest()
                #给request安装用户
                request.rk_user = UserBase._install(pid,'qq',uuid,mktid,version,client_type,macaddr,idfa,ios_ver, subarea=subarea)
                #数据校正
                if request.rk_user.baseinfo['platform'] != 'qq':
                    request.rk_user.baseinfo['platform'] = 'qq'
                #检查用户是否账户被冻结
                if not request.rk_user.frozen:
                    #更新用户的openid和access_token
                    request.rk_user.account.update_info(openid,access_token)
                    request.rk_user.update_user_from_qq(result)
    return fg,pid

def auth_bind_for_qq(request,access_token,openid,bind_access_token,bind_openid):
    """论证qq开放平台账号绑定
    """
    fg = False
    pid = ''
    msg = ''
    user_info_url = 'https://open.t.qq.com/api/user/info?format=json&oauth_consumer_key=%s&access_token=%s&openid=%s&oauth_version=2.a&scope=all' % (settings.QQ_APP_ID,access_token,openid)

    #检查被绑定的oneclick账号是否合法
    if not check_openid(bind_openid):
        msg = get_msg('login','invalid_bind')
        return fg,msg,pid
    account = AccountMapping.get(bind_openid)
    if account and account.access_token == bind_access_token:
        url_request = urllib2.urlopen(str(user_info_url), timeout=12)
        rc = url_request.code
        res  = url_request.read()
        res = res.strip()
        res = res.replace('false','False')
        res = res.replace('true','True')
        res = res.replace('null','None')
        if rc == 200:
            exec('result = %s' % res)
            if not result['ret']:
                get_openid = str(result['data']['openid'])
                if get_openid == openid:
                    fg, pid, msg = _bind_new_platform(request, 'qq', openid, account, result)
                    return fg, pid, msg
    else:
        msg = get_msg('login','invalid_bind')
    return fg,pid,msg

def auth_bind_for_sina(request,access_token,openid,bind_access_token,bind_openid):
    """论证sina开放平台账号绑定
    """
    fg = False
    pid = ''
    msg = ''
    SINA_OPEN_URL = 'https://api.weibo.com/2/account/get_uid.json'
    request_url = '%s?access_token=%s' % (SINA_OPEN_URL, str(access_token))
    user_info_url = 'https://api.weibo.com/2/users/show.json?access_token=%s&uid=%s'

    #检查被绑定的oneclick账号是否合法
    if not check_openid(bind_openid):
        msg = get_msg('login','invalid_bind')
        return fg,msg,pid
    account = AccountMapping.get(bind_openid)
    if account and account.access_token == bind_access_token:
        url_request = urllib2.urlopen(request_url, timeout=12)
        rc = url_request.code
        res  = url_request.read()
        if rc == 200:
            res = res.strip()
            res = res.replace('false','False')
            res = res.replace('true','True')
            res = res.replace('null','None')
            exec('result = %s' % res)
            get_openid = str(result.get('uid'))
            if get_openid == openid:
                fg, pid, msg = _bind_new_platform(request, 'sina', openid, account, result)

                #调用平台的api，取得用户名等信息，并且更新
                user_info_url = user_info_url % (str(access_token),str(openid))
                #更新用户平台信息不影响绑定操作
                try:
                    res = urllib2.urlopen(str(user_info_url), timeout=12).read()
                    res = res.strip()
                    res = res.replace('false','False')
                    res = res.replace('true','True')
                    res = res.replace('null','None')
                    exec('result = %s' % res)
                    request.rk_user.update_user_from_sina(result)
                except:
                    pass
                return fg,pid,msg
    else:
        msg = get_msg('login','invalid_bind')
    return fg,pid,msg


#def auth_token_for_360____old(request,access_token,openid,uuid,mktid,version,client_type,macaddr,idfa,ios_ver):
#   #old before 2014/10/22
#    fg = False
#    pid = ''
#    subarea = request.REQUEST.get("subarea", "1")
#    #360平台验证
#    if not 'authorizationCode' in request.REQUEST:
#        return fg, pid
#    else:
#        authorizationCode = str(request.REQUEST['authorizationCode'])
#
#    platform = str(request.REQUEST['platform'])
#    if authorizationCode:
#        client_secret = settings.APP_SECRET_KEY_360
#        client_id = settings.APP_KEY_360
#        url_360 = 'https://openapi.360.cn'
#        code_url = '%s/oauth2/access_token?grant_type=authorization_code&code=%s&client_id=%s&client_secret=%s&redirect_uri=oob' % (url_360, authorizationCode, client_id, client_secret)
#        url_request = urllib2.urlopen(code_url, timeout=12)
#        code, res = url_request.code, url_request.read()
#
#        if code == 200:
#            res_dict = json.loads(res)
#            access_token = str(res_dict['access_token'])
#            refresh_token = str(res_dict['refresh_token'])
#            expires_in = float(res_dict['expires_in'])
#            access_token_url = '%s/user/me.json?access_token=%s&fields=id,name,avatar,sex,area' % (url_360, access_token)
#            token_res = urllib2.urlopen(str(access_token_url), timeout=12).read()
#            fg = True
#            res_dict = json.loads(token_res)
#            openid = str(res_dict['id'])
#            pid = md5.md5('360' + openid).hexdigest()
#            request.rk_user = UserBase._install(pid, platform,uuid,mktid,version,client_type,macaddr,idfa,ios_ver, subarea=subarea)
#            #检查用户是否账户被冻结
#            if not request.rk_user.frozen:
#                #更新用户的openid和access_token
#                request.rk_user.account.update_info(openid,access_token)
#                request.rk_user.update_user_from_360(res_dict)
#                expires_time = time.time() + expires_in
#                Session.set(platform, pid, access_token, refresh_token, expires_time)
#    return fg,pid


def auth_token_for_360(request,access_token,openid,uuid,mktid,version,client_type,macaddr,idfa,ios_ver):
    #print '##### in auth_token_for_360'
    fg = False
    pid = ''
    subarea = request.REQUEST.get("subarea", "1")

    #360平台验证
    if not 'access_token' in request.REQUEST:
        return fg, pid
    else:
        access_token = str(request.REQUEST['access_token'])

    platform = str(request.REQUEST['platform'])
    if access_token:
        url_360 = 'https://openapi.360.cn/user/me.json'
        code_url = '%s?access_token=%s&fields=id,name,avatar,sex,area' % (url_360, access_token)
        url_request = urllib2.urlopen(code_url, timeout=12)
        code, res = url_request.code, url_request.read()

        #print '#### 360, code, res=', code, res
        #可能360不需要refresh_token ?
        #refresh_token = str(request.REQUEST['refresh_token'])
        refresh_token = ''
        #print '#### refresh_token=', refresh_token
        #expires_in = float(request.REQUEST['expires_in'])  # "['123.45']" ?
        #print '#### expires_in=', request.REQUEST['expires_in']
        expires_in = 24*3600

        if code == 200:
            res_dict = json.loads(res)
            #print '#### 360, res_dict=', res_dict

            fg = True
            openid = str(res_dict['id'])
            pid = md5.md5('360' + openid).hexdigest()
            request.rk_user = UserBase._install(pid, platform,uuid,mktid,version,client_type,macaddr,idfa,ios_ver, subarea=subarea)
            #检查用户是否账户被冻结
            if not request.rk_user.frozen:
                #更新用户的openid和access_token
                request.rk_user.account.update_info(openid,access_token)
                request.rk_user.update_user_from_360(res_dict)
                expires_time = time.time() + expires_in

                #print '##### 360 start set session'
                Session.set(platform, pid, access_token, refresh_token, expires_time)
    return fg,pid

def auth_token_for_sina(request,access_token,openid,uuid,mktid,version,client_type,macaddr,idfa,ios_ver):
    """论证新浪开放平台
    """
    fg = False
    pid = ''
    subarea = request.REQUEST.get("subarea", "1")
    SINA_OPEN_URL = 'https://api.weibo.com/2/account/get_uid.json'
    request_url = '%s?access_token=%s' % (SINA_OPEN_URL, str(access_token))
    user_info_url = 'https://api.weibo.com/2/users/show.json?access_token=%s&uid=%s'
    url_request = urllib2.urlopen(request_url, timeout=12)
    rc,res = url_request.code, url_request.read()
    if rc == 200:
        res = res.strip()
        res = res.replace('false','False')
        res = res.replace('true','True')
        res = res.replace('null','None')
        exec('result = %s' % res)
        get_openid = str(result.get('uid'))
        if get_openid == openid:
            fg = True
            pid = md5.md5('sina' + str(openid)).hexdigest()
            #给request安装用户
            request.rk_user = UserBase._install(pid,'sina',uuid,mktid,version,client_type,macaddr,idfa,ios_ver, subarea=subarea)
            #数据校正
            if request.rk_user.baseinfo['platform'] != 'sina':
                request.rk_user.baseinfo['platform'] = 'sina'
            #检查用户是否账户被冻结
            if not request.rk_user.frozen:
                #更新用户的openid和access_token
                request.rk_user.account.update_info(openid,access_token)
                #调用平台的api，取得用户名等信息，并且更新，但非必须
                try:
                    user_info_url = user_info_url % (str(access_token),str(openid))
                    res = urllib2.urlopen(str(user_info_url), timeout=12).read()
                    res = res.strip()
                    res = res.replace('false','False')
                    res = res.replace('true','True')
                    res = res.replace('null','None')
                    exec('result = %s' % res)
                    request.rk_user.update_user_from_sina(result)
                except:
                    pass
    return fg,pid

def auth_bind_for_fb(request,access_token,openid,bind_access_token,bind_openid):
    """论证fb开放平台账号绑定
    """
    fg = False
    pid = ''
    msg = ''
    user_info_url = 'https://graph.facebook.com/me?access_token=%s' % str(access_token)

    #检查被绑定的oneclick账号是否合法
    url_request = urllib2.urlopen(str(user_info_url), timeout=12)
    rc,res = url_request.code, url_request.read()
    res = res.strip()
    res = res.replace('false','False')
    res = res.replace('true','True')
    res = res.replace('null','None')
    #检查被绑定的oneclick账号是否合法
    if not check_openid(bind_openid):
        msg = get_msg('login','invalid_bind')
        return fg,pid,msg
    account = AccountMapping.get(bind_openid)
    if account and account.access_token == bind_access_token:
        url_request = urllib2.urlopen(str(user_info_url), timeout=12)
        rc,res = url_request.code, url_request.read()
        if rc == 200:
            res = res.strip()
            res = res.replace('false','False')
            res = res.replace('true','True')
            res = res.replace('null','None')
            exec('result = %s' % res)
            get_openid = str(result.get('id'))
            if get_openid == openid:
                fg, pid, msg = _bind_new_platform(request, 'fb', openid, account, result)
                return fg,pid,msg
    else:
        msg = get_msg('login','invalid_bind')
    return fg,pid,msg

def auth_token_for_fb(request,access_token,openid,uuid,mktid,version,client_type,macaddr,idfa,ios_ver):
    """论证fb开放平台
    """
    fg = False
    pid = ''
    subarea = request.REQUEST.get("subarea", "1") or '1'
    user_info_url = 'https://graph.facebook.com/me?access_token=%s' % str(access_token)
    res = urllib2.urlopen(user_info_url, timeout=12).read()
    res = res.strip()
    res = res.replace('false','False')
    res = res.replace('true','True')
    res = res.replace('null','None')
    exec('result = %s' % res)
    if 'error' not in result:
        get_openid = str(result.get('id'))
        openid = get_openid
        if get_openid == openid:
            fg = True
            pid = md5.md5('fb' + str(openid)).hexdigest()
            #给request安装用户
            request.rk_user = UserBase._install(pid,'fb',uuid,mktid,version,client_type,macaddr,idfa,ios_ver, subarea=subarea)
            #数据校正
            if request.rk_user.baseinfo['platform'] != 'fb':
                request.rk_user.baseinfo['platform'] = 'fb'
            #检查用户是否账户被冻结
            if not request.rk_user.frozen:
                #更新用户的openid和access_token
                request.rk_user.account.update_info(openid,access_token)
                # request.rk_user.update_user_from_fb(result)
    return fg,pid

def auth_token_for_oc(request,access_token,openid,uuid,mktid,version,client_type,macaddr,idfa,ios_ver):
    """论证无账号用户
    """
    print "debug_guochen access_token, openid", access_token, openid
    fg = False
    pid = ''
    msg = ''
    subarea = request.REQUEST.get("subarea", "1") or '1'
    #没有openid时，检查后控制自动分配id的开头是否开启，如果已经关闭，返回提示
    if not openid:
       if game_config.system_config.get('account_assign_switch'):
           fg = True
           pid = get_uuid()
           #验证成功，安装用户
           request.rk_user = UserBase._install(pid,'oc',uuid,mktid,version,client_type,macaddr,idfa,ios_ver, subarea=subarea)
           access_token = get_upwd()
           request.rk_user.account.update_info(pid, access_token)
       else:
           msg = get_msg('login','cannot_register')
           return fg,pid,msg
    if not check_openid(openid):
        msg = get_msg('login','cannot_register')
        return fg,pid,msg
    #有openid时，检查access_token是否正确
    account = AccountMapping.get(openid)
    if not account: 
        if game_config.system_config.get('account_assign_switch'):
            fg = True
            pid = openid
            #验证成功，安装用户
            request.rk_user = UserBase._install(pid,'oc',uuid,mktid,version,client_type,macaddr,idfa,ios_ver, subarea=subarea)
            # debug 模式下，将传入的access_token 作为新用户taken
            if settings.DEBUG is True:
                access_token = access_token or get_upwd()
            else:
                access_token = get_upwd()
            request.rk_user.account.update_info(pid, access_token)
            account = request.rk_user.account
            print "debug_guochen_new_token pid, access_token, openid", pid, access_token, openid
        else:
            msg = get_msg('login','cannot_register')
            return fg,pid,msg

    elif account.access_token == access_token:
        fg = True
        pid = openid
        #验证成功，安装用户
        request.rk_user = UserBase._install(pid, 'oc', subarea=subarea)
    else:
        print "debug_guochen_erro_token pid, access_token, openid", pid, access_token, openid
        msg = get_msg('login','session_overdue')
    return fg,pid,msg

def auth_token_for_mi(request,access_token,openid,uuid,mktid,version,client_type,macaddr,idfa,ios_ver):
    fg = False
    pid = ''
    subarea = request.REQUEST.get("subarea", "1")
    #mi平台验证 

    client_id = settings.MI_APP_ID
    url_mi = 'http://mis.migc.xiaomi.com/api/biz/service/verifySession.do'
    ready_signature = 'appId=%s&session=%s&uid=%s' % (client_id, access_token, openid)

    signature = hmac.new(settings.MI_SECRET_KEY, ready_signature, hashlib.sha1).hexdigest()

    data = dict(    
        appId = client_id,
        session = access_token,
        uid = openid,
        signature = signature,
    )
    pairs = urllib.urlencode(data)
    code_url = url_mi + '?' + pairs
    url_request = urllib2.urlopen(code_url, timeout=12)
    code, res = url_request.code, url_request.read()
    res_dict = json.loads(res)
    if code == 200 and res_dict['errcode'] == 200:

        pid = md5.md5('mi' + str(openid)).hexdigest()
        request.rk_user = UserBase._install(pid, 'mi',uuid,mktid,version,client_type,macaddr,idfa,ios_ver, subarea=subarea)
        #数据校正
        if request.rk_user.baseinfo['platform'] != 'mi':
            request.rk_user.baseinfo['platform'] = 'mi'
        #检查用户是否账户被冻结
        if not request.rk_user.frozen:
            #更新用户的openid和access_token
            request.rk_user.account.update_info(openid,access_token)
            res_dict['openid'] = openid
            request.rk_user.update_user_from_mi(res_dict)
        fg = True
    return fg, pid

def auth_token_for_pp(request,access_token,openid,uuid,mktid,version,client_type,macaddr,idfa,ios_ver):
    fg = False
    pid = ''
    subarea = request.REQUEST.get("subarea", "1")

    pp_url = 'http://passport_i.25pp.com:8080/index?tunnel-command=2852126756'
    headers = {"Host":"passport_i.25pp.com","Content-Length":"32"}
    req = urllib2.Request(pp_url, str(access_token))
    url_request = urllib2.urlopen(req, timeout=12)
    rc, res = url_request.code, url_request.read()
    if rc != 200:
        return fg, pid 
    res = res.strip()
    res = "{" + res + "}"
    result = {}
    exec('result = %s' % res)
    status = result.get('status', 1)
    if status != 0:
        return fg, pid
    
    get_openid = str(result.get('userid'))
    if get_openid != openid:
        return fg, pid
    pid = md5.md5('pp' + str(openid)).hexdigest()
    request.rk_user = UserBase._install(pid, 'pp',uuid,mktid,version,client_type,macaddr,idfa,ios_ver, subarea=subarea)
    #数据校正
    if request.rk_user.baseinfo['platform'] != 'pp':
        request.rk_user.baseinfo['platform'] = 'pp'
    #检查用户是否账户被冻结
    if not request.rk_user.frozen:
        #更新用户的openid和access_token
        request.rk_user.account.update_info(openid,access_token)
        request.rk_user.update_user_from_pp(get_openid)
    fg = True
    return fg, pid

def auth_token_for_91(request,access_token,openid,uuid,mktid,version,client_type,macaddr,idfa,ios_ver):
    """验证91平台
    """
    fg = False
    pid = ''
    subarea = request.REQUEST.get("subarea", "1")
    OPEN_URL = 'http://service.sj.91.com/usercenter/AP.aspx'
    #request_url = '%s?AppId=%s&Act=4&Uin=%s&SessionId=%s&Sign=%s'
    sign = md5.new(settings.APP_ID_91 + '4' + openid + access_token\
     + settings.APP_KEY_91).hexdigest()
    data = dict(    
        AppId = settings.APP_ID_91,
        Act = '4',
        Uin = openid,
        SessionId = access_token,
        Sign = sign,
    )
    pairs = urllib.urlencode(data)
    request_url = OPEN_URL + '?' + pairs
    url_request = urllib2.urlopen(request_url, timeout=12)
    rc,res = url_request.code, url_request.read()
    res_dict = json.loads(res)
    if rc == 200 and res_dict['ErrorCode'] == '1':
        fg = True
        pid = md5.md5('91'+str(openid)).hexdigest()
        #给request安装用户
        request.rk_user = UserBase._install(pid, '91',uuid,mktid,version,client_type,macaddr,idfa,ios_ver, subarea=subarea)
        #检查用户是否账户被冻结
        if not request.rk_user.frozen:
            #更新用户的openid和access_token
            request.rk_user.account.update_info(openid,access_token)
            #更新用户平台信息
            request.rk_user.update_user_from_91(openid)
    return fg,pid

def get_frozen_msg(rk_user):
    """检查是否是冻结用户
    """
    #如果用户被冻结，返回
    msg = ''
    if rk_user.baseinfo.get('frozen'):
        msg = get_msg('login','frozen') % rk_user.uid
        return msg
    #如果用户是暂时冻结,提示
    unfroze_time = rk_user.baseinfo.get('unfroze_time')
    if unfroze_time and int(time.time()) < unfroze_time:
        msg = get_msg('login','frozen_time')
        frozen_days = 2 if rk_user.baseinfo.get('frozen_count',0) == 1 else 7
        msg = msg % (frozen_days,timestamp_toString(unfroze_time,'%m.%d %H:%M'),rk_user.uid)
    return msg


def server_close_auth(func):
    """服务关闭，发送新版的礼品码

    # TODO(GuoChen) 未知的功能，待删除
    """
    def new_func(request,*args,**argw):
        if game_config.system_config.get('server_close'):
            uid = request.rk_user.uid
            
            data = {'rc':14,'data':{'msg':get_msg('login','server_close'),'server_now':int(time.time())}}
            gift_code = user_gift_record.get(uid,[])
            if gift_code:
                data['data']['gift_code'] = gift_code
            return HttpResponse(
                json.dumps(data, indent=1),
                content_type='application/x-javascript',
            )
        else:
            return func(request,*args,**argw)
    return new_func


def verify_key(func):
    #"""
    #测试验签
    #"""
    def new_func(request,*args,**argw):
        try:
            params = request.REQUEST
            oid = params.get('oid','')
            signature = params.get('sign','')
            key = RSA.importKey(_pub_rsa_key)
            h = SHA.new(str(oid))
            verifier = PKCS1_v1_5.new(key)
            if verifier.verify(h, b64decode(signature)):
                result = func(request,*args,**argw)
                return result
        except:
            send_exception_mail(request)
            print_err()
            #清空storage
            app.pier.clear()
        return HttpResponse(
              json.dumps({'rc':8,'data':{'msg':get_msg('login','server_exception'),'server_now':int(time.time())}}, indent=1),
              content_type='application/x-javascript',)
    return new_func 
