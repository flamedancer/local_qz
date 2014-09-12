# -*- encoding: utf-8 -*-
#import base64
#
#from M2Crypto.EVP import Cipher
#from M2Crypto import m2
#from django.conf import settings
#
#iv = '\0' * 32
#passKey = settings.AES_KEY
#
#def encrypt(buf):
#    cipher = Cipher(alg = 'aes_256_ecb', key = passKey, iv = iv, op = 1)
#    cipher.set_padding(padding = m2.no_padding)
#    v = cipher.update(buf)
#    v = v + cipher.final()
#    del cipher
#
#    #out = ""
#    #for i in v:
#    #    out += "%02X" % (ord(i))
#
#    return v
#
#
#def decrypt(buf):
#    cipher = Cipher(alg = 'aes_256_ecb', key = passKey, iv = iv, op = 0)
#    cipher.set_padding(padding = m2.no_padding)
#    v = cipher.update(buf)
#    v = v + cipher.final()
#    del cipher
#
#    return v
#
#
#def decryptEx(buf):
#    try:
#        bufEx = base64.decodestring(buf)
#        return decrypt(bufEx)
#    except:
#        return ""
#
#def encryptEx(buf):
#    cipher = Cipher(alg = 'aes_256_ecb', key = passKey, iv = iv, op = 1)
#    cipher.set_padding(padding = m2.no_padding)
#    v = cipher.update(buf)
#    v = v + cipher.final()
#    del cipher
#
#    #out = ""
#    #for i in v:
#    #    out += "%02X" % (ord(i))
#
#    return base64.encodestring(v)

