#-*- coding: utf-8 -*-
import time
import copy
import random
from apps.models.user_property import UserProperty
from apps.models.user_base import UserBase
from apps.models.user_login import UserLogin
from apps.models.user_dungeon import UserDungeon
from apps.models.friend import Friend
from apps.models.level_user import LevelUser
from apps.common import utils
from apps.config.game_config import game_config
from apps.models.user_gift import UserGift
from apps.models.user_pvp import UserPvp
from apps.models import data_log_mod


#def extend(rk_user,params):
#    """
#    消耗元宝扩展好友
#    """
#    max_friend_extend_num = game_config.system_config.get('max_friend_extend_num',0)
#    friend_extend_num = game_config.system_config.get('friend_extend_num',0)
#    #判断是否达到扩展上限
#    if rk_user.user_property.friend_extend_num+friend_extend_num > max_friend_extend_num:
#        return 11,{'msg':utils.get_msg('friend','cannot_extend')}
#    #判断元宝是否足够
#    friend_extend_coin = game_config.system_config.get('friend_extend_coin',0)
#    if not rk_user.user_property.minus_coin(friend_extend_coin,'friend_extend_coin'):
#        return 11,{'msg':utils.get_msg('user','not_enough_coin')}
#    #扩展好友
#    rk_user.user_property.extend_friend_num(friend_extend_num)
#    #记录消费
#    ConsumeRecord.set_consume_record(rk_user.uid,rk_user.subarea,rk_user.user_property.lv,friend_extend_coin,\
#     'extendFriend',rk_user.user_property.coin + friend_extend_coin,rk_user.user_property.coin)
#    return 0,{}


def del_request(rk_user,params):
    """
    撤销请求
    """
    fid = params.get('fid','')
    if fid:
        user_friend_obj = Friend.get(rk_user.uid)
        if fid in user_friend_obj.self_requests:
            user_friend_obj.self_requests.pop(fid)
            user_friend_obj.put()
        friend_friend_obj = Friend.get(fid)
        friend_friend_obj.del_request(rk_user.uid)
    return 0,{}



def add_request(rk_user,params):
    """
    添加好友的请求
    """
    fid = params.get('fid','')
    #检查好友id是否存在

    if 'npc' in fid:
        return 0, {}

    friend_user = UserBase.get(fid)
    if not friend_user:
        return 11,{'msg':utils.get_msg('user','no_user')}
    rc,msg = __check_can_add_friend(rk_user,friend_user)
    if rc:
        return rc,{'msg':msg}
    else:
        user_friend_obj = Friend.get(rk_user.uid)
        friend_friend_obj = Friend.get(fid)
        #如果对方申请过加自己为好友，则直接建立好友关系
        if fid in user_friend_obj.requests:
            #将对方加入到自己的好友列表
            user_friend_obj.add_friend(fid)
            #将自己加入到对方的好友列表
            friend_friend_obj.add_friend(rk_user.uid)
            #将对方从自己的申请列表中删除
            user_friend_obj.del_request(fid)
            #将自己从好友的申请列表中删除
            friend_friend_obj.del_self_request(rk_user.uid)
        else:
            user_friend_obj.self_requests[fid] = int(time.time())
            user_friend_obj.put()
            friend_friend_obj.add_request(rk_user.uid)
        return 0,{}

def __check_can_add_friend(rk_user,friend):
    """
    检查是否可以添加好友
    """
    #好友id不能是自己
    if rk_user.uid == friend.uid:
        return 11,utils.get_msg('friend','cannot_self')
    user_friend_obj = Friend.get(rk_user.uid)
    #已经添加过的好友不能再添加
    if friend.uid in user_friend_obj.friends:
        return 11,utils.get_msg('friend','already_friend')
    #检查自己是否已经达到最大好友数量
    if user_friend_obj.friend_num >= rk_user.user_property.max_friend_num:
        return 11,utils.get_msg('friend','self_max_friend')
    #检查对方是否已经达到最大好友数量
    friend_friend_obj = Friend.getEx(friend.uid)
    friend_property = UserProperty.get(friend.uid)
    if friend_friend_obj.friend_num >= friend_property.max_friend_num:
        return 11,utils.get_msg('friend','other_max_friend')
    return 0,''

