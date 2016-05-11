from base64 import b64decode, b64encode
from Crypto.Cipher import AES
from Crypto.Hash import HMAC, SHA256
from Crypto import Random

BS = 16
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS) 
unpad = lambda s : s[:-ord(s[len(s)-1:])]

def encrypt(key, plain):
    plain = pad(plain)
    iv = Random.new().read(AES.block_size)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted = b64encode(iv + cipher.encrypt(plain))
    return encrypted

def decrypt(key, encripted):
    encripted = b64decode(encripted)
    iv = encripted[:BS]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    plain = unpad(cipher.decrypt(encripted[BS:]))
    return plain

def hmacsha256(key,msg_list):
    msg=''
    for el in msg_list:
        msg += str(el)

    print key
    print msg




    hash_obj = HMAC.new(key=key, msg=bytearray(msg), digestmod=SHA256)
    return b64encode(hash_obj.digest())