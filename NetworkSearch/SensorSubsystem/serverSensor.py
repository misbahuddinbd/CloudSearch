""" Contain ServerSensor class.

This module contains a ServerSensor class used
for detect server information.

@author: Misbah Uddin
"""

import logging
import platform 
import re
import time
import psutil
from subprocess import PIPE, Popen

from NetworkSearch2.SensorSubsystem.genericSensor import GenericSensor

REFRESH_RATE = 0.5
CPU_INTERVAL = 0.1

class ServerSensor(GenericSensor):
    """ The sensor for detecting servers."""

    def __init__(self):
        super(ServerSensor,self).__init__()
        logging.info("Initiated")
        
    def updateInfs(self,server_object):
        """Amy's way for getting interface address"""
        ifconfig = Popen('ifconfig', stdout=PIPE).communicate()                 # Uses 'ifconfig' command for network info
            
        # Separate out interfaces                                                                               
        infs = re.split('\n{2}', ifconfig[0], re.S)
        if infs:
            infs.pop()
            server_object['ip-address'] = []
            for inf in infs:
                inf = re.findall('^(\w+)\s+(.*)', inf, re.S)
                if inf:
                    ifDesc = inf[0][1]
    
                    # IP address
                    ip = re.search('inet addr:(\S+)', ifDesc)
                    if ip:        ip = ip.group(1)
                    else:        ip = ''
                        
                    if ip != '': server_object['ip-address'].append(ip)
                    
    def run(self):
        """ Overwrite GenericSensor.run() method. This method will be called when the sensor started"""
        while 1:
            ######################
            # perform collection #
            ######################
            
            # Basic Information
            server_object = {'hostname': platform.uname()[1]}
            server_object['object-type'] = 'server'
            server_object['object-name'] = 'ns:'+str(server_object['hostname'])
            server_object['linux-distribution'] = ':'.join(platform.linux_distribution())
            server_object['kernel-version'] = platform.uname()[2]
            server_object['architecture'] = platform.machine()
    
            with open('/proc/cpuinfo','r') as f:
                cpuinfo = f.read()
                cpus = re.findall('processor', cpuinfo)
                server_object['cpu-cores'] = len(cpus) 
            
            #IP address Information
            self.updateInfs(server_object)
            
            # Harddisk Information
            df = Popen('df',stdout=PIPE).communicate()                              # Uses 'df' command to read disk size / util %          
            hd = re.search('\s+(\d+)\s+\d+\s+\d+\s+(\d+)%', df[0])          
            server_object['disk'] = int(hd.group(1)) * 1024                                # Total harddisk space (convert kB -> B)
            server_object['disk-load'] = int(hd.group(2))                                  # percent harddisk utilized ()
            
            # Memory Information
            with open('/proc/meminfo', 'r') as f:
                totalMem = int(re.match('MemTotal:\s+(\d+)', f.readline()).group(1))
                freeMem = int(re.match('MemFree:\s+(\d+)', f.readline()).group(1))
                server_object['memory'] = totalMem * 1024                              # Total memory (convert kB -> B)
                server_object['memory-load'] = (100 * (totalMem - freeMem))/totalMem   # percent memory utilized (int)
            
            # Uptime Information
            with open('/proc/uptime', 'r') as f:                                    # Uses /proc/uptime to get server uptime
                uptime = f.readline()
                times = re.match('([\d\.]+) ([\d\.]+)', uptime) 
                server_object['uptime'] = int(float(times.group(1)))                                   # Uptime (rounded to int)
                server_object['uptime-idle'] = int(float(times.group(2))/server_object['cpu-cores'])      # Uptime idle (averaged over num_cpu_cores)
            
            # CPULoad Information     
            with open('/proc/loadavg', 'r') as f:                           # Uses /proc/loadavg to get cpu load (number of tasks running)
                line = f.readline()
                avgs = re.match('([\d\.]+) ([\d\.]+) ([\d\.]+)', line)
                if avgs:                                                # Average load for 1 / 5 / 15 minute periods
                    server_object['cpu-load-1'] = float(avgs.group(1))
                    server_object['cpu-load-5'] = float(avgs.group(2))
                    server_object['cpu-load-15'] = float(avgs.group(3))
                if psutil:
                    server_object['cpu-load'] = psutil.cpu_percent()
            
            ##########
            # update #
            ##########  
            # call super's function to perform updating 
            self.send_update(server_object)

            #######################
            # sleep for some time #
            #######################
            # note it will take 0.07 second to get info, and 0.23 to update in the db  
            time.sleep(REFRESH_RATE)
        
if __name__=="__main__":
   
    p = ServerSensor()
    from NetworkSearch2.SensorSubsystem.dbConnector import DBConnector
    p.bind_connector(DBConnector())
    p.start()
    time.sleep(100)