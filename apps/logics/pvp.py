#-*- coding: utf-8 -*-

from apps.models.user_pvp import UserPvp
from apps.models.user_base import UserBase
from apps.models.pt_users import PtUsers
from apps.models.user_cards import UserCards
from apps.models.user_property import UserProperty
from apps.common import utils
from apps.config.game_config import game_config
import random
from apps.models.friend import Friend
from apps.models import data_log_mod
from apps.models import data_log_mod
import string
from django.conf import settings
from apps.models import pvp_redis
from apps.logics import vip
from apps.models.user_mail import UserMail
import datetime

def pvp_first_show(rk_user,params):
    data = {}
    return 0,data

def get_pvp_detail(rk_user,params):
    data = {}
    user_pvp = UserPvp.get(rk_user.uid)
    data.update(user_pvp.pvp_detail)
    return 0,{'pvp_info':data}

def __check_start(rk_user,params):
    """检查是否可以pvp
    """
    #检查用户武将数量是否已经超过上限
    user_card_obj = UserCards.get(rk_user.uid)
    if user_card_obj.arrive_max_num():
        return 11,utils.get_msg('card','max_num')
    #减少竞技点
    if rk_user.user_pvp.pvp_stamina <= 0:
        return 11,utils.get_msg('pvp','pvp_stamina_not_enough')
        
    #用户等级达到8级后开放”擂台”功能
    if rk_user.user_property.lv < 8:
        return 11,utils.get_msg('user', 'not_enough_lv')

    #无效的参数
    if not 'self_rank' in params or not 'player_uid' in params or not 'player_rank' in params:
        return 11,utils.get_msg('pvp', 'invalid_opponent')

    self_rank = rk_user.user_pvp.pvp_rank()
    if self_rank != int(params['self_rank']):
        return 11,utils.get_msg('pvp', 'invalid_opponent')

    #监测对手是否是可以挑战的排名
    top_model = pvp_redis.get_pvp_redis(rk_user.subarea)
    #获得可pvp的对手id列表
    arena_opponents_list = top_model.get_arena_opponents_uids(self_rank)
    fg = False
    for (rank, name) in arena_opponents_list:
        if rank == int(params['player_rank']):
            fg = True
    if not fg:
        return 11,utils.get_msg('pvp', 'invalid_opponent')

    return 0, ""

def start(rk_user,params):
    #检查是否重新编队
    if params.get("new_deck"):
        from apps.logics import card as cardmod
        rc, msg = cardmod.set_decks(rk_user, params)
        if rc :
            return rc, msg
    rc,msg = __check_start(rk_user,params)
    if rc:
        return rc, {'msg': msg,}
    #对手id
    player_uid = params['player_uid']
    #对手排名
    # player_rank = params['player_rank']
    #扣除玩家的体力
    rk_user.user_pvp.minus_pvp_stamina(1)

    #记录下挑战的对手id，在出战场的时候用于验证
    rk_user.user_pvp.set_pvp_vs_player(player_uid)

    data = {'vs_player':{'deck':[],'user_name':'','pt':0,'pvp_title':''}}

    data_log_mod.set_log('PvpRecord', rk_user,
                        statament='start',
                        card_deck=rk_user.user_cards.deck,
                        renown=rk_user.user_pvp.get_renown()
    )
    return 0, data

