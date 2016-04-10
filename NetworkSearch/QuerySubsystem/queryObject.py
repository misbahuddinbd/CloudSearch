""" contains QueryObject class.

It defines the QueryObject class. It contains the query information.
e.g. query statements, some specific parameters for an execution, etc.
It is served for being an data object.

@author: Misbah Uddin
"""

from pprint import pformat

class QueryObject(object):
    """ The query object. """
        
    def __init__(self, match_statement, projection_statement = {}, aggregation_function_list = None, group_attribute_list = None, parameters = {}):
    
        # collect information
        self.match_statement = match_statement
        self.projection_statement = projection_statement
        self.aggregation_function_list = aggregation_function_list
        self.group_attribute_list = group_attribute_list
        # e.g. aggregation_function_list = [('count','vm'),('max','util')]
        
        default_parameters = {
                              "limit" : None,
                              "isRank" : True,
                              "isApprox" : True,
                              "weightScore" : { "tf" : 4,
                                                "nr" : 10,
                                                "tr" : 7,
                                              },
                              # "rankOpFlag" : 'AND'   <<<< for the case of rank scoring 
                              }
        
        self.parameters = default_parameters
        self.parameters.update(parameters)
        
    def __str__(self):
        # for better presentation
        return pformat(self.__dict__)

