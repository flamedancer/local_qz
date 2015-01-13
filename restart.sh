#!/bin/bash
DIR=$(dirname $(readlink -f $0))
PSID=`ps aux|grep $DIR|grep uwsgi |grep -v grep|wc -l`

#python $DIR/import_test.py
/usr/local/bin/python $DIR/import_test.py

if [ $PSID -gt 0 ]; then
    kill -HUP `cat $DIR/logs/uwsgi.pid`
    echo "uwSGI restart done!"
else
    /usr/local/bin/uwsgi --ini $DIR/uwsgi.ini
    echo "uwSGI start done!"
fi

