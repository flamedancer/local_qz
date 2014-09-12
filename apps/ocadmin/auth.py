#-*- coding:utf-8 -*-

from apps.ocadmin.models.moderator import OcModerator
import datetime
import time
from apps.ocadmin import admin_config 
import urllib

def get_moderator_by_username(username):
    """
    获取管理员
    """
    moderator_list = OcModerator.find({'username': username})
    if moderator_list:
        return moderator_list[0]
    else:
        return None

def cv(request, moderator):
    """
    管理员登陆
    """
    login_time = datetime.datetime.now()
    login_ip = request.META["REMOTE_ADDR"]
    moderator.set_last_login(login_time,login_ip)
    mid = moderator.mid
    last_login_stamp = int(time.mktime(moderator.last_login.timetuple()))
    token = admin_config.build_rkauth_signature({
        "mid":mid,
        "last_login": last_login_stamp,
        "secret_key":admin_config.ADMIN_SECRET_KEY
    })
    cv = "%s|%s|%s" % (mid, last_login_stamp,token)
    cv = urllib.quote(cv.encode("ascii"))
    return cv

def get_moderator_by_request(request):
    "通过request获取moderator"
    cv = request.REQUEST.get("moderator")
    if not cv:
        return None
    else:
        cv = urllib.unquote(cv).decode("ascii")
        mid,login_stamp,token = cv.split('|')
        moderator = get_moderator(mid)
        if moderator is None:
            return None

        raw_last_login_stamp = int(time.mktime(moderator.last_login.timetuple()))
        new_token = admin_config.build_rkauth_signature({
            "mid":mid,
            "last_login": raw_last_login_stamp,
            "secret_key":admin_config.ADMIN_SECRET_KEY
        })

        if new_token == token:
            return moderator
        else:
            return None

def get_moderator(mid):
    """
    获取管理员
    """
    moderator_list = OcModerator.find({'mid':int(mid)})
    if moderator_list:
        return moderator_list[0]
    else:
        return None
