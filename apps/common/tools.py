# encoding: utf-8

"""
用于处理一些  游戏逻辑的函数  例如： 批量添加物品  批量添加物品
"""

def add_things(user, thing_infos, where=""):
    """添加物品，输出的格式易于前端将物品添加到本地

    每当玩家需要批量添加物品，例如战场掉落，探索时，
    可以使用此函数，返回的函数易于前端解析添加到本地

    thing_infos列表  其中中每项都需有_id, num 兩個字段
    Args:
        thing_infos: a list, each item is a dict,
            and the dict sould content keys _id, num
            For example:
                [
                    {"_id": "53003_equipSoul_1": "num": 1},
                    {"_id": '2_card': "num": 1},
                    ....
                ]
    Returns:
        {
            "gold": 300,
            "equip": [ {...equip_info...}, {...equip_info...}],
            "cardSoul": {"1_card": 4, "2_card": 5}
            ....
        }
    """
    return_info = {}

    user_property_obj = user.user_property
    user_pack_obj = user.user_pack
    for this_thing_info in thing_infos:
        pack = pack_good(this_thing_info["_id"], this_thing_info["num"])
        if not pack:
            continue
        thing_type = pack.keys()[0]
        thing_info = pack[thing_type]
        num = thing_info["num"]

        if thing_type == "coin":
            #处理元宝奖励
            user_property_obj.add_coin(num, where=where)
            return_info.setdefault("coin", 0)
            return_info["coin"] += num

        elif thing_type == "gold":
            #处理金币的奖励
            user_property_obj.add_gold(num, where=where)
            return_info.setdefault("gold", 0)
            return_info["gold"] += num

        elif thing_type == "fight_soul":
            # 处理战魂的奖励
            user_property_obj.add_fight_soul(num, where=where)
            return_info.setdefault("fight_soul", 0)
            return_info["fight_soul"] += num

        elif thing_type == "honor":
            # 处理pvp功勋点的奖励
            user_property_obj.user_real_pvp.add_honor(num, where=where)
            return_info.setdefault("honor", 0)
            return_info["honor"] += num

        elif thing_type == "card_exp_point":
            # 处理武将经验点
            user_property_obj.add_card_exp_point(num, where=where)
            return_info.setdefault("card_exp_point", 0)
            return_info["card_exp_point"] += num


        elif thing_type == 'stamina':
            #添加体力信息
            user_property_obj.add_stamina(num)
            return_info.setdefault("stamina", 0)
            return_info["stamina"] += num

        elif thing_type == "card":
            #处理武将的奖励
            uc = user.user_cards
            cid = thing_info["good_id"]
            detail = []
            for i in xrange(num):
                #添加武将并记录
                fg, all_cards_num, ucid, is_first = uc.add_card(cid, 1, where=where)
                card_info = {"ucid": ucid}
                card_info.update(uc.cards[ucid])
                #格式化返回的参数
                detail.append(card_info)
            return_info.setdefault("card", [])
            return_info["card"] += detail

        elif thing_type == "equip":
            ue = user.user_equips
            eid = thing_info["good_id"]
            quality = ''
            if "color" in thing_info:
                quality = thing_info["color"] + "+0"
            detail = []
            for i in xrange(num):
                #添加装备并记录
                fg, all_equips_num, ueid, is_first = ue.add_equip(eid, where=where, quality=quality)
                equip_info = {'ueid':ueid}
                equip_info.update(ue.equips[ueid])
                #格式化返回的参数
                detail.append(equip_info)
            return_info.setdefault("equip", [])
            return_info["equip"] += detail

        elif thing_type == "mat":
            mat_id = thing_info['good_id']
            user_pack_obj.add_material(mat_id, num, where=where)
            return_info.setdefault("mat", {})
            return_info["mat"].setdefault(mat_id, 0)
            return_info["mat"][mat_id] += num

        elif thing_type == 'props':
            props_id = thing_info['good_id']
            user_pack_obj.add_props(props_id, num, where=where)
            return_info.setdefault("props", {})
            return_info["props"].setdefault(props_id, 0)
            return_info["props"][props_id] += num

        elif thing_type == 'cardSoul':
            detail = {}
            soul_card_id = thing_info['good_id']
            us = user.user_souls

            us.add_normal_soul(soul_card_id, num, where=where)
            detail = {soul_card_id: num}
            return_info.setdefault("cardSoul", {})
            return_info["cardSoul"].setdefault(soul_card_id, 0)
            return_info["cardSoul"][soul_card_id] += num

        elif thing_type == 'equipSoul':
            soul_equip_id = thing_info['good_id']
            equip_type = thing_info.get("equip_type", "")

            us = user.user_souls
            if equip_type:
                soul_id = "_".join([soul_equip_id, equip_type])
            else:
                soul_id = soul_equip_id

            us.add_equip_soul(soul_id, num, where=where)

            return_info.setdefault("equipSoul", {})
            return_info["equipSoul"].setdefault(soul_id, 0)
            return_info["equipSoul"][soul_id] += num

    return return_info