def accept_request(rk_user,params):
    """
    同意好友申请
    """
    fid = params['fid']
    user_friend_obj = Friend.get(rk_user.uid)
    #检查是否有这条请求
    if not fid in user_friend_obj.requests:
        return 11,{'msg':utils.get_msg('friend','no_request')}
    friend_obj = UserBase.get(fid)
    friend_friend_obj = Friend.get(fid)
    rc,msg = __check_can_add_friend(rk_user,friend_obj)
    if rc:
        return rc,{'msg':msg}
    else:
        #将对方加入到自己的好友列表
        user_friend_obj.add_friend(fid)
        #将自己加入到对方的好友列表
        friend_friend_obj.add_friend(rk_user.uid)
        if rk_user.uid in friend_friend_obj.self_requests:
            friend_friend_obj.self_requests.pop(rk_user.uid)
            friend_friend_obj.put()
        #将对方从自己的申请列表中删除
        user_friend_obj.del_request(fid)
        return 0,{}

def refuse_request(rk_user,params):
    """
    拒绝好友申请
    """
    fid = params['fid']
    Friend.get(rk_user.uid).del_request(fid)
    friend_friend_obj = Friend.get(fid)
    if rk_user.uid in friend_friend_obj.self_requests:
        friend_friend_obj.self_requests.pop(rk_user.uid)
        friend_friend_obj.put()
    return 0,{}

def del_friend(rk_user,params):
    """
    删除好友
    """
    fid = params['fid']
    user_friend_obj = Friend.get(rk_user.uid)
    if user_friend_obj.is_lock(fid):
        return 11,{'msg':utils.get_msg('friend','is_locked')}
    Friend.get(fid).del_friend(rk_user.uid)
    user_friend_obj.del_friend(fid)
    return 0,{}

def get_friend_list(rk_user,params):
    """获取好友列表
    """
    data = {'friends':[]}
    user_friend_obj = Friend.get(rk_user.uid)
    for fid in user_friend_obj.get_friend_ids():
        friend_user = UserBase.get(fid)
        friend_property = UserProperty.get(fid)
        leader_card = friend_property.leader_card
        user_pvp_obj = UserPvp.getEx(fid)
        if user_pvp_obj:
            pvp_title = user_pvp_obj.pvp_title
        else:
            pvp_title = ''
        temp = {
            'fid':fid,
            'name':friend_user.username,
            'country':friend_property.country,
            'leader_card':leader_card,
            'lv':friend_property.lv,
            'login_time':friend_property.login_time,
            'want_gift':Friend.getEx(fid).friend_gift.get('want_gift',['','','']),
            'signature':friend_user.signature,
            'lock':user_friend_obj.is_lock(fid),
            'pvp_title':pvp_title,
        }
        data['friends'].append(temp)
    data['now_num'] = len(data['friends'])
    data['max_num'] = rk_user.user_property.max_friend_num
    return 0,data

def search_friend(rk_user,params):
    """查找好友
    """
    fid = params['fid']
    try:
        fid = str(fid)
    except:
        return 11,{'msg':utils.get_msg('friend','invalid_fid')}
    friend_user = UserBase.get(fid)
    if not friend_user:
        return 11,{'msg':utils.get_msg('user','no_user')}
    friend_friend_obj = Friend.getEx(fid)
    friend_property = UserProperty.get(fid)
    leader_card = friend_property.leader_card
    user_pvp_obj = UserPvp.getEx(fid)
    if user_pvp_obj:
        pvp_title = user_pvp_obj.pvp_title
    else:
        pvp_title = ''
    data = {
        'friend_info':{
            'fid':fid,
            'name':friend_user.username,
            'country':friend_property.country,
            'leader_card':leader_card,
            'lv':friend_property.lv,
            'max_friend_num':friend_property.max_friend_num,
            'now_friend_num':friend_friend_obj.friend_num,
            'signature':friend_user.signature,
            'pvp_title':pvp_title,
        }
    }
    return 0,data

