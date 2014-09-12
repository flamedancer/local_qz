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
    """ 接口加上这个修饰将进行平台验证"""
    def new_func(request,*args,**argw):
        # 用户在首次登陆时或再次登陆访问时（大多数情况下是访问/路径时）
        # 需要与开放平台进行验证，主要验证access_token以及openid
        access_token = request.REQUEST.get('access_token','')
        openid = request.REQUEST.get('openid','')
        platform = request.REQUEST.get('platform','')
        uuid = request.REQUEST.get("uuid", "")
        mktid = request.REQUEST.get("mktid", "")
        version = request.REQUEST.get("version", "1.0")
        client_type = request.REQUEST.get("client_type", "")
        #ios5以前用mac地址，ios6以后的用idfa
        macaddr = request.REQUEST.get("macaddr", "")
        idfa = request.REQUEST.get("idfa", "")
        ios_ver = request.REQUEST.get("ios_ver", "")

        if platform == 'oc':
            result,pid,msg = auth_token_for_oc(request,access_token,openid,uuid,\
                                               mktid,version,client_type,macaddr,idfa,ios_ver)
            if not result:
                data = {'rc':3,'data':{'msg':msg,'server_now':int(time.time())}}
                return HttpResponse(
                    json.dumps(data, indent=1),
                    content_type='application/x-javascript',
                )
        else:
            if platform != '360' and (not access_token or not openid or not platform):
                data = {'rc':6,'data':{'msg':get_msg('login','platform_overdue'),'server_now':int(time.time())}}
                return HttpResponse(
                    json.dumps(data, indent=1),
                    content_type='application/x-javascript',
                )
            try:
                if platform == 'qq':
                    result,pid = auth_token_for_qq(request,access_token,openid,uuid,\
                                                   mktid,version,client_type,macaddr,idfa,ios_ver)
                elif platform == 'fb':
                    result,pid = auth_token_for_fb(request,access_token,openid,uuid,\
                                                   mktid,version,client_type,macaddr,idfa,ios_ver)
                elif platform == 'sina':
                    result,pid = auth_token_for_sina(request,access_token,openid,uuid,\
                                                     mktid,version,client_type,macaddr,idfa,ios_ver)
                elif platform == '360':
                    result,pid = auth_token_for_360(request,access_token,openid,uuid,\
                                                    mktid,version,client_type,macaddr,idfa,ios_ver)
                elif platform == '91':
                    result,pid = auth_token_for_91(request,access_token,openid,uuid,\
                                                   mktid,version,client_type,macaddr,idfa,ios_ver)
                elif platform == 'mi':
                    result,pid = auth_token_for_mi(request,access_token,openid,uuid,\
                                                    mktid,version,client_type,macaddr,idfa,ios_ver)
                elif platform == 'pp':
                    result,pid = auth_token_for_pp(request,access_token,openid,uuid,\
                                                    mktid,version,client_type,macaddr,idfa,ios_ver)
                else:
                    result = False
                    pid = ''
            except:
                result = False
                pid = ''
        if not result:
            data = {'rc':3,'data':{'msg':get_msg('login','platform_overdue'),'server_now':int(time.time())}}
            return HttpResponse(
                json.dumps(data, indent=1),
                content_type='application/x-javascript',
            )
        #验证成功
        else:
            #检查用户是否处于冻结状态
            frozen_msg = get_frozen_msg(request.rk_user)
            if frozen_msg:
                data = {'rc':10,'data':{'msg':frozen_msg,'server_now':int(time.time())}}
                return HttpResponse(
                    json.dumps(data, indent=1),
                    content_type='application/x-javascript',
                )
            if platform != '360':
                Session.set(platform, pid)
            #更新版本号
#            if request.rk_user.current_version<float(version):
#                request.rk_user.baseinfo["current_version"] = float(version)
#                request.rk_user.put()
        result = func(request,*args,**argw)
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
    """ 接口加上这个修饰将进行session验证"""
    def new_func(request,*args,**argw):
        #此装饰器用于对api的请求，验证session
        para_pid = request.REQUEST.get('pid',None)
        para_platform = request.REQUEST.get('platform',None)

        session_overdue = False
        if para_platform is None or para_pid is None:
            session_overdue = True
        platform,pid = Session.get(para_platform+':'+para_pid)
        if not platform or not pid or platform != para_platform or para_pid != pid:
            session_overdue = True

        #session过期
        if session_overdue:
            data = {'rc':8,'data':{'msg':get_msg('login','server_exception'),'server_now':int(time.time())}}
            return HttpResponse(
                json.dumps(data, indent=1),
                content_type='application/x-javascript',
            )
        result = func(request,*args,**argw)
        return result
    return new_func

