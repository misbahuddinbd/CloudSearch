""" contains ECHOMessage class.

It defines the ECHOMessage class. It contains the Echo message information.
e.g. query object, message_type. invoke_id etc.
It is served for being an data object.

@author: Misbah Uddin
"""

import cPickle as pickle
from pprint import pformat
import time
# for profiling
from NetworkSearch2.ProfileTools.myProfiler import Profiler

class ECHOMessage():

    # define enumerator of message types
    MSG_TYPE_INVOKE = 0
    MSG_TYPE_EXP = 1 
    MSG_TYPE_ECHO = 2
    MSG_TYPE_RETURN = 3
    
    def __init__(self, msg_type=None, msg_id=None, sent_from=None, data=None):
        self.msg_type = msg_type
        self.msg_id = msg_id
        self.sender = sent_from #.strip('\x00')
        
        self.data = pickle.dumps(data, pickle.HIGHEST_PROTOCOL)
        
#         if data:
#             self.data = pickle.dumps(data, pickle.HIGHEST_PROTOCOL)
#         else:
#             self.data = "S''\n."

    def get_type(self):
        """ Return a message type"""
        return self.msg_type
    
    def get_id(self):
        """ Return a message id"""
        return self.msg_id
    
    def get_sender_name(self):
        """ Return a sender name"""
        return self.sender
    
    def get_data(self):
        """ Return a message data"""
        return pickle.loads(self.data)
    
    def serialize(self):
        """ Serialize the object so that it can transmit through a socket."""
        #note: right now it is fixed length of sender name
        #return struct.pack('>hI30s', self.msg_type, self.msg_id, self.sender)+self.data
        
        # collecting time for profiling
        if Profiler.enabled:
            self.t0 = time.time()
        
        return pickle.dumps(self, pickle.HIGHEST_PROTOCOL)
    
    @staticmethod
    def deserialize(string):
        """ De-serialize the string back to the python object."""
        #msg = ECHOMessage(*struct.unpack('>hI30s',string[:36]))
        #msg.data = string[36:]
        #return  msg
        
        return pickle.loads(string)
    
    def __str__(self):
        # for better presentation
        return pformat(self.__dict__)
    