#-*- coding: utf-8 -*-


import os
#import  json
from django.core.mail import send_mail
from apps.admin.models import Moderator
#import md5
import hashlib
from django.conf import settings
from django.http import HttpResponse,HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from apps.models import pvp_redis
from apps.models.config import Config
import apps.admin.auth
from apps.admin.decorators import require_permission
from apps.admin.views.forms import  ModeratorCreationForm,ModeratorManageForm,ModeratorResetPasswordForm
from apps.config.config_version import config_update
from apps.admin import admin_configuration
import datetime
import random
from apps.models.user_real_pvp import UserRealPvp
from apps.models.user_base import UserBase
from apps.models.gift_code import GiftCode
from apps.models.data_log_mod import ConfigHistory
from apps.config.game_config import game_config
import commands
import tempfile
from apps.admin.views.check_config_error import check_config_error

from apps.models.user_property import lv_top_model, UserProperty
from apps.admin.models import UpdateConfRecord
from apps.config import config_list
from apps.config.backup import show_config_backup
from apps.models.redis_tool import RedisTool

from apps.admin.views import RedisCaptcha
# captchaFactory = RedisCaptcha.Factory()
# from apps.admin.views.RedisCaptcha.Visual import Tests as captchaTests
import StringIO


def index(request):
    moderator = apps.admin.auth.get_moderator_by_request(request)
    if moderator is None:
        return HttpResponseRedirect("/admin/login/")
    else:
        return HttpResponseRedirect("/admin/main/")


def login(request):
    """
        首页，登录用
    """
    appname = settings.APP_NAME
    if request.method == "POST":
        username = request.POST.get("username")
        password = hashlib.md5(request.POST.get("password")).hexdigest()
        if not username or not password:
            return render_to_response("admin/login.html",{'status':1,"appname":appname},RequestContext(request))
        mid = apps.admin.auth.get_mid_by_username(username)
        if mid is None:
            return render_to_response("admin/login.html",{"status":2,"appname":appname},RequestContext(request))
        moderator = apps.admin.auth.get_moderator(mid)
        if moderator is None:
            return render_to_response("admin/login.html",{"status":2,"appname":appname},RequestContext(request))
        if not moderator.is_staff:
            return render_to_response("admin/login.html",{"status":4,"appname":appname},RequestContext(request))
        if moderator.check_password(password):
            response = HttpResponseRedirect("/admin/main/")
            apps.admin.auth.login(request,response,moderator)
            return response
        else:
            return render_to_response("admin/login.html",{"status":3,"appname":appname},RequestContext(request))
    else:
        return render_to_response("admin/login.html",{"appname":appname},RequestContext(request))


def registration(request):
    """
    注册帐号
    """
    username = request.POST.get("username")
    realname = request.POST.get("realname")
    password = request.POST.get("password")
    password2 = request.POST.get("password2")
    email = request.POST.get("email")
    email_verify_code = request.POST.get("email_verify_code")

    if not username or not password:
        return render_to_response("admin/registration.html",{"appname":'a'},RequestContext(request))

    elif not realname:
        return HttpResponse(u"真实姓名必填")

    elif not email:
        return HttpResponse(u"email必填")

    # elif not email_verify_code:
    #     return HttpResponse(u"Email确认码必填")

    # elif not verify_email_code (email, email_verify_code.strip()):
    #     return HttpResponse(u"Email确认码不对")

    elif not password or password != password2:
        return HttpResponse(u"密码为空，　或两次密码不同")

    else:
        moderator = Moderator.get(username)
        if moderator:
            return HttpResponse("该用户名已经存在，可以员工编号做为后缀")
        else:
            #测试开发期间，暂时允许同一个Email, 可以建多个 login name
            #不进一步处理

            moderator = Moderator.get_instance(username)
            moderator.username = username
            moderator.realname = realname
            moderator.email = email
            moderator.is_staff = 0
            moderator.set_password(hashlib.md5(password).hexdigest())
            moderator.in_review = True
            moderator.put()
            msg = "username: " + username + '\n'
            msg += str(request)

            # error_ml = [ settings.EMAIL_ACCOUNT ]



            # #测试期间，暂不发送
            # send_mail('[%s]: registration: ' % (request.path), msg, 
            #         settings.EMAIL_ACCOUNT, error_ml, fail_silently=False,
            #         auth_user=settings.EMAIL_ACCOUNT.split('@')[0],
            #         auth_password=settings.EMAIL_PASSWORD )
        return HttpResponse(u"谢谢注册, 请耐心等待我们管理员的人工审核.")