def get_request_list(rk_user,params):
    """获取申请列表以及自己申请的
    """
    data = {'self_requests':[],'friend_requests':[]}
    user_friend_obj = Friend.get(rk_user.uid)
    for fid in user_friend_obj.self_requests:
        request_friend_user = UserBase.get(fid)
        if not request_friend_user:
            continue
        request_friend_property = UserProperty.get(fid)
        leader_card = request_friend_property.leader_card
        temp = {
            'fid':fid,
            'name':request_friend_user.username,
            'country':request_friend_property.country,
            'leader_card':leader_card,
            'lv':request_friend_property.lv,
            'request_time':user_friend_obj.self_requests[fid],
        }
        data['self_requests'].append(temp)
    fids = user_friend_obj.get_request_ids()
    for fid in fids:
        friend_user = UserBase.get(fid)
        if not friend_user:
            continue
        friend_property = UserProperty.get(fid)
        leader_card = friend_property.leader_card
        temp = {
            'fid':fid,
            'name':friend_user.username,
            'country':friend_property.country,
            'leader_card':leader_card,
            'lv':friend_property.lv,
            'request_time':user_friend_obj.requests[fid],
        }
        data['friend_requests'].append(temp)
    return 0,data

def _check_invite_code(rk_user,invite_code):
    """检查
    """
    uid = ''
    if invite_code:
        try:
            invite_code = invite_code.lower()
            inviter_uid = str(int(invite_code,16))
            inviter = UserBase.get(inviter_uid)
            if inviter and inviter_uid != rk_user.uid:
                uid = inviter_uid
        except:
            pass
    return uid

def get_invite_award(rk_user,params):
    """新手的邀请奖励
    """
    invite_code = params['invite_code']
    uid = _check_invite_code(rk_user,invite_code)
    friend_obj = Friend.get(rk_user.uid)
    if uid and not friend_obj.invite_info['inviter']:
        #记录邀请新手的老玩家信息
        friend_obj.invite_info['inviter'] = uid
        friend_obj.put()

        data_log_mod.set_log('Invite', rk_user, inviter=uid, invited=rk_user.uid)

        #邀请者总邀请数增加
        inviter_friend = Friend.get(uid)
        inviter_friend.invite_info['total_invited_usernum'] += 1
        inviter_friend.record_invited_user(rk_user.uid,rk_user.user_property.lv)
        inviter_friend.put()
        #发邀请奖励
        invited_award = game_config.invite_config['invited_award']
        user_gift_obj = UserGift.get_instance(rk_user.uid)
        user_gift_obj.add_gift(invited_award,utils.get_msg('friend','invited_award_words'))
    else:
        if not uid:
            return 11,{'msg':utils.get_msg('friend', 'invalid_invite_code')}
        else:
            return 11,{'msg':utils.get_msg('friend', 'invite_code_only_once')}
    return 0,{}

def get_invite_info(rk_user,params):
    """
    获取邀请信息
    params:无
    return：
        total_invited_usernum:总邀请人数
        invite_award：邀请奖励信息
                    [{
                        'award_id':'1',#奖励id
                        'type':1,类型对应宝箱图片
                        'content':'xxxxx',宝箱里的物品
                        'condition':'领取条件',
                        'can_get':False,#能否领取
                        'has_got':True,是否已领取
                        
                    },
                    {
                        'award_id':'2',#奖励id
                        'type':1,类型对应宝箱图片
                        'content':'xxxxx',宝箱里的物品
                        'condition':'领取条件',
                        'can_get':False,#能否领取
                        'has_got':True,是否已领取
                        
                    }
                    ]
    """
    data = {}
    friend_obj = Friend.get(rk_user.uid)
    if not friend_obj:
        return 0,{}
    invite_info = friend_obj.invite_info
    #总邀请人数
    data['total_invited_usernum'] = invite_info['total_invited_usernum']
    #是否可以填邀请码
    if friend_obj.invite_info['inviter']:
        data['can_invite_code'] = False
    else:
        data['can_invite_code'] = True
    #邀请奖励
    data['invite_award'] = []
    invite_award = game_config.invite_config['invite_award']
    for _id in sorted([int(i) for i in invite_award]):
        _val = invite_award[str(_id)]
        #判断等级以及达到等级的人数
        tmp = {}
        tmp['type'] = _val['type']
        tmp['content'] = _val.get('content','')
        tmp['condition'] = _val.get('condition','')
        tmp['can_get'] = False
        tmp['has_got'] = False
        tmp['award_id'] = str(_id)
        if str(_id) in invite_info['got_invite_award']:
            tmp['can_get'] = False
            tmp['has_got'] = True
        else:
            need_lv = int(_val.get('lv',1))
            if need_lv:
                need_lv_str = str(need_lv)
                if need_lv_str in invite_info['invite_users'] and \
                  len(invite_info['invite_users'][need_lv_str])>=_val.get('invite_num',0) and \
                  _val.get('award',{}):
                    tmp['can_get'] = True
            else:
                if invite_info['total_invited_usernum'] >= _val.get('invite_num',0) and \
                 _val.get('award',{}):
                    tmp['can_get'] = True
        data['invite_award'].append(tmp)
    return 0,data
                
