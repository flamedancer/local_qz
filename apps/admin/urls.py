# -*- coding: utf-8 -*-
#from django.conf.urls.defaults import patterns, url
#from django.conf.urls import patterns, url

import django
if django.get_version() <= '1.3.1':
    from django.conf.urls.defaults import patterns, url
elif django.get_version() >= '1.6.0':
    from django.conf.urls import patterns, url    #Django 1.6

from django.conf import settings


urlpatterns = patterns('apps.admin.views.main',
    url(r'^$','index'),
    url(r'^api/$','api', name='admin_api'),
    url(r'^login/$','login'),
    url(r'^logout/$','logout'),
    url(r'^left/$','left'),
    url(r'^main/$','main'),

    url(r'^moderator/moderator_list/$','moderator_list'),
    url(r'^moderator/agree_inreview/$','agree_inreview'),
    url(r'^moderator/manage_moderator/$','manage_moderator'),
    url(r'^moderator/manage_moderator_done/$','manage_moderator_done'),

    url(r'^change_password/$','change_password'),
    url(r'^registration/$','registration'),
    url(r'^registration/send_verify_email_code/$','send_verify_email_code'),
    url(r'^forgot_password/$','forgot_password'),
    url(r'^captcha_image/','captcha_image'),   # PyCaptcha 验证码图片的产生
#   url(r'^captcha_check/$','captcha_check'),   # 和验证

    url(r'^moderator/view_permissions/$','moderator_permissions'),
    url(r'^moderator/view_all_permissions/$','view_all_permissions'),
    url(r'^moderator/add_moderator/$','add_moderator'),
    url(r'^moderator/add_moderator_done/$','add_moderator_done'),
    url(r'^moderator/delete_moderator/$','delete_moderator'),
    url(r'^moderator/delete_moderator_done/$','delete_moderator_done'),

    url(r'^common_setting/$', 'common_setting'),

    url(r'^game_setting/$', 'game_setting'),
    url(r'^game_setting/config_md5sum/$', 'config_md5sum'),
    url(r'^game_setting/sync_conf_to_subarea/$', 'sync_conf_to_subarea'),
    url(r'^game_setting/config_diff/$', 'config_diff'),
    url(r'^view_setting/$', 'view_setting'),
    url(r'^view_setting_backup/$', 'view_setting_backup'),
    url(r'^setting_backup_diff/$', 'setting_backup_diff'),
    url(r'^save_game_settings/$','save_game_settings'),
    url(r'^config_changes/$','config_changes'),

    url(r'^pk_top/$', 'pk_top'),
    url(r'^lv_top/$', 'lv_top'),
    url(r'^gift/$', 'gift'),
)

urlpatterns += patterns('apps.admin.views.user',
    url(r'^user/$', 'index'),
    url(r'^user/edit/$', 'edit_user'),
    url(r'^user/view/$', 'view_user'),
)

urlpatterns += patterns('apps.admin.views.record',
    url(r'^record/$', 'index'),
    url(r'^record/consume/$', 'consume'),
    url(r'^record/charge/$', 'charge'),
    url(r'^record/consume_contrast/$', 'consume_contrast'),
)

urlpatterns += patterns('apps.admin.views.upload',
    url(r'^upload/page/$', 'upload_page'),
    url(r'^upload/confirm/$', 'upload_confirm'),
    url(r'^upload/$', 'upload'),
    url(r'^download/$', 'download'),
)

urlpatterns += patterns('apps.admin.views.tool',
    url(r'^tool/$', 'index'),
    url(r'^tool/gacha/$', 'gacha'),
    url(r'^tool/card/$', 'card'),
    url(r'^tool/dungeon_test/$', 'dungeon_test'),
    url(r'^tool/monster_sort/$', 'monster_sort'),
    url(r'^tool/upload_static/$', 'upload_static'),
#   url(r'^tool/update_bulletin/$', 'update_bulletin'),
    url(r'^tool/customer_service/$', 'customer_service'),
    url(r'^tool/cards_product_statistic/$', 'cards_product_statistic'),
    url(r'^tool/view_static/$', 'view_static'),
    url(r'^tool/bulletin/$', 'bulletin'),
)

urlpatterns += patterns('apps.admin.views.config_release',
    url(r'^release_page/$', 'flash_release_page'),
    url(r'^flash_release/$', 'flash_release'),
    url(r'^config_release/$', 'config_release'),
)
urlpatterns += patterns('apps.admin.views.makegameconfig',
    url(r'^makegameconfig/$', 'makegameconfig'),
    url(r'^make_single_config/$', 'make_single_config'),
    url(r'^is_dict/$', 'is_dict'),
)

urlpatterns += patterns('apps.admin.views.xls_to_dict',
    url(r'^xls_to_dict/submit_game_settings_by_excel/$', 'submit_game_settings_by_excel'),
)

urlpatterns += patterns('apps.admin.views.monster',
    url(r'^monster/monster_drop_index/$', 'monster_drop_index'),
    url(r'^monster/monster_drop/$', 'monster_drop'),
)

urlpatterns += patterns('apps.admin.views.statistics',
    url(r'^statistics/$', 'index'),
    )

urlpatterns += patterns('',
    (r'^(?P<path>.*)$','django.views.static.serve',{'document_root':settings.BASE_ROOT + '/apps/admin'}),
)
