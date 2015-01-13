#!/bin/bash
BASEDIR=$(dirname $(readlink -f $0))
DIR=$BASEDIR/client

#if change LOGDIR, also need change in client/async_write.py
LOGDIR=$BASEDIR/../logs
if [ ! -d $LOGDIR ]; then 
    mkdir -p $LOGDIR
fi

#REDIS_LIST="0 1"    #一组redis 用来存储游戏数据, 见 apps.settings.py
REDIS_LIST="0"    #一组redis 用来存储游戏数据, 见 apps.settings.py
PROCESS_NUM=1
export PYTHONPATH=$BASEDIR
for index in $REDIS_LIST;do
    for((i=0;i<$PROCESS_NUM;i++));do 
        nohup python $DIR/async_write.py $index &
    done
done


sleep 1
pid=`ps xa |grep "$DIR/async_write.py" | grep -v grep |awk '{print $1}'`
echo "async_write started, process ID: $pid"
