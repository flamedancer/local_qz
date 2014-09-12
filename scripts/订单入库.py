#-*- coding: utf-8 -*-
import sys
sys.path.insert(0, '/data/sites/MaxStrikecn')
import apps.settings as settings
from django.core.management import setup_environ
setup_environ(settings)

from apps.models.user_base import UserBase

from apps.models.charge_record import ChargeRecord
from apps.common.utils import datetime_toString
import datetime
oid='12999763169054705758.1301353301481849'
uid='2100220172'
item_id = 'com.nega.fenglinhuoshangl.coin03'
item_num = 760
item_price = 68
charge_way='googleplay'
rk_user = UserBase.get(uid)
before_coin = rk_user.user_property.coin
rk_user.user_property.property_info['coin'] += item_num
after_coin = rk_user.user_property.property_info['coin']
record_data = {
    "oid":oid,
    "platform":rk_user.platform,
    "lv":rk_user.user_property.lv,
    "price":item_price,
    "item_id":item_id,
    "item_num":item_num,
    "createtime":datetime_toString(datetime.datetime.now()),
    "before_coin":before_coin,
    "after_coin":after_coin,
    "client_type":rk_user.client_type,
    "charge_way":charge_way,
}
ChargeRecord.set_record(rk_user, record_data)
rk_user.user_property.do_put()
