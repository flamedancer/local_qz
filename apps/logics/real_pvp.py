#-*- coding: utf-8 -*-

import bisect
import random

from apps.models.user_real_pvp import UserRealPvp

from apps.models import pvp_redis
from apps.oclib import app

from apps.realtime_pvp import readying_player_redis


def get_pvp_detail(rk_user, params):
    #判断新手引导
    newbie_step = int(params.get('newbie_step', 0))
    if newbie_step:
        rk_user.user_property.set_newbie_steps(newbie_step, "get_pvp_detail")
    return 0, {'pvp_info': rk_user.user_real_pvp.pvp_detail}


def get_real_pvp_info(uid):
    urp = UserRealPvp.get(uid)
    pvp_info_data = urp.get_pvp_need_info()


    user_equips_data = {}
    deck_ucids = [card_info['ucid'] for card_info in pvp_info_data['deck'] if 'ucid' in card_info]
    user_equip_info = urp.user_equips.get_equips()
    for ueid in user_equip_info:
        if user_equip_info[ueid]['used_by'] in deck_ucids:
            user_equips_data[ueid] = user_equip_info[ueid]

    user_pvp_info = {
        'pvp_opponent': {
            0: pvp_info_data,
        },
        'equip_info': user_equips_data,

    }
    return user_pvp_info


def result_fight(win_uid, lose_uid):
    win_real_pvp_obj = UserRealPvp.get(win_uid)
    lose_real_pvp_obj = UserRealPvp.get(lose_uid)
    print "winner  {}, loser   {}".format(win_uid, lose_uid)
    top_model = pvp_redis.get_pvp_redis(win_real_pvp_obj.user_base.subarea, top_name='real_pvp')

    pt_gap = lose_real_pvp_obj.pt - win_real_pvp_obj.pt

    win_add_pt = _calculate_win_or_lose_pt(win_real_pvp_obj.pt, pt_gap, victory=True)
    lose_deduct_pt = _calculate_win_or_lose_pt(lose_real_pvp_obj.pt, pt_gap, victory=False)

    win_pt = win_real_pvp_obj.add_pt(win_add_pt)
    win_real_pvp_obj.pvp_info['total_win'] += 1
    win_real_pvp_obj.pvp_info['total_join'] += 1

    lose_pt = lose_real_pvp_obj.add_pt(lose_deduct_pt)
    lose_real_pvp_obj.pvp_info['total_lose'] += 1
    lose_real_pvp_obj.pvp_info['total_join'] += 1

    top_model.set(win_uid, win_real_pvp_obj.pt)
    top_model.set(lose_uid, lose_real_pvp_obj.pt)

    win_info = {
        'pvp_title': win_real_pvp_obj.pvp_title,
        'pt': win_real_pvp_obj.pt,
        'pvp_rank': top_model.rank(win_uid),
        'change_pt': win_pt,
        'total_win': win_real_pvp_obj.pvp_info['total_win'],
        'total_lose': win_real_pvp_obj.pvp_info['total_lose'],
    }

    lose_info = {
        'pvp_title': lose_real_pvp_obj.pvp_title,
        'pt': lose_real_pvp_obj.pt,
        'pvp_rank': top_model.rank(lose_uid),
        'change_pt': lose_pt,
        'total_win': lose_real_pvp_obj.pvp_info['total_win'],
        'total_lose': lose_real_pvp_obj.pvp_info['total_lose'],
    }

    win_real_pvp_obj.do_put()
    lose_real_pvp_obj.do_put()
    return {
        'win_info': win_info,
        'lose_info': lose_info
    }


def clear(*uids):
    """玩家退出pvp的善后处
        清除 app.pier 中 uid 数据
    """
    for uid in uids:
        if uid in app.pier.get_data:
            app.pier.get_data.pop(uid)


def top_pvp(rk_user, params):
    data = {'friend':[],'all_player':[]}
    

    #前十的排行情况
    top_model = pvp_redis.get_pvp_redis(rk_user.subarea, top_name='real_pvp')
    top_30_uid_score = top_model.get(10)


    for uid, score in top_30_uid_score:
        pvp_obj = UserRealPvp.get(uid)
        data['all_player'].append(pvp_obj.get_pvp_need_info())

    urp = rk_user.user_real_pvp
    self_info = urp.get_pvp_need_info()
    self_info['self'] = True
    data['all_player'].append(self_info)

    return 0, data


PVP_IN_SUBAREA = False   # false为全玩家都可以pvp   true为只能同区pvp
VIRTUL_SERVER_IP = "10.200.55.32"  # 对内网服务器地址
TRUE_SERVER_IP = "42.121.15.153" # 真实的对外网服务器地址
def get_suitable_server(rk_user, params):
    """
    返回最适合此玩家pvp的服务器地址
    """
    score = rk_user.user_real_pvp.pt
    if PVP_IN_SUBAREA:
        candidate_server = readying_player_redis.subarea_server_conf[rk_user.subarea]
    else:
        candidate_server = readying_player_redis.all_server

    if len(candidate_server) == 1:
        return 0, {"server": candidate_server[0].replace(VIRTUL_SERVER_IP, TRUE_SERVER_IP) + '/pvp'}
    suitable_server = None
    min_gaps = []
    for server in candidate_server:
        server_redis = readying_player_redis.ALL_REDIS_MODEL[server]
        all_scores = server_redis.all_scores()
        min_gaps.append(_min_gap(all_scores, score))
    if min(min_gaps) == float("inf"):
        return 0, {"server": random.choice(candidate_server).replace(VIRTUL_SERVER_IP, TRUE_SERVER_IP) + '/pvp'}
    suitable_server = candidate_server[min_gaps.index(min(min_gaps))]

    return 0, {"server": suitable_server.replace(VIRTUL_SERVER_IP, TRUE_SERVER_IP) + '/pvp'}


def _min_gap(all_socres, score):
    """
    取得all_socres 中最接近score的，并算出两者的gap
    """
    if not all_socres:
        return float("inf")
    suitable_index = bisect.bisect(all_socres, score)
    neer_index = 0 # 最接近 score 的index
    if suitable_index == 0:
        neer_index = 0
    elif suitable_index == len(all_socres):
        neer_index = len(all_socres) - 1
    else:
        neer_left, neer_right = suitable_index - 1, suitable_index
        if (all_socres[neer_left] + all_socres[neer_right]) / 2 >= score:
            neer_index = neer_left
        else:
            neer_index = neer_right
    return abs(all_socres[neer_index] - score)


def _calculate_win_or_lose_pt(self_pt, gap, victory=True):
    # 胜负应获得积分的算法
    if self_pt < 2000:
        K = 30.0
    elif self_pt >= 2400:
        K = 10.0
    else:
        K = 130 - self_pt / 20
    if victory:
        get_point = max( K - round(K / (1 + (10 ** (gap / 400.0)))), 2)
    else:
        get_point = min( -round(K /(1+ (10 ** (-gap / 400.0)))), -2)
    return get_point