def send_verify_email_code(request):
    #让新用户确认email -- 将来可以做 e-business 淘宝类 网站用

    email = request.GET.get('email', '')
    reason = request.GET.get('reason', '')
    reason_msg = {
            'registration': u'谢谢您有意注册成为我们的用户',
            'forgot_password': u'听说您忘记了密码',
            }

    msg = reason_msg[reason] + u''',　您 email (%s) 的确认码为: 
    %s . 
本确认码一小时内有效。''' % ( 
            email, generate_verify_email_code(email) )

    send_mail(u'确认您的 email 地址', msg, 
            settings.EMAIL_ACCOUNT, [email], 
            fail_silently=False,
            auth_user=settings.EMAIL_ACCOUNT.split('@')[0],
            auth_password=settings.EMAIL_PASSWORD )


def generate_verify_email_code(email):
    ''' 注册时, 发一个email给用户, 内含确认码， 让用户确认. 
    含时间因子，只能1小时左右有效。

    假订 email 已含有@与.
    '''
    
    # 含 小时。 确认时，检查当前小时，前两个小时
    a = settings.SECRET_KEY  + email + str(datetime.datetime.now())[:13] 
    return hashlib.md5(a).hexdigest()


def verify_email_code(email, code):
    '''确认email里的确认码
    '''
    
    # 含 小时。 确认时，检查当前小时，前两个小时
    now = datetime.datetime.now()
    now_1 = now - datetime.timedelta(hours=1)
#   now_2 = now - datetime.timedelta(hours=2)

    code_match = False
    for dt in (now, now_1):
        if code == hashlib.md5(settings.SECRET_KEY + email + str(dt)[:13]).hexdigest():
            code_match = True
            break

    return code_match


def logout(request):
    """
    登出
    """
    response = HttpResponseRedirect("/admin/")
    apps.admin.auth.logout(request,response)
    return response


def forgot_password(request):
    """
    忘记密码. 若作公开上线，开放注册的网站，须要让用户可以找回忘记的密码
    """
    username = request.POST.get("username")
    password = request.POST.get("password")
    password2 = request.POST.get("password2")
    email = request.POST.get("email")
    email_verify_code = request.POST.get("email_verify_code")

    data = {}

    captcha_word = request.POST.get("captcha_word", '')
    captcha_img_id = request.POST.get("captcha_img_id", '')
    if not captcha_img_id:
        captcha_img_id = get_captcha_image_id()
    data['captcha_img_id'] = captcha_img_id

    if not username or not password or not email or not email_verify_code:
        #请用户填表格
        return render_to_response("admin/forgot_password.html", 
                data, RequestContext(request))

    #开始检查用户的输入
    if not captcha_check(img_id=captcha_img_id, word=captcha_word):
        return HttpResponse(u"图片验证码不对, 或已过期, 或已用它查过一次(不论对或错). 请返回, 刷新, 重试.")

    elif not email_verify_code:
        return HttpResponse(u"Email确认码必填")

    elif not verify_email_code (email, email_verify_code.strip()):
        return HttpResponse(u"Email确认码不对")

    elif password != password2:
        return HttpResponse(u"两次密码不同")

    else:
        moderator = Moderator.get(username)
        if not moderator:
            return HttpResponse("不存在该用户名.")

        if moderator.email != email:
            return HttpResponse("用户 " + username + " 的Email 不是: " + email)

        moderator.set_password(hashlib.md5(password).hexdigest())
        moderator.put()

        return HttpResponse(u"您的密码已更新, 请重新登录.")


@require_permission
def main(request):
    """
    左侧列表页
    """
    #获取当前用户
    moderator = apps.admin.auth.get_moderator_by_request(request)
    # index_list = admin_configuration.view_perm_mappings.get_allow_index_paths(moderator)

    return "admin/main.html", {}


@require_permission
def moderator_list(request):
    """
    管理员列表
    """
    # 取数据库
    from apps.admin.models import Moderator
    mod_list = Moderator.find({'is_staff':1})
    mod_list.sort(key=lambda mod: mod.last_login, reverse=True)   #sort according to data
    return "admin/moderator_list.html", {"moderator_list":mod_list}

@require_permission
def agree_inreview(request):
    """
    带审核的帐号列表列表
    """
    # 取数据库
    from apps.admin.models import Moderator
    mod_list = Moderator.find({'in_review':True})
    return "admin/moderator_list.html", {"moderator_list":mod_list}


@require_permission
def pk_top(request):
    ''' PK, 即实时 PvP (Real Time Peer-vs-Peer)
    '''
    data = []
