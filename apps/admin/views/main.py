#-*- coding: utf-8 -*-


import os
import  json
from django.core.mail import send_mail
from apps.admin.models import Moderator
import md5
from django.conf import settings
from django.http import HttpResponse,HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from apps.models import pvp_redis
from apps.models.config import Config
import apps.admin.auth
from apps.admin.decorators import require_permission
from apps.admin.views.forms import  ModeratorCreationForm,ModeratorManageForm,ModeratorResetPasswordForm
from apps.config import config_update
from apps.admin import admin_configuration
import datetime
import random
from apps.models.user_pvp import UserPvp
from apps.models.user_base import UserBase
from apps.models.gift_code import GiftCode
from apps.config.game_config import game_config

from apps.models.user_property import lv_top_model
from apps.ocadmin.models.updateconf_record import UpdateConfRecord
from apps.config import config_list

def index(request):
    moderator = apps.admin.auth.get_moderator_by_request(request)
    if moderator is None:
        return HttpResponseRedirect("/admin/login/")
    else:
        return HttpResponseRedirect("/admin/main/")


@require_permission
def main(request):
    return render_to_response("admin/main.html",{"appname":settings.APP_NAME},RequestContext(request))

def login(request):
    """
        首页，登录用
    """
    appname = settings.APP_NAME
    if request.method == "POST":
        username = request.POST.get("username")
        password = md5.md5(request.POST.get("password")).hexdigest()
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
    password = request.POST.get("password")
    if not username or not password:
        return render_to_response("admin/registration.html",{"appname":'a'},RequestContext(request))
    else:
        moderator = Moderator.get(username)
        if moderator:
            return HttpResponse("该用户名已经存在，可以员工编号做为后缀")
        else:
            moderator = Moderator.get_instance(username)
            moderator.username = username
            moderator.is_staff = 0
            moderator.set_password(md5.md5(password).hexdigest())
            moderator.in_review = True
            moderator.put()
            msg = "username: " + username + '\n'
            msg += str(request)
            error_ml = ['haiou.chen@newsnsgame.com']
            send_mail('[%s]: registration: ' % (request.path), msg, 'maxstrike_ios_cn@touchgame.net', error_ml, fail_silently=False,\
            auth_user='maxstrike_ios_cn',auth_password='oneclick101')

        return HttpResponse("请耐心等待审核通过")

def logout(request):
    """
    登出
    """
    response = HttpResponseRedirect("/admin/")
    apps.admin.auth.logout(request,response)
    return response

@require_permission
def left(request):
    """
    左侧列表页
    """
    #获取当前用户
    moderator = apps.admin.auth.get_moderator_by_request(request)
    index_list = admin_configuration.view_perm_mappings.get_allow_index_paths(moderator)
    message = False
    if moderator.permissions == 'super':
        in_review_list = Moderator.find({'in_review' : True}) 
        if in_review_list:
            message = True
    return render_to_response("admin/left.html",{"index_list":index_list, 'message': message},RequestContext(request))

@require_permission
def moderator_list(request):
    """
    管理员列表
    """
    # 取数据库
    from apps.admin.models import Moderator
    mod_list = Moderator.find({'is_staff':1})
    return render_to_response("admin/moderator_list.html",{"moderator_list":mod_list},RequestContext(request))

def agree_inreview(request):
    """
    带审核的帐号列表列表
    """
    # 取数据库
    from apps.admin.models import Moderator
    mod_list = Moderator.find({'in_review':True})
    return render_to_response("admin/moderator_list.html",{"moderator_list":mod_list},RequestContext(request))

@require_permission
def pvp_top(request):
    data = []
    top_model = pvp_redis.get_pvp_redis("1")
    top_30_list = top_model.get(30, desc=False)
    for uid,pt in top_30_list:
        tmp = {}
        tmp['uid'] = uid
        tmp['pt'] = int(pt)
        tmp['pvp_title'] = UserPvp.getEx(uid).pvp_title if UserPvp.getEx(uid) else ''
        tmp['username'] = UserBase.get(uid).username if UserBase.get(uid) else ''
        data.append(tmp)
    return render_to_response("admin/pvp_top.html",{'data':data},RequestContext(request))

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
    return render_to_response("admin/lv_top.html",{'data':data},RequestContext(request))

@require_permission
def moderator_permissions(request):
    mid = request.GET.get("mid")
    if mid is None:
        return
    moderator = apps.admin.auth.get_moderator(mid)

    perms = []
    for perm in moderator.get_permissions():
        perms.append(admin_configuration.all_permissions[perm])

    return render_to_response("admin/moderator_permissions.html",{"perm_list":perms},RequestContext(request))

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
            moderator.set_password(md5.md5(password).hexdigest())
            moderator.set_permissions(permissions)
            moderator.put()
            return HttpResponseRedirect('/admin/moderator/add_moderator_done/')
    else:
        form = ModeratorCreationForm()

    return render_to_response("admin/add_moderator.html",{'form':form},context_instance = RequestContext(request))

def add_moderator_done(request):
    return render_to_response("admin/add_moderator_done.html")

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
            password = md5.md5(form.cleaned_data["password1"]).hexdigest()
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
    return render_to_response("admin/manage_moderator.html",{'moderator':moderator,'form':form,"mid":mid},RequestContext(request))

@require_permission
def manage_moderator_done(request):
    return render_to_response("admin/manage_moderator_done.html",{},RequestContext(request))

