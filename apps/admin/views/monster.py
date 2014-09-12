# -*- encoding: utf-8 -*-
import copy
import datetime
import time

from django.shortcuts import render_to_response
from django.template import RequestContext
from apps.config.game_config import game_config



def monster_drop_index(request):
    """敌将掉落首页
    """
    data = {}
    return render_to_response('monster/monster_drop_index.html', data, RequestContext(request))



def monster_drop(request):
    """敌将掉落信息
    """
    data = {"Monster_drop_info":[],
            "query_dungeon_type_title":"",
            "Normal_monster_drop_info":[],
            "query_dungeon_type":"normal"}

    floor_id_str = request.REQUEST.get("floor_id", "None")
    if floor_id_str == "None":
        query_dungeon_type = request.REQUEST.get('query_dungeon_type')
        if query_dungeon_type == "normal":
            getNormalMonster(data)
            return render_to_response('monster/monster_drop_normal.html', data, RequestContext(request))

        elif query_dungeon_type == "today_special":
            getToday_SpecialMonster(data)
            return render_to_response('monster/monster_drop_special.html', data, RequestContext(request))

        elif query_dungeon_type == "special":
            getSpecialMonster(data)
            return render_to_response('monster/monster_drop_special.html', data, RequestContext(request))

        else:
            pass
    else:
        floor_id = int(floor_id_str)
        floor_expand = request.REQUEST.get("floor_expand")
        getNormalMonster(data, floor_id, floor_expand)
        return render_to_response('monster/monster_drop_normal.html', data, RequestContext(request))


def getNormalMonster(data, floor_id_expand = None, floor_expand = None):
    """普通战场敌将掉落
    """
    dungeon_config = copy.deepcopy(game_config.normal_dungeon_config)
    monster_config = copy.deepcopy(game_config.monster_config)
    lstfloor_id = dungeon_config.keys()
    lstfloor_id_n = [int(x) for x in lstfloor_id]
    lstfloor_id_n.sort()

    for floor_id in lstfloor_id_n:
        floor_info = dungeon_config[str(floor_id)]["rooms"]
        floor_name = dungeon_config[str(floor_id)]["name"]
        if floor_id_expand is None:
            data["Normal_monster_drop_info"].append([True, floor_name, floor_id, True])
        else:
            if floor_expand == "0" or floor_id != floor_id_expand:
                data["Normal_monster_drop_info"].append([True, floor_name, floor_id, True])
            else:
                data["Normal_monster_drop_info"].append([True, floor_name, floor_id, False])
                common_drop_rate = dungeon_config[str(floor_id)]["common_drop_rate"]
                lstroom_id = floor_info.keys()
                lstroom_id_n = [int(x) for x in lstroom_id]

                for room_id in lstroom_id_n:
                    room_info = floor_info[str(room_id)]
                    getNormalRoomDungeonInfo(common_drop_rate, floor_name, room_info,
                                             monster_config, data)
    data["query_dungeon_type"] = "normal"
    lstCardInfos = data["Normal_monster_drop_info"]
    bFirst = True
    for lstCardInfo in lstCardInfos:
        if lstCardInfo[0] is False:
            if bFirst is True:
                #lstCardInfo[5]
                lstCardInfo.append(True)
                bFirst = False
            else:
                lstCardInfo.append(False)

def getToday_SpecialMonster(data):
    """特殊战场今日掉落敌将
    """
    monster_config = copy.deepcopy(game_config.monster_config)
    special_dungeon_config = copy.deepcopy(game_config.special_dungeon_config)

    #特殊战场
    special_dungeon = special_dungeon_config.get("special", {})
    for special_id in special_dungeon:
        floor_name = special_dungeon[special_id]["name"]
        rooms_info = special_dungeon[special_id].get("rooms", {})
        start_time = special_dungeon[special_id]["start_time"]
        end_time = special_dungeon[special_id]["end_time"]
        now = datetime.datetime.now()
        now_str = now.strftime('%Y-%m-%d %H:%M:%S')
        if now_str > start_time and now_str < end_time:
            common_drop_rate = special_dungeon[special_id].get("common_drop_rate", 0)
            for room_id in rooms_info:
                room_info = rooms_info[room_id]
                getRoomDungeonInfo("today_special", common_drop_rate, floor_name, room_info,
                                   monster_config, data, start_time, end_time)

    strtitle = datetime.datetime.now().strftime("%Y-%m-%d")
    data["query_dungeon_type_title"] = u"特殊战场今天(" + strtitle + u")敌将掉落"
    data["query_dungeon_type"] = "today_special"