#       data.append(tmp)

    top_model = pvp_redis.get_pvp_redis('1', top_name='real_pvp')
    top_30_uid_score = top_model.get(30, desc=False)
    top_30_uid_score.reverse()

    for uid, score in top_30_uid_score:
        pk_obj = UserRealPvp.get(uid)
        ub_obj = UserBase.get(uid)

        if pk_obj and ub_obj:
            user_prop_obj = UserProperty.get(uid)
            tmp = {}
            #base_info = pvp_obj.pvp_info['base_info']
            tmp['uid'] = uid
            tmp['pt'] = int(score)
            tmp['pvp_title'] = pk_obj.pvp_title
            tmp['username'] = ub_obj.username
            tmp['lv'] = user_prop_obj.lv
            data.append(tmp)

    return "admin/pk_top.html", {'data':data}


@require_permission
def lv_top(request):
    data = []
    lv_top_100_list = lv_top_model.get(100)
    for uid,lv in lv_top_100_list:
        tmp = {}
        tmp['uid'] = uid
        tmp['lv'] = int(lv)
        tmp['username'] = UserBase.get(uid).username
        data.append(tmp)
    return "admin/lv_top.html", {'data':data}


@require_permission
def moderator_permissions(request):
    mid = request.GET.get("mid")
    if mid is None:
        return
    moderator = apps.admin.auth.get_moderator(mid)

    perms = []
    for perm in moderator.get_permissions():
        perms.append(admin_configuration.all_permissions[perm])

    return "admin/moderator_permissions.html", {"perm_list":perms}


@require_permission
def view_all_permissions(request):
    from apps.admin.models import Moderator
    mod_list = list( Moderator.find({'is_staff':1}) )
    mod_list.sort(key=lambda mod: mod.mid)   #sort according to 'mid'

#   return render_to_response("admin/moderator_list.html",{"moderator_list":mod_list},RequestContext(request))

    for mod in mod_list:
        mod.perms = []
        for perm in mod.get_permissions():
            mod.perms.append(admin_configuration.all_permissions[perm])

    return "admin/moderator_all_perm.html", {"moderator_list":mod_list}


@require_permission
def add_moderator(request):
    """
     新建管理员
    """
    if request.method == "POST":
        from apps.admin.models import Moderator
        form = ModeratorCreationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password1"]
            permissions = form.cleaned_data["permissions"]
            moderator = Moderator.get_instance(username)
            moderator.username = username
            moderator.is_staff = 1
            moderator.email = form.cleaned_data["email"]
            moderator.last_login = datetime.datetime.now()
            moderator.set_password(hashlib.md5(password).hexdigest())
            moderator.set_permissions(permissions)
            moderator.put()
            return HttpResponseRedirect('/admin/moderator/add_moderator_done/')
    else:
        form = ModeratorCreationForm()
    return "admin/add_moderator.html", {'form':form}

@require_permission
def add_moderator_done(request):
    return "admin/add_moderator_done.html", {}


@require_permission
def manage_moderator(request):
    """
        管理员管理表单
    """
    mid = request.GET.get("mid")
    if mid is None:
        return render_to_response("admin/manage_moderator.html",{"status":1,"mid":mid},RequestContext(request))
    moderator = apps.admin.auth.get_moderator(mid)
    if moderator is None:
        return render_to_response("admin/manage_moderator.html",{"status":2,"mid":mid},RequestContext(request))
    if request.method == "POST":
        form = ModeratorManageForm(data = request.POST)
        if form.is_valid():
            password = hashlib.md5(form.cleaned_data["password1"]).hexdigest()
            permissions = form.cleaned_data["permissions"]
            moderator.is_staff = 1
            #密码
            if form.cleaned_data["password1"]:
                if password != "d41d8cd98f00b204e9800998ecf8427e":
                    moderator.set_password(password)
            #权限
            moderator.in_review = False
            moderator.clear_permissions()
            moderator.set_permissions(permissions)

            # apps.admin.auth.update_moderator(moderator)
            return HttpResponseRedirect("/admin/moderator/manage_moderator_done/")
        else:
            return render_to_response("admin/manage_moderator.html",{"form":form,"mid":mid},RequestContext(request))

    form = ModeratorManageForm({"permissions":moderator.get_permissions()})
    return "admin/manage_moderator.html", {'moderator':moderator, 'form':form, "mid":mid}


@require_permission
def manage_moderator_done(request):
    return "admin/manage_moderator_done.html", {}


@require_permission
def change_password(request):
    """
        修改密码
    """
    moderator = apps.admin.auth.get_moderator_by_request(request)
    if request.method == "POST":
        form = ModeratorResetPasswordForm(request.POST)
        if form.is_valid():
            moderator.set_password(hashlib.md5(form.cleaned_data["password1"]).hexdigest())
            # apps.admin.auth.update_moderator(moderator)
            moderator.put()
            return render_to_response("admin/change_password_done.html",{},RequestContext(request))
    else:
        form = ModeratorResetPasswordForm()

    return "admin/change_password.html", {'moderator':moderator,'form':form}


