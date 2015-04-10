#coding: utf-8
import sys
import os
import time
import datetime
import json
import copy
import glob
import random
import bisect
from json import dumps
import thread
import socket

import geventwebsocket
from geventwebsocket import WebSocketServer

base_dir = os.path.dirname(os.path.abspath(__file__)).rstrip("/apps/realtime_pvp")
sys.path.insert(0, base_dir)
import apps.settings as settings
from django.core.management import setup_environ
setup_environ(settings)

from apps.logics import real_pvp
from apps.models.user_real_pvp import UserRealPvp
import readying_player_redis
from apps.models import data_log_mod


port = "9040" if len(sys.argv) != 2 else sys.argv[1]


# localIP = socket.gethostbyname(socket.gethostname())
localIP = "10.200.55.32"
server_site = localIP + ":" + port
THIS_READYING_REDIS = readying_player_redis.ALL_REDIS_MODEL[server_site]
print "$$$$$$$$THIS  server_site is", server_site 


all_players = []  # æ‰€æœ‰è¿žæŽ¥æˆåŠŸçš„çŽ©å®¶


# ç”¨äºŽåŒ¹é…åˆ†æ•°æœ€æŽ¥è¿‘å¯¹æ‰‹
readying_players_scores = []   # å’Œç­‰å¾…å¯¹æ‰‹çŽ©å®¶çš„ä»Žå°åˆ°å¤§çš„æœ‰åºscore list
readying_players = []   # å’Œreadying_players_scoreæŒ‰é¡ºåºå¯¹åº”çš„ç­‰å¾…å¯¹æ‰‹çš„çŽ©å®¶å®žä¾‹



# 'losing_connect_uid' : opponent_player_object
losing_connection_info = {}
use_reconnect = False

#to_print = False
to_print = True


def debug_print(*msgs):
    if to_print:
       print(msgs)


def get_user_pvp_info(uid):
    return real_pvp.get_real_pvp_info(uid)

import maps
MAPS = maps.maps
# maps_dir = base_dir + "/apps/realtime_pvp/maps/"
# for map_name in glob.glob(maps_dir + "*.map"):
#     print map_name
#     with open(map_name, 'rb') as fight_f:
#         maps.append(fight_f.read().decode('utf-8'))