def get_invite_friend_award(rk_user,params):       
    """
    领取邀请好友的奖励
    params:
       'award_id':奖励id
    """     
    friend_obj = Friend.get(rk_user.uid)
    if not friend_obj:
        return 0,{}
    invite_award = game_config.invite_config['invite_award']
    award_id = params.get('award_id')
    if award_id and award_id in invite_award:
        invite_info = friend_obj.invite_info
        #已经领取过
        if award_id in invite_info['got_invite_award']:
            return 11,{'msg':utils.get_msg('friend', 'invite_award_has_got')}
        
        invite_award_val = invite_award[award_id]
        need_lv = int(invite_award_val.get('lv',1))
        can_get = False
        if need_lv:
            need_lv_str = str(need_lv)
            if need_lv_str in invite_info['invite_users'] and \
              len(invite_info['invite_users'][need_lv_str])>=invite_award_val.get('invite_num',0) and \
              invite_award_val.get('award',{}):
                can_get = True
        else:
            if invite_info['total_invited_usernum'] >= invite_award_val.get('invite_num',0) and \
              invite_award_val.get('award',{}):
                can_get = True
        #can_get = True#测试需要暂时可以领取
        if can_get:
            user_gift_obj = UserGift.get_instance(rk_user.uid)
            invite_info['got_invite_award'].append(award_id)
            friend_obj.put()
            user_gift_obj.add_gift(invite_award_val['award'],utils.get_msg('friend','invite_award_words'))
        else:
            return 11,{'msg':utils.get_msg('friend', 'invite_award_cannot_get')}
    else:
        return 11,{'msg':utils.get_msg('friend', 'invite_award_err')}
    return 0,{}
                
    
def __remove_null(_list):
    """去空
    """
    return [ i for i in _list if i ]

def __check_want_gift(want_ls,friend_gift_conf,_split='-'):
    """
    检查礼物列表是否正确
    """
    if len(want_ls)<0 or len(want_ls)>3:
        return 11,utils.get_msg('friend','gift_num_err')
    for want_item in want_ls:
        if want_item in ['stone','gold','gacha_pt']:
            if want_item not in friend_gift_conf:
                return 11,utils.get_msg('friend','gift_not_exist')
        elif want_item.startswith('m'+_split):
            m,ma_id = want_item.split(_split)
            if ma_id not in friend_gift_conf.get('material',{}):
                return 11,utils.get_msg('friend','gift_not_exist')
        elif want_item:
            return 11,utils.get_msg('friend','gift_not_exist')
    return 0,''

def __check_send_gift(send_ls,friend_gift_conf,_split='-'):
    """
    检查礼物列表是否正确
    """
    for want_item in send_ls:
        if want_item in ['stone','gold','gacha_pt']:
            if want_item not in friend_gift_conf:
                return 11,utils.get_msg('friend','gift_not_exist')
        elif want_item.startswith('m'+_split):
            m,ma_id = want_item.split(_split)
            if ma_id not in friend_gift_conf.get('material',{}):
                return 11,utils.get_msg('friend','gift_not_exist')
        elif want_item:
            return 11,utils.get_msg('friend','gift_not_exist')
    return 0,''