@require_permission
def delete_moderator(request):
    """
       删除管理员
    """
    if request.method == "POST":
        mid = request.GET.get("mid")
        if mid is None:
            return render_to_response("admin/delete_moderator.html",{'status':1},RequestContext(request))
        moderator = apps.admin.auth.get_moderator(mid)
        if moderator is None:
            return render_to_response("admin/delete_moderator.html",{'status':2},RequestContext(request))

        apps.admin.auth.delete_moderator(mid,moderator.mid)
        return HttpResponseRedirect("/admin/moderator/delete_moderator_done/")
    else:
        return "admin/delete_moderator.html", {}

@require_permission
def delete_moderator_done(request):
    """
    删除管理员成功
    """
    return "admin/delete_moderator_done.html", {}


def _config_skill_params_by_ruby(config_value, request):
    # 调用ruby的脚本处理ruby_skill_params_config，将得到的最终配置存入skill_params_config
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    ruby_script = cur_dir + "/ruby_files/gen_skill.rb"
    in_file_path = "/tmp/qz_admin_in.txt"
    out_file_path = "/tmp/qz_admin_out.txt"
    with open(in_file_path, 'w') as in_file:
        in_file.write(config_value)
        in_file.close()
    ruby_cmd = "/usr/local/ruby212/bin/ruby {} {} {}".format(ruby_script, in_file_path, out_file_path)
    (status, output) = commands.getstatusoutput(ruby_cmd)
    print "ruby_result", status, output
    if status:
        return output[:120]
    # ruby_r = os.popen("/usr/local/ruby212/bin/ruby {} {} {}".format(ruby_script, in_file_path, out_file_path)).read()
    # print "ruby_result", ruby_r
    with open(out_file_path, 'r') as out_file:
        skill_params = out_file.read()
    # ruby脚本成功执行
    if not skill_params:
        return 'ruby-error: skill_params is none'
    request_info = dict(request.REQUEST)
    request_info['config_name'] = "skill_params_config"
    request_info['config_value'] = skill_params.decode('utf-8')
    m = game_setting(request, request_info, return_dict=True)
    # if m['rc']: 
    #     return 'ruby-error: {}'.format(m['msg'])
    os.remove(in_file_path)
    os.remove(out_file_path)
    return ''


