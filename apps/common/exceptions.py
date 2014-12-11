# encoding: utf-8

from apps.common import utils


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class ParamsError(Error):
    """参数错误异常

    在游戏逻辑处理中发现前端传的参数有缺失
    或不符要求，抛出此异常
    """
    rc = 6
    msg = "ParamsError"


class GameLogicError(Error):
    """游戏逻辑错误异常

    在游戏逻辑处理中发现逻辑不通时，抛出此异常

    Attributes:
        msg: 具体给前端显示的错误信息

    Args:
        msg_key: 出错所属计算逻辑类别
        msg_value: 此类别类别的具体出错原因

    """
    rc = 11

    def __init__(self, msg_key, msg_value=""):
        self.msg = utils.get_msg(msg_key, msg_value) or msg_key


