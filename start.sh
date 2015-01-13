#!/bin/bash
DIR=$(dirname $(readlink -f $0))

#python $DIR/import_test.py
/usr/local/bin/python $DIR/import_test.py

PSID=`ps aux|grep $DIR/uwsgi.ini |grep -v grep|wc -l`
if [ $PSID -gt 2 ]; then
    echo "uWSGI is runing!"
    exit 0
else
    #add sudo -u svnrelease, so that even run ./restart under root, this uwsgi
    #process can still be killed, restarted by later svn source update.
    #Then need add /usr/local/bin/uwsgi into /etc/sudoers
    sudo -u cxu1 /usr/local/bin/uwsgi --ini $DIR/uwsgi.ini

    echo "uwSGI start done!"
fi
