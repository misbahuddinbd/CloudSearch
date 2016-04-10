""" a process for an Echo execution.

It defines the EchoProcess and EchoProtocol classes 
used for execution in Echo protocol. The EchoProcess
is a process on which the EchoProtocol is executed.
It also provides a module method for initiation of the
Echo process. 

@author: Misbah Uddin
"""

import logging
from multiprocessing import Process, Queue
import zmq

from echoMessage import ECHOMessage
from echoAggregator import EchoAggregator
from executor import executor

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
NEIGHBOR_LIST = confparser.get('Echo_protocol','neighbor_list').split(',') # get a list
if len(NEIGHBOR_LIST)==1 and NEIGHBOR_LIST[0]=='':
    NEIGHBOR_LIST = []
NAME = confparser.get('Echo_protocol','hostname')
NPROCESS = confparser.getint('Echo_protocol','n_process')

DISPATCHER_PORT = confparser.getint('Dispatcher','dispatcher_port')
INTERFACE_PORT = confparser.getint('Interface','interface_port')

#MID_LIST_CAPPED = confparser.getint('Echo_protocol','message_list_capped')

del confparser

##############################

        
def initializer():
    """ () ->  list(queue)
    
    Initaiize a Echo process service consisting of <NPROCESS> process(es).
    Each process has an input queue. 
    
    Return a list of input queue for interacting with the processes.
    """
    
    # create queues and processs
    queue_list = []
    
    for _ in xrange(NPROCESS):
        #create a queue 
        input_queue = Queue()
        #create a process and start it
        EchoProcess(input_queue).start()
        # append the queue for future use
        queue_list.append(input_queue)
        
    logging.info("Echo process(es) initiated Successfully.")
    
    return queue_list

class EchoProcess(Process):
    """ A process for handling echo execution"""
    
    def __init__(self, input_queue):
        # base class initialization
        super(EchoProcess,self).__init__()
        
        self.input_queue = input_queue
        
        
    def run(self):
        """ This method will be called when the process started.
        Its responsibility is to get a message from the queue and 
        ask EchoProtocol class to perform the task"""
        
        # initiate EchoProtocol
        echo_protocol = EchoProtocol()
        input_queue = self.input_queue
        while 1:
            # get message out
            echo_message = input_queue.get()
            
            # collect queue time
            if Profiler.enabled:
                Profiler.send_data('Queue_time',time.time()-echo_message.t0)
            
            # perform a task (blocking call)
            echo_protocol.execute(echo_message)
            

        
