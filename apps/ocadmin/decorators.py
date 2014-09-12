#-*- coding:utf-8 -*-

import urllib
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from apps.oclib.utils import rkjson as json
from apps.ocadmin.views import process_response
from apps.ocadmin import auth
import traceback

def require_permission(view_func):
    """
    装饰器，用于判断管理后台的帐号是否有权限访问
    """
    def wrapped_view_func(request,*args,**kwargs):
        try:
            data = {
                'rc': 0,
            }
            path = request.META.get('PATH_INFO', '')
            moderator = auth.get_moderator_by_request(request)
            # 管理员信息失效
            if not moderator:
                data['rc'] = 100
                data['require_permission'] = 'false'
            else:
                allow_paths = moderator.allow_paths(path)
                if not allow_paths:
                    data['rc'] = 2
                    data['msg'] = u'无权限操作'
            if data['rc'] != 0:
                response = HttpResponse(json.dumps(data, indent=1),content_type='application/x-javascript',)
                return process_response(response)
            else:
                return view_func(request,*args,**kwargs)
        except:
            print traceback.format_exc()
    return wrapped_view_func
