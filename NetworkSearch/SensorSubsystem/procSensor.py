""" Contain ProcSensor class.

This module contains a ProcSensor class used
for detect processes information.

@author: Misbah Uddin
"""

import time
import datetime
import logging
import psutil

from NetworkSearch2.SensorSubsystem.genericSensor import GenericSensor

REFRESH_RATE = 0.5
#CPU_INTERVAL = 0.0

class ProcSensor(GenericSensor):
    """ The sensor for detecting processes."""

    def __init__(self):
        super(ProcSensor,self).__init__()
        logging.info("Initiated")
        
    def run(self):
        """ Overwrite GenericSensor.run() method. This method will be called when the sensor started"""
        while 1:
            
            ######################
            # perform collection #
            ######################
            
            process_dict = {}

            # loop through processes
            for process in psutil.process_iter():
                
                try:
                    # Don't store processes without cmdlines
                    if not process.cmdline:
                        continue
                    
                    #######################
                    # collect information #
                    #######################
                                  
                    name = "ns:{0}:{1}".format(process.pid, process.name)
                    cmdline = ':'.join(process.cmdline)
                    
                    # general information               
                    proc_object =  {'object-type'    : 'process',
                                    'object-name'    : name,
                                    'process-id'     : process.pid,
                                    'process-type'   : process.name,
                                    'user'           : 'ns:'+str(process.username),
                                    'command-line'   : cmdline,
                                    'num-threads'    : process.get_num_threads(),
                                    'start-time'     : datetime.datetime.fromtimestamp(process.create_time),
                                    }
    
                    # Memory & CPU utilization
                    proc_object['memory-load'] = process.get_memory_percent()   
                    # TODO: use non-blocking call for now, but the % will derive from CPU times elapsed since last call           
                    proc_object['cpu-load'] = process.get_cpu_percent(interval=0)
                    
                    #TODO: Socket connections
    #                     conns = process.get_connections()
    #                     if conns:
    #                         print conns
    #                         proc['local-connection'], proc['remote-connection'] = getConnLists(conns)
    
                    # Extra information
                    try:
                        if process.terminal:
                            proc_object['terminal'] = process.terminal                    
                        proc_object['exe'] = process.exe
                        proc_object['cwd'] = process.getcwd()
                        io_counter = process.get_io_counters()
                        proc_object['read-count'] = io_counter.read_count
                        proc_object['write-count'] = io_counter.write_count
                        proc_object['read-bytes'] = io_counter.read_bytes
                        proc_object['write-bytes'] = io_counter.write_bytes
                    except psutil.AccessDenied:
                        pass
                    #TODO: get file object
    #                 try:
    #                     print process.get_open_files() # and Try and see if any of the cmd is a file
    #                 except psutil.AccessDenied:
    #                     pass
                except psutil.NoSuchProcess:
                    continue
                ############################
                # added to key-value store #
                ############################
                # add a process object into a class dict variable
                process_dict[proc_object['object-name']] = proc_object

            #####################
            # update and delete #
            #####################  
            # call super's function to perform updating and deleting
            self.updates_and_deletes(process_dict)

            #######################
            # sleep for some time #
            #######################
            # note it will take 0.07 second to get info, and 0.23 to update in the db  
            time.sleep(REFRESH_RATE)

            
if __name__=="__main__":
  
    p = ProcSensor()
    from NetworkSearch2.SensorSubsystem.dbConnector import DBConnector
    p.bind_connector(DBConnector())
    p.start()
    time.sleep(100)