""" Contain FlowSensor class (and FlowObject class).

This module contains a FlowSensor class used
for detect IP flow information.

@author: Misbah Uddin
”””


# arg = 'sudo -S tcpdump -nnq -i eth0 tcp and net 10.10.0.0/20 and not port 22'
# tcpdump = Popen(shlex.split(arg),stdout=PIPE,stdin=PIPE).communicate('qweasdzxc\n')
# print tcpdump[0]
# #tcpdump = Popen('sudo tcpdump -nnq -i br100 tcp and net 10.10.0.0/20 and not port 22',stdout=PIPE).communicate()

import time
import logging
from datetime import datetime
from threading import Thread
import platform 

from scapy.all import sniff

from NetworkSearch2.SensorSubsystem.genericSensor import GenericSensor

#OBSERVER = 'cloud-1'
#OBJECT_LIFETIME = 5 # not in used
REFRESH_RATE = 0.5
OBJECT_DIETIME = 30
SNIFF_INTERFACE = 'br100'
SNIFF_FILTER = 'tcp and ip and net 10.10.0.0/20 and not port 22' # 'ip and tcp'

class flowObject:
    """ a data object defines and collects the information of the IP flow."""
    
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
        self.object_name = 'ns:' + ':'.join([platform.uname()[1],srcIP,str(srcPort),dstIP,str(dstPort)])

    def update(self,time,byte):
        """ (Datetime,number) -> None
         
        Update the value of last-seen time, the byte counts, and packet counts.
        """
        
        self.counts += 1
        self.end_time = time
        self.total_bytes += byte
        
    def to_dict(self):
        """ () -> dict 
        return a Json object (dict) used for the database. """
        
        #TODO: we should have used below method to return a dictionay.
        # However, python won't allow attribute name with '-'. 
        # Thus, wee need to convert it ourself
        #     return self.__dict__
        
        #TODO: This is not so good
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
        self.flow_dict = dict()
        
        logging.info("Initiated")
      
    def collecting_callback(self,pkt):
        """ A callback function for each packet received from sniffing. """
        
        if 'IP' in pkt and 'TCP' in pkt: # TCP and IP
            
            timestamp = datetime.today()
            # franky enough pymongo round up to millisecond, so we need to round it here in order to compare.
            timestamp = timestamp.replace(microsecond=timestamp.microsecond/1000 *1000)
            IP_segment = pkt['IP']
            TCP_segment = pkt['TCP']
            from_IP = IP_segment.src
            from_port = TCP_segment.sport
            dest_IP = IP_segment.dst
            dest_port = TCP_segment.dport
            byte = IP_segment.len
              
            key = 'ns:'+from_IP+":"+str(from_port)+":"+dest_IP+":"+str(dest_port)
            
            #####################
            # store information #
            #####################
            try:
                #update the information if possible
                self.flow_dict[key].update(timestamp,byte)
            except KeyError:
                # can't find history record, create instead
                self.flow_dict[key] = flowObject(timestamp,from_IP,from_port,dest_IP,dest_port,byte)
      
    def sniffing_thread(self):
        """ A sniffing thread."""
        sniff(prn=self.collecting_callback, iface=SNIFF_INTERFACE, filter=SNIFF_FILTER, store=0)
 
    def update_thread(self):
        """ send an update/delete to database via the Connector."""
        # assign local variables for faster execution 
        object_dietime = OBJECT_DIETIME
        flow_list = self.flow_dict
          
        while 1:
            # clean up the flow that life longer than die time
            now = datetime.now()
            for key in flow_list.keys():
                if (now - flow_list[key].start_time).total_seconds() > object_dietime:
                    # send the delete signal to database via calling superclass's send_delete()
                    self.send_delete(flow_list[key].to_dict())
                    del flow_list[key]
  
            # send the update to database via calling superclass's send_update()
            for flowObjects in flow_list.values():
                self.send_update(flowObjects.to_dict())
                
            # database update rate
            time.sleep(REFRESH_RATE)
            
    def run(self):
        """ Overwrite GenericSensor.run() method. This method will be called when the sensor started"""
         
        # initialize a thread for reading and collecting information
        t = Thread(target=self.sniffing_thread)
        t.daemon = True
        t.start()
        # initialize a thread for updating information to database via connector
        t2 = Thread(target=self.update_thread)
        t2.daemon = True
        t2.start()
        
        # wait forever
        t.join()
        t2.join()
        
if __name__ == '__main__':
    f = FlowSensor()
    from NetworkSearch2.SensorSubsystem.dbConnector import DBConnector
    f.bind_connector(DBConnector())
    f.start()
    time.sleep(100)
