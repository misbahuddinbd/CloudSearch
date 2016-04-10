""" contains EchoAggregator class.

It defines the EchoAggregator class. It contains the aggregator object information.
e.g. remaining neighbors, results, parent, etc.
It is served for being an data object.

Note that the functions of the aggregator object is defined in executor.py

@author: Misbah Uddin
"""

class EchoAggregator:
    """ The Echo Aggregator object. """
    
    def __init__(self,neighbors,parent,results=None,limit=None,aggregation_function_list = None):
        self.neighbors = neighbors[:]
        self.parent = parent
        self.results = results
        self.limit = limit
        self.aggregation_function_list = aggregation_function_list
        
    def remove_neighbor(self,neighbor):
        """ (str,) -> None
        
        Remove a neighbor from the self.neighbors. 
        """
        
        try:
            self.neighbors.remove(neighbor)
        except ValueError:
            pass