def getSpecialMonster(data):
    """特殊战场掉落所有敌将
    """
    monster_config = copy.deepcopy(game_config.monster_config)
    special_dungeon_config = copy.deepcopy(game_config.special_dungeon_config)

    #特殊战场
    special_dungeon = special_dungeon_config.get("special", {})
    for special_id in special_dungeon:
        floor_name = special_dungeon[special_id]["name"]
        rooms_info = special_dungeon[special_id].get("rooms", {})
        start_time = special_dungeon[special_id]["start_time"]
        end_time = special_dungeon[special_id]["end_time"]
        common_drop_rate = special_dungeon[special_id].get("common_drop_rate", 0)
        for room_id in rooms_info:
            room_info = rooms_info[room_id]
            getRoomDungeonInfo("special", common_drop_rate, floor_name, room_info,
                               monster_config, data, start_time, end_time)

    data["query_dungeon_type_title"] = u"特殊战场敌将掉落"
    data["query_dungeon_type"] = "special"

def getRoomDungeonInfo(strType, common_drop_rate, floor_name, room_info, monster_config, data,
                       start_time = None, end_time = None):
    """获得以room为单位的战场信息
    """
    #普通敌将
    lstCardInfo = ['', [], [], [], ""]

    common_monster = room_info.get("common_monster", {})
    for monster_id in common_monster:
        lstCardInfo[0] = floor_name + u" 之 " + room_info['name']
        strcid = monster_config[monster_id]['cid']
        card_detail = [None, None, None, ""]
        card_detail[0] = strcid.replace("card", 'head.png')
        #武将技
        card_detail[3] = getSkidNameBySkid(strcid)
        #敌将掉落级别
        card_detail[1] = "lv:"+str(common_monster[monster_id])
        if common_drop_rate > 0:
            card_detail[2] = True
        else:
            card_detail[2] = False
        lstCardInfo[1].append(card_detail)

    #特殊敌将
    special_monster = room_info.get("special_monster", {})
    for special_monster_id in special_monster:
        lstCardInfo[0] = floor_name + u" 之 " + room_info['name']
        strcid = special_monster[special_monster_id].get("drop_cid", "")
        if strcid.strip() != "":
            card_detail = [None, None, None, ""]
            #武将技
            card_detail[3] = getSkidNameBySkid(strcid)
            card_detail[0] = strcid.replace("card", 'head.png')
            card_detail[1] = "lv:" + str(special_monster[special_monster_id].get("drop_lv", 1))
            if special_monster[special_monster_id]["appear_rate"] > 0:
                card_detail[2] = True
            else:
                card_detail[2] = False
            lstCardInfo[2].append(card_detail)

    #BOSS
    boss_monster = room_info.get("boss_monster", {})
    boss_drop_rate = room_info["boss_drop_rate"]
    boss_drop_more = room_info.get("boss_drop_more", {})
    lsStep_id = boss_monster.keys()
    lsStep_id_n = [int(x) for x in lsStep_id]
    lsStep_id_n.sort()
    for step_id in lsStep_id_n:
        monster_info = boss_monster[str(step_id)]
        for monster_id in monster_info:
            lstCardInfo[0] = floor_name + u" 之 " + room_info['name']
            drop_info= monster_info[monster_id]
            if isinstance(drop_info, (unicode, str)):
                strcid = drop_info
                if strcid.strip() != "":
                    card_detail = [None, None, None, '']
                    #武将技
                    card_detail[3] = getSkidNameBySkid(strcid)
                    card_detail[0] = strcid.replace("card", 'head.png')
                    card_detail[1] = u'lv:1'
                    if (boss_drop_more.get(str(step_id), 0) + boss_drop_rate) > 0:
                        card_detail[2] = True
                    else:
                        card_detail[2] = False
                    lstCardInfo[3].append(card_detail)
            else:
                strcid = monster_info[monster_id]["drop_cid"]
                if strcid.strip() != "":
                    card_detail = [None, None, None, '']
                    card_detail[3] = getSkidNameBySkid(strcid)
                    card_detail[0] = strcid.replace("card", 'head.png')
                    card_detail[1] = "lv:" + str(monster_info[monster_id].get("drop_lv", 1))
                    if (boss_drop_more.get(str(step_id), 0) + boss_drop_rate) > 0:
                        card_detail[2] = True
                    else:
                        card_detail[2] = False
                    lstCardInfo[3].append(card_detail)

    if start_time is not None and end_time is not None:

        now = datetime.datetime.now()
        now_str = now.strftime('%Y-%m-%d %H:%M:%S')
        if now_str > end_time:
            lstCardInfo[4] = u"已结束"
        else:
            struct_time = time.strptime(end_time, '%Y-%m-%d %H:%M:%S')
            end_dateime = datetime.datetime(struct_time.tm_year, struct_time.tm_mon,
                                            struct_time.tm_mday, struct_time.tm_hour,
                                            struct_time.tm_min, struct_time.tm_sec)
            fixdate = end_dateime - now
            if fixdate.days > 0:
                lstCardInfo[4] = str(fixdate.days) + u"天"
            else:
                if fixdate.seconds/3600 > 0:
                    lstCardInfo[4] = str(fixdate.seconds/3600) + u"小时"
                else:
                    lstCardInfo[4] = str(fixdate.seconds/60) + u"分钟"

    if lstCardInfo[0] != "":
        data["Monster_drop_info"].append(lstCardInfo)