def signature_auth(func):
    """ 接口加上这个修饰将进行session验证"""
    def new_func(request,*args,**argw):
        #此装饰器用于对api的请求，验证客户端签名
        try:
            timestamp = request.REQUEST.get('timestamp')
            if not timestamp:
                data = {'rc':6,'data':{'msg':get_msg('login','refresh'),'server_now':int(time.time())}}
                return HttpResponse(
                    json.dumps(data, indent=1),
                    content_type='application/x-javascript',
                )
            all_post_datas = request.POST
            all_post_datas_copy = {}
            for _key in all_post_datas:
                if _key == 'signature':
                    all_post_datas_copy[_key] = all_post_datas[_key].replace(' ','+')
                else:
                    all_post_datas_copy[_key] = all_post_datas[_key]

            debug_print('all_post_datas>>>>>>>>>>>>>>'+str(all_post_datas_copy))
            arg = all_post_datas_copy.pop('arg')
            all_string = ''
            for _key in sorted(all_post_datas_copy.keys()):
                all_string += '%s=%s&' % (_key,all_post_datas_copy[_key])
            #时间戳超过一定时间后，论证不通过
            if abs(time.time() - int(timestamp)) > settings.AUTH_AGE:
                data = {'rc':1,'data':{'msg':get_msg('login','refresh'),'server_now':int(time.time())}}
                print 'timestamp auth failed!',request.REQUEST.get('pid','none')
                return HttpResponse(
                    json.dumps(data, indent=1),
                    content_type='application/x-javascript',
                )
            local_arg = md5.md5(all_string.encode('utf-8') + settings.SIG_SECRET_KEY).hexdigest()[:10]
            #签名认证不通过
            if local_arg != arg:
                path = request.META.get('PATH_INFO')
                signature_fail = True
                if 'method' in request.REQUEST and request.REQUEST['method'] in ['main.set_signature']:
                    signature_fail = False
                elif path == '/tutorial/' and request.REQUEST.get('step') == '1':
                    signature_fail = False
                if signature_fail:
                    print 'signature auth failed!',request.REQUEST.get('pid','none')
                    data = {'rc':1,'data':{'msg':get_msg('login','refresh'),'server_now':int(time.time())}}
                    #data = {'rc':100,'msg':u'系统检测到您在非法操作，请停止这种行为，以免账户冻结'}
                    return HttpResponse(
                        json.dumps(data, indent=1),
                        content_type='application/x-javascript',
                    )
            #认证通过
            result = func(request,*args,**argw)
            return result
        except:
            print_err()
            #清空storage
            app.pier.clear()
            #send mail
            send_exception_mail(request)

            data = {'rc':8,'data':{'msg':get_msg('login','server_exception'),'server_now':int(time.time())}}
            return HttpResponse(
                json.dumps(data, indent=1),
                content_type='application/x-javascript',
            )
    return new_func

def __get_uid(platform, openid, pid, subarea):
    '''
    取得uid
    '''
    if not pid:
        if platform == 'oc':
            pid = openid
        else:
            pid = md5.md5(platform + str(openid)).hexdigest()
    ac = AccountMapping.get(pid)
    return ac.get_subarea_uid(subarea) if ac else ''

def maintenance_auth(func):
    """ 接口加上这个修饰将进行游戏维护验证"""
    def new_func(request,*args,**argw):
        try:
            if game_config.system_config['maintenance']:
                pid = request.REQUEST.get('pid','')
                platform = request.REQUEST.get('platform','')
                openid = request.REQUEST.get('openid','')
                subarea = request.REQUEST.get('subarea', '1')
                allow = False
                if platform and (pid or openid):
                    uid = __get_uid(platform, openid, pid, subarea)
                    if uid and uid in game_config.system_config.get('allow_uids',[]):
                        allow = True
                if not allow:
                    data = {'rc':9,'data':{'msg':get_msg('login','maintenance'),'server_now':int(time.time())}}
                    return HttpResponse(
                        json.dumps(data, indent=1),
                        content_type='application/x-javascript',
                    )
            result = func(request,*args,**argw)
            return result
        except:
            print_err()
            app.pier.clear()
            #send mail
            send_exception_mail(request)
            data = {'rc':8,'data':{'msg':get_msg('login','server_exception'),'server_now':int(time.time())}}
            return HttpResponse(
                json.dumps(data, indent=1),
                content_type='application/x-javascript',
            )
    return new_func