class Player(object):
    def __init__(self, core_id, websocket):
        #self.fight_start = False
        self.uid = ''
        self.score = 0

        self.opponent = None

        self.core_id = core_id

        self.connecting = True

        self.fight_statue = -2  # -2 ä¸ºè¿žæŽ¥ä¸Šæœªåšä»»ä½•æ“ä½œ  -1 readyingç­‰å¾…åˆé€‚å¯¹æ‰‹ä¸­ 0 æ‰¾åˆ°å¯¹æ‰‹ï¼Œä½†å¯ä»¥å–æ¶ˆ  1 fightingæ­£åœ¨pk  2 endæˆ˜æ–—ç»“æŸ

        self.last_recv_fg = True    # åˆ¤æ–­æ˜¯å¦æ´»è·ƒé€šä¿¡çš„æ ‡ç¤ºï¼Œç”¨äºŽä¸»åŠ¨æ–­å¼€é•¿æ—¶é—´æ²¡æœ‰é€šä¿¡çš„çŽ©å®¶

        self.websocket = websocket

        self.changeround_switch = 0
        # 
        # self.first_attacker = False

    def send(self, response):
        """send msg to self
        """
        if response and self.connecting:
            response['coreid'] = self.core_id
            response = dumps(response)
            debug_print("send-to", self.uid, response)
            try:
                self.websocket.send(response)
            except geventwebsocket.WebSocketError:
                disconnect_player(self, reason_msg='no msg')

    def send_opponent(self, response):
        if response and self.opponent:
            self.opponent.send(response)

    def broad(self, response):
        self.send(response)
        self.send_opponent(response)

    def response_error(self, msg_dict, check_msg):
        response = response_error(msg_dict, check_msg)
        print 'error !!!!!!', response
        self.send(response)

    def get_suitable_opponent(self):
        """
        è¿”å›žæœ€é€‚åˆçš„å¯¹æ‰‹indexï¼Œè‹¥æ— åˆé€‚å¯¹æ‰‹è¿”å›žNone
        """
        score = self.score
        if not readying_players_scores:
            readying_players_scores.append(score)
            readying_players.append(self)
            THIS_READYING_REDIS.set(self.uid, score)
            return

        index = bisect.bisect_left(readying_players_scores, score)
        most_near_index = 0

        max_index = len(readying_players_scores) - 1

        if self not in readying_players:
            # ä¸ºå…¨é˜Ÿ æœ€å°
            if index == 0:
                most_near_index = 0
            # å…¨é˜Ÿæœ€å¤§
            elif index == max_index + 1:
                most_near_index = max_index
            else:
                near_left,  near_right = index - 1, index
                # ç›¸é‚»çš„å·¦å³
                if (readying_players_scores[near_left] + readying_players_scores[near_right]) / 2 <= score:
                    most_near_index = near_right
                else:
                    most_near_index = near_left
        else:
            # åªæœ‰è‡ªå·±åœ¨ç­‰å¾…
            if len(readying_players) == 1:
                return
            # ä¸ºå…¨é˜Ÿ æœ€å°
            if index == 0:
                most_near_index = 1
            # å…¨é˜Ÿæœ€å¤§
            elif index == max_index:
                most_near_index = max_index - 1
            else:
                near_left, near_right = index - 1, index + 1
                # ç›¸é‚»çš„å·¦å³
                if (readying_players_scores[near_left] + readying_players_scores[near_right]) / 2 <= score:
                    most_near_index = near_right
                else:
                    most_near_index = near_left
        print "debug ", most_near_index, readying_players_scores
        # å¦‚æžœæ˜¯é¦–æ¬¡åŒ¹é…è€Œä¸” gap å¤ªå¤§ï¼Œ ä¸è¿›è¡ŒåŒ¹é…ï¼Œè€Œæ˜¯åŠ å…¥ç­‰å¾…
        if self.fight_statue == -2 and abs(readying_players_scores[most_near_index] - score) < 0:
            readying_players_scores.insert(index, score)
            readying_players.insert(index, self)
            THIS_READYING_REDIS.set(self.uid, score)
            return
        else:
            # ç§»é™¤å¹¶èŽ·å–å¯¹æ‰‹
            readying_players_scores.pop(most_near_index)
            opponent = readying_players.pop(most_near_index)
            THIS_READYING_REDIS.remove(opponent.uid)
            # ç§»é™¤è‡ªå·±
            if self in readying_players:
                self_index = readying_players.index(self)
                readying_players_scores.pop(self_index)
                readying_players.pop(self_index)
                THIS_READYING_REDIS.remove(self.uid)
            return opponent

    def try_start_fight(self, msg_dict):
        print 'I try to get opponent......', self.uid, datetime.datetime.now()
        opponent = self.get_suitable_opponent()
        if opponent is None:
            self.fight_statue = -1
            
        else:
            self.opponent = opponent
            self.opponent.opponent = self

            self.fight_statue = self.opponent.fight_statue = 0

            # self.first_attacker = True

            debug_print('oppoent_core_id', self.opponent.core_id)
            debug_print('self_uid', self.uid)
            # self.broad_pvp_info(msg_dict)
            self.inf_readying_pvp(msg_dict)

    def inf_readying_pvp(self, msg_dict):
        response = inf_readying_pvp(msg_dict)
        self.broad(response)

    def rsp_readying_pvp(self, msg_dict):
        # æœ‰å¯èƒ½æ­¤æ—¶å¯¹æ‰‹å·²ç»é€€å‡ºåŒ¹é…
        if not self.opponent:  # self.fight_statue != 0
            return
        response_self = inf_opponent(msg_dict, self.opponent.uid, self.opponent.core_id)
        print "***** {} PK  {} ****".format(self.uid, self.opponent.uid), datetime.datetime.now()
        self.send(response_self)
        # print "have send", response_self
        self.fight_statue = 1
        # å½“ä¸¤è¾¹éƒ½å‡†å¤‡å¥½äº† æ‰å‘å¼€å§‹æˆ˜æ–—æ¶ˆæ¯
        if self.opponent.fight_statue == 1:
            # attack_core_id = self.core_id if self.first_attacker else self.opponent.core_id
            attack_core_id = self.core_id if random.randint(0, 1) else self.opponent.core_id
            # ç»™ä¸¤æ–¹å¹¿æ’­ å¼€å§‹æˆ˜æ–—æ¶ˆæ¯  åŒ…æ‹¬è°æ˜¯æ”»å‡»æ–¹ä¿¡æ¯
            response = inf_start_fight(msg_dict, attack_core_id=attack_core_id)
            self.broad(response)

    def req_pvp(self, msg_dict):
        response = req_pvp(msg_dict)
        self.uid = msg_dict['uid']
        self.score = UserRealPvp.get(self.uid).pt
        self.send(response)

        print 'I am reading to pvp......   ', self.uid, datetime.datetime.now()
        if self.uid in losing_connection_info:
            self.reconnect()
            self.broad_fight_image(msg_dict)
        else:
            self.try_start_fight(msg_dict)

    # def broad_pvp_info(self, msg_dict):
    #     # ç»™ä¸¤æ–¹åˆ†åˆ«å‘ å„è‡ªçš„å¯¹æ‰‹ä¿¡æ¯
    #     response_self = inf_opponent(msg_dict, self.opponent.uid, self.opponent.core_id)
    #     response_opponent = inf_opponent(msg_dict, self.uid, self.core_id)
    #     print "***** {} PK  {} ****".format(self.uid, self.opponent.uid), datetime.datetime.now()
    #     debug_print('get pvp opp', response_self)
    #     self.send(response_self)
    #     self.send_opponent(response_opponent)
    #     # ç»™ä¸¤æ–¹å¹¿æ’­ å¼€å§‹æˆ˜æ–—æ¶ˆæ¯  åŒ…æ‹¬è°æ˜¯æ”»å‡»æ–¹ä¿¡æ¯
    #     response = inf_start_fight(msg_dict, attack_core_id=self.core_id)
    #     self.broad(response)

    def ans_opponent(self, msg_dict):
        debug_print("get_ans : ans_opponent")

    def ans_start_fight(self, msg_dict):
        debug_print("get_ans : ans_start_fight")
        #self.fight_start = True

    def req_fight_command(self, msg_dict):
        # å›žå¤
        # response_self = req_fight_command(msg_dict)
        # self.send(response_self)
        # è½¬å‘ç»™å¯¹æ‰‹
        response_opponent = inf_fight_command(msg_dict)
        self.send_opponent(response_opponent)

    def req_touch_move(self, msg_dict):
        self.req_fight_command(msg_dict)

    def req_touch_end(self, msg_dict):
        self.req_fight_command(msg_dict)

    def req_hostcal(self, msg_dict):
        self.req_fight_command(msg_dict)

    def req_ani(self, msg_dict):
        self.req_fight_command(msg_dict)

    def req_skill(self, msg_dict):
        self.req_fight_command(msg_dict)

    def req_hostskillcal(self, msg_dict):
        self.req_fight_command(msg_dict)

    def ans_fight_command(self, msg_dict):
        debug_print("get_ans : ans_fight_command")
        pass

    def req_end_round(self, msg_dict):
        response = req_end_round(msg_dict)
        self.send(response)

        self.inf_switch_attack(msg_dict)

    def inf_switch_attack(self, msg_dict):
        response = inf_switch_attack(msg_dict, self.opponent.core_id)
        self.broad(response)

    def ans_switch_attack(self, msg_dict):
        debug_print("get_ans : ans_switch_attack", self.core_id)
        pass

    def req_changeround(self, msg_dict):
        self.changeround_switch = 1
        if self.opponent.changeround_switch:
            response = inf_changeround(msg_dict)
            self.broad(response)
            self.changeround_switch = self.opponent.changeround_switch = 0

    def req_end_fight(self, msg_dict):
        response = rsp_end_fight(msg_dict)
        self.broad(response)

        result_info = inf_result_fight(msg_dict, self, self.opponent)
        self.fight_statue = self.opponent.fight_statue = 2
        self.broad(result_info)

    def ans_result_fight(self, msg_dict):
        debug_print("get_ans : ans_result_fight")
        end_fight_reason = msg_dict['end_fight']["pvp_end_reason"]
        disconnect_player(self, reason_msg=end_fight_reason)
        pass

    def req_cancel_pvp(self, msg_dict):
        if self.fight_statue > 0:
            return
        response = req_cancel_pvp(msg_dict)
        self.send(response)
        disconnect_player(self, reason_msg='cancel by self')
        # è‹¥æ˜¯åœ¨å‡†å¤‡æˆ˜æ–—é˜¶æ®µ å°†å¯¹æ‰‹å¯¹æ‰‹é‡ç½®æˆ æ­£åœ¨å¯»æ‰¾å¯¹æ‰‹
        if self.opponent:
            # disconnect_player(self.opponent, reason_msg='cancel by opponent')

            # é€šçŸ¥å¯¹æ–¹è‡ªå·±å·²ç»æ”¾å¼ƒ
            self.opponent.send(inf_opponent_cancel(msg_dict))

            self.opponent.opponent = None
            self.opponent.fight_statue = -1
            self.opponent.first_attacker = False

            readying_players_scores.append(self.opponent.score)
            readying_players.append(self.opponent)
            THIS_READYING_REDIS.set(self.opponent.uid, self.opponent.score)

    def ans_opponent_cancel(self, msg_dict):
        # å®¢æˆ·ç«¯å›žå¤ å¯¹æ‰‹å·²å–æ¶ˆæ­¤æ¬¡åŒ¹é…
        pass

    def req_heart_beat(self, msg_dict):
        response = req_heart_beat(msg_dict, self.core_id)
        print "resv heart_beat", time.time(), self.core_id, self.uid
        self.send(response)

        if self.fight_statue == -1:
            self.try_start_fight(msg_dict)

    def reconnect(self):
        self.opponent = losing_connection_info.pop(self.uid)
        self.opponent.opponent = self

        self.opponent.core_id = self.opponent.core_id
        debug_print('reconnect oppoent_core_id', self.opponent.core_id)
        debug_print('self_uid', self.uid)

    def broad_fight_image(self, msg_dict):
        response = inf_fight_image(msg_dict)
        self.broad(response)

    def ans_fight_image(self, msg_dict):
        # æ”¶åˆ°æœªæ–­çº¿çŽ©å®¶çš„æˆ˜åœºé•œåƒåŽï¼ŒæŠŠé•œåƒå‘ç»™çŸ­çº¿æ–¹
        self.broad_reconnect_fight(self, msg_dict)

    def broad_reconnect_fight(self, msg_dict):
        response = inf_reconnect_fight(msg_dict)
        self.broad(response)

    def ans_reconnect_fight(self, msg_dict):
        pass

    def handle_msg(self, msg):
        #msg_dict = json.loads(msg.replace("\n", "\\n"))
        if msg is None:
            disconnect_player(self, reason_msg='no msg')
            return
        # if not msg:
        #     if time.time() - self.last_recv_time >= 15:
        #         disconnect_player(self, reason_msg='no msg resv in 15s')
        #     return
        msg = msg.strip()
        debug_print("~~~~~~~~~~reseve", msg)
        if not msg.startswith("{") or not msg.endswith("}"):
            print "!!!!!!is not a json", msg
            return
        try:
            msg_dict = json.loads(msg)
        except Exception:
            print "!!!!!!erro json msg ", msg
            return
        check_msg = check_statu(msg_dict)
        if check_msg:
            print "warnning: get logic_error_msg", msg_dict
            return
            self.response_error(msg_dict, check_msg)

        else:
            response_fuc = getattr(self, msg_dict['msgtype'], None)
            if not response_fuc:
                return
            #print 'ok!!!!!!', response
            self.last_recv_fg = True
            response_fuc(msg_dict)


