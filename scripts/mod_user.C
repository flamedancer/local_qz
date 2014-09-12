#-*- coding: utf-8 -*-
import sys
sys.path.insert(0, '/data/sites/MaxStrikecn')
import apps.settings as settings
from django.core.management import setup_environ
setup_environ(settings)
from apps.models.user_property import UserProperty
from apps.models.user_cards import UserCards
##########加经验##############
uids=['1100243195','1100236173']
for uid in uids:
    up=UserProperty.get(uid)
    up.add_exp(80000,where='qa_add')
    up.do_put()
###########加元宝##############
uids=['1100243092','1100241664']
for uid in uids:
    up=UserProperty.get(uid)
    up.add_coin(3000,where='qa_add')
    up.do_put()


##########加小乔##########
uid = '1100213894'
uc=UserCards.get(uid)
uc.add_card('155_card',where='qa_add')
uc.do_put()

#####加添加5星甄姬#######
uid = '1008243312'
uc=UserCards.get(uid)
uc.add_card('170_card',where='qa_add')
uc.do_put()


from apps.models.user_property import UserProperty
from apps.models.user_cards import UserCards
uids=['1100332342','1100213697']
for uid in uids:
    up=UserProperty.get(uid)
    up.add_coin(3000,where='cs_add')
    up.do_put()
    uc=UserCards.get(uid)
    uc.add_card('153_card',where='cs_add',category='4')
    uc.do_put()

