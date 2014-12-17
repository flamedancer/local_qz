#-*- coding:utf-8 -*-
import urllib
import datetime
import time
from apps.admin import admin_configuration
from apps.oclib.auth import build_rkauth_signature


def get_moderator_by_request(request):
    "通过request获取moderator"
    port = request.META["HTTP_HOST"].split(":")[1]
    cv = request.COOKIES.get("rkmoderator" + port)
    if cv is None:
        return None
    else:
        cv = urllib.unquote(cv).decode("ascii")
        mid,login_stamp,token = cv.split('|')
        moderator = get_moderator(mid)
        if moderator is None:
            return None

        raw_last_login_stamp = int(time.mktime(moderator.last_login.timetuple()))
        new_token = build_rkauth_signature({
            "mid":mid,
            "last_login": raw_last_login_stamp,
            "secret_key":admin_configuration.ADMIN_SECRET_KEY
        })

        if new_token == token:
            return moderator
        else:
            return None

def get_moderator(mid):
    """
    获取管理员
    """
    from apps.admin.models import Moderator
    moderator_list = Moderator.find({'mid':int(mid)})
    if moderator_list:
        return moderator_list[0]
    else:
        return None

def get_mid_by_username(username):
    "获取管理员"
    from apps.admin.models import Moderator
    moderator = Moderator.get(username)
    if moderator:
        return moderator.mid
    else:
        return None

def login(request,response,moderator):
    """
    管理员登陆
    """
    login_time = datetime.datetime.now()
    login_ip = request.META["REMOTE_ADDR"]
    port = request.META["HTTP_HOST"].split(":")[1]
    moderator.set_last_login(login_time,login_ip)

    mid = moderator.mid
    last_login_stamp = int(time.mktime(moderator.last_login.timetuple()))
    token = build_rkauth_signature({
        "mid":mid,
        "last_login": last_login_stamp,
        "secret_key":admin_configuration.ADMIN_SECRET_KEY
    })
    cv = "%s|%s|%s" % (mid, last_login_stamp,token)
    cv = urllib.quote(cv.encode("ascii"))
    response.set_cookie("rkmoderator" + port,cv,expires=datetime.datetime.now() + datetime.timedelta(seconds = int(60*60*24)))
    return response

def logout(request,response):
    port = request.META["HTTP_HOST"].split(":")[1]
    response.delete_cookie("rkmoderator" + port)

def delete_moderator(mid,operator):
    """
     删除管理员
     mid: 被删除管理员标志
     operator: 操作人
    """
    moderator = get_moderator(mid)
    moderator.delete()