def application(environ, start_response):
    websocket = environ.get("wsgi.websocket")

    if websocket is None:
        start_response('200 OK', [('Content-Type','text/html')])
        return ''

    core_id = str(environ['HTTP_SEC_WEBSOCKET_KEY'])
    player = Player(core_id, websocket)
    all_players.append(player)
    print "\n##Connecting#########################websockets...", core_id, datetime.datetime.now()

    try:
        while player.connecting:
            message = websocket.receive()
            debug_print("msg", time.time(), message)
            player.handle_msg(message)
    except geventwebsocket.WebSocketError, ex:
        print "{0}: {1}".format(ex.__class__.__name__, ex)
    finally:
        disconnect_player(player, reason_msg='no msg')


def disconnect_player(player, reason_msg=''):
    if not player.connecting and not player in all_players:
        return
    real_pvp.clear(player.uid)

    player.connecting = False
    player.websocket.close()

    all_players.remove(player)

    if player in readying_players:
        player_index = readying_players.index(player)
        readying_players.pop(player_index)
        readying_players_scores.pop(player_index)
        THIS_READYING_REDIS.remove(player.uid)
    elif use_reconnect:  # å¦‚æžœæ˜¯åœ¨æˆ˜æ–—ä¸­æŽ‰çº¿ è®°å½•å¯¹æ‰‹ä¿¡æ¯ä»¥ä¾¿é‡è¿ž
        # åˆ¤æ–­å¯¹æ‰‹æ˜¯å¦ä¹ŸæŽ‰çº¿
        if player.opponent.uid in losing_connection_info:
            losing_connection_info.pop(player.opponent.uid)
        # åªæ˜¯è‡ªå·±æŽ‰çº¿
        else:
            losing_connection_info[player.uid] = player.opponent
    # å¦‚æžœè‡ªå·±æŽ‰çº¿  åˆ¤å®šå¯¹æ‰‹èƒœåˆ©
    elif reason_msg.startswith('no msg') and player.fight_statue == 1 and player.opponent and player.opponent.connecting:
        player.req_end_fight(lose_connect_end_fight_msg(player))
        print '\n å¼‚å¸¸æŽ‰çº¿äº†!!!!!  :****   ({}|--{})'.format(player.core_id, player.uid), datetime.datetime.now()

    print 'disconnect player:**** {}  ({}|--{})'.format(reason_msg, player.core_id, player.uid)


