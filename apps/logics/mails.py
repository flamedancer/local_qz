#-*- coding: utf-8 -*-

from apps.models.user_mail import UserMail
import datetime

def show_mails(rk_user,params):
    """
    获取邮件列表
    'type': 'system': 系统邮件
    'type': 'pvp'   : pvp邮件 
    return 
    data = {
        '1': {
            'type': 'system',
            'content': u'停机维护提醒\n发件人：小冰冰\n2014-25-04',
            'can_get': True,
            'awards_description': u'恭喜您， 你将获得一下道具：\n元宝 * 3',
            'mid': '201425041211',
        },
        '2':{
            'type': 'pvp',
            'content': u'pvp奖励\n2014-25-04',
            'can_get': False,
            'mid': '201425041212',
        },
    }
    """
    rk_user.user_pvp
    data = {}
    all_info = UserMail.hgetall(rk_user.uid)
    clear_date = (datetime.datetime.now() - datetime.timedelta(days=2)).strftime('%Y%m%d')
    mid_list = [(m, all_info[m]['mail_info'].get('create_time', ''), ) for m in all_info]
    mid_list = sorted(mid_list , key=lambda mid_list : mid_list[1],reverse=True)
    for i, v in enumerate(mid_list):
        v = v[0]
        can_get = all_info[v]['mail_info'].get('can_get', False)
        mid = all_info[v]['mail_info']['mid']
        if can_get is False and clear_date > mid:
        #if can_get is False:
            umobj = UserMail.hget(rk_user.uid, v)
            umobj.delete()
            continue

        data[str(i + 1)] = {}
        data[str(i + 1)]['type'] = all_info[v]['mail_info'].get('type', 'system')
        data[str(i + 1)]['content'] = all_info[v]['mail_info'].get('content', '')
        data[str(i + 1)]['can_get'] = all_info[v]['mail_info'].get('can_get', False)
        data[str(i + 1)]['awards_description'] = all_info[v]['mail_info'].get('awards_description', '')
        data[str(i + 1)]['mid'] = all_info[v]['mail_info']['mid']

    return 0, {'show_mails': data}

def receive(rk_user, params):
    '''
    领取邮件中的内容
    '''
    mails_id = str(params['mails_id'])
    all_info = UserMail.hgetall(rk_user.uid)
    for m in all_info:
        mid = all_info[m]['mail_info']['mid']
        if mid == mails_id:
            can_get = all_info[m]['mail_info'].get('can_get', False)  
            if can_get is False:          
                break
            awards = all_info[m]['mail_info']['awards']
            rk_user.user_property.give_award(awards, where='mails')
            umobj = UserMail.hget(rk_user.uid, m)
            umobj.mail_info['can_get'] = False
            umobj.hput()

    return 0, {'receive': {}}

def _get_pvprank_record(uid):
    pvprank_record_list = []
    all_info = UserMail.hgetall(uid)
    for mid in all_info:
        type = all_info[mid]['mail_info'].get('type', '')
        can_get = all_info[mid]['mail_info'].get('can_get', False)
        if type == 'pvp':
            pvprank_record = all_info[mid]['mail_info'].get('pvprank_record', {})
            for r in pvprank_record:
                pvprank_record_list.append((r, pvprank_record[r]))
    if pvprank_record_list:
        pvprank_record_list = [ (i[0][:13], i[1]) for i in sorted(pvprank_record_list, key=lambda d:d[0],reverse=False)]
    return pvprank_record_list
