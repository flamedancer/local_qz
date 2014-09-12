#coding: utf-8
import sys
import os
import time
import datetime
import json
import copy
import glob
import random
from json import dumps

import uwsgi
import gevent.select
import redis

base_dir = os.path.dirname(os.path.abspath(__file__)).rstrip("/apps/realtime_pvp")
sys.path.insert(0, base_dir)
import apps.settings_stg as settings
from django.core.management import setup_environ
setup_environ(settings)

from apps.logics import real_pvp

readying_players= []

# 'losing_connect_uid' : opponent_player_object
losing_connection_info = {}
use_reconnect = False

to_print = False
#to_print = True

def debug_print(*msgs):
    if to_print:
       print(msgs)

redis_conf = settings.STORAGE_CONFIG[settings.STORAGE_INDEX]['realtime_pvp_redis']


def get_user_pvp_info(uid):

    return real_pvp.get_real_pvp_info(uid)


COMMON_ROOM_ID = 'ROOM_1'

maps = []
maps_dir = base_dir + "/apps/realtime_pvp/maps/"
for map_name in glob.glob(maps_dir + "*.map"):
    print map_name
    with open(map_name, 'rb') as fight_f:
        maps.append(fight_f.read().decode('utf-8'))

channels = []


#status = ['req_pvp', 'ans_opponent', 'ans_start_fight', 'req_fight_command', 'ans_fight_command', 'req_end_rount', 'ans_switch_attack']

