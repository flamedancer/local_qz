#-*- coding: utf-8 -*-

import os
import sys
import random

base_dir = os.path.dirname(os.path.abspath(__file__)).replace('/scripts/test', '')
sys.path.insert(0, base_dir)
import apps.settings as settings
from django.core.management import setup_environ
setup_environ(settings)

from apps.oclib import app
from apps.models.user_base import UserBase
from apps.views.charge import charge_api

uid = '56100215461' if len(sys.argv) != 2 else sys.argv[1]

ub = UserBase.get(uid)
print 'before_charge_coin', ub.user_property.coin
print charge_api(ub, 'test'+str(random.randint(0, 100)), 'coin60', platform='test', charge_way='test', charge_money='60')
print 'after_charge_coin', ub.user_property.coin

app.pier.save()