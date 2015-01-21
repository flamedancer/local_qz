#-*- coding: utf-8 -*-

import datetime

from apps.common import tools, utils
from apps.models.user_mail import UserMail
from apps.config.game_config import game_config

def show_mails(rk_user, params):
    """
    获取邮件列表
    'type': 'system': 系统邮件
    'type': 'pvp'   : pvp邮件 
    Returns:
        {'show_mails': 
            {1: {'awards': [
                    {'equipSoul': {'equip_type': u'1', 'good_id': u'53003_equip', 'num': 1}},                
                    {'mat': {'good_id': u'3_mat', 'num': 2}},
                    {'gold': {'good_id': u'gold', 'num': 10}},
                    {'props': {'good_id': u'1_props', 'num': 1}},
                    {'equip': {'color': u'green', 'good_id': u'13001_equip', 'num': 3}},
                    {'cardSoul': {'good_id': u'5_card', 'num': 1}},
                    {'fight_soul': {'good_id': u'fight_soul', 'num': 100}},
                    {'card': {'good_id': u'5_card', 'num': 1}},
                    {'honor': {'good_id': u'honor', 'num': 100}},
                    {'equipSoul': {'good_id': u'12002_equip', 'num': 1}}
                ],
                'can_get': True,
                'content': u'5345',
                'create_time': u'2014-11-04 11:32:56',
                'mid': u'201411041132562390414',
                'type': u'system'},
            2:  ......
    """
    data = {}
    all_info = UserMail.hgetall(rk_user.uid)
    expire_days = game_config.mail_config.get('expire_days', 2)
    clear_date = (datetime.datetime.now() - datetime.timedelta(days=expire_days)).strftime('%Y-%m-%d %H:%M:%S')
    # 根据创建时间排序
    key_create_time_list = [(m, 
        all_info[m]['mail_info'].get('create_time', ''), 
        all_info[m]['mail_info'].get('open_time', '9999-99-99 99:99:99')) for m in all_info]

    key_create_time_list = sorted(key_create_time_list , key=lambda key_time: key_time[1], reverse=True)
    for index, key_create_time in enumerate(key_create_time_list):
        key, create_time, open_time = key_create_time
        mail_info = all_info[key]['mail_info']
        can_get = mail_info.get('can_get', False)

        if can_get is False and clear_date > open_time:
        #if can_get is False:
            umobj = UserMail.hget(rk_user.uid, key)
            umobj.delete()
            continue

        this_data = {
            'type': mail_info['type'],
            'title': mail_info['title'],
            'content': mail_info['content'],
            'can_get': mail_info['can_get'],
            'awards': [tools.pack_good(good, num) for good, num in mail_info['awards'].items()],
            'create_time': mail_info['create_time'],
            'mid': mail_info['mid'],
        }
        data[index + 1] = this_data
    return {'show_mails': data}


def receive(rk_user, params):
    '''
    领取邮件中的内容
    '''
    mails_id = str(params['mails_id'])
    all_info = UserMail.hgetall(rk_user.uid)
    return_info = {}
    for m in all_info:
        mid = all_info[m]['mail_info']['mid']
        if mid == mails_id:
            can_get = all_info[m]['mail_info'].get('can_get', False)
            if can_get is False:
                break
            awards = all_info[m]['mail_info']['awards']
            where = 'mail_' + all_info[m]['mail_info']['title']
            return_info = tools.add_things(rk_user, [{"_id": goods, "num": awards[goods]} for goods in awards if goods], where)

            umobj = UserMail.hget(rk_user.uid, m)
            umobj.mail_info['can_get'] = False
            umobj.mail_info['open_time'] = utils.datetime_toString(datetime.datetime.now())
            umobj.hput()
            break

    return 0, {'receive': return_info}


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


def send_op_mail(rk_user):
    '''
    发运营邮件
    判断运营是否有新配邮件,这里邮件特指mail_config['mail_list']里的邮件,需要一些实时性，非一些登陆奖励类邮件
    '''
    mail_conf = game_config.mail_config.get('mail_list', {})

    for mail_info in mail_conf:
        mid = mail_info['mail_id']
        received_mails = rk_user.baseinfo['received_mails']
        # 没收过这封邮件,并且邮件在时间段内，发邮件
        if mid not in received_mails:
            if _is_between_times(mail_info):
                sid = 'system_%s' % (utils.create_gen_id())
                mailtype = 'system_qa'
                title = mail_info['title']
                content = mail_info['content']
                award = mail_info['award']
                user_mail_obj = UserMail.hget(rk_user.uid, sid)
                user_mail_obj.set_mail(mailtype=mailtype, title=title, content=content, award=award)

                received_mails.append(mid)
                # 去掉时间太久的不必要的邮件
                if len(received_mails) > 30:
                    received_mails.pop(0)
                rk_user.put()


def _is_between_times(mail):
    # start 和end time 要符合 年月日 时分秒的格式 ，例如'2014-10-06 11:00:00'
    try:
        start_time = utils.string_toDatetime(mail['start_time'])
        end_time = utils.string_toDatetime(mail['end_time'])
    except ValueError:
        return False

    if start_time <= datetime.datetime.now() <= end_time:
        return True
    else:
        return False
