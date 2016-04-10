""" A profiler tools.
 
A module contains a context manager class of
a profiler using for wrapping blocks of code that you want to time 
and the class also has a decorator method for collecting 
the latency information. All collect information will send to the profile server.

@author: Misbah Uddin
"""

import time
import zmq
from functools import wraps


class Profiler(object):
    """ A context manager class that used for (1) timing the execution time of a block of code.
    There is a class variable named 'enebled', which can be set if you want to enable it,
    otherwise, it will not enable. In addition, (2) it has a decorator method for timing the function.
    All collect information will send to the profile server. (3) It has additional method for sending
    the information in case you already measure the value and want to send that value to the server.
    
    Example of usage
    
    >>> with profiler('test_name_1') as p:
    >>>    time.sleep(1)
    
    or 
    
    >>> @Profiler.profile('test_name_2')
    >>> def foo():
    >>>     pass
    >>> foo()
    
    or 
    
    >>> Profiler.send_data('test_name_3',0.03)
    
    """
    
    # A class variable
    enabled = False
    context = zmq.Context()
    
    #=====================context management methods==============================
        
    def __init__(self, name):
        self.name = name
        if Profiler.enabled:
            self.sender = self.context.socket(zmq.PUSH)
            self.sender.connect("ipc:///tmp/profile")


    def __enter__(self):
        """ this method will be called automatically before it gets into with statements"""
    
        if Profiler.enabled:
            self.start = time.time()
        return self

    def __exit__(self, *args):
        """ this method will be called automatically after it gets into with statements"""
        
        if Profiler.enabled:
            self.sender.send_multipart([self.name,`time.time() - self.start`])
            self.sender.close()
        
    #=====================A decorator method==============================
    
    @staticmethod
    def profile(profile_name):
        """ A decorator method for timing the execution 
        when it is called. <profile_name> is a name for the profiling section of codes.
        
        Example of usage
        
        >>> @Profiler.profile('test-1')
        >>> def foo():
        >>>     pass
        >>> foo()
        
        """
        def inner(func):
            """ get the function name and produce a decorator function."""
            @wraps(func)
            def wrap(*args, **kwargs):
                
                if Profiler.enabled:
                    # connect to the profile server
                    sender = Profiler.context.socket(zmq.PUSH)
                    sender.connect("ipc:///tmp/profile")
                    # timing
                    t0 = time.time()
                    result = func(*args, **kwargs)
                    sender.send_multipart([profile_name,`time.time() - t0`])
                    sender.close()
                    
                    return result
                else:
                    result = func(*args, **kwargs)
                    return result
            return wrap
        return inner        
    
    #=====================A send value method==============================
    
    @staticmethod
    def send_data(name,value):
        """ (str,number) -> None 
        This function is used when there is some other means to measure information and
        you want to send that information to a profile server for collecting.
        
        Example of usage
        
        >>> Profiler.send_data('foo-3',0.03)
                
        """
        if Profiler.enabled:
            # connect to the profile server
            sender = Profiler.context.socket(zmq.PUSH)
            sender.connect("ipc:///tmp/profile")
            sender.send_multipart([str(name),`value`])
            sender.close()
                    
                    
# testing
# if __name__=="__main__":
#     Profiler.enabled = True
#     import random
#     for i in xrange(50):
#         for _ in xrange(1000):
#             with Profiler(str(i)) as e:
#                 time.sleep(random.random()/1000)

#     
#     @Profiler.profile('bbefwegweg')
#     def test(a):
#         print a
#     test('asd')
#     print 'done'   
    
#     ###################### 1 ######################
#     t0 = time.time()
#     #for _ in xrange(1000):
#     with Profiler(True) as p:
#         pass
#     print `(time.time()-t0)*1000` + ' ms' 
#     
#     ###################### 2 ######################
#     @Profiler.profile
#     def test():
#         pass
#     
#     t0 = time.time()
#     test()
#     print `(time.time()-t0)*1000` + ' ms' 
#         
#     ###################### 3 ######################
#     
#     ProfilerServer()

    