def lose_connect_end_fight_msg(player):
    # æŽ‰çº¿çš„é€šçŸ¥ä¿¡æ¯

    msg = {
       "coreid" : player.core_id,
       "datafield" : "end_fight",
       "pvp_end_reason" : "network_error",
       "winner" : player.opponent.uid,
       "errormsg" : "",
       "msg_ref" : int(time.time()),
       "msgtype" : "req_end_fight",
       "rc" : 0
    }
    return msg


def response_error(msg_data, error_msg):
    msg_data = copy.deepcopy(msg_data)
    msg_data['rc'] = '1'
    msg_data['errormsg'] = error_msg
    return dumps(msg_data)


def response_success(msg_data, success_data):
    msg_data = copy.deepcopy(msg_data)
    msg_data.update(success_data)
    return msg_data

def check_statu(msg_data):
    # check_keys = ['msgtype', 'coreid', 'datafield', 'msg_ref', 'rc', 'errormsg']
    check_keys = ['msgtype', 'coreid', 'msg_ref', 'rc', 'errormsg']
    if set(check_keys) - set(msg_data.keys()):
        print '!!!!! json missing keys:', set(check_keys) - set(msg_data.keys())
        return 'missing keys'
    if msg_data['rc']:
        print '!!!!! json rc error:', msg_data['errormsg']
        return msg_data['errormsg']