class EchoProtocol():
    """ This class serves as a task executor.
    it holds variables and states related to echo execution."""
    
    def __init__(self):
        # TODO: need some way to remove old invoke id ,say, after some seconds pass 
        self.aggregator_collections = {}
        
        self.executor = executor()
        
        #setup outgoing sockets to neighbors
        self.context = zmq.Context()
        self.senders = {}
        for neighbor in NEIGHBOR_LIST:
            self.senders[neighbor] = self.context.socket(zmq.PUSH)
            self.senders[neighbor].connect("tcp://{0}:{1}".format(neighbor,DISPATCHER_PORT))
            
        #setup a special outgoing socket to an interface
        self.senders['localhost'] = self.context.socket(zmq.PUSH)
        self.senders['localhost'].connect("tcp://{0}:{1}".format('localhost',INTERFACE_PORT))
        
    def execute(self,echo_message):
        """ (ECHOMessage,) -> None
        
        This function will be called each Echo message received. 
        Then, it executes an echo execution."""
        
        #ECHO protocol 
      
        msg_type = echo_message.get_type()
        
        # invoke type
        if msg_type == ECHOMessage.MSG_TYPE_INVOKE:
            self.invoke_case(echo_message)
        # explorer type 
        elif msg_type == ECHOMessage.MSG_TYPE_EXP:
            self.exp_case(echo_message)
        # echo type
        elif msg_type == ECHOMessage.MSG_TYPE_ECHO:
            self.echo_case(echo_message)
        # invalid case
        else:
            self.invalid_case(echo_message)        
   
    @Profiler.profile('invoke_case')
    def invoke_case(self,invoke_msg):
        """ (ECHOMessage,) -> None
        
        An execution when receiving an invoke message. 
        """       
        #TODO: assume that we won't invoke the same ID *
        
        # get variables from a message
        invoke_id = invoke_msg.get_id()
        parent = invoke_msg.get_sender_name()

        # create an aggregator object
        aggregator = EchoAggregator(NEIGHBOR_LIST,parent)
        # save it for future reference
        self.aggregator_collections[invoke_id] = aggregator
        
        #if N != zero_set
        if len(aggregator.neighbors) != 0:
            #change an invoke message to an explorer message
            exp_msg = invoke_msg
            exp_msg.msg_type = ECHOMessage.MSG_TYPE_EXP
            exp_msg.sender = NAME

            # send explorer messages
            for host in aggregator.neighbors:
                self.senders[host].send(exp_msg.serialize())
            
            # A.initiate()
            # get the query object
            query = invoke_msg.get_data()
            # add more information to echo aggregator
            aggregator.limit = query.parameters['limit']
            aggregator.aggregation_function_list = query.aggregation_function_list
            # execute the result
            results = self.executor.execute(query)
            # store local results
            aggregator.results = results
        else:
            # A.initiate()
            # get the query object
            query = invoke_msg.get_data()
            # add more information to echo aggregator
            aggregator.limit = query.parameters['limit']
            aggregator.aggregation_function_list = query.aggregation_function_list
            # execute the result
            results = self.executor.execute(query)
            # create a return message
            return_msg = ECHOMessage(ECHOMessage.MSG_TYPE_RETURN,invoke_id,NAME,results)
            # return
            self.senders[parent].send(return_msg.serialize())
            # clean up
            self.aggregator_collections[invoke_id] = None
            del aggregator
            
    @Profiler.profile('exp_case')
    def exp_case(self,exp_msg):
        """ (ECHOMessage,) -> None
        
        An execution when receiving an explorer message. 
        """  
        # get variables from a message
        invoke_id = exp_msg.get_id()
        sender_name = exp_msg.get_sender_name()
        logging.debug("From {0} with invoke id {1}, received an explorer message".format(sender_name,invoke_id))
        
        # create a socket to parent if not exist
        if sender_name not in self.senders:
            self.senders[sender_name] = self.context.socket(zmq.PUSH)
            self.senders[sender_name].connect("tcp://{0}:{1}".format(sender_name,DISPATCHER_PORT))
        
        #  get a aggregator object from the collection. if not exist, create it
        try: 
            aggregator = self.aggregator_collections[invoke_id]
        except KeyError:
            aggregator = EchoAggregator(NEIGHBOR_LIST,sender_name)
            
        # N := N-{from}
        aggregator.remove_neighbor(sender_name)
        
        # if not visited
        if invoke_id not in self.aggregator_collections:
            # save it for future reference
            self.aggregator_collections[invoke_id] = aggregator
    
            # create local result, and store it locally
            # A.initiate()
            # get a query object
            query = exp_msg.get_data()
            # add more information to echo aggregator
            aggregator.limit = query.parameters['limit']
            aggregator.aggregation_function_list = query.aggregation_function_list
            
            # if there are neighbors
            if len(aggregator.neighbors)!=0:
                # change a sender name of a explorer message
                exp_msg.sender = NAME
                # broadcast explorer messages
                for host in aggregator.neighbors:
                    self.senders[host].send(exp_msg.serialize())
                
                # execute
                results = self.executor.execute(query)
                # store the result
                aggregator.results = results
                
            # if it is a leaf
            else: 
                # execute
                results = self.executor.execute(query)
                # create a return message
                echo_msg = ECHOMessage(ECHOMessage.MSG_TYPE_ECHO,invoke_id,NAME,results)
                # send to parent
                self.senders[aggregator.parent].send(echo_msg.serialize())
                #clean up
                self.aggregator_collections[invoke_id] = None
                del aggregator
        # visited and  N = zero_set
        else:
            if len(aggregator.neighbors) == 0:
            
                # return an echo message to parent
                echo_msg = ECHOMessage(ECHOMessage.MSG_TYPE_ECHO,invoke_id,NAME,aggregator.results)
                # return
                self.senders[aggregator.parent].send(echo_msg.serialize())
                #clean up
                self.aggregator_collections[invoke_id] = None
                del aggregator
                
    @Profiler.profile('echo_case')    
    def echo_case(self,echo_msg):
        """ (ECHOMessage,) -> None
        
        An execution when receiving an echo message. 
        """  
        #TODO: assume that we won't receive an echo if we didn't initiate an explorer
        
        # get variables from a message
        invoke_id = echo_msg.get_id()
        sender_name = echo_msg.get_sender_name()
        logging.debug("From {0} with invoke id {1}, received an echo message".format(sender_name,invoke_id))
        
        # get the aggregator from a collection
        aggregator = self.aggregator_collections[invoke_id]
        # perform aggregate
        aggregator.results = self.executor.aggregate(aggregator.results,echo_msg.get_data(),aggregator.limit,aggregator.aggregation_function_list)
        
        # N := N-{from} 
        aggregator.remove_neighbor(sender_name)
        
        # if N = zero_set
        if len(aggregator.neighbors) == 0:
        
            # return an echo message to parent
            return_msg = ECHOMessage(ECHOMessage.MSG_TYPE_ECHO,invoke_id,NAME,aggregator.results)
            # return
            self.senders[aggregator.parent].send(return_msg.serialize())            
            #clean up
            self.aggregator_collections[invoke_id] = None
            del aggregator
        
    def invalid_case(self,msg):
        logging.warning('Error: Invalid echo message type from {}'.format(msg.get_sender_name()))
        