#!/usr/bin/env python
# encoding: utf-8

from apps.oclib.model import HashModel
import copy
import datetime
from apps.common.utils import create_gen_id

class UserMail(HashModel):
    """
    用户游戏内部基本信息
    """
    pk = 'uid'
    opk = 'ouid'
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

    def set_mail(self, mailtype, content, award=None, can_get=True, awards_description='', create_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')):
        self.mail_info['type'] = mailtype
        self.mail_info['content'] = content
        self.mail_info['awards'] = award
        self.mail_info['can_get'] = can_get
        self.mail_info['awards_description'] = self.set_awards_description(award)
        self.mail_info['mid'] = create_gen_id()
        self.mail_info['create_time'] = create_time
        self.hput()

    def set_pvprank_record(self, date, rank):
        if not 'pvprank_record' in self.mail_info:
            self.mail_info['pvprank_record'] = {}
        self.mail_info['pvprank_record'][date] = rank
        self.hput()

    @classmethod
    def hgetall(cls,pk):
        all_data = super(UserMail,cls).hgetall(pk)
        if all_data is None:
            all_data = {}
        return all_data

    def set_awards_description(self, award):
        awards = copy.deepcopy(award)
        if not awards:
            awards = {
                'gold': 1,#
            }
        awards_description = u'恭喜您， 你将获得以下奖励：\n'
        blen = len(awards_description)
        for a in awards:
            if a == 'renown':
                awards_description += u'声望 * ' + str(awards[a]) + '\n'
            elif a == 'gold':
                awards_description += u'铜钱 * ' + str(awards[a]) + '\n'
            elif a == 'honor':
                awards_description += u'功勋 * ' + str(awards[a]) + '\n'
            
        if len(awards_description) == blen:
            return ''
        return awards_description                    
