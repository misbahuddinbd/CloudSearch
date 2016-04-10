""" A sensor for detecting flow objects. 
The flow die time is slightly longer than the flow lifetime for optimizing purpose."""


# arg = 'sudo -S tcpdump -nnq -i eth0 tcp and net 10.10.0.0/20 and not port 22'
# tcpdump = Popen(shlex.split(arg),stdout=PIPE,stdin=PIPE).communicate('qweasdzxc\n')
# print tcpdump[0]
# #tcpdump = Popen('sudo tcpdump -nnq -i br100 tcp and net 10.10.0.0/20 and not port 22',stdout=PIPE).communicate()
import logging
from datetime import datetime
import time

import re
import sys
import shlex
from subprocess import PIPE, Popen
from Queue import Queue
from threading import Thread

from NetworkSearch2.SensorSubsystem.genericSensor import GenericSensor

#OBSERVER = 'cloud-1'
REFRESH_RATE = 0.5
OBJECT_LIFETIME = 5 # not in used
OBJECT_DIETIME = 30

class flowObject:
    def __init__(self,start_time,srcIP,srcPort,dstIP,dstPort,byte):
        self.start_time =start_time
        self.end_time = start_time
        self.src_IP = srcIP
        self.src_port = srcPort
        self.dst_IP = dstIP
        self.dst_Port = dstPort
        self.total_bytes = byte
        self.counts = 1
        #self.observer = OBSERVER
        self.object_name = 'ns:' + ':'.join([srcIP,str(srcPort),dstIP,str(dstPort)])

    def update(self,time,byte):
        # if a flow exist more than its lifetime, then reset start_time,end_time,total_bytes, and counts
#         if (time-self.start_time).total_seconds()>OBJECT_LIFETIME:
#             self.start_time = time
#             self.end_time = time
#             self.counts = 1
#             self.total_bytes = byte
#         else:
            self.counts += 1
            self.end_time = time
            self.total_bytes += byte
        
    def to_dict(self):
        #TODO: we should have used below method to return a dictionay.\
        # However, python won't allow attribute name with '-'. \
        # Thus, wee need to convert it ourself
        #     return self.__dict__
        
        #TODO: This is not good
        if self.counts == 1:
            bandwidth = self.total_bytes
        else:
            try:
                bandwidth = self.total_bytes / (self.end_time - self.start_time).total_seconds()
            except ZeroDivisionError:
                bandwidth = self.total_bytes
            
        return {'object-name':self.object_name,
                'object-type':'flow',
                'src-ip':self.src_IP,
                'src-port':self.src_port,
                'dst-ip':self.dst_IP,
                'dst-port':self.dst_Port,
                'start-time':self.start_time,
                'end-time':self.end_time,
                'bytes':self.total_bytes,
                'bandwidth':bandwidth,
                'packets':self.counts,
                }
        
    def __str__(self):
        return `self.to_dict()`
    
class FlowSensor(GenericSensor):
    """ The sensor for detecting a flow."""

    def __init__(self):
        super(FlowSensor,self).__init__()
        
        # object variables
        self.queue = Queue()
        self.flow_dict = dict()
        
        logging.info("Initiated")
      
    def read_tcpdump_thread(self, out):
        """ read a line from a opened file and put in a queue"""
        
        for line in iter(out.readline, b''):
            self.queue.put(line)
        out.close()
        
    def collecting_thread(self):
        """ get a line from the queue and parse it, then 
        store or update a flowObject in self.flow_dict."""
            
        while 1 :
            line = self.queue.get()
              
            #######################
            # parsing information #
            #######################
            value = re.split(':|\.| ',line)
            timestamp = datetime.today()
            timestamp = timestamp.replace(hour=int(value[0]),
                              minute=int(value[1]),
                              second=int(value[2]),
                              microsecond=int(value[3]))
            
            from_IP = '.'.join(value[5:9])
            from_port = int(value[9])
            dest_IP = '.'.join(value[11:15])
            dest_port = int(value[15])
            byte = int(value[18]) + 64
              
            key = from_IP+":"+str(from_port)+":"+dest_IP+":"+str(dest_port)
              
            #####################
            # store information #
            #####################
            try:
                #update the information if possible
                self.flow_dict[key].update(timestamp,byte)
            except KeyError:
                # can't find history record, create instead
                self.flow_dict[key] = flowObject(timestamp,from_IP,from_port,dest_IP,dest_port,byte)        
          
    def update_thread(self):
        """ send an update/delete to database via the Connector."""
        # assign local variables for faster execution 
        object_dietime = OBJECT_DIETIME
        flow_list = self.flow_dict
          
        while 1:
            # clean up the flow that life longer than die time
            now = datetime.now()
            #TODO: this is too slow (0.1-0.2 ms)
            for key in flow_list.keys():
                if (now - flow_list[key].start_time).total_seconds() > object_dietime:
                    # send the delete signal to database via calling superclass's send_delete()
                    self.send_delete(flow_list[key].to_dict())  #   removeObjectByName('flow',flow_list[key].object_name)
                    del flow_list[key]
  
              
            # send the update to database via calling superclass's send_update()
            for flowObjects in flow_list.values():
                self.send_update(flowObjects.to_dict())
            #map(connector.update,flow_dict.iteritems())
              
            #print len(flow_dict)
            time.sleep(REFRESH_RATE)
            
    def run(self):
        """ Overwrite GenericSensor.run() method. This method will be called when the sensor started"""
        
        # set up process open to tcpdump
        args = shlex.split('sudo -S tcpdump -nnq tcp and ip')   
        ON_POSIX = 'posix' in sys.builtin_module_names
        p = Popen(args, stdout=PIPE, bufsize=1, close_fds=ON_POSIX)
         
        # initialize a thread for reading information
        t = Thread(target=self.read_tcpdump_thread, args=(p.stdout,))
        t.daemon = True
        t.start()
        # initialize a thread for collecting information
        t2 = Thread(target=self.collecting_thread)
        t2.daemon = True
        t2.start()
        # initialize a thread for updating information to database via connector
        t3 = Thread(target=self.update_thread)
        t3.daemon = True
        t3.start()
        
        logging.info("Started")
        
        # wait forever
        t.join()
        t2.join()
        t3.join()
        