def inf_readying_pvp(msg_data):
    success_data = dict(
        msgtype = 'inf_readying_pvp',
    )
    return response_success(msg_data, success_data)


def inf_opponent(msg_data, opponent_player_id, opponent_core_id):
    opp_info = get_user_pvp_info(opponent_player_id)
    opp_info['opponent_coreid'] = opponent_core_id
    success_data = dict(
        msgtype = 'inf_opponent',
        datafield = 'opp_info',
        opp_info = opp_info,
        msg_ref = int(time.time()),
    )
    return response_success(msg_data, success_data)


def req_pvp(msg_data):
    success_data = dict(
        msgtype = 'rsp_pvp',
        status_msg = u'',
    )
    return response_success(msg_data, success_data)


def inf_start_fight(msg_data, attack_core_id):
    success_data = dict(
        msgtype = 'inf_start_fight',
        datafield = 'pvp_info',
        attacker = attack_core_id,
        bead_list = _make_bead_list(),
        msg_ref = int(time.time()),
    )
    return response_success(msg_data, success_data)


# def inf_start_fight(msg_data):
#     success_data = dict(
#         msgtype = 'inf_start_fight',
#     )
#     return response_success(msg_data, success_data)


def req_fight_command(msg_data):
    success_data = dict(
        msgtype = 'rsp_fight_command',
    )
    return response_success(msg_data, success_data)