def needuser(func):
    """ 接口加上这个修饰将安装用户，需要先验证"""
    def new_func(request,*args,**argw):
        pid = request.REQUEST.get("pid")
        platform = request.REQUEST.get("platform")
        subarea = request.REQUEST.get("subarea", "1")

        if pid and platform:
            #调用UserBase的install方法安装用户
            request.rk_user = UserBase._install(pid, platform, subarea=subarea)
            frozen_msg = get_frozen_msg(request.rk_user)
            if frozen_msg:
                data = {'rc':10,'data':{'msg':frozen_msg,'server_now':int(time.time())}}
                return HttpResponse(
                    json.dumps(data, indent=1),
                    content_type='application/x-javascript',
                )
        else:
            data = {'rc':6,'data':{'msg':get_msg('login','platform_overdue'),'server_now':int(time.time())}}
            return HttpResponse(
                json.dumps(data, indent=1),
                content_type='application/x-javascript',
            )
        return func(request,*args,**argw)
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
    update_function = getattr(request.rk_user, "update_user_from_" + platform_name)
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

def auth_token_for_360(request,access_token,openid,uuid,mktid,version,client_type,macaddr,idfa,ios_ver):
    fg = False
    pid = ''
    subarea = request.REQUEST.get("subarea", "1")
    #360平台验证
    if not 'authorizationCode' in request.REQUEST:
        return fg, pid
    else:
        authorizationCode = str(request.REQUEST['authorizationCode'])

    platform = str(request.REQUEST['platform'])
    if authorizationCode:
        client_secret = settings.APP_SECRET_KEY_360
        client_id = settings.APP_KEY_360
        url_360 = 'https://openapi.360.cn'
        code_url = '%s/oauth2/access_token?grant_type=authorization_code&code=%s&client_id=%s&client_secret=%s&redirect_uri=oob' % (url_360, authorizationCode, client_id, client_secret)
        url_request = urllib2.urlopen(code_url, timeout=12)
        code, res = url_request.code, url_request.read()

        if code == 200:
            res_dict = json.loads(res)
            access_token = str(res_dict['access_token'])
            refresh_token = str(res_dict['refresh_token'])
            expires_in = float(res_dict['expires_in'])
            access_token_url = '%s/user/me.json?access_token=%s&fields=id,name,avatar,sex,area' % (url_360, access_token)
            token_res = urllib2.urlopen(str(access_token_url), timeout=12).read()
            fg = True
            res_dict = json.loads(token_res)
            openid = str(res_dict['id'])
            pid = md5.md5('360' + openid).hexdigest()
            request.rk_user = UserBase._install(pid, platform,uuid,mktid,version,client_type,macaddr,idfa,ios_ver, subarea=subarea)
            #检查用户是否账户被冻结
            if not request.rk_user.frozen:
                #更新用户的openid和access_token
                request.rk_user.account.update_info(openid,access_token)
                request.rk_user.update_user_from_360(res_dict)
                expires_time = time.time() + expires_in
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
    subarea = request.REQUEST.get("subarea", "1")
    user_info_url = 'https://graph.facebook.com/me?access_token=%s' % str(access_token)
    res = urllib2.urlopen(user_info_url, timeout=12).read()
    res = res.strip()
    res = res.replace('false','False')
    res = res.replace('true','True')
    res = res.replace('null','None')
    exec('result = %s' % res)
    if 'error' not in result:
        get_openid = str(result.get('id'))
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
                request.rk_user.update_user_from_fb(result)
    return fg,pid

def auth_token_for_oc(request,access_token,openid,uuid,mktid,version,client_type,macaddr,idfa,ios_ver):
    """论证无账号用户
    """
    fg = False
    pid = ''
    msg = ''
    subarea = request.REQUEST.get("subarea", "1")
    #没有openid时，检查后控制自动分配id的开头是否开启，如果已经关闭，返回提示
#    if not openid:
#        if game_config.system_config.get('account_assign_switch'):
#            fg = True
#            pid = get_uuid()
#            #验证成功，安装用户
#            request.rk_user = UserBase._install(pid,'oc',uuid,mktid,version,client_type,macaddr,idfa,ios_ver, subarea=subarea)
#            access_token = get_upwd()
#            request.rk_user.account.update_info(pid, access_token)
#        else:
#            msg = get_msg('login','cannot_register')
#            return fg,pid,msg
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
            access_token = get_upwd()
            request.rk_user.account.update_info(pid, access_token)
            account = request.rk_user.account
        else:
            msg = get_msg('login','cannot_register')
            return fg,pid,msg

    if account and account.access_token == access_token:
        fg = True
        pid = openid
        #验证成功，安装用户
        request.rk_user = UserBase._install(pid, 'oc', subarea=subarea)
    else:
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
