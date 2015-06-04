
Redis (version 2.2.12)
MongoDB (version 2.4.5)
msgpack-python


本地化 qz

sudo pip install Django==1.3.1
sudo pip install uwsgi

cp -r ../../qz_svn/back-end-code/guochen\ \(branch\)

更改或替换 文件   restart.sh uwsgi.ini application.py setting.py 
更改这些文件中内容有路径的为本地路径
如 DIR=/data/sites/MaxStrike 改为 DIR=`pwd`

安装  sudo pip install pymongo
      sudo pip install redis
      sudo pip install msgpack-python
      sudo pip install xlrd
      sudo pip install pycrypto
      sudo pip install pycurl

修改 pymongo bug  ：  在  /python2.7/site-packages/pymongo/common.py  第392行加入一行：
     'max_pool_size': validate_positive_integer_or_none,


注释掉： apps/views/main.py", line 41 
# from M2Crypto import RSA as M2Crypto_RSA


修改 setting 里面的数据库地址



设置第一个admin权限：
            进入  manage shell
            from apps.admin.models import Moderator
            import hashlib
            username = 'guochen'
            password = '1'
            moderator = Moderator.get_instance(username)
            moderator.username = username
            moderator.is_staff = True
            moderator.set_password(hashlib.md5(password).hexdigest())
            moderator.in_review = False
            moderator.permissions = 'super'
            moderator.put()


设置第一个uid:
   在mongo中创建sequence并初始化：
   db.sequence.insert(
       {
          _id: "userid",
          seq: 100000000
       }
    )