def end(rk_user,params):
    #检查是否能符合胜利条件
    data = {}
    rc,msg = __check_end(rk_user,params)
    if rc:
        return rc,{'msg':msg}
    if not rk_user.user_pvp.pvp_info['last']:
        return 0,{}
    #被挑战者的id
    player_uid = opponent_uid = str(params['player_uid'])
    self_uid = rk_user.uid
    #被挑战者的排名
    opponent_rank = int(params['player_rank'])
    self_rank = int(params['self_rank'])
    top_model = pvp_redis.get_pvp_redis(rk_user.subarea)
    user_pvp_obj = rk_user.user_pvp
    #jjc失败点数公式=（对方ABP-自己ABP)/25-80   {10}
    # jjc胜利点数公式=80+（对方ABP-自己ABP)/25   {10}
    self_result = params.get('self_result','win')  # win or lose
    if not 'npc' in player_uid:
        play_pvp_obj = UserPvp.getEx(user_pvp_obj.pvp_info['last']['vs_player'])
        add_least = game_config.pvp_config.get('add_least')
        minus_least = game_config.pvp_config.get('minus_least')
        if self_result == 'win':
            self_get_pt = (play_pvp_obj.pt - user_pvp_obj.pt)/25 + 80
            update_award = user_pvp_obj.add_pt(min(max(add_least,self_get_pt),200))
            user_pvp_obj.pvp_info['detail_info']['continue_win'] += 1
            user_pvp_obj.pvp_info['detail_info']['total_win'] += 1
            user_pvp_obj.pvp_info['detail_info']['total_join'] += 1
        else:
            self_get_pt = abs((play_pvp_obj.pt - user_pvp_obj.pt)/25 - 80)
            update_award = user_pvp_obj.add_pt(max(min(-minus_least,-self_get_pt),-200))
            user_pvp_obj.pvp_info['detail_info']['continue_win'] = 0
            user_pvp_obj.pvp_info['detail_info']['total_join'] += 1
            user_pvp_obj.pvp_info['detail_info']['total_lose'] += 1
    else:
        add_least = game_config.pvp_config.get('add_least')
        minus_least = game_config.pvp_config.get('minus_least')
        if self_result == 'win':
            self_get_pt = 80
            update_award = user_pvp_obj.add_pt(max(add_least,self_get_pt))
            user_pvp_obj.pvp_info['detail_info']['continue_win'] += 1
            user_pvp_obj.pvp_info['detail_info']['total_win'] += 1
            user_pvp_obj.pvp_info['detail_info']['total_join'] += 1
        else:
            self_get_pt = 80
            update_award = user_pvp_obj.add_pt(min(-minus_least,-self_get_pt))
            user_pvp_obj.pvp_info['detail_info']['continue_win'] = 0
            user_pvp_obj.pvp_info['detail_info']['total_join'] += 1
            user_pvp_obj.pvp_info['detail_info']['total_lose'] += 1
    user_pvp_obj.record_pk_result(self_result)
    user_pvp_obj.clear_dungeon()
    if int(params.get('time_out_win',0)):
        user_pvp_obj.pvp_info['detail_info']['time_out_win'] += 1
    if int(params.get('perfect_win',0)):
        user_pvp_obj.pvp_info['detail_info']['perfect_win'] += 1
    if int(params.get('bb_win',0)):
        user_pvp_obj.pvp_info['detail_info']['bb_win'] += 1
    if int(params.get('max_spark_time',0)):
        if int(params.get('max_spark_time',0)) > user_pvp_obj.pvp_info['detail_info']['max_spark_time']:
            user_pvp_obj.pvp_info['detail_info']['max_spark_time'] = int(params.get('max_spark_time',0))
    if int(params.get('one_bout_max_attack',0)):
        if int(params.get('one_bout_max_attack',0)) > user_pvp_obj.pvp_info['detail_info']['one_bout_max_attack']:
            user_pvp_obj.pvp_info['detail_info']['one_bout_max_attack'] = int(params.get('one_bout_max_attack',0))
    if int(params.get('kill_attack',0)):
        user_pvp_obj.pvp_info['detail_info']['kill_attack'] += int(params.get('kill_attack',0))
    if int(params.get('total_attack',0)):
        user_pvp_obj.pvp_info['detail_info']['total_attack'] += int(params.get('total_attack',0))
    if int(params.get('total_recover',0)):
        user_pvp_obj.pvp_info['detail_info']['total_recover'] += int(params.get('total_recover',0))
    if int(params.get('total_spark_time',0)):
        user_pvp_obj.pvp_info['detail_info']['total_spark_time'] += int(params.get('total_spark_time',0))
    if int(params.get('BB_total_time',0)):
        user_pvp_obj.pvp_info['detail_info']['BB_total_time'] += int(params.get('BB_total_time',0))
    for i in range(1,7):
        user_pvp_obj.pvp_info['detail_info']['property_kill'][str(i)] += int(params.get('%s_property_kill'%i,0))
    for i in range(1,6):
        user_pvp_obj.pvp_info['detail_info']['star_kill'][str(i)] += int(params.get('%s_star_kill'%i,0))
    user_pvp_obj.put()


    data_log_mod.set_log('PvpRecord', rk_user,
                        user_level=rk_user.user_property.lv,
                        statament=self_result,
                        card_deck=rk_user.user_cards.deck,
                        pvp_pt=user_pvp_obj.pt,
                        pvp_level=user_pvp_obj.pvp_level,
                        renown=rk_user.user_pvp.get_renown(),
    )
    #交换对手的排名，0为交换失败，1为交换成功
    if self_result == 'win':
        if 'npc' in opponent_uid:
            opponent_uid = "@" + opponent_uid
        crc = top_model.pvp_exchange(self_uid, self_rank, opponent_uid, opponent_rank)
        if not crc:
            return 11,{'msg':utils.get_msg('pvp', 'invalid_opponent')}

        if user_pvp_obj.set_history_max_rank(opponent_rank):
            pvp_rank_awards = utils.get_rank_awards_by_rank(opponent_rank)
            sid = 'system_%s' % (utils.create_gen_id())
            content=u'擂台排名提升至：%s\n来自：系统奖励\n%s'%(str(opponent_rank), str(datetime.datetime.now())[:16])
            user_mail_obj = UserMail.hget(self_uid, sid)
            user_mail_obj.set_mail(type='system',content=content,award=pvp_rank_awards['awards'])

        if not "npc" in opponent_uid:
            opponent_user_base = UserBase.get(opponent_uid)
            content=u'擂台排名变化\n挑战者：%s\n%s'%( opponent_user_base.username,str(datetime.datetime.now())[:16])
            user_mail_obj = UserMail.hget(opponent_uid, self_uid)
            user_mail_obj.set_mail(type='pvp',content=content)
            user_mail_obj.set_pvprank_record(str(datetime.datetime.now())[:16], opponent_rank)

        user_pvp_obj.record_pvp_back(opponent_uid)

    data['update_award'] = update_award
    data['get_pvp_opponents'] = {}
    data['get_pvp_opponents']['self_rank'] = user_pvp_obj.pvp_rank()
    data['get_pvp_opponents']['pvp_opponents'] = user_pvp_obj.get_arena_opponents()
    data['get_pvp_opponents']['renown'] = user_pvp_obj.get_renown()
    return 0, data

