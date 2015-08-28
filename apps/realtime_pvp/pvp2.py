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

# 获得本机ip
import fcntl
import struct
def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])
localIP = get_ip_address('eth1')
# localIP = socket.gethostbyname(socket.gethostname())
# localIP = '42.96.168.85'
server_site = localIP + ":" + port
THIS_READYING_REDIS = readying_player_redis.ALL_REDIS_MODEL[server_site]
print "$$$$$$$$THIS  server_site is", server_site 


all_players = []  # 所有连接成功的玩家


# 用于匹配分数最接近对手
readying_players_scores = []   # 和等待对手玩家的从小到大的有序score list
readying_players = []   # 和readying_players_score按顺序对应的等待对手的玩家实例



# 'losing_connect_uid' : opponent_player_object
losing_connection_info = {}
use_reconnect = False

to_print = False
#to_print = True


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

        self.fight_statue = -2  # -2 为连接上未做任何操作  -1 readying等待合适对手中 0 找到对手，但可以取消  1 fighting正在pk  2 end战斗结束

        self.last_recv_fg = True    # 判断是否活跃通信的标示，用于主动断开长时间没有通信的玩家

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
        返回最适合的对手index，若无合适对手返回None
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
            # 为全队 最小
            if index == 0:
                most_near_index = 0
            # 全队最大
            elif index == max_index + 1:
                most_near_index = max_index
            else:
                near_left,  near_right = index - 1, index
                # 相邻的左右
                if (readying_players_scores[near_left] + readying_players_scores[near_right]) / 2 <= score:
                    most_near_index = near_right
                else:
                    most_near_index = near_left
        else:
            # 只有自己在等待
            if len(readying_players) == 1:
                return
            # 为全队 最小
            if index == 0:
                most_near_index = 1
            # 全队最大
            elif index == max_index:
                most_near_index = max_index - 1
            else:
                near_left, near_right = index - 1, index + 1
                # 相邻的左右
                if (readying_players_scores[near_left] + readying_players_scores[near_right]) / 2 <= score:
                    most_near_index = near_right
                else:
                    most_near_index = near_left
        print "debug ", most_near_index, readying_players_scores
        # 如果是首次匹配而且 gap 太大， 不进行匹配，而是加入等待
        # if self.fight_statue == -2 and abs(readying_players_scores[most_near_index] - score) > 100:
        if self.fight_statue == -2 and abs(readying_players_scores[most_near_index] - score) < 0:
            readying_players_scores.insert(index, score)
            readying_players.insert(index, self)
            THIS_READYING_REDIS.set(self.uid, score)
            return
        else:
            # 移除并获取对手
            readying_players_scores.pop(most_near_index)
            opponent = readying_players.pop(most_near_index)
            THIS_READYING_REDIS.remove(opponent.uid)
            # 移除自己
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
        # 有可能此时对手已经退出匹配
        if not self.opponent:  # self.fight_statue != 0
            return
        response_self = inf_opponent(msg_dict, self.opponent.uid, self.opponent.core_id)
        print "***** {} PK  {} ****".format(self.uid, self.opponent.uid), datetime.datetime.now()
        self.send(response_self)
        # print "have send", response_self
        self.fight_statue = 1
        # 当两边都准备好了 才发开始战斗消息
        if self.opponent.fight_statue == 1:
            # attack_core_id = self.core_id if self.first_attacker else self.opponent.core_id
            attack_core_id = self.core_id if random.randint(0, 1) else self.opponent.core_id
            # 给两方广播 开始战斗消息  包括谁是攻击方信息
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
    #     # 给两方分别发 各自的对手信息
    #     response_self = inf_opponent(msg_dict, self.opponent.uid, self.opponent.core_id)
    #     response_opponent = inf_opponent(msg_dict, self.uid, self.core_id)
    #     print "***** {} PK  {} ****".format(self.uid, self.opponent.uid), datetime.datetime.now()
    #     debug_print('get pvp opp', response_self)
    #     self.send(response_self)
    #     self.send_opponent(response_opponent)
    #     # 给两方广播 开始战斗消息  包括谁是攻击方信息
    #     response = inf_start_fight(msg_dict, attack_core_id=self.core_id)
    #     self.broad(response)

    def ans_opponent(self, msg_dict):
        debug_print("get_ans : ans_opponent")

    def ans_start_fight(self, msg_dict):
        debug_print("get_ans : ans_start_fight")
        #self.fight_start = True

    def req_fight_command(self, msg_dict):
        # 回复
        # response_self = req_fight_command(msg_dict)
        # self.send(response_self)
        # 转发给对手
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

    def req_skill_ball(self, msg_dict):
        self.req_fight_command(msg_dict)


    def ans_fight_command(self, msg_dict):
        debug_print("get_ans : ans_fight_command")
        pass

    # def req_end_round(self, msg_dict):
    #     response = req_end_round(msg_dict)
    #     self.send(response)

    #     self.inf_switch_attack(msg_dict)

    # def inf_switch_attack(self, msg_dict):
    #     response = inf_switch_attack(msg_dict, self.opponent.core_id)
    #     self.broad(response)

    def req_changeround(self, msg_dict):
        self.changeround_switch = 1
        if self.opponent.changeround_switch:
            response = inf_changeround(msg_dict)
            self.broad(response)
            self.changeround_switch = self.opponent.changeround_switch = 0

    def ans_switch_attack(self, msg_dict):
        debug_print("get_ans : ans_switch_attack", self.core_id)
        pass

    def req_end_fight(self, msg_dict):
        response = rsp_end_fight(msg_dict)
        self.broad(response)

        result_info = inf_result_fight(msg_dict, self, self.opponent)
        self.fight_statue = self.opponent.fight_statue = 2
        self.broad(result_info)

    def ans_result_fight(self, msg_dict):
        debug_print("get_ans : ans_result_fight")
        end_fight_reason = msg_dict["pvp_end_reason"]
        disconnect_player(self, reason_msg=end_fight_reason)
        pass

    def req_cancel_pvp(self, msg_dict):
        if self.fight_statue > 0:
            return
        response = req_cancel_pvp(msg_dict)
        self.send(response)
        disconnect_player(self, reason_msg='cancel by self')
        # 若是在准备战斗阶段 将对手对手重置成 正在寻找对手
        if self.opponent:
            # disconnect_player(self.opponent, reason_msg='cancel by opponent')

            # 通知对方自己已经放弃
            self.opponent.send(inf_opponent_cancel(msg_dict))

            self.opponent.opponent = None
            self.opponent.fight_statue = -1
            self.opponent.first_attacker = False

            readying_players_scores.append(self.opponent.score)
            readying_players.append(self.opponent)
            THIS_READYING_REDIS.set(self.opponent.uid, self.opponent.score)

    def ans_opponent_cancel(self, msg_dict):
        # 客户端回复 对手已取消此次匹配
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
        # 收到未断线玩家的战场镜像后，把镜像发给短线方
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
    elif use_reconnect:  # 如果是在战斗中掉线 记录对手信息以便重连
        # 判断对手是否也掉线
        if player.opponent.uid in losing_connection_info:
            losing_connection_info.pop(player.opponent.uid)
        # 只是自己掉线
        else:
            losing_connection_info[player.uid] = player.opponent
    # 如果自己掉线  判定对手胜利
    elif reason_msg.startswith('no msg') and player.fight_statue == 1 and player.opponent and player.opponent.connecting:
        player.req_end_fight(lose_connect_end_fight_msg(player))
        print '\n 异常掉线了!!!!!  :****   ({}|--{})'.format(player.core_id, player.uid), datetime.datetime.now()

    print 'disconnect player:**** {}  ({}|--{})'.format(reason_msg, player.core_id, player.uid)


