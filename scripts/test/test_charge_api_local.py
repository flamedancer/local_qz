#-*- coding: utf-8 -*-

import os
import sys
import random

base_dir = os.path.dirname(os.path.abspath(__file__)).replace('/scripts/test', '')
sys.path.insert(0, base_dir)
import apps.settings_local as settings
from django.core.management import setup_environ
setup_environ(settings)

from apps.oclib import app
from apps.models.user_base import UserBase
from apps.views.charge import charge_api

uid = '0100000048' if len(sys.argv) != 2 else sys.argv[1]

ub = UserBase.get(uid)


def charge_test(item_id, charge_money):
    print 'before_charge_coin', ub.user_property.coin
    print charge_api(ub, 'test'+str(random.randint(0, 100)), 'monthCard300', platform='test', charge_way='test', charge_money='30')
    print 'after_charge_coin', ub.user_property.coin
    print '*'*20 + '\n'

charge_test('monthCard300', '30') 
charge_test('coin980', '98') 

app.pier.save()
