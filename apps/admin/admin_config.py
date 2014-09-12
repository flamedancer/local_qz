#-* coding:utf-8 -*-
# 权限列表
permissions = [
    {
        "code":"super",
        "description":u"超级管理权限,能干全部事情"
    },
    {
        "code":"edit_user",
        "description":u"允许修改用户数据"
    },
    {
        "code":"submit_setting",
        "description":u"允许修改配置"
    },
    {
        "code":"view_charge",
        "description":u"查询充值"
    },
    {
        "code":"view_consume",
        "description":u"查询消费"
    },
    {
        "code":"tool",
        "description":u"运营工具"
    },
    {
        "code":"qa_tool",
        "description":u"QA工具"
    },
    {
        "code":"customer_service",
        "description":u"客服工具"
    },
]

# view method mapping permissions
# mappings：view函数映射关系
#   path: view path
#   index:  是否是管理后台的导航页面
#   permissions: 额外指定的权限列表
views_perms_mappings={
    "index":[
        {
            "path":'/admin/moderator/moderator_list/',
            "name":"管理员管理",
            "order":0,
            "permissions":"super",
        },
        {
            "path":'/admin/change_password/',
            "name":"修改密码",
            "order":0,
            "permissions":"all",
        },
        {
            "path": '/admin/game_setting/',
            "name": '游戏设置',
            "order": 0,
            "permissions": "submit_setting",
        },
        #{
            #"path": '/admin/common_setting/',
            #"name": '运营设置',
            #"order": 0,
            #"permissions": "all",
        #},

        #{
            #"path":'/admin/download/',
            #"name":"下载配置",
            #"order":0,
            #"permissions":"all",
        #},

        #{
            #"path":'/admin/upload/page/',
            #"name":"上传配置",
            #"order":0,
            #"permissions":"all",
        #},

        #{
            #"path":'/admin/notice/',
            #"name":"公告配置",
            #"order":0,
            #"permissions":"all",
        #},

        #{
            #"path":'/admin/release_page/',
            #"name":"版本发布",
            #"order":0,
            #"permissions":"all",
        #},
        {
            "path": '/admin/user/?user_type=view',
            "name": '查看用户',
            "order": 0,
            "permissions": "all",
        },
        {
            "path": '/admin/user/',
            "name": '修改用户',
            "order": 0,
            "permissions": "edit_user",
        },
        {
            "path": '/admin/record/?type=consume',
            "name": '查询消费',
            "order": 0,
            "permissions": "view_consume",
        },
        {
            "path": '/admin/record/?type=charge',
            "name": '查询充值',
            "order": 0,
            "permissions": "view_charge",
        },
        {
            "path": '/admin/tool/',
            "name": '运营工具',
            "order": 0,
            "permissions": "tool",
        },
        {
            "path": '/admin/gift/',
            "name": '礼品码',
            "order": 0,
            "permissions": "tool",
        },
        # {
        #     "path": '/admin/makegameconfig/',
        #     "name": '生成配置',
        #     "order": 0,
        #     "permissions": "all",
        # },
        {
            "path": '/admin/pvp_top/',
            "name": 'pvp排名',
            "order": 0,
            "permissions": "all",
        },
        {
            "path": '/admin/lv_top/',
            "name": '等级排名',
            "order": 0,
            "permissions": "all",
        },
        {
            "path": '/admin/record/?type=consume_contrast',
            "name": '对比消费',
            "order": 0,
            "permissions": "view_consume",
        },
#        {
#            "path": '/admin/monster/monster_drop_index/',
#            "name": '敌将掉落',
#            "order": 0,
#            "permissions": "all",
#        },
#        {
#            "path": '/admin/tool/qa_tool/',
#            "name": 'QA工具',
#            "order": 0,
#            "permissions": "qa_tool",
#        },
        # {
        #     "path": '/admin/schedule/sendcoin/',
        #     "name": '定期送元宝',
        #     "order": 0,
        #     "permissions": "super",
        # },
        {
            "path": '/admin/tool/customer_service/',
            "name": '客服工具',
            "order": 0,
            "permissions": "customer_service",
        },
        {
            "path":'/admin/logout/',
            "name":"登出",
            "order":0,
            "permissions":"all",
        },


    ],
    "mappings":[
        {
            "path" : r'^/admin/main/$',
            "permissions" : "all"
        },
        {
            "path" : r'^/admin/left/$',
            "permissions" : "all"
        },
        {
            "path" : r'/admin/gift/',
            "permissions" : "tool"
        },
        {
            "path" : r'/admin/moderator/moderator_list/',
            "permissions" : "super"
        },
        {
            "path" : r'/admin/moderator/view_permissions/',
            "permissions" : "super"
        },
        {
            "path":r"/admin/moderator/manage_moderator/",
            "permissions":"super"
        },
        {
            "path":r"/admin/moderator/manage_moderator_done/",
            "permissions":"super"
        },
        {
            "path":r"/admin/moderator/add_moderator/",
            "permissions":"super"
        },
        {
            "path":r"/admin/moderator/add_moderator_done/",
            "permissions":"super"
        },
        {
            "path":r"/admin/moderator/delete_moderator/",
            "permissions":"super"
        },
        {
            "path":r"/admin/moderator/delete_moderator_done/",
            "permissions":"super"
        },
        {
            "path":r"/admin/change_password/",
            "permissions":"all"
        },
        {
            "path":r"/admin/change_password_done/",
            "permissions":"all"
        },
        {
            "path":r"/admin/game_setting/",
            "permissions":"submit_setting"
        },
        {
            "path":r"/admin/user/",
            "permissions":"edit_user"
        },
        {
            "path":r"/admin/common_setting/",
            "permissions":"all"
        },
        {
            "path":r"/admin/notice_edit/",
            "permissions":"all"
        },
        {
            "path":r"/admin/notice_new/",
            "permissions":"all"
        },
        {
            "path":r"/admin/download/",
            "permissions":"super"
        },
        {
            "path":r"/admin/upload/page/",
            "permissions":"super"
        },
        {
            "path":r"/admin/makegameconfig/",
            "permissions":"all"
        },
        {
            "path":r"/admin/pvp_top/",
            "permissions":"all"
        },
        {
            "path":r"/admin/lv_top/",
            "permissions":"all"
        },
        {
            "path":r"/admin/tool/customer_service/",
            "permissions":"customer_service"
        },
        {
            "path":r"/admin/xls_to_dict/submit_game_settings_by_excel/",
            "permissions":"submit_setting"
        },
    ],
}

# 管理后台安全校验码
ADMIN_SECRET_KEY='s3avlj$=vk16op_s1g!xyilse9azcu&oh#wln8_@!b+_p7-+@='
