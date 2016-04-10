""" Contain DBConnector class.

This module contains a DBConnector class used
as a main connector for the sensors to send 
the information they detect to the database 
as well as to the index system.

@author: Misbah Uddin
"""

import pymongo
import time 
from datetime import datetime

from NetworkSearch2.SensorSubsystem.genericConnector import GenericConnector

MONGODB_IPADDRESS = "localhost"
MONGODB_PORT = 27017
MONGODB_DATABASE_NAME = "sensor"
MONGODB_COLLECTION_NAME = "objects"

import zmq
INDEXING_PORT = 7733
context = zmq.Context()

class DBConnector(GenericConnector):
    """ this class is for update information to the local mongodb database """
    
    def __init__(self):
        super(DBConnector,self).__init__()
        
        # setup mongoDB
        connection = pymongo.MongoClient(MONGODB_IPADDRESS,MONGODB_PORT)
        self.db_collection = connection[MONGODB_DATABASE_NAME][MONGODB_COLLECTION_NAME]
        
        # the host name that discovered the object
        import platform
        self.HOST_SERVER = 'ns:' + platform.uname()[1]
        
        # a connection to index system
        self.index_connector = context.socket(zmq.PUSH)
        self.index_connector.connect("tcp://localhost:"+str(INDEXING_PORT))
    
    def update(self,obj):
        """ Override the super class. this method is for performing
        an update when the sensor detects changes"""
        
        obj['server'] = self.HOST_SERVER
                
        # list of all attributes and values
        content = list(self._flatten_to_list(obj)) 
        
        # find object in the database by object-name
        obj_in_db = self.db_collection.find_one({'object-name':obj['object-name']},{'last-updated':0,'content':0})
        
        # if exist
        if obj_in_db:
            # get the changed values, in a form of {key:value}
            changes_dict = self._get_change(obj, obj_in_db)
            
            # add additional information    
            changes_dict.update({'last-updated':datetime.now(),
                                 'content':content })
            
            # if there is a change, update index as well
            if len(changes_dict) > 2:
                obj.update({'_id':obj_in_db['_id'],'content':list(content)})
                # TODO: disable the update for now, need to do the update one in a while
                self.index_connector.send_pyobj([1,obj])
                            
            # get the keys that have been removed from the object,  in a form of {key:""}
            removed_key_dict = {attr:"" for attr in (obj_in_db.viewkeys() - obj.viewkeys()) if attr != '_id'}
            
            # apply changes to the database
            if changes_dict or removed_key_dict:
                self.db_collection.update({'object-name':obj['object-name']},{'$set':changes_dict, '$unset':removed_key_dict})

        # not exist, do insert
        else:
            obj.update({'content':content})
            self.db_collection.insert(obj)
            # send to index as well
            self.index_connector.send_pyobj([1,obj])
            # we don't need '_id' information since object-name is uniquely identify
            del obj['_id']
            
    def delete(self,obj):
        """ Override the super class. this method is for performing
        a deletion when the sensor detects changes"""
        
        obj_in_db = self.db_collection.find_one({'object-name':obj['object-name']},{'_id':1})
        if obj_in_db: 
            self.index_connector.send_pyobj([2,obj_in_db])
            self.db_collection.remove({'object-name':obj['object-name']})
    
    def _get_change(self,new_obj,old_obj):
        """ (dict,dict) -> dict
        get the changed values, in a form of {key:value,}"""
        
        try:
            changes_dict = dict(new_obj.viewitems() - old_obj.viewitems())
        except TypeError: 
            # in case of the value contain a list, since a list is a unhashable type
            
            new_attr_set = new_obj.viewkeys() - old_obj.viewkeys() # get new attribute
            new_attr_value_dict = {attr:new_obj[attr] for attr in new_attr_set} # get new attribute-value
            
            common_attrs = new_obj.viewkeys() & old_obj.viewkeys() # get intersection of attributes
            changes_dict = {attr:new_obj[attr] for attr in common_attrs if new_obj[attr] != old_obj[attr]} # get changed values by checking from the common attributes
            
            changes_dict.update(new_attr_value_dict)
            
        return changes_dict
            
    def _flatten_to_list(self,x):
        """ flatten nested dicts, lists, tuples, or sets generators to lists"""
        
        # if x is a dict, we need to pop both values and keys
        if isinstance(x, dict):
            for key in x.iterkeys():
                yield key
            for value in x.itervalues():
                for item in self._flatten_to_list(value):
                    yield item
        # if x is a list, tuple, or set pop out each item
        elif isinstance(x, (list, tuple, set)):
            for item in x:
                for subitem in self._flatten_to_list(item):
                    yield subitem
        else:
            yield x     