@require_permission
def game_setting(request,request_info=None, return_dict=False):
    """游戏配置
    """
    if not request_info:
        request_info = request.REQUEST
    data = {}
    subarea = request_info.get('subarea')
    categories = config_list.get_conflist_by_subarea(subarea)
    config_name = request_info.get('config_name')
    saved = False

    sconfig_name = config_list.get_configname_by_subarea(config_name,subarea)
    str_subareas_confname = config_list.get_configname_by_subarea('subareas_conf', '1')
    subareas_conf = Config.get(str_subareas_confname)
    if not subareas_conf:
        subareas_conf = Config.create(str_subareas_confname)

    subareas_conf_dict = eval(subareas_conf.data)

    return_subareas_conf = []
    for key in sorted(subareas_conf_dict.keys()):
        return_subareas_conf.append((key, subareas_conf_dict[key]))
    data['config_title'] = config_list.get_description(config_name)
    data['config_title'] += '__%s' % config_name
    if sconfig_name:
        #修改具体的一个
        config = Config.get(sconfig_name)
        if not config:
            config = Config.create(sconfig_name)
        config_value = config.data
        if request.method == 'POST':
            before_config = config_value
            if not return_dict:
                config_md5sum_from_web = request.POST['config_md5sum'] #before this update
                if type( config_value ) == unicode:
                    config_md5sum_calculated = hashlib.md5( config_value.strip().encode('utf-8') ).hexdigest()
                else:
                    config_md5sum_calculated = hashlib.md5( config_value.strip() ).hexdigest()

                if config_md5sum_from_web !=  config_md5sum_calculated:
                    return HttpResponse('<script>alert("配置内容, 已被别人修改过. 请重新刷新，再作修改。");</script>')

            config_value = request_info['config_value'].encode('utf-8').replace('\r','').strip()
            config.data = config_value
            if config_name != 'ruby_skill_params_config':
                verify_info = verify_game_config(config_name, eval(config_value))
            # 通过ruby的配置  简化技能的配置
            else:
                verify_info = _config_skill_params_by_ruby(config_value, request)
            if verify_info != '':
                return HttpResponse('<script>alert("%s");history.go(-1)</script>' % verify_info)
            config.put()
            config_update(subarea, config_name)

            moderator = apps.admin.auth.get_moderator_by_request(request)
            username,date,subarea,configname,REMOTE_ADDR = moderator.username,datetime.datetime.now(),subarea, data['config_title'], request.META["REMOTE_ADDR"]
            UpdateConfRecord.record(username, date, subarea, configname, REMOTE_ADDR)
            saved = True

            
            log_data = {}
            diff_result = diff_2_str(config_value, before_config)
            if diff_result:
                log_data['diff'] = diff_result
                log_data['subarea'] = subarea
                log_data['config_name'] = config_name
                log_data['before_config'] = before_config
                log_data['after_config'] = config_value
                log_data["username"] =  moderator.username
                ConfigHistory.set_log(**log_data)


            #多分区，保存配置后，要允许运营同学 同步到其它分区。
            config_use_subarea = False 
            for g in config_list.g_lConfig:
                if g['name'] == config_name and g['use_subarea']:
                    config_use_subarea = True 
                    break

            if config_use_subarea:
                #本配置, 不同的分区，有差别, 要同步到其它分区
                same_contents_subareas = {}
                diff_contents_subareas = {}
                for other_subarea_id, other_subarea_name in subareas_conf_dict.items():
                    if other_subarea_id == subarea:
                        continue

                    other_subarea = Config.get(config_name + '_' + other_subarea_id)
                    if not other_subarea:
                        other_subarea = Config.create(config_name + '_' + other_subarea_id)
                    #print '#### other_subarea.data=', other_subarea.data.encode('utf8')
                    #print '#### config_value=', config_value
                    #print '#### other_subarea.data == config_value ', other_subarea.data == config_value
                    if other_subarea.data == config_value or other_subarea.data.encode('utf8') == config_value:
                        same_contents_subareas[other_subarea_id] = other_subarea_name
                    else:
                        diff_contents_subareas[other_subarea_id] = other_subarea_name

                data = {'subarea': subarea, 'config_name': config_name}
                data['config_description'] = config_list.get_description(config_name)
                data['subarea_name'] = subareas_conf_dict[subarea]
                data['same_contents_subareas'] = same_contents_subareas
                data['diff_contents_subareas'] = diff_contents_subareas
                return 'admin/sync_conf_to_subarea.html', data

    else:
        #显示所有
        config_value = None
    data['subarea'] = subarea
    data['subareas_conf'] = return_subareas_conf
    #data['g_l_config'] = g_l_config
    data['categories'] = categories
    data['config_name'] = config_name
    data['config_value'] = beautify_config_value (config_value)
    data['saved'] = saved
    data['updateconfrecord'] = UpdateConfRecord.infos()['infos_list']
    if return_dict:
        return data

    data['config_error'] = ''
    if subarea == '1' and not config_name:
        data['config_error'] = check_config_error()

    #print '#### data[config_error]=', data['config_error']

    if config_value:
        if type( config_value ) == unicode:
            config_md5sum_calculated = hashlib.md5( config_value.strip().encode('utf-8') ).hexdigest()
        else:
            config_md5sum_calculated = hashlib.md5( config_value.strip() ).hexdigest()
        data['config_md5sum'] = config_md5sum_calculated

    #data['app_name'] = settings.APP_NAME
    #data['environment_type'] = settings.ENVIRONMENT_TYPE

    #show config backup
    conf_backup_date = RedisTool.get('conf_backup_date')

    data['conf_backup_date'] = conf_backup_date
    data['backup_diff_from_now'] = {}
    data['changed_from_today'] = []    #from today's early morning backup

    if config_name: #display one specific config (in certain subarea)
        old_conf_data = show_config_backup(config_name=config_name, 
               subarea=subarea, date_str=conf_backup_date)

        if old_conf_data in ('', None): #never backed up yet
            data['backup_diff_from_now'] = ''
        elif Config.get(config_name + '_' + subarea):
            if old_conf_data == Config.get(config_name + '_' + subarea).data:
                data['backup_diff_from_now'] = ''
            else:
                data['backup_diff_from_now'] = 'Yes'

    else: #display overview of all config
      if subarea:
        for conf_name in config_list.get_game_config_name_list(subarea=subarea):
            conf_obj = Config.get(conf_name + '_' + subarea)
            if not conf_obj:
                continue

            morning_conf_data = show_config_backup( config_name=conf_name, 
                                subarea=subarea, date_str=conf_backup_date)
            if morning_conf_data:   #if '', i.e. not exist/backed up yet, 
                                    #don't display
                if conf_obj.data != morning_conf_data:
                    data['changed_from_today'] += [
                         '<a href="/admin/game_setting/?config_name=' + 
                         conf_name + '&subarea=' + subarea + '">' + conf_name + '(' + subarea + ')</a>' ]
        data['changed_from_today'] = ', '.join(data['changed_from_today'])

    return 'admin/game_setting.html', data