def lose_connect_end_fight_msg(player):
    # 掉线的通知信息

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
    # if msg_data['datafield'] not in msg_data:
    #     print '!!!!! json missing datafield:', msg_data['datafield']
    #     return "has no that datafield", msg_data['datafield']


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
#     # 不接受自己广播的息信
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


# def inf_switch_attack(msg_data, attack_core_id):
#     success_data = dict(
#         msgtype = 'inf_switch_attack',
#         datafield = 'pvp_info',
#         pvp_info = {
#             'attacker': attack_core_id,
#         },
#         msg_ref = int(time.time()),
#     )
#     return response_success(msg_data, success_data)


def inf_changeround(msg_data):
    success_data = dict(
        msgtype = 'inf_changeround',
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
    """剔除长时间没有数据交互的晚间，每隔15秒检查
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
        time.sleep(15000)


if __name__ == "__main__":
    path = os.path.dirname(geventwebsocket.__file__)
    agent = "gevent-websocket/%s" % (geventwebsocket.get_version())

    print "start check user connecting"         # 开启检查掉线玩家进程
    thread.start_new_thread(check_dead_user, ())
    try:
        print "Running %s from %s" % (agent, path)
        print "start pvp serve", datetime.datetime.now()
        # 保证等待列表数据库表为空
        THIS_READYING_REDIS.clear()
        WebSocketServer(("", int(port)), application, debug=False).serve_forever()
    except KeyboardInterrupt:
        print "close-server"
    finally:
        THIS_READYING_REDIS.clear()
        # for player in all_players:
        #     disconnect_player(player, "server-close")

