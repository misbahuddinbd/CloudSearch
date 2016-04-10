#!/bin/bash
#kth-lcn-opdata-in-clouds/startall.sh $@

#variable
APATH="/home/amy/kth-lcn-opdata-in-clouds/NetworkSearch2"
BPATH="/home/user/amy/kth-lcn-opdata-in-clouds/NetworkSearch2"
PYPATH="PYTHONPATH=/home/user/amy/kth-lcn-opdata-in-clouds/"
export PYTHONPATH=/home/amy/kth-lcn-opdata-in-clouds/


echo "===============$@ sensing module================="
sudo env PYTHONPATH=/home/amy/kth-lcn-opdata-in-clouds/ python $APATH/SensorSubsystem/sensorManager.py $@ &

for i in {2..9}
do
    ssh user@cloud-$i "sudo env $PYPATH python $BPATH/SensorSubsystem/sensorManager.py $@" &
done

sleep 1
#EXIT
