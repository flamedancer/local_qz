from apps.models.account_oneclick import AccountOneclick
from apps.models.account_mapping import AccountMapping
from apps.models.user_base import UserBase
new_uid='1100537246'
old_uid='1100213598'

ub_old = UserBase.get(old_uid)
ac_old = AccountOneclick.get(ub_old.pid)

ub_new = UserBase.get(new_uid)
ac_new = AccountMapping.get(ub_new.pid)
ac_new.uid = old_uid
ac_new.put()
ub_old.baseinfo['platform']='qq'
ub_old.baseinfo['openid']=ac_new.openid
ub_old.baseinfo['pid']=ac_new.pid
ub_old.do_put()
ac_old.delete()
