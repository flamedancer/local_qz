#!/usr/bin/env python
#coding=utf8
"""
Will be used by PyCaptacha.Captcha.Base.Factory

"""
from apps.oclib.model import BaseModel
import pickle


class RedisCaptchaDict(BaseModel):
    ''' just to save in redis:
        captcha_dict[captcha_id] = instance
    '''
    pk = 'id'   # always = '0'. Need differ for different instances, but here 
                # we only save one dict in redis.
    fields = ['id', 'captcha_dict']

    @classmethod
    def create(cls, pk='0'):
        obj = cls()
        obj.id = pk
        obj.captcha_dict = {}
        obj.put()
        return obj

    def put(self):
        for k,v in self.captcha_dict.items():
            if type(v) != str:
                self.captcha_dict['__str_' + k] = pickle.dumps(v)
                del(self.captcha_dict[k])
        super(RedisCaptchaDict, self).put()

    @classmethod
    def get(cls, pk):
        obj = super(RedisCaptchaDict, cls).get(pk)
        if not obj:
            obj = cls.create()

        for k,v in obj.captcha_dict.items():
            if k[:6] == '__str_':
                obj.captcha_dict[ k[6:] ] = pickle.loads( str(v) )
                del(obj.captcha_dict[ k ])

        return obj

    @classmethod
    def get_instance(cls, pk):
        obj = cls.get(pk)
        if not obj:
            obj = cls.create(pk)
            obj.put()
        return obj
