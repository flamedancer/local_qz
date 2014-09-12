#-* coding:utf-8 -*-

import hashlib

# 管理后台安全校验码
ADMIN_SECRET_KEY='s3avlj$=vk16op_s1g!xyilse9azcu&oh#wln8_@!b+_p7-+@='

def build_rkauth_signature(rkauth_fields):
    """生成rkauth签名"""
    payload = "&".join(k + "=" + str(rkauth_fields[k]) for k in sorted(rkauth_fields.keys()) if k != "rkauth_token")
    return hashlib.md5(payload).hexdigest()
