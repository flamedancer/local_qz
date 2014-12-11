#!/usr/bin/env python
# encoding: utf-8

from apps.oclib.model import HashModel
from apps.common import utils
import datetime


class UserMail(HashModel):
    """
    用户游戏内部基本信息
    """
    pk = 'uid'
    opk = 'ouid'    #对方的uid, opposite uid
    fields = ['uid','ouid', 'mail_info']

    @classmethod
    def hget(cls,pk,opk):
        obj = super(UserMail,cls).hget(pk,opk)
        if obj is None:
            obj = cls.create(pk,opk)
        return obj

    @classmethod
    def create(cls,pk,opk):
        obj = cls()
        obj.uid = pk
        obj.ouid = opk
        obj.mail_info = {
        }
        return obj

    def set_mail(self, mailtype, title, content, award=None, can_get=True, awards_description='', create_time=""):
        self.mail_info['type'] = mailtype
        self.mail_info['title'] = title
        self.mail_info['content'] = content
        self.mail_info['awards'] = award
        self.mail_info['can_get'] = can_get
        self.mail_info['create_time'] = create_time or datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.mail_info['mid'] = utils.create_gen_id()
        self.hput()

    def set_pvprank_record(self, date, rank):
        if not 'pvprank_record' in self.mail_info:
            self.mail_info['pvprank_record'] = {}
        self.mail_info['pvprank_record'][date] = rank
        self.hput()

    @classmethod
    def hgetall(cls, pk):
        all_data = super(UserMail,cls).hgetall(pk)
        if all_data is None:
            all_data = {}
        return all_data

    @classmethod
    def new_mail_num(cls, pk):
        """ 未读邮件数量"""
        num = 0
        all_mail_data = UserMail.hgetall(pk)
        for all_mail in all_mail_data.values():
            info = all_mail['mail_info']
            num = (num + 1) if info['can_get'] else num
        return num