class Player(object):
    def __init__(self, core_id, redis_com, channel):
        #self.fight_start = False
        self.uid = ''
        self.channel_id = ''
        self.opponent = None

        self.core_id = core_id
        self.opponent_core_id = ''
        self.redis_com = redis_com
        self.channel = channel

        self.connecting = True
        self.end_fight = False

        self.last_recv_time = time.time()


    def send(self, response):
        debug_print("---------send", response)
        if response:
            if isinstance(response, dict):
                response = dumps(response)
            uwsgi.websocket_send(response)

    def broad(self, response):
        debug_print("---------broad", response)
        if response:
            if isinstance(response, dict):
                response = dumps(response)
            self.redis_com.publish(self.channel_id, response)

    def response_error(self, msg_dict, check_msg):
        response = response_error(msg_dict, check_msg)
        print 'error!!!!!!', response
        self.send(response)

    def req_pvp(self, msg_dict):
        response = req_pvp(msg_dict, self.core_id)
        self.uid = msg_dict['uid']
        self.send(response)
        if self.uid in losing_connection_info:
            self.reconnect()
            self.broad_fight_image(msg_dict)
        elif not readying_players:
            readying_players.append(self)
            self.channel_id = self.uid
            self.channel.subscribe(self.channel_id)
            self.channel.unsubscribe(COMMON_ROOM_ID)
            print 'channeling', self.channel_id
        else:
            self.opponent = readying_players.pop()
            self.opponent.opponent = self

            self.opponent_core_id = self.opponent.core_id
            debug_print('oppoent_core_id', self.opponent_core_id)
            debug_print('self_uid', self.uid)

            self.channel_id = self.opponent.channel_id
            self.channel.subscribe(self.channel_id)
            self.channel.unsubscribe(COMMON_ROOM_ID)

            self.broad_pvp_info(response)

    def broad_pvp_info(self, msg_dict):
        response = broad_pvp_info(msg_dict, self.core_id, self.opponent.uid, self.opponent_core_id)
        debug_print('get pvp opp', response)
        self.send(response)
        self.broad(response)

        gevent.sleep(0.5)
        response = broad_start_fight(msg_dict, self.core_id)
        self.send(response)
        self.broad(response)

    def inf_opponent(self, msg_dict):
        self.opponent_core_id = self.opponent.core_id
        response = inf_opponent(msg_dict, self.core_id, self.opponent.uid, self.opponent.core_id)
        debug_print('get inf _opponent', response)
        self.send(response)

    def ans_opponent(self, msg_dict):
        debug_print("get_ans : ans_opponent")
        # self.inf_start_fight(msg_dict)

    def inf_start_fight(self, msg_dict):
        response = inf_start_fight(msg_dict, self.core_id)
        self.send(response)

    def ans_start_fight(self, msg_dict):
        debug_print("get_ans : ans_start_fight")
        #self.fight_start = True

    def req_fight_command(self, msg_dict):
        #
        response_self = req_fight_command(msg_dict, self.core_id)

        self.send(response_self)
        #  广播给对手
        response_opponent = broad_fight_command(msg_dict, self.core_id)
        self.broad(response_opponent)

        # for test

    def inf_fight_command(self, msg_dict):
        # 来自redis 的收到广播信息
        response_self = inf_fight_command(msg_dict, self.core_id)
        self.send(response_self)

    def ans_fight_command(self, msg_dict):
        debug_print("get_ans : ans_fight_command")
        pass

    def req_end_round(self, msg_dict):
        response = req_end_round(msg_dict, self.core_id)
        self.send(response)

        response = broad_end_round(msg_dict, self.core_id, self.opponent_core_id)
        self.send(response)
        self.broad(response)

    def ans_switch_attack(self, msg_dict):
        debug_print("get_ans : ans_switch_attack", self.core_id)
        pass

    def inf_switch_attack(self, msg_dict):
        response = inf_switch_attack(msg_dict, self.core_id)
        self.send(response)

    def req_end_fight(self, msg_dict):
        #response = req_end_fight(msg_dict, self.core_id)

        #self.send(response)
        response = broad_end_fight(msg_dict, self.core_id)
        self.send(response)
        self.broad(response)

        gevent.sleep(0.5)
        result_info = broad_result_fight(msg_dict, self.core_id, self.uid, self.opponent.core_id, self.opponent.uid)
        self.end_fight = True
        self.opponent.end_fight = True
        self.send(result_info)
        self.broad(result_info)

    def rsp_end_fight(self, msg_dict):
        response = rsp_end_fight(msg_dict, self.core_id)
        self.send(response)

    def inf_result_fight(self, msg_dict):
        response = inf_result_fight(msg_dict, self.core_id)
        self.send(response)

    def ans_result_fight(self, msg_dict):
        debug_print("get_ans : ans_result_fight")
        end_fight_reason = msg_dict['end_fight']["pvp_end_reason"]
        disconnect_player(self, self.core_id, self.uid, end_fight_reason)
        pass

    def req_cancel_pvp(self, msg_dict):
        response = req_cancel_pvp(msg_dict, self.core_id)
        self.send(response)
        disconnect_player(self, self.core_id, self.uid, 'cancel by user')


    def reconnect(self):
        self.opponent = losing_connection_info.pop(self.uid)
        self.opponent.opponent = self

        self.opponent_core_id = self.opponent.core_id
        debug_print('reconnect oppoent_core_id', self.opponent_core_id)
        debug_print('self_uid', self.uid)

        self.channel_id = self.opponent.channel_id
        self.channel.subscribe(self.channel_id)
        self.channel.unsubscribe(COMMON_ROOM_ID)

    def broad_fight_image(self, msg_dict):
        response = broad_fight_image(msg_dict, self.core_id)
        self.broad(response)

    def inf_fight_image(self, msg_dict):
        response = inf_fight_image(msg_dict, self.core_id)
        self.send(response)

    def ans_fight_image(self, msg_dict):
        # 收到未断线玩家的战场镜像后，把镜像发给短线方
        self.broad_reconnect_fight(self, msg_dict)

    def broad_reconnect_fight(self, msg_dict):
        response = broad_reconnect_fight(msg_dict, self.core_id)
        self.broad(response)

    def inf_reconnect_fight(self, msg_dict):
        response = inf_reconnect_fight(msg_dict, self.core_id)
        self.send(response)

    def ans_reconnect_fight(self, msg_dict):
        pass

    def req_heart_beat(self, msg_dict):
        response = req_heart_beat(msg_dict, self.core_id)
        print "resv heart_beat", time.time(), self.core_id, self.uid
        self.send(response)


