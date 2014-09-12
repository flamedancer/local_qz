#!/bin/bash
DIR=/data/sites/MaxStrike
/usr/local/bin/python $DIR/import_test.py
PSID=`ps aux|grep $DIR|grep uwsgi |grep -v grep|wc -l`
if [ $PSID -gt 2 ]; then
    echo "uWSGI is runing!"
    exit 0
else
    /usr/local/bin/uwsgi --ini $DIR/uwsgi.ini
    echo "uwSGI start done!"
fi