def verify_game_config(config_name, value):
    #用于验证配置是否正确
    verify_dict = {
        # 'system_config': ['maintenance'],#key为配置名称，value为该配置名称必须存在的key
        # 'loginbonus_config': ['bonus'],
        # 'shop_config': [],
        # 'user_level_config': ['1'],
        # 'gacha_config': ['charge_rate',],
        # 'card_config': ['1_card', ],
        # 'card_level_config': ['exp_type', ],
        # 'card_update_config': ['cost_gold', ],
        # 'monster_config': [],
        # 'dungeon_config': ['1', ],
        # 'normal_dungeon_effect_config': ['rule', ],
    }
    verify_info = ''
    if config_name in verify_dict:
        for verify_value in verify_dict[config_name]:
            if not verify_value in value:
                verify_info = config_name + " miss '" + verify_value + "'"

    #战场掉落敌将，而在敌将配置中未配置的验证
    # dcverify = verify_dungeon_config(config_name, value)
    # if dcverify:
    #     return dcverify

    return verify_info


def verify_dungeon_config(config_name, value):
    """战场掉落敌将，而在敌将配置中未配置的验证"""
    if config_name == 'normal_dungeon_config':
        for dungeon_floor in value:
            mdset = set(value[dungeon_floor]['monster_drop'].keys())
            mset = set(game_config.monster_config.keys())
            if mdset & mset != mdset:
                vdresult = mdset - (mdset & mset)
                if vdresult:
                    for mid in vdresult:
                        return "敌将配置__monster_config 缺少配置ID：" + str(mid)
    return ''


@require_permission
def gift(request):
    data = {}
    data['status'] = '0'
    gift_keys = game_config.gift_config['gift_config']
    if request.method == "POST":
        if request.POST.get("add_num", "") and request.POST.get("gift_id", ""):
            add_num = min(int(request.POST.get("add_num")),5000)
            gift_id = request.POST.get("gift_id")
            gift_code_obj = GiftCode.get_instance(gift_id)
            # if int(gift_id) < 10:
            #     gift_id = '0' + gift_id
            # if (len(gift_id) != 2 and int(gift_id) < 100) or (add_num < 1 or add_num >10000):
            #     data['status'] = '1'
            if gift_id not in gift_keys:
                data['status'] = '1'
            # elif len(gift_code_obj.codes) > 0:
            #     data['status'] = '2'
            else:
                new_gift_codes = random.sample(xrange(10000,100000),add_num)                
                new_gift_codes_dict = {gift_id+str(gift_code):'' for gift_code in new_gift_codes}
                gift_code_obj.give_codes(new_gift_codes_dict)
    gift_record = []
    for gift_id in gift_keys:
        temp = {}
        gift_code_obj = GiftCode.get(gift_id)
        if not gift_code_obj:
            continue
        temp["gift_id"] = gift_id
        temp['used_expand'] = False
        temp['not_used_expand'] = False
        gift_record.append(temp)
        used_code = [gift_code for gift_code in gift_code_obj.codes if gift_code_obj.codes[gift_code]]
        not_used_code = [gift_code for gift_code in gift_code_obj.codes if not gift_code_obj.codes[gift_code]]
        temp["used_code"] = ', '.join(used_code)
        temp["not_used_code"] = ', '.join(not_used_code)
    data["gift_record"] = gift_record
    return 'admin/gift.html', data


def save_game_settings(request):
    '''
    保存配置, 多个分区的 subarea_list
    '''
    data = {}
    config_value = ''
    config_name = request.GET.get('config_name','')

    subarea_list = request.POST.getlist('subarea_list')
    if not subarea_list:
        subarea_default_save = request.POST.get('subarea_default_save')
        subarea_list.append(subarea_default_save)
    u_config_description = config_list.get_description(config_name)
    data['config_title'] = u_config_description
   
    str_subareas_confname = config_list.get_configname_by_subarea('subareas_conf', '1')
    subareas_conf = Config.get(str_subareas_confname)
    if not subareas_conf:
        #subareas_conf = Config.create(sconfig_name)
        subareas_conf = Config.create(str_subareas_confname)

    subareas_conf_dict = eval(subareas_conf.data)
    return_subareas_conf = []
    for key in sorted(subareas_conf_dict.keys()):
        return_subareas_conf.append((key, subareas_conf_dict[key]))

    for subarea in subarea_list:
        sconfig_name = config_list.get_configname_by_subarea(config_name,subarea)
        config = Config.get(sconfig_name)
        if not config:
            config = Config.create(sconfig_name)
        before_config_data = config.data

        config_value = request.POST['config_value'].encode('utf-8').replace('\r','').strip()
        config.data = config_value
        if config_name != 'ruby_skill_params_config':
            verify_info = verify_game_config(config_name, eval(config_value))
        #通过ruby的配置  简化技能的配置
        else:
            verify_info = _config_skill_params_by_ruby(config_value, request)
        config.put()
        config_update(subarea, config_name)

        moderator = apps.admin.auth.get_moderator_by_request(request)

        log_data = {}
        diff_result = diff_2_str(config.data, before_config_data)
        if diff_result:
            log_data['diff'] = diff_result
            log_data['subarea'] = subarea
            log_data['config_name'] = config_name
            log_data['before_config'] = before_config_data
            log_data['after_config'] = config_value
            log_data["username"] =  moderator.username
            ConfigHistory.set_log(**log_data)

    data['config_value'] = config_value
    data['config_title'] = u_config_description
    data['subareas_conf'] = return_subareas_conf
    data['saved'] = True
    data['submit_game_settings_by_excel'] = True
    return render_to_response('admin/game_setting.html',data,context_instance = RequestContext(request))


