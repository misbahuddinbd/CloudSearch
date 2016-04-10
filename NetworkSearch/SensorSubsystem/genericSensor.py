""" Contain an abstract class for a sensor.

This module contains a GenericSensor class, 
which is used as an abstract class for sensors.
All sensors should inherit this class. 

@author: Misbah Uddin
"""

import logging
from threading import Thread

from NetworkSearch2.SensorSubsystem.genericConnector import GenericConnector

class GenericSensor(Thread):
    """ An abstract class for a sensor. The sensor is a thread-based class.
    It is needed to implement the "run()" method. In addition, the implementation of run()
    require an infinite loop for making sensor run forever (as long as the main thread is alive.)"""
    
    
    object_name_history_set = None # used for deletion of the old and not existed object is case of using updates_and_deletes()
    
    def __init__(self):
        super(GenericSensor,self).__init__()
        self._connectors = []
        self.daemon = True

    def bind_connector(self,connector):
        """ this method is to bind the connector with the sensor. 
        when the sensor detect changes, all binded connectors will be notified."""
        
        # sanity check
        if not isinstance(connector, GenericConnector):
            raise TypeError("the argument object has to be subclass of the GenericConnector")
         
        # binding
        self._connectors.append(connector)
        
    def updates_and_deletes(self,Adict):
        """ (dict,) -> None
        
        This method perform an update and a deletion from the states (aDict) provided.
        It also saves a historical object-name set for checking for object existence
        in order to signal the deletion via connectors  
        
        Attribute: aDict - a python dictionary used as key-value store, 
        i.e. key of dictionary is a 'object-name' and value is a (JSON)
        dictionary object. 
        """
        
        ##################
        # perform update #
        ##################
                    
        # send the update
        for userObjects in Adict.values():
            self.send_update(userObjects)
            
        ####################
        # perform deletion #
        ####################
        # get marked delete objects
        try:
            not_existed_object_name_set = self.object_name_history_set - Adict.viewkeys()
        except TypeError: # encouter for the first time
            self.object_name_history_set = set(Adict.viewkeys()) 
            not_existed_object_name_set = set()
            
        # send delete updates
        for name in not_existed_object_name_set:
            self.send_delete({'object-name':name})

        # replace history set
        self.object_name_history_set = set(Adict.viewkeys())
        
    def send_update(self,obj):
        """ Delegate the task to connectors."""
        if self._connectors:
            for connector in self._connectors:
                connector.update(obj)
        else:
            logging.warning("Sensor has no connector")
        
    def send_delete(self,obj):
        """ Delegate the task to connectors."""
        
        if self._connectors:
            for connector in self._connectors:
                connector.delete(obj)
        else:
            logging.warning("Sensor has no connector")
        
    def run(self):
        """ This is an abstract method, you need to implement this."""
        raise NotImplementedError( "Should have implemented this" )
    