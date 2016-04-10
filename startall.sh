#!/bin/bash
#kth-lcn-opdata-in-clouds/startall.sh $@

#variable
APATH="/home/amy/kth-lcn-opdata-in-clouds/NetworkSearch2"
BPATH="/home/user/amy/kth-lcn-opdata-in-clouds/NetworkSearch2"
PYPATH="PYTHONPATH=/home/user/amy/kth-lcn-opdata-in-clouds/"
export PYTHONPATH=/home/amy/kth-lcn-opdata-in-clouds/


echo "===============$@ query processing module ================="
python $APATH/manager.py $@ &

for i in {2..9}
do
    ssh user@cloud-$i "export $PYPATH; python $BPATH/manager.py $@" &
    sleep 0.5
done
sleep 2

echo "===============$@ indexing module ================="
python $APATH/IndexingSubsystem/indexManager.py $@ &

for i in {2..9}
do
    ssh user@cloud-$i "export $PYPATH; python $BPATH/IndexingSubsystem/indexManager.py $@" &
done
sleep 2

echo "===============$@ sensing module================="
sudo env PYTHONPATH=/home/amy/kth-lcn-opdata-in-clouds/ python $APATH/SensorSubsystem/sensorManager.py $@ &

for i in {2..9}
do
    ssh user@cloud-$i "sudo env $PYPATH python $BPATH/SensorSubsystem/sensorManager.py $@" &
done

sleep 2
#EXIT