def application(env, sr):

    # ws_scheme = 'ws'
    # if 'HTTPS' in env or env['wsgi.url_scheme'] == 'https':
    #     ws_scheme = 'wss'

    if env['PATH_INFO'] == '/':
        sr('200 OK', [('Content-Type','text/html')])
        return ''

    elif env['PATH_INFO'] == '/foobar/':
        uwsgi.websocket_handshake(env['HTTP_SEC_WEBSOCKET_KEY'], env.get('HTTP_ORIGIN', ''))

        redis_com = redis.StrictRedis(**redis_conf)
        channel = redis_com.pubsub()
        channel.subscribe(COMMON_ROOM_ID)

        websocket_fd = uwsgi.connection_fd()
        redis_fd = channel.connection._sock.fileno()

        core_id = str(env['uwsgi.core'])

        print "\n##Connecting#########################websockets...", core_id, datetime.datetime.now()
        player = Player(core_id, redis_com, channel)


        def handle_msg(msg):
            #msg_dict = json.loads(msg.replace("\n", "\\n"))
            msg = msg.strip()
            debug_print("~~~~~~~~~~reseve", msg)
            if not msg:
                if time.time() - player.last_recv_time >= 15:
                    disconnect_player(player, core_id, player.uid, 'no msg resv in 15s')
                return
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
                player.response_error(msg_dict, check_msg)

            else:
                response_fuc = getattr(player, msg_dict['msgtype'], None)
                if not response_fuc:
                    return
                #print 'ok!!!!!!', response
                player.last_recv_time = time.time()
                response_fuc(msg_dict)

        ready_count = 0


        while player.connecting:
            ready = gevent.select.select([websocket_fd, redis_fd], [], [], 1.0)
            # print "gevent---change", ready, player.core_id, player.uid 
            if not ready[0]:
                try:
                    msg =  uwsgi.websocket_recv_nb()
                except IOError:
                    #continue
                    if ready_count <= 10:
                        ready_count += 1
                        print "retry ready", ready_count
                        gevent.sleep()
                        continue
                    disconnect_player(player, core_id, player.uid, 'no ready')
                    return ''
                handle_msg(msg)

            for fd in ready[0]:
                if fd == websocket_fd:
                    try:
                        msg = uwsgi.websocket_recv_nb()
                    except IOError:
                        disconnect_player(player, core_id, player.uid, 'no msg')
                        return ''
                    handle_msg(msg)

                elif fd == redis_fd:
                    msg = channel.parse_response()
                    if msg[0] == 'message':
                        debug_print("broad msg", msg[2])
                        msg_dict = json.loads(msg[2])
                        response_fuc = getattr(player, msg_dict['msgtype'], None)
                        if not response_fuc:
                            continue

                        response_fuc(msg_dict)
        return ''


def disconnect_player(player, core_id, uid, reason_msg=''):
    if player in readying_players:
        readying_players.remove(player)
    elif use_reconnect:  # 如果是在战斗中掉线 记录对手信息以便重连
        # 判断对手是否也掉线
        if player.opponent.uid in losing_connection_info:
            losing_connection_info.pop(player.opponent.uid)
        # 只是自己掉线
        else:
            losing_connection_info[player.uid] = player.opponent
    # 如果自己掉线  判定对手胜利
    elif reason_msg.startswith('no msg') and not player.end_fight and player.opponent and player.opponent.connecting:
        player.broad(lose_connect_end_fight_msg(player))
        print '\n异常掉线了!!!!!  :****   ({}|--{})'.format(core_id, uid), datetime.datetime.now()
    real_pvp.clear(uid)
    player.connecting = False
    player.end_fight = True
    print '\ndisconnect player:**** {}  ({}|--{})'.format(reason_msg, core_id, uid), datetime.datetime.now()

