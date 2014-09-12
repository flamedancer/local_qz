#!/usr/bin/env python
# encoding: utf-8
"""
friend.py
"""
import datetime
import time
from apps.common import utils
from apps.oclib.model import UserModel
from apps.config.game_config import game_config

class Friend(UserModel):
    """用户好友信息

    Attributes:
        uid: 用户ID str
        friend_ids: 平台好友 list
    """
    pk = 'uid'
    fields = ['uid','friends','requests','self_requests','friend_gift','lock_friends','invite_info']
    def __init__(self):
        """初始化用户好友信息

        Args:
            uid: 平台用户ID
        """
        self.uid = None
        self.friends = {}
        self.requests = {}
        self.self_requests = {}
        self.lock_friends = []
        self.friend_gift = {
                            'upd_time':utils.get_today_str(),
                            'send_fids':[],#已经送出的好友列表
                            'receive_fids':[],#已经收到的好友列表
                            'want_gift':['','',''],#想要的礼物
                            'gift_award':{},#收到的礼物
                            }
        self.invite_info = {
                                'inviter':'',
                                'got_invite_award':[],
                                'invite_users':{},
                                'total_invited_usernum':0,
                                'reset_invite_date': '2013',
                            }
        
    @classmethod
    def get_instance(cls,uid):

        obj = super(Friend,cls).get(uid)
        if obj is None:
            obj = cls._install(uid)

        return obj

    @classmethod
    def get(cls,uid):
        obj = super(Friend,cls).get(uid)
        if obj:
            obj.refresh_info()
        return obj
    
    @classmethod
    def getEx(cls,uid):
        obj = super(Friend,cls).get(uid)
        return obj

    @classmethod
    def _install(cls,uid):
        """为新用户初始安装好友信息

        Args:
            uid: 用户ID

        Returns:
            friend: 用户好友信息对象实例
        """
        friend = cls()
        friend.uid = uid
        friend.friends = {}
        friend.requests = {}
        friend.self_requests = {}
        friend.lock_friends = []
        friend.friend_gift = {
                            'upd_time':utils.get_today_str(),
                            'send_fids':[],#已经送出的好友列表
                            'receive_fids':[],#已经收到的好友列表
                            'want_gift':['','',''],#想要的礼物
                            'gift_award':{},#收到的礼物
                            }
        friend.invite_info = {
                                'inviter':'',
                                'got_invite_award':[],
                                'invite_users':{},
                                'total_invited_usernum':0,
                            }
        friend.put()

        return friend

    def refresh_info(self):
        """
        刷新信息
        """
        today_str = utils.get_today_str()
        if today_str != self.friend_gift['upd_time']:
            self.friend_gift['upd_time'] = today_str
            self.friend_gift['send_fids'] = []
            self.friend_gift['receive_fids'] = []
            self.put()
    

    @property
    def inviter(self):
        return self.invite_info.get('inviter','')
    
    def record_invited_user(self, uid, lv):
        """
        记录邀请的用户等级信息
        """
        pt_fg = False
        invite_award = game_config.invite_config['invite_award']
        for _id,_val in invite_award.iteritems():
            need_lv = int(_val.get('lv',1))
            if lv >= need_lv:
                need_lv_str = str(need_lv)
                if self.invite_info['invite_users'].get(need_lv_str,[]):
                    if uid not in self.invite_info['invite_users'][need_lv_str]:
                        self.invite_info['invite_users'][need_lv_str].append(uid)
                        pt_fg = True
                else:
                    self.invite_info['invite_users'][need_lv_str] = [uid]
                    pt_fg = True
        if pt_fg:
            self.put()
            
    def lock(self,fid):
        """
        锁定，解锁好友
        """
        if fid not in self.friends:
            return False
        if fid in self.lock_friends:
            self.lock_friends.remove(fid)
        else:
            self.lock_friends.append(fid)
        self.put()
        return True

    def is_lock(self,fid):
        """
        是否锁定
        """
        return fid in self.lock_friends

    def has_gift_from(self,fid):
        """
        是否已经收到了好友送的礼物
        """
        if fid in self.friend_gift['receive_fids']:
            return True
        return False

    def add_friend(self,fid):
        """
        添加好友
        """
        self.friends[fid] = None
        self.put()

    def del_friend(self,fid):
        """
        删除好友
        """
        if fid in self.friends:
            self.friends.pop(fid)
            self.put()

    @property
    def friend_num(self):
        return len(self.friends)

    def add_request(self,fid):
        """'
        添加好友请求
        """
        time_now = int(time.time())
        self.requests[fid] = time_now
        max_request_num = game_config.system_config.get('max_friend_request',30)
        if len(self.requests) > max_request_num:
            self.requests.pop(self.get_request_ids()[-1])
        self.put()

    def del_request(self,fid):
        """
        删除好友请求
        """
        if fid in self.requests:
            self.requests.pop(fid)
            self.put()
            
    def del_self_request(self,fid):
        """
        删除自己发出的申请
        """
        if fid in self.self_requests:
            self.self_requests.pop(fid)
            self.put()

    def get_friend_ids(self):
        """获取好友id列表
        """
        return self.friends.keys()

    def get_request_ids(self):
        """获取好友申请列表
        """
        fids = self.requests.keys()
        fids.sort(key=lambda x:self.requests[x],reverse=True)
        return fids

    def set_borrow_friend(self,helper_id):
        """更新借好友卡的时间
        """
        if helper_id in self.friends:
            self.friends[helper_id] = int(time.time())
            self.put()

    def get_gift_num(self):
        return len(self.friend_gift['gift_award'])

    def is_friend(self,uid):
        return uid in self.friends

    @property
    def user_base(self):
        if not hasattr(self, '_user_base'):
            from apps.models.user_base import UserBase
            self._user_base = UserBase.get(self.uid)
        return self._user_base

    def getreset_invite_date(self):
        if not 'reset_invite_date' in self.invite_info:
            self.invite_info['reset_invite_date'] = '2013'
            self.put()
        return self.invite_info['reset_invite_date']

    def recordreset_invite_date(self):
        self.invite_info['reset_invite_date'] = str(datetime.datetime.now())
        self.put()