def diff_2_str(str1='', str2=''):
    ''' bash's diff command, give better result than Python's difflib

    We write to 2 tempfiles first, after diff, delete them.

    diff -b is to ignore 1+ spaces
    '''
    str1=str1.strip()
    str2=str2.strip()

    if str1 == str2:
        return ''

    tmpFile1 = tempfile.mktemp()
    tmpFile2 = tempfile.mktemp()
    f=open(tmpFile1, 'w')
    if type(str1) == unicode:
        print >>f, str1.encode('utf-8'),
    else:
        print >>f, str1,
    f.close()

    f=open(tmpFile2, 'w')
    if type(str2) == unicode:
        print >>f, str2.encode('utf-8'),
    else:
        print >>f, str2,
    f.close()

    return commands.getoutput( '/usr/bin/diff -b %s %s && /bin/rm %s %s' % (tmpFile1, tmpFile2,
                        tmpFile1, tmpFile2) ).strip()


@require_permission
def config_md5sum(request):
    config_name = request.GET.get('config_name')
    subarea = request.GET.get('subarea')

    config_value = None
    if config_name:
        sconfig_name = config_list.get_configname_by_subarea(config_name,subarea)
        config = Config.get(sconfig_name)
        if config:
            config_value = config.data
    if config_value:
        return HttpResponse(hashlib.md5( config_value.strip().encode('utf-8') ).hexdigest())


@require_permission
def config_changes(request):
    '''config change history'''

    logs = ConfigHistory.log_mongo_find_last_n({}, 
                sort_field="date_time", n=50)
    data = {}
    data['logs'] = logs
    return 'admin/config_changes.html', data


@require_permission
def view_setting(request):
    config_name = request.GET.get('config_name')
    if config_name == 'language_config':
        return game_setting(request, view_only=False)
    else:
        return game_setting(request, view_only=True)


@require_permission
def view_setting_backup(request):
    config_name = request.GET.get('conf')
    subarea = request.GET.get('area')
    date_str = request.GET.get('date')
    return HttpResponse( show_config_backup(config_name=config_name,
            subarea=subarea, date_str=date_str),  
            content_type="text/plain; charset=UTF8")


@require_permission
def setting_backup_diff(request):
    ''' config backup difference from today's config
    '''
    config_name = request.GET.get('conf')
    subarea = request.GET.get('area')
    date_str = request.GET.get('date')

    bk_data = show_config_backup(config_name=config_name,
            subarea=subarea, date_str=date_str)
#   if bk_contents in ('', None):
#       return HttpResponse('Backup of ' + date_str + 'does not exist.')

    conf = Config.get(config_name + '_' + subarea)
    if not conf:
        return HttpResponse(config_name + ' does not exist.')

    diffs = diff_2_str(conf.data, bk_data)
#   print '#### diffs="' + diffs + '", total length=', len(diffs)
    
    return HttpResponse( diffs, content_type="text/plain; charset=UTF8" )


@require_permission
def config_diff(request):
    '''
    config difference (most time, same config in different areas)
    config1, area1, config2, area2 are required parameters
    '''

    config1 = request.GET.get('config1')
    area1 = request.GET.get('area1')
    config2 = request.GET.get('config2')
    area2 = request.GET.get('area2')

    conf1_obj = Config.get(config1 + '_' + area1)
    if not conf1_obj:
        return HttpResponse(config1 + ', ' +  area1 + u'区, 不存在.')

    conf2_obj = Config.get(config2 + '_' + area2)
    if not conf2_obj:
        return HttpResponse(config2 + ', ' +  area2 + u'区, 不存在.')

    diffs = diff_2_str(conf1_obj.data, conf2_obj.data)