def inf_fight_command(msg_data):
    success_data = dict(
        # msgtype = 'inf_fight_command',
        msgtype = msg_data['msgtype'].replace('req', 'inf'),
    )
    return response_success(msg_data, success_data)


# def inf_fight_command(msg_data, self_core_id):
#     # ä¸æŽ¥å—è‡ªå·±å¹¿æ’­çš„æ¯ä¿¡
#     if msg_data['coreid'] == self_core_id:
#         return {}
#     success_data = dict(
#         coreid = self_core_id,
#     )
#     return response_success(msg_data, success_data)


def req_end_round(msg_data):
    success_data = dict(
        msgtype = 'rsp_end_round',
    )
    return response_success(msg_data, success_data)


def inf_switch_attack(msg_data, attack_core_id):
    success_data = dict(
        msgtype = 'inf_switch_attack',
        datafield = 'pvp_info',
        pvp_info = {
            'attack': attack_core_id,
        },
        msg_ref = int(time.time()),
    )
    return response_success(msg_data, success_data)


# def inf_switch_attack(msg_data, self_core_id):
#     if msg_data['coreid'] == self_core_id:
#         return {}
#     success_data = dict(
#         coreid = self_core_id,
#     )
#     return response_success(msg_data, success_data)

#def req_end_fight(msg_data, self_core_id):
#    if msg_data['coreid'] != self_core_id:
#        return {}
#    success_data = dict(
#        coreid = self_core_id,
#        msgtype = 'rsp_end_fight',
#    )
#    return response_success(msg_data, success_data)


def inf_changeround(msg_data):
    success_data = dict(
        msgtype = 'inf_changeround',
    )
    return response_success(msg_data, success_data)


def rsp_end_fight(msg_data):
    success_data = dict(
        msgtype = 'rsp_end_fight',
    )
    return response_success(msg_data, success_data)