@require_permission
def change_password(request):
    """
        修改密码
    """
    moderator = apps.admin.auth.get_moderator_by_request(request)
    if request.method == "POST":
        form = ModeratorResetPasswordForm(request.POST)
        if form.is_valid():
            moderator.set_password(md5.md5(form.cleaned_data["password1"]).hexdigest())
            # apps.admin.auth.update_moderator(moderator)
            moderator.put()
            return render_to_response("admin/change_password_done.html",{},RequestContext(request))
    else:
        form = ModeratorResetPasswordForm()

    return render_to_response("admin/change_password.html",{'moderator':moderator,'form':form},RequestContext(request))

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
        return render_to_response("admin/delete_moderator.html",{},RequestContext(request))

def delete_moderator_done(request):
    """
    删除管理员成功
    """
    return render_to_response("admin/delete_moderator_done.html",{},RequestContext(request))

def _config_skill_params_by_ruby(config_value, request):
    # 调用ruby的脚本处理ruby_skill_params_config，将得到的最终配置存入skill_params_config
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    ruby_script = cur_dir + "/ruby_files/gen_skill.rb"
    in_file_path = "/tmp/qz_admin_in.txt"
    out_file_path = "/tmp/qz_admin_out.txt"
    with open(in_file_path, 'w') as in_file:
        in_file.write(config_value)
        in_file.close()
    ruby_r = os.system("/usr/local/ruby212/bin/ruby {} {} {}".format(ruby_script, in_file_path, out_file_path))
    with open(out_file_path, 'r') as out_file:
        skill_params = out_file.read()
    # ruby脚本成功执行
    if ruby_r or not skill_params:
        return 'ruby-error: skill_params is none'
    request_info = dict(request.REQUEST)
    request_info['config_name'] = "skill_params_config"
    request_info['config_value'] = skill_params.decode('utf-8')
    m = game_setting(request, request_info, return_dict=False)
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
    g_l_config = config_list.get_conflist_by_subarea(subarea)
    config_name = request_info.get('config_name')
    saved = False
    sconfig_name = config_list.get_configname_by_subarea(config_name,subarea)
    str_subareas_confname = config_list.get_configname_by_subarea('subareas_conf', '1')
    subareas_conf = Config.get(str_subareas_confname)
    if not subareas_conf:
        subareas_conf = Config.create(sconfig_name)
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
            config_value = request_info['config_value'].encode('utf-8').replace('\r','').strip()
            config.data = config_value
            if config_name != 'ruby_skill_params_config':
                verify_info = verify_game_config(config_name, eval(config_value))
            # 通过ruby的配置  简化技能的配置
            else:
                verify_info = _config_skill_params_by_ruby(config_value, request)
            if verify_info != '':
                verify_info += ' KeyError'
                return HttpResponse('<script>alert("%s");history.go(-1)</script>' % verify_info)
            config.put()
            config_update(subarea, config_name)
            moderator = apps.admin.auth.get_moderator_by_request(request)
            username,date,subarea,configname,REMOTE_ADDR = moderator.username,datetime.datetime.now(),subarea, data['config_title'], request.META["REMOTE_ADDR"]
            UpdateConfRecord.record(username, date, subarea, configname, REMOTE_ADDR)
            saved = True
    else:
        #显示所有
        config_value = None
    data['subarea'] = subarea
    data['subareas_conf'] = return_subareas_conf
    data['g_l_config'] = g_l_config
    data['config_name'] = config_name
    data['config_value'] = config_value
    data['saved'] = saved
    data['updateconfrecord'] = UpdateConfRecord.infos()['infos_list']
    if return_dict:
        return data
    return render_to_response('admin/game_setting.html',data,context_instance = RequestContext(request))

def verify_game_config(config_name, value):
    #用于验证配置是否正确
    verify_dict = {
        'system_config': ['maintenance'],#key为配置名称，value为该配置名称必须存在的key
        'loginbonus_config': ['bonus'],
        'shop_config': ['sale'],
        'user_level_config': ['1'],
        'gacha_config': ['charge_rate',],
        'card_config': ['1_card', ],
        'card_level_config': ['exp_type', ],
        'card_update_config': ['cost_gold', ],
        'monster_config': [],
        'dungeon_config': ['1', ],
        'normal_dungeon_effect_config': ['rule', ],
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
            elif len(gift_code_obj.codes) > 0:
                data['status'] = '2'
            else:
                new_gift_codes = random.sample(xrange(10000,99999),add_num)                
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
    return render_to_response('admin/gift.html',data,RequestContext(request))

def save_game_settings(request):
    '''
    保存配置
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
        subareas_conf = Config.create(sconfig_name)
    subareas_conf_dict = eval(subareas_conf.data)
    return_subareas_conf = []
    for key in sorted(subareas_conf_dict.keys()):
        return_subareas_conf.append((key, subareas_conf_dict[key]))

    for subarea in subarea_list:
        sconfig_name = config_list.get_configname_by_subarea(config_name,subarea)
        config = Config.get(sconfig_name)
        if not config:
            config = Config.create(sconfig_name)
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

    data['config_value'] = config_value
    data['config_title'] = u_config_description
    data['subareas_conf'] = return_subareas_conf
    data['saved'] = True
    data['submit_game_settings_by_excel'] = True
    return render_to_response('admin/game_setting.html',data,context_instance = RequestContext(request))
