""" A message dispatcher.
 
This is a module for a message dispatcher 
for both incoming messages and outgoing messages.
However, the outgoing message dispatcher is not in used.
 
@author: Misbah Uddin
"""

import logging
import threading
import zmq

from NetworkSearch2.QuerySubsystem.echoMessage import ECHOMessage

# for profiling
from NetworkSearch2.ProfileTools.myProfiler import Profiler
import time

#############################
# read a configuration file #
#############################
from ConfigParser import SafeConfigParser
from sys import path

confparser = SafeConfigParser()
confparser.read([str(path[0])+'/config.cfg'])

# get values
DISPATCHER_PORT = confparser.getint('Dispatcher','dispatcher_port')

del confparser

#############################

class IncomingDispatcher(threading.Thread):
    """ A thread that receives incoming messages, multiplexes 
    and load-balances to workers (echoProcesses)."""
    
    def __init__(self,process_queue_list):
        # base class initialization
        super(IncomingDispatcher,self).__init__()
        
        self.process_queue_list = process_queue_list
        self.Nprocess = len(process_queue_list)
        
        # open message receiving socket.
        self.context = zmq.Context()
        self.receiver = self.context.socket(zmq.PULL)
        self.receiver.bind("tcp://*:"+str(DISPATCHER_PORT))   
        
        logging.info("Incoming dispatcher initiated Successfully.")
        
    def run(self):
        """ Override method run() in a Thread"""
        
        #assign function addresses locally
        dispatch = self.dispatch
        receiver = self.receiver
        
        while 1:
            #receive a digested message from other nodes
            digested_message = receiver.recv()

            dispatch(ECHOMessage.deserialize(digested_message))
        
    def dispatch(self, echoMessage):
        """ dispatch a message to a echoProcess worker based on load-balancing scheme."""
        
        if Profiler.enabled:
            Profiler.send_data(('transmission_of_msg_type_%i' % echoMessage.get_type()),time.time()-echoMessage.t0)
            # re-measure t0 for queuing time
            echoMessage.t0 = time.time()
        
        #TODO: add proper load balancing. For now, use id%Nprocess
        invoke_id = echoMessage.get_id()
        # send to a queue
        self.process_queue_list[invoke_id%self.Nprocess].put(echoMessage)
        
        #print "{}".format(self.process_queue_list[0].qsize())
                
        
        #Correct load balance
#         #TODO: need a capped dict, reduce CPU usage or come up with the new idea to LB
#         try:
#             # send to the queue in case of its invoke id has been visited before
#             self.process_queue_list[self.multiplex_table[invoke_id]].put(echoMessage)
#         except KeyError:
#             # send to a queue by apply load balancing
#             #TODO: what if all queue empty all the time
#             min_queue = min(self.process_queue_list, key=lambda x: x.qsize())
#             min_queue.put(echoMessage)
#             self.multiplex_table[invoke_id] = self.process_queue_list.index(min_queue)
# 
#         #print "{} {} {}".format(self.process_queue_list[0].qsize(),self.process_queue_list[1].qsize(),self.process_queue_list[2].qsize())

#TODO: not in used
# class OutgoingDispatcher(threading.Thread):
#     """ It receives outgoing messages from workers (echoProcesses) and transmits to destinations."""
#      
#     def __init__(self,neighbor_list):
#         # base class initialization
#         super(OutgoingDispatcher,self).__init__()
#         
#         self.context = zmq.Context()
#         self.receiver = self.context.socket(zmq.PULL)
#         self.receiver.bind("ipc:///tmp/outgoing") # ipc : local inter-process communication
#         
#         #setup queues and outgoing_socket_thread
#         self.setup_outgoing_queue_and_socket(neighbor_list)
#         
#         logging.info("Outgoing dispatcher initiated Successfully.")
#         
#     def setup_outgoing_queue_and_socket(self,neighbor_list): 
#         """ initialize outgoing queues and sockets"""
#         
#         #setup queues and outgoing_socket_thread
#         self.outgoing_queues = {}
#         for neighbor in neighbor_list:
#             self.outgoing_queues[neighbor] = Queue.Queue()
#             threading.Thread(target=self.outgoing_socket_thread,
#                              args=(self.outgoing_queues[neighbor],neighbor,DISPATCHER_PORT)).start()
#         
#         #add a special outgoing_socket_thread for sending a return message
#         self.outgoing_queues['localhost'] = Queue.Queue()
#         threading.Thread(target=self.outgoing_socket_thread,
#                         args=(self.outgoing_queues['localhost'],'localhost',INTERFACE_PORT)).start()
# 
#     def outgoing_socket_thread(self,queue,neighbor_address,port):
#         """ a thread for getting a message from the queue and send it to destination """
#         
#         sender = self.context.socket(zmq.PUSH)
#         sender.connect("tcp://{0}:{1}".format(neighbor_address,port))
#         
#         while 1:
#             sender.send(queue.get())
#             
#             
#     #override method run() in a Thread
#     def run(self):
#         #assign function addresses locally
#         dispatch = self.dispatch
#         receiver = self.receiver
#         
#         while 1:
#             #receive a message tuple from echoProcess 
#             message_tuple = receiver.recv_multipart()
#             dispatch(message_tuple)
#             
#         
#     def dispatch(self, message_tuple):
#         """ dispatch a message from a echoProcess worker and place in outgoing queue."""
#         message_content = message_tuple[0]
#         destination_list = message_tuple[1:]
#         
#         for destination_name in destination_list:
#             try:
#                 self.outgoing_queues[destination_name].put(message_content)
#             except KeyError:
#                 logging.error("Can't find destination to {0} for sending a message".format(destination_name))            
#         