def inf_result_fight(msg_data, self, opponent):
    print "!!!!!!!!", msg_data
    if "winner" in msg_data:
        self_uid = self.uid
        opponent_uid = opponent.uid
        # self_core_id = self.core_id
        # opponent.core_id = opponent.core_id
        if not opponent.connecting:
            win_uid, lose_uid = (self_uid, opponent_uid)
        else:
            # datafield = msg_data['datafield']
            # win_core_id = msg_data[datafield]["win"]
            # win_uid, lose_uid = (self_uid, opponent_uid) if win_core_id == self_core_id else (opponent_uid, self_uid)
            win_uid = msg_data["winner"]
            win_uid, lose_uid = (self_uid, opponent_uid) if win_uid == self_uid else (opponent_uid, self_uid)
        result_info = real_pvp.result_fight(win_uid, lose_uid)

        self_user_pvp_object = UserRealPvp.get(win_uid)
        opponent_user_pvp_object = UserRealPvp.get(lose_uid)

        data_log_mod.set_log('PvpRecord', UserRealPvp.get(self.uid),
                            **{
                                "winner": self_user_pvp_object.pvp_detail,
                                "loser": opponent_user_pvp_object.pvp_detail,
                                "end_reason": msg_data["pvp_end_reason"],
                            })

        success_data = dict(
            msgtype = 'inf_result_fight',
        )
        msg_data.update(result_info)
        return response_success(msg_data, success_data)
    return {}

def req_cancel_pvp(msg_data):
    success_data = dict(
        msgtype = 'rsp_cancel_pvp',
    )
    return response_success(msg_data, success_data)


def inf_opponent_cancel(msg_data):
    success_data = dict(
        msgtype = 'opponent_cancel',
    )
    return response_success(msg_data, success_data)


def req_heart_beat(msg_data, self_core_id):
    success_data = dict(
        coreid = self_core_id,
        msgtype = 'rsp_heart_beat',
    )
    return response_success(msg_data, success_data)


def inf_fight_image(msg_data, self_core_id):
    success_data = dict(
        msgtype = 'inf_fight_image',
        datafield = 'fight_image',
        fight_image = {
        },
        coreid = self_core_id,
    )
    return response_success(msg_data, success_data)


def inf_reconnect_fight(msg_data):
    success_data = dict(
        msgtype = 'inf_reconnect_fight',
    )
    return response_success(msg_data, success_data)


INIT_BEAD_LIST = []
[INIT_BEAD_LIST.extend([i] * 40) for i in range(5)]
def _make_bead_list():
    random.shuffle(INIT_BEAD_LIST)
    return INIT_BEAD_LIST


def check_dead_user():
    """å‰”é™¤é•¿æ—¶é—´æ²¡æœ‰æ•°æ®äº¤äº’çš„æ™šé—´ï¼Œæ¯éš”15ç§’æ£€æŸ¥
    """
    while True:
        # print "checking connecting"
        for user in all_players:
            # print user.uid
            if user.last_recv_fg == False:
                print "disconnect ", user.uid
                disconnect_player(user, reason_msg='no msg in 15s')
            else:
                user.last_recv_fg = False
        time.sleep(15)


if __name__ == "__main__":
    path = os.path.dirname(geventwebsocket.__file__)
    agent = "gevent-websocket/%s" % (geventwebsocket.get_version())

#    print "start check user connecting"         # å¼€å¯æ£€æŸ¥æŽ‰çº¿çŽ©å®¶è¿›ç¨‹
#    thread.start_new_thread(check_dead_user, ())
    try:
        print "Running %s from %s" % (agent, path)
        print "start pvp serve", datetime.datetime.now()
        # ä¿è¯ç­‰å¾…åˆ—è¡¨æ•°æ®åº“è¡¨ä¸ºç©º
        THIS_READYING_REDIS.clear()
        WebSocketServer(("", int(port)), application, debug=False).serve_forever()
    except KeyboardInterrupt:
        print "close-server"
    finally:
        THIS_READYING_REDIS.clear()
        # for player in all_players:
        #     disconnect_player(player, "server-close")
