
import platform
import time
import cPickle as pickle

import zmq


from NetworkSearch2.interpreter.nsInterfaceAlpha import nsInterface
from NetworkSearch2.QuerySubsystem.queryObject import QueryObject

HOST = platform.uname()[1]
EXTERNAL_PORT = 7735

def query(statement):
    print statement
    cs = UnifiedInterface(statement,{})
    cs.search()
    print cs.results
    return cs.results


class UnifiedInterface():
    
    def __init__(self, queryExpression, specified_parameters):
        #super(UnifiedInterface,self).__init__(queryExpression, source, qId, rank, limit, returnRank)
        # NOTE : parameters ={'rank':None, 'returnRank':True, 'limit':limit , 'isApprox':true, 'tf':tf,'nr':nr,'tr':tr}
        
        # default parameters
        parameters = {'limit':None , 'isApprox':True, 'tf':5,'nr':5,'tr':5}
        parameters.update(specified_parameters)
        
        print "xxxx : " + `queryExpression`
        print parameters
        self.parameters = parameters
        self.queryExpression = queryExpression
        try:
            self.weightScore = { "tf" : int(parameters['tf']),
                                 "nr" : int(parameters['nr']),
                                 "tr" : int(parameters['tr'])
                                }
        except ValueError:
            self.weightScore = { "tf" : 5,
                                 "nr" : 5,
                                 "tr" : 5
                                }
            self.parameters['tf'] = 5
            self.parameters['nr'] = 5
            self.parameters['tr'] = 5
        self.isApprox = parameters['isApprox']
        try:
            if not parameters['limit']: 
                self.limit = None
            else:
                self.limit = int(parameters['limit'])
        except ValueError:
            self.limit = None
            self.parameters['limit'] = None
        
        context = zmq.Context()
        self.socket = context.socket(zmq.REQ)
        self.socket.connect("tcp://localhost:%s" % EXTERNAL_PORT)
         
    def search(self):
        self.dbQuery = ""
        print "\n\n\n"
        print self.queryExpression
        print "\n\n\n"        
        
        t0 = time.time()
        
        # parse user query
        match_query,project_query,aggr_query,group_query,pass_one_query,link_attributes,pass_two_query,flags = nsInterface(self.queryExpression, not self.isApprox)
        print flags,match_query
        print '\n\n\n' 
        
        if 'link' in flags and flags['link']:
            self.link(pass_one_query,link_attributes,pass_two_query,flags)
        elif 'projection' in flags:
            self.projection(match_query,project_query)
        elif 'aggregation' in flags:
            self.aggregation(match_query, project_query, aggr_query, group_query)
        else:
            # normal execution
            self.basic(match_query,flags)
            
        self.clean_up_result()
        
        self.numResults = len(self.results)
        self.time = time.time()-t0
        
    def link(self,pass_one_query,link_attributes,pass_two_query,flags):
              
        link_attributes = {} if not link_attributes else link_attributes
        
        # perform first pass
        self.socket.send_pyobj(QueryObject(pass_one_query,link_attributes,parameters={'isRank':False,"isApprox":False}))            
        initial_results = pickle.loads(self.socket.recv())
        
        # collect linking attribute
        if 'link_all' in flags and flags['link_all']:
            linking_attributes_values =  [{'content':v} for obj in initial_results for a,v in obj.iteritems() if str(v).find('ns:')==0]
        else:
            linking_attributes_values =  [{'content':v} for obj in initial_results for a,v in obj.iteritems() if a in link_attributes]
            
        print 'Linking attribute: '+`linking_attributes_values`
        
        if len(linking_attributes_values) == 0:
            self.results = ""
            return      
 
        # form second pass query  
        if pass_two_query:
            query = {'$and':[pass_two_query,{'$or':linking_attributes_values}]}
        else:
            query = {'$or':linking_attributes_values}
            
        print 'Second pass query: '+`query`
        
        # perform second pass
        self.socket.send_pyobj(QueryObject(query,parameters={'isRank':False,"isApprox":False}))
        self.results = pickle.loads(self.socket.recv())
        self.parameters['isApprox'] = False
    
    def projection(self,match_query,project_query):
        
        project_query.update({'object-name':1,'object-type':1})
        
        print "exact : " + `match_query` + " Proj : " + `project_query`
        
        if not match_query:
            self.results = ""
            return
        self.socket.send_pyobj(QueryObject(match_query,project_query,parameters={'isRank':False,"isApprox":False}))
        self.parameters['isApprox'] = False
        self.parameters['isProject'] = True
        self.results = pickle.loads(self.socket.recv())
    
    def aggregation(self,match_query,project_query,aggr_query , group_query):
        
        print "exact : " + `match_query` + " Proj : " + `project_query` +  " Aggr : " + `aggr_query`+ " group-by : " + `group_query`
         
        if not match_query:
            self.results = ""
            return
        self.socket.send_pyobj(QueryObject(match_query,project_query,aggr_query,group_query,parameters={'isRank':False,"isApprox":False}))
        self.parameters['isApprox'] = False    
        self.results = pickle.loads(self.socket.recv())           
    
    def clean_up_result(self):
        results =self.results
        name_list = ['tf_score','nr_score','tr_score','tf','nr','tr','keyword' , 'document','_id']
        for obj in results:
            for key_name in name_list:
                if obj.has_key(key_name):
                    del obj[key_name]
        temp = []
        for obj in results:
            try:
                temp.append((obj['total_score'],obj))
                del obj['total_score']
            except KeyError:
                break
        else: # execute when for loop finish without break
            self.results = temp

    
    def basic(self,match_query,flags):
        """basic query execution"""
        
        if not match_query:
            self.results = ""
            return
        
        if 'approximate' in flags:
            
            print "approx : " + `match_query`
            self.socket.send_pyobj(QueryObject(match_query,parameters={'isRank':True,"limit":self.limit,"isApprox":True,"weightScore":self.weightScore}))
            self.parameters['isApprox'] = True
        elif 'exact' in flags:
            
            print "exact : " + `match_query`
            self.socket.send_pyobj(QueryObject(match_query,parameters={'isRank':False,"isApprox":False}))
            self.parameters['isApprox'] = False         
        else:
            print "ERROR : unknown query"
            self.results = [{'Error':'unknown query'}]
            return
            
        # receive pickled dict
        self.results = pickle.loads(self.socket.recv())

        
# cs = UnifiedInterface('-aggr(count(server-name), sum(command-line)) -g(command-line) (object-type)',isApprox = False,limit=0)
# cs.search()
# print cs.results
# print len(cs.results)
# print cs.time


# paremeters = {'rank':None, 'returnRank':True, 'limit':123124 , 'isApprox':True, 'tf':4,'nr':4,'tr':4}
# query = "130.237.50.205 + network-interface"
# cs = UnifiedInterface(query, paremeters)
# cs.search()
# query = "server + eth0"
# cs = UnifiedInterface(query, paremeters)
# cs.search()