def is_things_enough(user, things):
    user_property_obj = user.user_property
    user_pack_obj = user.user_pack

    for thing_type, thing_info in things.items():
        num = thing_info
        if thing_type in ['coin', 'gold', 'stamina']:
            judge = "is_" + thing_type + "_enough"
            if not getattr(user_property_obj, judge)(num):
                return False

        elif thing_type in ['mat', 'props']:
            if thing_type == "mat":
                judge = "is_material_enough"
            else:
                judge = "is_props_enough"
            # judge = "is_" + thing_type + "_enough"
            for thing_id, num in  thing_info.items():
                if not getattr(user_pack_obj, judge)(thing_id, num):
                    return False
        else:
            return False
    return True


def del_things(user, things, where=""):
    """
    批量删除物品
    """
    if not is_things_enough(user, things):
        return
    user_property_obj = user.user_property
    user_pack_obj = user.user_pack
    for thing_type, thing_info in things.items():
        num = thing_info
        if thing_type in ['coin', 'gold', 'stamina']:
            delete = "minus_" + thing_type
            getattr(user_property_obj, delete)(num, where=where)

        elif thing_type in ['mat', 'props']:
            if thing_type == "mat":
                delete = "minus_material"
            else:
                delete = "minus_props"
            for thing_id, num in  thing_info.items():
                getattr(user_pack_obj, delete)(thing_id, num, where=where)


def pack_good(good, num=0):
    """格式化物品，输出的格式易于前端展示

    游戏中又大量的展示物品的界面，例如神秘商店，战场掉落
    等，为了避免各个功能给前端返回的物品数据格式不统一造成混乱，
    因此提供此函数用来格式化物品的数据，前端只需解析此类型的格式
    来展示物品即可。

    num标示数量, 若good为 id 代表物品的唯一标示
    个物品都可以用它标示出来, 各举例如下：

        武将碎片：      1_cardSoul            孙权碎片
        装备碎片：      12001_equipSoul       火云刀碎片（普通装备碎片）
                      53002_equipSoul_2     诗经的第二种碎片（宝物碎片）
        武将：         1_card                孙权
        装备或宝物：    12001_equip_white     白装火云刀
                      12001_equip           火云刀（颜色由前端判断）
        材料：         1_mat                 铁矿钻
        道具：         1_props               更名令
        元宝：         coin
        铜钱：         gold
        体力：         stamina
        战魂：         fight_soul
        功勋点：       honor
        武将经验点：    card_exp_point

    若good为str类型，good表示_id， num表示数量

    Args:
        good: a str represent a thing id
            For example:
                '53003_equipSoul_1'
        num:  Only if the type of `good` is str, this is needed

    Returns:
        只有一个key的字典，key为物品类型，value需包含以下字段：
            num： 数量
            _type：类型
            good_id：用于定位原始的物品id
                例如：53003_equipSoul_1的
                    good_id 为  53003_equip
            equip_type：宝物碎片类型
            color： 装备颜色

        For example:
        {
            "equipSoul":  
                {
                    '_id': '53003_equipSoul_1',
                    'num': 10,
                    '_type': 'equipSoul',
                    'good_id': '53003_equip',
                    'equip_type': '1',
                    ...
                },
        }

    """

    good_id = good
    
    good_type = ""
    good_info = {}
    if good_id in ["coin", "gold", "fight_soul", "stamina", "card_exp_point", "honor"]:
        good_type = good_id
    elif "cardSoul" in good_id:
        good_type = "cardSoul"
        good_id = good_id.replace("Soul", "")
    elif "equipSoul" in good_id:
        good_type = "equipSoul"
        equipSoul_id_type = good_id.split("_")

        good_id = "_".join(equipSoul_id_type[:2]).replace("Soul", "")
        if len(equipSoul_id_type) > 2:
            equipSoul_type = equipSoul_id_type[2]
            good_info["equip_type"] = equipSoul_type
    elif "card" in good_id:
        good_type = "card"
    elif "equip" in good_id:
        good_type = "equip"
        equip_id_color = good_id.split("_")
        good_id = "_".join(equip_id_color[:2])
        if len(equip_id_color) > 2:
            equip_color = equip_id_color[2]
            good_info["color"] = equip_color
    elif "mat" in good_id:
        good_type = "mat"
    elif "props" in good_id:
        good_type = "props"

    if good_type:
        good_info["num"] = num
        good_info["good_id"] = good_id
        good_info["_type"] = good_type
        return {good_type: good_info}
    return {}

