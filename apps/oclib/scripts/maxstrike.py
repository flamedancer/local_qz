#!/usr/bin/env python
# encoding: utf-8
#******************************
# 索引配置文件
#
#******************************

{
   'mongodb': {
        # Collection
        'config': {
            'index': 'config_name',
            'unique': True
        },
        'accountmapping': {
            'index': 'pid',
            'unique': True
        },
        'usercollection': {
            'index': 'uid',
            'unique': True
        },
        'friend': {
            'index': 'uid',
            'unique': True
        },
        'exceptusers': {
            'index': 'except_type',
            'unique': True
        },
        'leveluser': {
            'index': 'lv',
            'unique': True
        },
        'userbase': {
            'index': 'uid',
            'unique': True
        },
        'usercards': {
            'index': 'uid',
            'unique': True
        },
        'userdungeon': {
            'index': 'uid',
            'unique': True
        },
        'userequips': {
            'index': 'uid',
            'unique': True
        },
        'usergift': {
            'index': 'uid',
            'unique': True
        },
        'userlogin': {
            'index': 'uid',
            'unique': True
        },
        'userproperty': {
            'index': 'uid',
            'unique': True
        },
        'userrealpvp': {
            'index': 'uid',
            'unique': True
        },
        'usergacha': {
            'index': 'uid',
            'unique': True
        },
        'usersouls': {
            'index': 'uid',
            'unique': True
        },
        'usermysterystore': {
            'index': 'uid',
            'unique': True
        },
        'useractivity': {
            'index': 'uid',
            'unique': True
        },
        'usermarquee': {
            'index': 'uid',
            'unique': True
        },
        'userpkstore': {
            'index': 'uid',
            'unique': True
        },

    },
    'log_mongodb': {
        'chargerecord': [
            {
                'index': 'oid',
                'unique': True
            },
            {
                'index': 'uid'
            },
            {
                'index': 'platform'
            },
            {
                'index': 'createtime'
            }
        ],
        'consumerecord': [
            {
                'index': 'uid',
            },
            {
                'index': 'consume_type'
            },
            {
                'index': 'createtime'
            }
        ],

    }
}
