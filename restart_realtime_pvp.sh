#!/bin/bash
DIR=`pwd`
PSID=`ps aux|grep $DIR|grep uwsgi_realtime_pvp.ini|grep -v grep|wc -l`
if [ $PSID -gt 0 ]; then
    kill -HUP `cat $DIR/logs/realtime_pvp_uwsgi.pid`
    echo "uwSGI restart done!"
else
    /usr/local/bin/uwsgi204 --ini $DIR/uwsgi_realtime_pvp.ini
    echo "uwSGI start done!"
fi