def __check_send_fids(fids,friend_obj):
    """
    检查好友是否合法
    """
    send_fids = friend_obj.friend_gift['send_fids']
    for fid in fids:
        #当天只能送给同一个好友一次
        if fid in send_fids:
            return 11,utils.get_msg('friend','send_gift_err')
        #不能送给非好友
        friend_friend_obj = Friend.get(fid)
        if not friend_friend_obj or fid not in friend_obj.friends:
            return 11,utils.get_msg('friend','not_friend')
        if friend_friend_obj.has_gift_from(friend_obj.uid):
            return 11,utils.get_msg('friend','send_gift_err')
    return 0,''

def get_friend_gift(rk_user,params):
    """
    获取好友礼物信息
    """
    friend_obj = Friend.get(rk_user.uid)
    friend_gift = friend_obj.friend_gift
    data = {
           'want_gift':friend_gift['want_gift'],
           'gift_award':friend_gift['gift_award'],
           'send_to_fids':friend_gift['send_fids'],
           }
    return 0,data

def gift(rk_user,params):
    """
    互赠礼物接口
    params：
       want: gold,stone,m:1_mat
       send: uid:gold,uid:stone,uid:m-1_mat,uid:m-2_mat
       get_gift:uid,uid,uid,uid
    """
    want_str = params.get('want','')
    #处理希望得到的礼物
    friend_obj = Friend.get(rk_user.uid)
    friend_gift_conf = copy.deepcopy(game_config.invite_config['friend_gift_conf'])
    pt_fg = False
    if want_str:
        want_ls = want_str.split(',')
        ret,msg = __check_want_gift(want_ls,friend_gift_conf)
        if ret:
            return ret,{'msg':msg}
        friend_obj.friend_gift['want_gift'] = want_ls
        pt_fg = True
    #赠送礼物
    send_str = params.get('send','')
    if send_str:
        send_ls = __remove_null(send_str.split(','))
        fids = []
        send_gifts = []
        for send_item in send_ls:
            fid,gift = send_item.split(':')
            fids.append(fid)
            send_gifts.append(gift)
        if len(fids) != len(send_gifts) or len(fids) != len(set(fids)):
            return 11,{'msg':utils.get_msg('friend','send_gift_err')}
        ret,msg = __check_send_gift(send_gifts,friend_gift_conf,'-')
        if ret:
            return ret,{'msg':msg}
        ret,msg = __check_send_fids(fids,friend_obj)
        if ret:
            return ret,{'msg':msg}
        for fid in fids:
            friend_friend_obj = Friend.get(fid)
            gift = send_gifts[fids.index(fid)]
            tmp_gift = {}
            if gift in ['gold', 'stone','gacha_pt']:
                tmp_gift[gift] = friend_gift_conf[gift]
            elif gift.startswith('m-'):
                m,ma_id = gift.split('-')
                tmp_gift['material'] = {ma_id:friend_gift_conf['material'][ma_id]}
            friend_friend_obj.friend_gift['gift_award'][rk_user.uid] = {
                                                                'award':tmp_gift,
                                                                'name':rk_user.username,
                                                                'leader_card':rk_user.user_property.leader_card,
                                                                }
            friend_friend_obj.friend_gift['receive_fids'].append(rk_user.uid)
            friend_friend_obj.put()
            friend_obj.friend_gift['send_fids'].append(fid)
            pt_fg = True
    #领取礼物
    get_gift_str = params.get('get_gift','')
    if get_gift_str:
        fids_ls = __remove_null(get_gift_str.split(','))
        #检查是否有重复的
        if len(fids_ls) != len(set(fids_ls)):
            return 11,{'msg':utils.get_msg('friend','get_gift_err')}
        gift_award = friend_obj.friend_gift['gift_award']
        #检查是否有不存在的
        if [k for k in fids_ls if k not in gift_award]:
            return 11,{'msg':utils.get_msg('friend','get_gift_err')}
        for fid in fids_ls:
            rk_user.user_property.give_award(gift_award[fid]['award'])
            gift_award.pop(fid)
            pt_fg = True
    if pt_fg:
        friend_obj.put()
    return 0,{}

def lock_friend(rk_user,params):
    """
    锁定好友
    """
    fid = params['fid']
    fg = Friend.get(rk_user.uid).lock(fid)
    if not fg:
        return 11,{'msg':utils.get_msg('friend','not_friend')}
    return 0,{}