def recover_pvp_stamina(rk_user,params):
    recove_pvp_stamina_coin = game_config.pvp_config.get('recove_pvp_stamina_coin',1)
    user_pvp_obj = UserPvp.get(rk_user.uid)
    if user_pvp_obj.pvp_stamina >= user_pvp_obj.max_pvp_stamina:
        return 11,{'msg':utils.get_msg('pvp','pvp_stamina_full')}
    #miaoyichao start
    if not vip.check_limit_recover(rk_user,'recover_pvp_stamina'):
        return 11,{'msg':utils.get_msg('user','max_times')}
    #回复次数+1
    rk_user.user_property.add_recover_times('recover_pvp_stamina')
    #miaoyichao end
    #扣除元宝
    if not UserProperty.get(rk_user.uid).minus_coin(recove_pvp_stamina_coin,'recover_pvp_stamina'):
        return 11,{'msg':utils.get_msg('user','not_enough_coin')}
    user_pvp_obj.recover_pvp_stamina()
    data_log_mod.set_log("ConsumeRecord", rk_user, 
                        lv=rk_user.user_property.lv,
                        num=recove_pvp_stamina_coin,
                        consume_type='recover_pvp_stamina',
                        before_coin=rk_user.user_property.coin + recove_pvp_stamina_coin,
                        after_coin=rk_user.user_property.coin
    )

    return 0 ,{}


