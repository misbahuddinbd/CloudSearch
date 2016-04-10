""" Contain an abstract class for a connector used by a sensor.

This module contains a GenericConnector class, 
which is used as an abstract class for connectors 
used by a sensor. 

@author: Misbah Uddin
"""

class GenericConnector(object):
    """ An abstract class for connector used by a sensor. """
    
    
    def update(self,obj):
        """ This is an abstract method for performing an update when the sensor detects changes"""
        raise NotImplementedError( "Should have implemented this" )
    
    def delete(self,obj):
        """ This is an abstract method for performing an update when the sensor detects expires"""
        raise NotImplementedError( "Should have implemented this" )