#   print '#### diffs="' + diffs + '", total length=', len(diffs)
    
    return HttpResponse( diffs, content_type="text/plain; charset=UTF8" )


@require_permission
def sync_conf_to_subarea(request):
    config_name = request.GET.get('config_name')
    current_subarea = request.GET.get('current_subarea')
    subarea_list = request.GET.getlist('subarea_list')

    current_config_data = Config.get(config_name + '_' + current_subarea).data
    for sa in subarea_list:
        c = Config.get(config_name + '_' + sa)
        if not c:
            c = Config.create(config_name + '_' + sa)
        c.data = current_config_data
        c.put()


    str_subareas_confname = config_list.get_configname_by_subarea('subareas_conf', '1')
    subareas_conf = Config.get(str_subareas_confname)
    if not subareas_conf:
        subareas_conf = Config.create(str_subareas_confname)
    subareas_conf_dict = eval(subareas_conf.data)
    subarea_id_name_list = []
    for s in subarea_list:
        subarea_id_name_list += [ u'分区' + s + ': ' + subareas_conf_dict[s] ]


    data = {
            'config_name': config_name,
            'config_description': config_list.get_description(config_name),
            'subarea': current_subarea,
            'subarea_id_name_list': subarea_id_name_list,
            }
    return 'admin/sync_subarea_done.html', data



def beautify_config_value(value_str):
    ''' 
    config_value is a string, can't use pprint, pformat to beautify
    automatically. Need some extra tweak.

    Beautify config value, will eaze other users to reduce errors.

    Single {, will add indent 4 spaces on next line;
    Single }, will subtract 4 spaces indent on next line;

    { ### 321, need indent
    } ## 123: # need indent

    We can only do partial beautify now, or need call this function
    several times to get best results.

    Return result may not be perfect, but most time should close to perfect
    '''

    if not value_str:
        return None

    lines = value_str.replace('\r\n', '\n').split('\n')
    indent = 0
    for i in range(len(lines)): 
        ls = lines[i].strip()

        if '#' in ls:   #consider as comments, after #
            # if # is in string, '#', then problem; treat later
            ls_first_sharp = ls.index('#') 
            ls_no_sharp = ls[:ls_first_sharp].strip()
        else:
            ls_no_sharp = ls

        num = ls_no_sharp.count('{') - ls_no_sharp.count('}') + \
                ls_no_sharp.count('[') - ls_no_sharp.count(']') + \
                ls_no_sharp.count('(') - ls_no_sharp.count(')') 
        next_indent = indent + 4*num

        if ls == '':
            continue
        elif ls[0] == '#':
            lines[i] = ' '*indent + ls
        else:
            if ls_no_sharp in ( '}', '},', ']', '],', ')', '),' ):
                #若本行是: "}", "},",   则本行，也要减一层缩进
                lines[i] = ' '*next_indent + ls
                indent = next_indent 
            elif ls_no_sharp in ( '{', '[', '(' ):
                #若本行是: "[", "{,",   4*num 会大4, 要减回来; 或与上行同样缩进
                lines[i] = ' '*indent + ls
                indent = next_indent
            else:
                #其它，则保持上一行的缩进
                lines[i] = ' '*indent + ls
                indent = next_indent

    return '\n'.join(lines)


# def captcha_image(request):
#     '''利用 PyCaptcha (它用了PIL, Python Image Library),
#     处理 /admin/captcha_image/?id=#X$#@123
#     返回 jpeg 图像给网页浏览器
#     '''
#     img_id=request.GET.get('id', '')
#     print '#### captchaFactory.storedInstances=', captchaFactory.storedInstances
#     test = captchaFactory.get(img_id)
#     if not test:
#         return HttpResponse('Invalid id')

#     img = test.render()
#     buf= StringIO.StringIO()
#     img.save(buf, format= 'JPEG')
#     jpeg_str= buf.getvalue()
#     buf.close()

#     return HttpResponse(jpeg_str, content_type="image/jpeg" )


# def get_captcha_image_id():
#     '''利用 PyCaptcha (它用了PIL, Python Image Library)
#     '''
#     test = captchaFactory.new( captchaTests.PseudoGimpy )
#     #test = captchaFactory.new( captchaTests.AntiSpam )
#     return test.id


# def captcha_check(img_id='', word=''):
#     '''利用 PyCaptcha (它用了PIL, Python Image Library),
#     '''

#     test = captchaFactory.get(img_id)
#     if not test:
#         return HttpResponse('Invalid id')

#     # Invalid tests will always return False, to prevent
#     # random trial-and-error attacks. This could be confusing to a user...
#     return ( test.valid and test.testSolutions([word]) )