def getNormalRoomDungeonInfo(common_drop_rate, floor_name, room_info, monster_config, data):
    """获得普通战场以room为单位的战场信息
    """

    lstCardInfo = [False, "", [], [], []]
    #普通敌将
    common_monster = room_info.get("common_monster", {})
    for monster_id in common_monster:
        lstCardInfo[1] = floor_name + u" 之 " + room_info['name']
        strcid = monster_config[monster_id]['cid']
        card_detail = [None, None, None, '']
        #武将技
        card_detail[3] = getSkidNameBySkid(strcid)
        card_detail[0] = strcid.replace("card", 'head.png')
        #敌将掉落级别
        card_detail[1] = "lv:"+str(common_monster[monster_id])
        if common_drop_rate > 0:
            card_detail[2] = True
        else:
            card_detail[2] = False

        lstCardInfo[2].append(card_detail)

    #特殊敌将
    special_monster = room_info.get("special_monster", {})
    for special_monster_id in special_monster:
        lstCardInfo[1] = floor_name + u" 之 " + room_info['name']
        strcid = special_monster[special_monster_id].get("drop_cid", "")
        if strcid.strip() != "":
            card_detail = [None, None, None, '']
            card_detail[3] = getSkidNameBySkid(strcid)
            card_detail[0] = strcid.replace("card", 'head.png')
            card_detail[1] = "lv:" + str(special_monster[special_monster_id].get("drop_lv", 1))
            if special_monster[special_monster_id]["appear_rate"] > 0:
                card_detail[2] = True
            else:
                card_detail[2] = False
            lstCardInfo[3].append(card_detail)
    #BOSS
    boss_monster = room_info.get("boss_monster", {})
    boss_drop_rate = room_info["boss_drop_rate"]
    boss_drop_more = room_info.get("boss_drop_more", {})
    lsStep_id = boss_monster.keys()
    lsStep_id_n = [int(x) for x in lsStep_id]
    lsStep_id_n.sort()
    for step_id in lsStep_id_n:
        monster_info = boss_monster[str(step_id)]
        for monster_id in monster_info:
            lstCardInfo[1] = floor_name + u" 之 " + room_info['name']
            drop_info= monster_info[monster_id]
            if isinstance(drop_info, (unicode, str)):
                strcid = drop_info
                if strcid.strip() != "":
                    card_detail = [None, None, None, '']
                    card_detail[3] = getSkidNameBySkid(strcid)
                    card_detail[0] = strcid.replace("card", 'head.png')
                    card_detail[1] = u'lv:1'
                    if (boss_drop_more.get(str(step_id), 0) + boss_drop_rate) > 0:
                        card_detail[2] = True
                    else:
                        card_detail[2] = False
                    lstCardInfo[4].append(card_detail)
            else:
                strcid = monster_info[monster_id]["drop_cid"]
                if strcid.strip() != "":
                    card_detail = [None, None, None, '']
                    card_detail[3] = getSkidNameBySkid(strcid)
                    card_detail[0] = strcid.replace("card", 'head.png')
                    card_detail[1] = "lv:" + str(monster_info[monster_id].get("drop_lv", 1))
                    if (boss_drop_more.get(str(step_id), 0) + boss_drop_rate) > 0:
                        card_detail[2] = True
                    else:
                        card_detail[2] = False
                    lstCardInfo[4].append(card_detail)


    if lstCardInfo[1] != "":
        data["Normal_monster_drop_info"].append(lstCardInfo)



def getSkidNameBySkid(strcid):
    """通过cid获得技能名称
    """
    strSkillName = ""
    card_config = copy.deepcopy(game_config.card_config)
    if card_config.has_key(strcid):
        card_config_info = card_config[strcid]
        skid = card_config_info.get("skid", None)
        if skid is not None:
            skill_config = copy.deepcopy(game_config.skill_config)
            if skill_config.has_key(skid):
                skill_info = skill_config[skid]
                strSkillName = skill_info.get("name", "")

    return strSkillName

