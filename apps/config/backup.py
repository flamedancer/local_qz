#coding: utf-8
#Just generate today-morning-backup, as we have subarea, it seems too much
#

import datetime

from apps.models.config import Config
from apps.models.redis_tool import RedisTool
from apps.config.config_list import get_game_config_name_list


def generate_backup():
    ''' 一天只备份一次, 在最早的一次发生(任何)配置变更后。

    每天的第一次配置改动后，触发 config reload_all,备份一次改动后的所有区的内容.

    每天第一次备份全部分区的全部配置时,可能会要花些时间,
    但实际测试显示是很快的, 基本在1秒内全备份完成。 

    如果 redis 重启了，要从mongo中调出所有的配置，再备份，则可能略花点时间。
    只要不是redis重启，实测速度基本可以接受。
    '''

    today_str = str( datetime.datetime.now().date() )

    #need put into redis, or when program restarted, it will re-backup
    conf_backup_date = RedisTool.get('conf_backup_date')  #is a string

    if today_str == conf_backup_date:
        return

    #conf_with_multi_area = [ c['name'] for c in g_lConfig if c['use_subarea'] ]

    subarea_conf_obj = Config.get('subareas_conf_1')
    if not subarea_conf_obj:
        subarea_conf_obj = Config.create('subareas_conf_1')
    subarea_conf = eval(subarea_conf_obj.data)
    subarea_ids = subarea_conf.keys()

#   print '#### in backup, subarea_config.data=', subarea_conf
#   print '#### in backup, subarea_ids=', subarea_ids

    subarea_ids.remove('1') #put 1 as first
    subarea_ids = ['1'] + subarea_ids

    for area_id in subarea_ids:    
        all_config_name_list=get_game_config_name_list(area_id)
        for conf_name in all_config_name_list:
            full_conf_name = conf_name + '_' + area_id
            print '##### in config backup,', full_conf_name, '@', datetime.datetime.now()

            #need backup conf_obj.data, which has comments "# ... "
            conf_obj = Config.get(full_conf_name)
            if not conf_obj:
                continue

            #conf_bk = Config.get(full_conf_name + '_' + today_str)
            #if conf_bk is None:
            conf_bk = Config.create(full_conf_name + '_' + today_str)
            conf_bk.data = conf_obj.data
            conf_bk.put()
            
            
            #delete old backups
            old_conf_obj = Config.get(full_conf_name + '_' + conf_backup_date)
            if not old_conf_obj:
                continue
            old_conf_obj.delete()

    RedisTool.set('conf_backup_date', today_str) # str


def show_config_backup(config_name='', subarea='1', date_str=''):
    if not subarea:
        subarea = '1'
    conf= Config.get(config_name + '_' + subarea + '_' + date_str)
    if not conf or not conf.data:
        return ''
        
    return conf.data
 


#def delete_backup():
#    '''只在测试用，删除已有的备份，再重新产生, 看速度/耗时
#    '''
#
#    today_str = str( datetime.datetime.now().date() )
#
#    #need put into redis, or when program restarted, it will re-backup
#    conf_backup_date = RedisTool.get('conf_backup_date')  #is a string
#
#    if today_str == conf_backup_date:
#        return
#
#    subarea_conf_obj = Config.get('subareas_conf_1')
#    if not subarea_conf_obj:
#        subarea_conf_obj = Config.create('subareas_conf_1')
#    subarea_conf = eval(subarea_conf_obj.data)
#    subarea_ids = subarea_conf.keys()
#
#    subarea_ids.remove('1') #put 1 as first
#    subarea_ids = ['1'] + subarea_ids
#
#    for area_id in subarea_ids:    
#        all_config_name_list=get_game_config_name_list(area_id)
#        for conf_name in all_config_name_list:
#            full_conf_name = conf_name + '_' + area_id
#            #print '##### in config delete_backup,', full_conf_name, '@', datetime.datetime.now()
#
#            conf_obj = Config.get(full_conf_name)
#            if not conf_obj:
#                continue
#
#            conf_obj.delete()
#
#    RedisTool.delete('conf_backup_date')
