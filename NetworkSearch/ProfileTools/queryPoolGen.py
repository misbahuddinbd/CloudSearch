import pymongo
import random
import zmq

from NetworkSearch2.interpreter.nsInterfaceAlpha import nsInterface
from NetworkSearch2.QuerySubsystem.queryObject import QueryObject
from NetworkSearch2.QuerySubsystem.echoMessage import ECHOMessage

DF_THRESHOLD = 300
MIN_DF_THRESHOLD = 2
MIN_COMBINATION = 2
MAX_COMBINATION = 5
FILE = 'queryPool.txt'

#############################
# read a configuration file #
#############################
from ConfigParser import SafeConfigParser
from sys import path

confparser = SafeConfigParser()
confparser.read([str(path[0])+'/../config.cfg'])

# get values
INTERFACE_PORT = confparser.getint('Interface','interface_port')
DISPATCHER_PORT = confparser.getint('Dispatcher','dispatcher_port')
START_QID = confparser.getint('Interface','start_qid')

#############################

server_names = ["cloud-1","cloud-2","cloud-3","cloud-4","cloud-5","cloud-6","cloud-7","cloud-8","cloud-9"]
#server_names = ['localhost']  
    

def _flatten_to_list(x):
    """ flatten nested dicts, lists, tuples, or sets generators to lists"""
    
    # if x is a dict, we need to pop both values and keys
    if isinstance(x, dict):
        for key in x.iterkeys():
            yield key
        for value in x.itervalues():
            for item in _flatten_to_list(value):
                yield item
    # if x is a list, tuple, or set pop out each item
    elif isinstance(x, (list, tuple, set)):
        for item in x:
            for subitem in _flatten_to_list(item):
                yield subitem
    else:
        yield x       
    

def main():
  
    keywords = set()
    
    ####################
    # getting keywords #
    ####################
    for server_name in server_names:
        connection = pymongo.MongoClient(server_name,27017)
        collection = connection["sensor"]["objects"]
        objects_cursor = collection.find({},{'_id':0,'content':0,'last-updated':0})
        for obj in objects_cursor:
            for keyword in _flatten_to_list(obj):
                if isinstance(keyword,unicode) and len(keyword)<200 and\
                   not ' ' in keyword and not '/' in keyword and\
                   not '@' in keyword and not 'mac-address' in keyword and\
                   not '[' in keyword and not 'image-id' in keyword and\
                   not 'command-line' in keyword and not 'memory-util' in keyword and\
                   not 'count' in keyword and not 'link_' in keyword and\
                   not 'group' in keyword and not 'sum' in keyword and\
                   not 'max' in keyword and not 'min' in keyword and\
                   not 'project' in keyword and not '_fake' in keyword:
                    #term.count(':')<=1 and term.count('-') <=2 and \
                    keywords.add(keyword)
        print "keywords length of %s = %d" %(server_name,len(keywords))
        
    #######################################
    # check the number of returned result #
    #######################################
    qid = 999999
    tailered_keywords = set()
    
    context = zmq.Context()
    receiver = context.socket(zmq.PULL)
    receiver.bind("tcp://*:{}".format(INTERFACE_PORT))
    sender = context.socket(zmq.PUSH)
    sender.connect ("tcp://localhost:{}".format(DISPATCHER_PORT))
    for keyword in keywords:
#        print keyword
        # create query object
        match_query,project_query,aggr_query,group_query,pass_one_query,link_attributes,pass_two_query,flags = nsInterface("count(object-name) "+keyword,True)
        
        if not match_query:
            print "unable to parse %s" % keyword
            continue
        
        if 'aggregation' in flags:
            query = QueryObject(match_query,project_query,aggr_query,group_query,parameters={'isRank':False,"isApprox":False})
        else:
            print 'parsing query error'
        
        # create echo msg and send
        msg = ECHOMessage(ECHOMessage.MSG_TYPE_INVOKE,qid,"localhost",query)
        sender.send(msg.serialize())          
        qid += 1
        # receive results
        results = receiver.recv()
        msg = ECHOMessage.deserialize(results)
        n_object_match = msg.get_data()[0]['object-name-count']
        
        if n_object_match > MIN_DF_THRESHOLD and n_object_match < DF_THRESHOLD:
            tailered_keywords.add(keyword)
#        print len(tailered_keywords)    
    print "tailered keywords length = "+str(len(tailered_keywords))
    
    ###################
    # add combination #
    ###################

    temp_pool = set()
    for i in xrange(MIN_COMBINATION,MAX_COMBINATION):
        for j in xrange(0,400):
            temp_pool.add(' | '.join(random.sample(tailered_keywords,i)))
            
    print "total keywords length = "+str(len(tailered_keywords)+len(temp_pool))    
    ###################
    # write to a file #
    ###################
    
    print 'writing...'    
    with open(FILE,'w') as f:
        if MIN_COMBINATION == 1:
            f.write('\n'.join(tailered_keywords))
        f.write('\n'.join(temp_pool))
    print 'DONE'
    
if __name__ == "__main__" :
    exit(main())
