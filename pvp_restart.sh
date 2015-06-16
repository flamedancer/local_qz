#!/bin/bash

DIR=$(dirname $(readlink -f $0))
./pvp_stop.sh


echo "restart"
#!/bin/bash
ports=(9040)
for port in ${ports[@]}
do
    nohup python ${DIR}/apps/realtime_pvp/pvp2.py "${port}" >> ${DIR}/logs/realtime_pvp_oneclick.log 2>&1  &
done
echo `ps aux|grep $DIR/apps/realtime_pvp/pvp2.py`