#!/bin/bash


DIR=/alidata/sites/stg/qz
./gevent_test_stop.sh


echo "restart"
#!/bin/bash
ports=(9040 9045 9042 9043 9044)
for port in ${ports[@]}
do

    nohup python ${DIR}/apps/realtime_pvp/pvp2.py "${port}" >> ${DIR}/logs/realtime_pvp_oneclick.log 2>&1  &
done
echo `ps aux|grep $DIR/apps/realtime_pvp/pvp2.py`
[test2 /data/sites/stg/qz]$ cat gevent_test_stop.sh
\#!/bin/bash
DIR=/alidata/sites/stg/qz
PID=`ps aux |grep $DIR |grep realtime_pvp/pvp2.py |grep -v grep |awk '{print $2}'`
echo `ps aux|grep $DIR/apps/realtime_pvp/pvp2.py`
for i in $PID
do
    echo "close pid ${i}"
        kill -9 ${i}
done
