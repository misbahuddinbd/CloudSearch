""" an initiation module for starting all sensors.

This module contains a SensorManager class,
which is a daemon running in background.
It has a responsibility to start all sensors

@author: Misbah Uddin
"""

import argparse
import logging
import sys
import pymongo

from NetworkSearch2.SensorSubsystem.dbConnector import DBConnector

#below configuration for start/stop service
from NetworkSearch2.util.daemon import Daemon

RECREATE_COLL_FLAG = True 
MONGODB_IPADDRESS = "localhost"
MONGODB_PORT = 27017
MONGODB_DATABASE_NAME = "sensor"
MONGODB_COLLECTION_NAME = "objects"

def get_args():
    parser = argparse.ArgumentParser(description = "Sensor subsystem module")
    parser.add_argument("-debug", action='store_true', default=False,
                        help='add debug information to a log')
    parser.add_argument("mode", choices=['start','stop','restart'],
                        help='to start/stop/restart the Network Search module')
    return parser.parse_args()

class SensorManager(Daemon):
    """ A class for initiation of all sensors and theirs components."""

    def run(self):
        """ Overwrite Daemon class. This method will be called when the daemon started."""
        
        logging.info("="*20)
        logging.info("Sensor subsystem module stated ")
        logging.info("="*20)
        
        # clean up all database
        if RECREATE_COLL_FLAG:
            logging.info("Dropping database.")
            connection = pymongo.MongoClient(MONGODB_IPADDRESS,MONGODB_PORT)
            connection[MONGODB_DATABASE_NAME].drop_collection(MONGODB_COLLECTION_NAME)
            logging.info("Database dropped.")
            
            self.collection = connection[MONGODB_DATABASE_NAME][MONGODB_COLLECTION_NAME]
            self.collection.ensure_index([("object-name", pymongo.ASCENDING)])
            self.collection.ensure_index([("content", pymongo.ASCENDING)])
            logging.info("Database created.")
        
        #TODO: initialize sensors (need a list of sensors)
        
        from NetworkSearch2.SensorSubsystem.flowSensorV2 import FlowSensor
        f = FlowSensor()
        f.bind_connector(DBConnector())
        f.start()
        
        from NetworkSearch2.SensorSubsystem.userSensor import UserSensor
        u = UserSensor()
        u.bind_connector(DBConnector())
        u.start()
        
        from NetworkSearch2.SensorSubsystem.procSensor import ProcSensor
        p = ProcSensor()
        p.bind_connector(DBConnector())
        p.start()
        
        from NetworkSearch2.SensorSubsystem.serverSensor import ServerSensor
        s = ServerSensor()
        s.bind_connector(DBConnector())
        s.start()
        
        from NetworkSearch2.SensorSubsystem.interfaceSensor import InterfaceSensor
        i = InterfaceSensor()
        i.bind_connector(DBConnector())
        i.start()
        
        from NetworkSearch2.SensorSubsystem.imageSensor import ImageSensor
        im = ImageSensor()
        im.bind_connector(DBConnector())
        im.start()
        
        from NetworkSearch2.SensorSubsystem.vmSensor import VmSensor
        v = VmSensor()
        v.bind_connector(DBConnector())
        v.start()
        
        from NetworkSearch2.SensorSubsystem.customerSensor import CustomerSensor
        c = CustomerSensor()
        c.bind_connector(DBConnector())
        c.start()
        
        from NetworkSearch2.SensorSubsystem.fileSensor import FileSensor
        fi = FileSensor()
        fi.bind_connector(DBConnector())
        fi.start()
        
        logging.info("End of initiation phase")
        f.join()
    
def main():
    
    # Read command arguments
    try:
        args = get_args()
    except IOError as (errno, strerror):
        print "IOError({0}): {1}".format(errno,strerror)
        
    # setup a logging
    logging_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(filename=str(sys.path[0])+'/SensorManager2.log',
                    level=logging_level,format='%(asctime)s %(levelname)s: %(module)s: %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')
        
    # setup a daemon
    daemon = SensorManager('/tmp/sensor2.pid', stdout=sys.stdout, stderr='SensorManager2.log')
    if 'start' == args.mode:
        print 'started'
        daemon.start()
    elif 'stop' == args.mode:
        daemon.stop()
        print 'stopped'
    elif 'restart' == args.mode:
        daemon.restart()
    else:
        pass
    
if __name__ == "__main__" :
    exit(main())
    