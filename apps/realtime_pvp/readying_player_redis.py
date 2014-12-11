#!/usr/bin/env python
# encoding: utf-8
"""
用redis存储当前在等待pk的玩家
"""
import datetime

from apps.oclib.client import Redis
import apps.settings as settings

Redis_Conf = settings.STORAGE_CONFIG[settings.STORAGE_INDEX]['realtime_pvp_redis']


all_server = settings.REAL_PVP_ALL_SERVERS

subarea_server_conf = settings.REAL_PVP_SUBAREA_SERVER_CONF


class ReadingPlayerRedis(object):
    """pvp排名信息
    """
    def __init__(self, server_site):
        self.redis = Redis(Redis_Conf['host'], Redis_Conf['port'], Redis_Conf['db'])
        self.top_name = server_site

    def set(self, uid, score):
        print(datetime.datetime.now(), str(uid), "  set score: ", score)
        return self.redis.zadd(self.top_name, score, uid)

    def remove(self, *uids):
        """踢出去一部分人 返回被踢出人数 uids=[uid1,uid2 ...]"""
        return self.redis.zrem(self.top_name, *uids)

    def count(self):
        """返回总数"""
        return self.redis.zcard(self.top_name)

    def all_scores(self):
        """返回所有分数"""
        res = self.redis.zrange(self.top_name, 0, -1, withscores=True)
        return [name_score[1] for name_score in res]

    def clear(self):
        self.redis.delete(self.top_name)


ALL_REDIS_MODEL = {}

for server_site in all_server:
    ALL_REDIS_MODEL[server_site] = ReadingPlayerRedis(server_site)



