#!/usr/bin/env python
#-*- coding: utf-8 -*-



import sys
import os
import datetime
import importlib


cur_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(cur_dir, ".."))
# import apps.settings as settings
env = "apps.settings"
if len(sys.argv) > 1:
    env = "apps.settings_" + sys.argv[1]
settings = importlib.import_module(env)

# import apps.settings_stg as settings
from django.core.management import setup_environ
setup_environ(settings)

from apps.oclib import app
from apps.config.game_config import game_config
from apps.models import pvp_redis


top_name = 'real_pvp'
all_subareas = game_config.subareas_conf()


def save_yesterday_pvp_top():
    # 每天于22：00 将此刻排行榜信息存入 昨日排行榜 
    for subarea_num in all_subareas:
        now_top = pvp_redis.get_pvp_redis(subarea_num, top_name)
        yesterday_top = pvp_redis.get_yesterday_pvp_redis(subarea_num, top_name)

        # 清空老的昨日排名
        yesterday_top.zremrangeallrank()

        now_member_scores = app.top_redis.zrange(now_top.top_name, 0, -1, withscores=True)
        for uid, score in now_member_scores:
            yesterday_top.set(uid, score)


def clean_top():
    # 如果是周日 则 重置 排行榜
    if datetime.datetime.today().weekday() == 7:
        for subarea_num in all_subareas:
            now_top = pvp_redis.get_pvp_redis(subarea_num, top_name)
            now_top.zremrangeallrank()


if __name__ == "__main__":
    save_yesterday_pvp_top()
    clean_top()
