#-*- coding:utf-8 -*-
import urllib
from django.http import HttpResponseRedirect

import apps.admin.auth
from django.conf import settings
from apps.admin import admin_configuration
from django.template import RequestContext
from django.shortcuts import render_to_response

def require_permission(view_func):
    """
    装饰器，用于判断管理后台的帐号是否有权限访问
    """
    def wrapped_view_func(request,*args,**kwargs):
        path = request.path
        moderator = apps.admin.auth.get_moderator_by_request(request)

        # 管理员信息失效
        if moderator is None:
            return HttpResponseRedirect("/admin/login/")

        if not admin_configuration.view_perm_mappings.is_view_allow(path,moderator):
            return HttpResponseRedirect("/admin/login/")
        else:
            index_list = admin_configuration.view_perm_mappings.get_allow_index_paths(moderator)
            # request.index_list = index_list
            return_inf = view_func(request, *args, **kwargs)
            if isinstance(return_inf, tuple):
                template, data = return_inf
                data["appname"] = settings.APP_NAME
                data["index_list"] = index_list
                return render_to_response(template, data ,RequestContext(request))
            else:
                return return_inf

    return wrapped_view_func

def get_moderator_username(request):
    """获得用户的名字
    """
    port = request.META["HTTP_HOST"].split(":")[1]
    username = ''
    #指定账号使用查询武将丢失的功能
    cv = request.COOKIES.get("rkmoderator" + port, '')
    if cv:
        cv = urllib.unquote(cv).decode("ascii")
        mid,login_stamp,token = cv.split('|')
        moderator = apps.admin.auth.get_moderator(mid)
        username = moderator.username
    return username
