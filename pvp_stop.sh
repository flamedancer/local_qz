#!/bin/bash


DIR=$(dirname $(readlink -f $0))
PID=`ps aux |grep $DIR |grep realtime_pvp/pvp2.py |grep -v grep |awk '{print $2}'`
echo `ps aux|grep $DIR/apps/realtime_pvp/pvp2.py`
for i in $PID
do
    echo "close pid ${i}"
        kill -9 ${i}
done