""" Contain InterfaceSensor class.

This module contains a InterfaceSensor class used
for detect network interface information.

@author: Misbah Uddin
"""

import time
import re
import platform
from subprocess import PIPE, Popen
import logging
from NetworkSearch2.SensorSubsystem.genericSensor import GenericSensor

REFRESH_RATE = 0.5
#CPU_INTERVAL = 0.1

class InterfaceSensor(GenericSensor):
    """ The sensor for detecting network interfaces."""

    def __init__(self):
        super(InterfaceSensor,self).__init__()
        logging.info("Initiated")
        
    def run(self):
        """ Overwrite GenericSensor.run() method. This method will be called when the sensor started"""
        while 1:
            ######################
            # perform collection #
            ######################
            inf_dict = {}
            
            # Uses 'ifconfig' command for network info  
            ifconfig = Popen('ifconfig', stdout=PIPE).communicate()                       
            # Separate out interfaces                                                                               
            infs = re.split('\n{2}', ifconfig[0], re.S)
            if infs:
                infs.pop()
                for inf in infs:
                    inf = re.findall('^(\w+)\s+(.*)', inf, re.S)
                    if inf:
                        
                        ifName = inf[0][0]
                        ifDesc = inf[0][1]
        
                        # IP address
                        ip = re.search('inet addr:(\S+)', ifDesc)
                        if ip:       ip = ip.group(1)
                        else:        ip = ''
        
                        # IPv6 address
                        ipv6 = re.search('inet6 addr: (\S+)', ifDesc)
                        if ipv6:     ipv6 = ipv6.group(1)
                        else:        ipv6 = ''
        
                        # MAC address
                        mac = re.search('HWaddr (\S+)', ifDesc)
                        if mac:      mac = mac.group(1)
                        else:        mac = ''
                        
                        # Received bytes
                        rx = re.search('RX bytes:(\d+)', ifDesc)
                        if rx:      rx = rx.group(1)
                        else:       rx = ''
                        
                        # sent bytes
                        tx = re.search('TX bytes:(\d+)', ifDesc)
                        if tx:      tx = tx.group(1)
                        else:       tx = ''
        
                        # collect into a object
                        interface_object =     {'object-type'   : 'network-interface',
                                                'object-name'   : 'ns:'+str(ifName),
                                                'server' :  'ns:'+ platform.uname()[1]}
                        if ip:        interface_object['ip']     = ip
                        if ipv6:      interface_object['ipv6']    = ipv6
                        if mac:       interface_object['mac-address']= mac
                        interface_object['traffic-in-bytes']= int(rx)
                        interface_object['traffic-out-bytes']= int(tx)
                        
                        ############################
                        # added to key-value store #
                        ############################
                        # add a process object into a class dict variable                        
                        inf_dict[interface_object['object-name']]=interface_object
            
            #####################
            # update and delete #
            #####################  
            # call super's function to perform updating and deleting
            self.updates_and_deletes(inf_dict)

            #######################
            # sleep for some time #
            ####################### 
            time.sleep(REFRESH_RATE)
            
if __name__=="__main__":
  
    p = InterfaceSensor()
    from NetworkSearch2.SensorSubsystem.dbConnector import DBConnector
    p.bind_connector(DBConnector())
    p.start()
    time.sleep(100)
