""" Contain VmSensor class.

This module contains a VmSensor class used
for detect virtual machine information.

@author: Misbah Uddin
"""

import time
import logging
from datetime import datetime
import xml.etree.ElementTree as ET
from NetworkSearch2.SensorSubsystem.genericSensor import GenericSensor

try:
    import psutil
except ImportError:
    psutil = None
# To avoid import errors if libvirt not used on this server
try: 
    import libvirt
except ImportError: 
    libvirt = None

    
### Global variables ###
REFRESH_RATE = 0.5


class VmSensor(GenericSensor):
    """ The sensor for detecting virtual machines."""

    def __init__(self):
        super(VmSensor,self).__init__()
        logging.info("Initiated")
        
    # Requires XML parsing for additional information about the VM
    def updateLibvirtXML(self,lv_conn,vm_object):
        """Amy's way of collect more information"""
        
        try:
            lv_vm = lv_conn.lookupByID(vm_object['libvirt-id'])
            devs = []; macs = []; ips = []
            for inf in ET.XML(lv_vm.XMLDesc(0)).findall('devices/interface'):
                dev = inf.find('target')
                if dev is not None:     dev = dev.attrib['dev']
                else:            dev = ''
    
                mac = inf.find('mac')
                if mac is not None:    mac = mac.attrib['address']
                else:            mac = ''
                
                ip = ''
                for param in inf.findall('filterref/parameter'):
                    if param.attrib['name'] == 'IP': 
                        ip = param.attrib['value']
                devs.append(dev)
                macs.append(mac)
                ips.append(ip)
            vm_object['network-interface']= devs
            vm_object['mac-address']    = macs
            vm_object['ip-address']    = ips
    
        # VM no longer exists
        except libvirt.libvirtError:
            pass
        
    def updateProcInfo(self,vm_object):
        """Amy's way of collect more information"""
        if psutil:
            name = vm_object['object-name'][vm_object['object-name'].find(':')+1:]
            for p in psutil.process_iter():
                try:
                    if name in p.cmdline:
                        
                        vm_object['start-time'] = datetime.fromtimestamp(p.create_time)
                        
                        # uptime
                        vm_object['uptime'] = (datetime.now()-vm_object['start-time']).total_seconds()
                                                
                        # Mem & CPU util
                        vm_object['memory-load'] = p.get_memory_percent()                
                        vm_object['cpu-load'] = p.get_cpu_percent(interval=0)
                except psutil.NoSuchProcess:
                    pass
    def run(self):
        """ Overwrite GenericSensor.run() method. This method will be called when the sensor started"""
        # connect to libvirt
        if libvirt:
            try:
                lv_conn = libvirt.openReadOnly('qemu:///system')    # Open these connections only once for all VMs
            except libvirt.libvirtError:
                logging.info("Cannot connect to 'qemu:///system'")
                logging.info("Ended")                
                return
        else:
            logging.info("Unsupport Libvirt library")            
            logging.info("Ended")
            return
        
        while 1:
            ######################
            # perform collection #
            ######################
            vm_dict = {}
            
            # loop though ID of vms
            for vid in lv_conn.listDomainsID():
                try:
                    # general information
                    dom = lv_conn.lookupByID(vid)
                    info = dom.info()
                    vm_object = {'libvirt-id'   : vid,
                                 'object-type'  :'vm',
                                 'object-name'  :'ns:'+str(dom.name()),
                                 'os-type'      : dom.OSType(),
                                 'uuid'         : dom.UUIDString(),
                                 'status'       : info[0],
                                 'memory'       : info[1] * 1024,    # Convert KiB -> B
                                 'cpu-cores'    : info[3],
                                 'cpu-time'       : info[4] / 10**9,   # parse to seconds
                                }

                    # additional information
                    self.updateLibvirtXML(lv_conn,vm_object)
                    
                    # process information
                    self.updateProcInfo(vm_object)
                    
                    ############################
                    # added to key-value store #
                    ############################
                    # add a vm object into a class dict variable  
                    vm_dict[vm_object['object-name']] = vm_object    
                    
                # VM no longer exists
                except libvirt.libvirtError:
                    continue
                          
            #####################
            # update and delete #
            #####################  
            # call super's function to perform updating and deleting
            self.updates_and_deletes(vm_dict)

            #######################
            # sleep for some time #
            #######################
            time.sleep(REFRESH_RATE)
            
if __name__=="__main__":
  
    p = VmSensor()
    from NetworkSearch2.SensorSubsystem.dbConnector import DBConnector
    p.bind_connector(DBConnector())
    p.start()
    time.sleep(100)