def lose_connect_end_fight_msg(player):

    msg = {
       "coreid" : player.core_id,
       "datafield" : "end_fight",
       "end_fight" : {
          "pvp_end_reason" : "network_error",
          "win" : player.opponent.core_id,
       },
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
    check_keys = ['msgtype', 'coreid', 'datafield', 'msg_ref', 'rc', 'errormsg']
    if set(check_keys) - set(msg_data.keys()):
        print 'missing keys', set(check_keys) - set(msg_data.keys())
        return 'missing keys'
    if msg_data['rc']:
        return msg_data['errormsg']
    if msg_data['datafield'] not in msg_data:
        return "has no that datafield"

def broad_pvp_info(msg_data, self_core_id, opponent_player_id, opponent_core_id):
    print self_core_id,":I get_opponent_id is", opponent_player_id,
    opp_info = get_user_pvp_info(opponent_player_id)
    opp_info['opponent_coreid'] = opponent_core_id
    success_data = dict(
        msgtype = 'inf_opponent',
        coreid = self_core_id,
        datafield = 'opp_info',
        opp_info = opp_info,
        msg_ref = int(time.time()),
    )
    return response_success(msg_data, success_data)

def inf_opponent(msg_data, self_core_id, opponent_player_id, opponent_core_id):
    debug_print("got inf opponent",msg_data, self_core_id, opponent_player_id, opponent_core_id)
    if msg_data['coreid'] == self_core_id:
        return {}
    print self_core_id,":I get_opponent_id is", opponent_player_id,
    opp_info = get_user_pvp_info(opponent_player_id)
    opp_info['opponent_coreid'] = opponent_core_id
    success_data = dict(
        opp_info = opp_info,
        coreid = self_core_id,
    )
    return response_success(msg_data, success_data)

def req_pvp(msg_data, self_core_id):
    success_data = dict(
        msgtype = 'rsp_pvp',
        coreid = self_core_id,
        status_msg = '系统正在配对中…'.decode('utf-8'),
    )
    return response_success(msg_data, success_data)

def broad_start_fight(msg_data, self_core_id):
    success_data = dict(
        msgtype = 'inf_start_fight',
        datafield = 'pvp_info',
        coreid = self_core_id,
        pvp_info = {
            'attack': self_core_id,
            'fight_info': random.choice(maps),
        },
        msg_ref = int(time.time()),
    )
    return response_success(msg_data, success_data)

def inf_start_fight(msg_data, self_core_id):
    if msg_data['coreid'] == self_core_id:
        return {}
    success_data = dict(
        msgtype = 'inf_start_fight',
        coreid = self_core_id,
    )
    return response_success(msg_data, success_data)

def req_fight_command(msg_data, self_core_id):
    if msg_data['coreid'] != self_core_id:
        return {}
    success_data = dict(
        msgtype = 'rsp_fight_command',
    )
    return response_success(msg_data, success_data)

def broad_fight_command(msg_data, self_core_id):
    if msg_data['coreid'] != self_core_id:
        return {}
    success_data = dict(
        msgtype = 'inf_fight_command',
    )
    return response_success(msg_data, success_data)

def inf_fight_command(msg_data, self_core_id):
    # 不接受自己广播的息信
    if msg_data['coreid'] == self_core_id:
        return {}
    success_data = dict(
        coreid = self_core_id,
    )
    return response_success(msg_data, success_data)

def req_end_round(msg_data, self_core_id):
    if msg_data['coreid'] != self_core_id:
        return {}
    success_data = dict(
        msgtype = 'rsp_end_round',
    )
    return response_success(msg_data, success_data)

def broad_end_round(msg_data, self_core_id, opponent_core_id):
    attack = msg_data[msg_data['datafield']]
    success_data = dict(
        coreid = self_core_id,
        msgtype = 'inf_switch_attack',
        datafield = 'pvp_info',
        pvp_info = {
            'attack': attack,
        },
        msg_ref = int(time.time()),
    )
    return response_success(msg_data, success_data)

def inf_switch_attack(msg_data, self_core_id):
    if msg_data['coreid'] == self_core_id:
        return {}
    success_data = dict(
        coreid = self_core_id,
    )
    return response_success(msg_data, success_data)

#def req_end_fight(msg_data, self_core_id):
#    if msg_data['coreid'] != self_core_id:
#        return {}
#    success_data = dict(
#        coreid = self_core_id,
#        msgtype = 'rsp_end_fight',
#    )
#    return response_success(msg_data, success_data)

def broad_end_fight(msg_data, self_core_id):
    success_data = dict(
        coreid = self_core_id,
        msgtype = 'rsp_end_fight',
    )
    return response_success(msg_data, success_data)

def rsp_end_fight(msg_data, self_core_id):
    if msg_data['coreid'] == self_core_id:
        return {}
    success_data = dict(
        coreid = self_core_id,
    )
    return response_success(msg_data, success_data)

def broad_result_fight(msg_data, self_core_id, self_uid, opponent_core_id, opponent_uid):
    datafield = msg_data['datafield']
    win_core_id = msg_data[datafield]["win"]
    win_uid, lose_uid = (self_uid, opponent_uid) if win_core_id == self_core_id else (opponent_uid, self_uid)
    result_info = real_pvp.result_fight(win_uid, lose_uid)
    
    success_data = dict(
        coreid = self_core_id,
        msgtype = 'inf_result_fight',
    )
    msg_data[datafield].update(result_info)
    return response_success(msg_data, success_data)

def inf_result_fight(msg_data, self_core_id):
    if msg_data['coreid'] == self_core_id:
        return {}
    success_data = dict(
        coreid = self_core_id,
    )
    return response_success(msg_data, success_data)

def req_cancel_pvp(msg_data, self_core_id):
    success_data = dict(
        coreid = self_core_id,
        msgtype = 'rsp_cancel_pvp',
    )
    return response_success(msg_data, success_data)



def broad_fight_image(msg_data, self_core_id):
    success_data = dict(
        coreid = self_core_id,
        msgtype = 'inf_fight_image',
    )
    return response_success(msg_data, success_data)

def inf_fight_image(msg_data, self_core_id):
    if msg_data['coreid'] == self_core_id:
        return {}
    success_data = dict(
        datafield = 'fight_image',
        fight_image = {
        },
        coreid = self_core_id,
    )
    return response_success(msg_data, success_data)

def broad_reconnect_fight(self, msg_data, self_core_id):
    success_data = dict(
        coreid = self_core_id,
        msgtype = 'inf_reconnect_fight',
    )
    return response_success(msg_data, success_data)

def inf_reconnect_fight(self, msg_data, self_core_id):
    if msg_data['coreid'] == self_core_id:
        return {}
    success_data = dict(
        coreid = self_core_id,
    )
    return response_success(msg_data, success_data)

def req_heart_beat(msg_data, self_core_id):
    success_data = dict(
        coreid = self_core_id,
        msgtype = 'rsp_heart_beat',
    )
    return response_success(msg_data, success_data)