def top_pvp(rk_user,params):
    data = {'friend':[],'all_player':[]}
    friend = Friend.get(rk_user.uid)
    tmp = {}
    #好友的排行情况
    for uid in friend.friends.keys()+[rk_user.uid]:
        if uid == rk_user.uid:
            pvp_obj = UserPvp.get(uid)
        else:
            pvp_obj = UserPvp.getEx(uid)
        if pvp_obj:
            base_info = pvp_obj.pvp_info['base_info']
            tmp[uid] = {}
            if rk_user.uid == uid:
                tmp[uid]['self'] = True
            user_base_obj = UserBase.get(uid)
            tmp[uid]['pt'] = base_info['pt']
            tmp[uid]['win'] = base_info['win']
            tmp[uid]['lose'] = base_info.get('lose',0)
            tmp[uid]['pvp_title'] = base_info['pvp_title']
            tmp[uid]['name'] = user_base_obj.username
            tmp[uid]['leader_card'] = user_base_obj.user_property.leader_card
            tmp[uid]['lv'] = user_base_obj.user_property.lv
    data['friend'] = [ i[1] for i in sorted(tmp.items(),key=lambda d:d[1]['pt'],reverse=True)]
    #前十的排行情况
    top_model = pvp_redis.get_pvp_redis(rk_user.subarea)
    top_30_uid_score = top_model.get(30, desc=False)
    top_30_uids = [ uid for uid,score in top_30_uid_score]
    if not rk_user.uid in top_30_uids:
        top_30_uids += [rk_user.uid]
    for uid in top_30_uids:
        pvp_obj = UserPvp.getEx(uid)
        ub_obj = UserBase.get(uid)
        if pvp_obj and ub_obj:
            user_prop_obj = UserProperty.get(uid)
            tmp = {}
            base_info = pvp_obj.pvp_info['base_info']
            tmp['pt'] = base_info['pt']
            tmp['win'] = base_info['win']
            tmp['lose'] = base_info.get('lose',0)
            tmp['pvp_title'] = base_info['pvp_title']
            tmp['name'] = ub_obj.username
            tmp['leader_card'] = user_prop_obj.leader_card
            tmp['lv'] = user_prop_obj.lv
            if uid == rk_user.uid:
                rank = rk_user.user_pvp.pvp_rank()
                tmp['self'] = True
                tmp['rank'] = rank
            data['all_player'].append(tmp)
    return 0,data

def __check_end(rk_user, params):
    """检查是否能够胜利完成pvp
    """
    #检查用户武将数量是否已经超过上限
    user_card_obj = UserCards.get(rk_user.uid)
    if user_card_obj.arrive_max_num():
        return 11,utils.get_msg('card','max_num')
    # #检查用户统御力是否超出
    # if user_card_obj.arrive_max_cost():
    #     return 11,utils.get_msg('card','over_cost')

    #用户等级达到8级后开放”擂台”功能
    if rk_user.user_property.lv < 8:
        return 11,utils.get_msg('user', 'not_enough_lv')
    #无效的参数
    if not 'self_rank' in params or not 'player_uid' in params or not 'player_rank' in params:
        return 11,utils.get_msg('pvp', 'invalid_opponent')
    player_uid = str(params['player_uid'])
    #监测出战场请求的对手id是否合法
    if not player_uid or rk_user.user_pvp.get_pvp_vs_player() != player_uid:
        return 12,utils.get_msg('pvp', 'invalid_opponent')
    self_rank = rk_user.user_pvp.pvp_rank()
    if self_rank != int(params['self_rank']):
        return 13,utils.get_msg('pvp', 'invalid_opponent')
    #监测对手是否是可以挑战的排名
    top_model = pvp_redis.get_pvp_redis(rk_user.subarea)
    #获得可pvp的对手id列表
    arena_opponents_list = top_model.get_arena_opponents_uids(self_rank)
    fg = False
    for (rank, name) in arena_opponents_list:
        if rank == int(params['player_rank']):
            fg = True
    if not fg:
        return 14,utils.get_msg('pvp', 'invalid_opponent')
    return 0, ""

def get_pvp_opponents(rk_user,params):
    """获得对手的信息
        return:{ rank:{
            player_uid:对手id
            user_lv：对手等级
            user_name：对手名字
            user_decks:编队信息
            gold: 铜钱
            pt: 名声
            }
        }
    """
    data = {}
    data['pvp_opponents'] = rk_user.user_pvp.get_arena_opponents()
    data['self_rank'] = rk_user.user_pvp.pvp_rank()
    data['renown'] = rk_user.user_pvp.get_renown()
    return 0, data
