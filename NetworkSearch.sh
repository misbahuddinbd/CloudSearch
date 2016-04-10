#!/bin/bash
#NetworkSearch.sh $@

if [ -z "$@" ]
then
	echo "Basic usage : ./NetworkSearch.sh {start,stop}"
	exit 1 
fi


# get current working directory
_pwd=`pwd`

# export the python path
export PYTHONPATH=$_pwd

echo "$@ Query processing module..."
python "$_pwd/NetworkSearch2/manager.py" $@ &
sleep 1

echo "$@ Indexing module..."
python "$_pwd/NetworkSearch2/IndexingSubsystem/indexManager.py" $@ &
sleep 1

echo "$@ Sensor module..."
sudo env PYTHONPATH=$_pwd python "$_pwd/NetworkSearch2/SensorSubsystem/sensorManager.py" $@ &
sleep 1

echo "$@ web module..."
nohup python "$_pwd/NetworkSearch2/web/web.py" $@ &
sleep 1

echo "Done"





