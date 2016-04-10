""" a executor class for an aggregator execution.

It defines an executor class used for an execution of
an aggregator in Echo protocol. In the executor class,
it has two method exposes to other modules, i.e., execute()
and aggregate(). The methods here are delegated from the Echo aggregator.

@author: Misbah Uddin
"""

import logging
import pymongo
from math import sqrt
import operator
import itertools

# for profiling
from NetworkSearch2.ProfileTools.myProfiler import Profiler

# #############################
# # read a configuration file #
# #############################
# from ConfigParser import SafeConfigParser
# from sys import path
# 
# confparser = SafeConfigParser()
# confparser.read([str(path[0])+'/config.cfg'])
# 
# # get values
# #CAPPED_RETURN = confparser.get('Echo_protocol','capped_return')
# #CAPPED_RETURN = None if CAPPED_RETURN=='' or CAPPED_RETURN=='0' else int(CAPPED_RETURN)
# 
# del confparser
# 
# #############################

class executor:
    """ a class defines the execution of the aggragator for the echo protocol. """
    
    def __init__(self):
        self.mongo_connection = pymongo.MongoClient("127.0.0.1",27017)
        
    def _rank_aggregate(self,query):
        """(QueryObject) -> list of json object
        
        Calculate the total rank score for each object associated with the query.
        """
        ##############
        ## matching ##
        ##############
        collection = self.mongo_connection["index"]["termdoc"]
        
        with Profiler("index_DB_access_for_approx_match"):
            results_cursor = list(collection.find(query.match_statement))
       
        results = self._groupbyDoc(query,results_cursor)
        return results
        
    @Profiler.profile('Ranking')    
    def _groupbyDoc(self,query,results_cursor):
        """(pymongo.cursor) -> list of json objects
        
        Group the document and calculate the total score.
        """
        # eg. {ObjectID('xxx'):{u'object-type': u'network-interface',...},}
        
        ##########################
        ## grouping and ranking ##
        ##########################
        
        numbers_of_keyword = len(query.match_statement['$or'])
        
        results = {}
        list_results =[]
        for new_obj in results_cursor:
            if results.has_key(new_obj['document']):
                result_object = results[new_obj['document']]
                result_object['tf_score'] = result_object['tf_score'] + new_obj['tf']**2 if new_obj.has_key('tf') else result_object['tf_score']
                result_object['nr_score'] = result_object['nr_score'] + new_obj['nr'] if new_obj.has_key('nr') else result_object['nr_score']
                result_object['tr_score'] = result_object['tr_score'] + new_obj['tr'] if new_obj.has_key('tr') else result_object['tr_score']
                
            else:
                new_obj['tf_score'] = new_obj['tf']**2 if new_obj.has_key('tf') else 0
                new_obj['nr_score'] = new_obj['nr'] if new_obj.has_key('nr') else 0
                new_obj['tr_score'] = new_obj['tr'] if new_obj.has_key('tr') else 0
                results[new_obj['document']] = new_obj
        for result in results.itervalues():
            result['total_score'] = (query.parameters['weightScore']['tf'] * result['tf_score']/float(numbers_of_keyword) + \
                                     query.parameters['weightScore']['nr'] * result['nr_score']/float(numbers_of_keyword) + \
                                     query.parameters['weightScore']['tr'] * result['tr_score']/float(numbers_of_keyword)
                                     )/sum(query.parameters['weightScore'].itervalues())
                                    
            list_results.append(result)
        
        return list_results
    
    @Profiler.profile('Aggregator.local()')
    def execute(self,query):
        """ (QueryObject) -> list of json objects
        
        execute the local aggregator function. (similar to A.local() in echo context)
        """
        #########################
        # matching + projection #
        #########################
        
        # assign local variables
        object_collection = self.mongo_connection["sensor"]["objects"]
        limit = query.parameters['limit']

        # also filter out 'content' and '_id' fields
        if not query.projection_statement or len(query.projection_statement)==0:
            query.projection_statement = {"content":0} #,"_id":0}
        #TODO: should have else: filter "_id":0
        
        if query.parameters['isApprox']:
            # Approx. match
            
            # get index objects
            results = self._rank_aggregate(query)
            sorted_results = sorted(results, key=operator.itemgetter('total_score'),reverse=True)
            sorted_results = sorted_results[:limit]
            
            # get list of real-object oids from the index
            oid_list = map(operator.itemgetter('document'),sorted_results)
            
            with Profiler("object_DB_access_for_approx_match"):
                # get actual objects
                if oid_list:
                    real_object_results = list(object_collection.find({"_id":{'$in':oid_list}},query.projection_statement))
                else:
                    return []
            
            # add 'total_score' attribute to the real object
            temp = {}
            for obj in real_object_results:
                temp[obj['_id']] = obj
            for obj_index in sorted_results:
                try:
                    temp[obj_index['document']]['total_score'] = obj_index['total_score']
                except KeyError:
                    logging.warning("mismatch index object and real object : " + str(obj_index['document']))
                    
            results = temp.itervalues()
            sorted_results = sorted(results, key=operator.itemgetter('total_score'),reverse=True)
                              
        else:
            # exact match
            with Profiler("object_DB_access_for_exact_match"):
                results_cursor = object_collection.find(query.match_statement,query.projection_statement,limit=limit if limit else 0)            
                sorted_results = list(results_cursor)

        ########################
        # Aggregation function #
        ########################
        ## unique
        if query.aggregation_function_list and len(query.aggregation_function_list)==1 and 'unique' in query.aggregation_function_list[0]:
            temp = {}
            func_name,attr_name = query.aggregation_function_list[0]
            
            # generator object of values of an attribute that exists
            generator_values = (obj[attr_name] for obj in sorted_results if attr_name in obj) 
            for attr_value in generator_values:
                temp[attr_value] = 1
            sorted_results = [{attr_name:list(temp.iterkeys())}]
            return sorted_results
        
        temp_results = []
        
        # perform group by 
        if query.group_attribute_list:
            
            #filter the object that doesn't have the group attribute out
            sorted_results = filter( lambda x : all (k in x for k in query.group_attribute_list) , sorted_results)
 
            # sort base on attributes in a group_attribute_list
            sorted_results = sorted(sorted_results,key=operator.itemgetter(*query.group_attribute_list))

            # perform group by
            for k,g in itertools.groupby(sorted_results,key = operator.itemgetter(*query.group_attribute_list)):

                # perform aggregate on g
                obj = self._aggr_perform(query.aggregation_function_list,g)
                
                # add to result object  
                for i in range(len(query.group_attribute_list)):
                    obj[query.group_attribute_list[i]] = k[i] if isinstance(k,tuple) else k
                    
                temp_results.append(obj)
            sorted_results = temp_results
        ## normal aggregation case
        elif query.aggregation_function_list:
            sorted_results = [self._aggr_perform(query.aggregation_function_list,sorted_results)]
        ## don't perform an aggregation
        else:
            pass
        
        return sorted_results
            
    def _aggr_perform(self,aggregation_function_list,iterator_objects):
        """ (list((str,str)),iterable) -> json object 
        
        perform query aggregation without query groupby function
        """
        obj = {}
         
        for func_name,attr_name in aggregation_function_list:
            
            # generator object of values of an attribute that exists
            generator_values = (obj[attr_name] for obj in iterator_objects if attr_name in obj and obj[attr_name])
            
            # apply the function
            if func_name.lower() == "sum":
                try:
                    result = sum(generator_values)
                except TypeError:
                    # cannot sum some specific variable types
                    result =  'cannot perform sum in this attribute'
                    
            elif  func_name.lower() == "count":
                result = sum(1 for _ in generator_values)
            elif  func_name.lower() == "max":
                try:
                    result = max(generator_values)
                except ValueError:
                    # cannot find any value
                    result = None  #'cannot find any value'
                    
            elif  func_name.lower() == "min":
                try:
                    result = min(generator_values)
                except ValueError:
                    # cannot find any value
                    result = None # 'cannot find any value'
                                      
            else:
                result = 'Unknown aggragation method'
                
            obj[attr_name+'-'+func_name.lower()] = result
            
        return obj
    
    @Profiler.profile('Aggregator.aggregate()')
    def aggregate(self,local_result,agg,limit,aggregation_function_list):
        """ (QueryObject) -> list of json object 
        
        execute the aggregate function of an aggregator . (similar to A.aggregate() in echo context)
        """
        temp = local_result[:]
        temp.extend(agg)
        try:
            return sorted(temp, key=operator.itemgetter('total_score'),reverse=True)[:limit]
        except KeyError:
            if aggregation_function_list:
                ## unique
                if  len(aggregation_function_list)==1 and 'unique' in aggregation_function_list[0]:
                    
                    func_name,attr_name = aggregation_function_list[0]
                    unique_value = list(set(local_result[0][attr_name]).union(set(agg[0][attr_name]))) 
                    temp = [{attr_name:unique_value}]
                    
                    return temp
                    
                else:
                    ## normal aggregation
                    #print local_result , agg
                    temp = local_result[0]
                    for key,value in agg[0].iteritems():
                        if '-sum' in key or '-count' in key:
                            try:
                                temp[key] += value
                            except (KeyError,TypeError):
                                temp[key] = value
                                
                        elif '-max' in key:
                            try:
                                temp[key] = max(temp[key], value)
                            except KeyError:
                                temp[key] = value
                        elif '-min' in key:
                            try:
                                temp[key] = min(filter(None,(temp[key], value))) # filter `None` value out
                            except (KeyError,ValueError):
                                temp[key] = value
                        else:
                            temp[key] = value
                    #print temp
                    return [temp]   
            else:
                return temp
        