# -*- encoding: utf-8 -*-  
from django.conf.urls.defaults import patterns, url
from django.conf import settings


urlpatterns = patterns('apps.ocadmin.views.main',
    url(r'^game_settings_menu/$','game_settings_menu', name='game_settings_menu'),
    url(r'^get_game_settings/$','get_game_settings', name='get_game_settings'),
    url(r'^save_game_settings/$','save_game_settings', name='save_game_settings'),
    url(r'^login/$','login'),
    url(r'^moderator/moderator_list/$','moderator_list'),
    url(r'^moderator/add_moderator/$','add_moderator'),
    url(r'^moderator/get_roles_list/$','get_roles_list'),
    url(r'^moderator/add_roles/$','add_roles'),
    url(r'^moderator/del_moderator/$','del_moderator'),
    url(r'^moderator/del_role/$','del_role'),
    url(r'^moderator/manage_moderator/$','manage_moderator'),
    url(r'^moderator/edit_moderator/$','edit_moderator'),
    url(r'^role/manage_role/$','manage_role'),
    url(r'^role/edit_role/$','edit_role'),
    url(r'^config/record/$','updateconfig_record'),
    url(r'^change_password/$','change_password'),
    url(r'^head_title/$','head_title'),
)

urlpatterns += patterns('apps.ocadmin.views.user',
    url(r'^user/view/$', 'view_user'),
    url(r'^user/edit/$', 'edit_user'),
)

urlpatterns += patterns('apps.ocadmin.views.timingconfig',
    url(r'^get_system_config/$','get_system_config', name='get_system_config'),
)

urlpatterns += patterns('apps.ocadmin.views.xls_to_dict',
    url(r'^file/upload_config/$', 'submit_game_settings_by_excel'),
)
