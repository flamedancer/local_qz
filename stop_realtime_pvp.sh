#!/bin/bash
DIR=`pwd`
PID=`ps aux |grep $DIR |grep uwsgi_realtime_pvp.ini |grep -v grep |awk '{print $2}'`
for i in $PID
do
        rm -f $DIR/logs/realtime_pvp_uwsgi.pid
        `/bin/kill -9 $i`
done
echo "uwSGI stop done!"
