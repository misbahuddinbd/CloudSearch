import psutil
import threading
import time
import argparse
from collections import OrderedDict
#below configuration for start/stop service
from NetworkSearch2.util.daemon import Daemon


COLLECTING_INTERVAL	= 0.5
CHECKING_PROCESS_INTERVAL = 0.1
LOGGING_INTERVAL = 0.5
# CAPTURE_NAME = [
# 		'sensor',
# 		'mongo',
# 		'queryInjection',
# 		'queryListener',
#         'MemCPUprofiler'
# ]
CAPTURE_NAME = ['manager.py','indexManager.py','/usr/bin/mongod','sensorManager.py']

#TODO think about the using result object instead of passing around the result dict
#TODO find the way to organize the result object and print it out maybe dict of dict

class ResultObject:
    """ not in use """
    def __init__(self):
        self.CPU_dict = {}
        self.mem_dict = {}

def get_args():
    parser = argparse.ArgumentParser(description='CPU and Memory monotoring')
    parser.add_argument("-file", type=argparse.FileType('w'), default=None,
                        help='result to a output file')
    parser.add_argument('-duration', type=int, default=180, help='Injection \
                                     duration in second')
    parser.add_argument('-warmup_time', type=int, default=30, 
                        help='A initial time that it will not collect the information,\
                              due to warm up period of the system (second)(default = 30)')  
    parser.add_argument("mode", choices=['start','stop','restart'],
                        help='to start/stop/restart the Network Search module')
    return parser.parse_args()


def monitoring(name, p, results):
    """ Monitoring a process and collecting %CPU and %Memory. 
    This method uses as a thread"""
    while 1:
        try:
            pid=p.pid
            p.get_cpu_percent()
            time.sleep(COLLECTING_INTERVAL)
            results['CPU-'+name+str(pid)] = p.get_cpu_percent()
            results['Mem-'+name+str(pid)] = p.get_memory_percent()
        except psutil.error.NoSuchProcess:
            try:
                del results['CPU-'+name+str(pid)]
                del results['Mem-'+name+str(pid)]
            except KeyError:
                print 'key error'
            break

def logging(results,f=None):
    """ logging the monitoring result for each interval"""
    #TODO find the way to organize the result and print 
    time.sleep(LOGGING_INTERVAL)

    #TODO this is the easy way to organize data, buy not neat
    compact_results = OrderedDict()
    for name in CAPTURE_NAME:
        compact_results['CPU-'+name] = 0
    for name in CAPTURE_NAME:
        compact_results['Mem-'+name] = 0
 
    for k,v in results.iteritems():
        for key in compact_results.iterkeys():
            if key in k:
                compact_results[key] += v
                break
        else: print 'some problems'
        
    #printing to a file if applicable
    list_a = zip(*compact_results.items()) #list_a = zip(*[(k, v) for k,v in summary.iteritems()])
    header = str(list_a[0]).strip("()").replace("'","") +"\n"
    content = str(list_a[1]).strip("()").replace("'","") +"\n"
    if f:
        if f.tell() == 0: f.write(header)
        f.write(content)
    else:
        print list_a
    
    
def sensingProcess(procs,results):
    """ sense all process and initiate a new monitoring thread 
    for each found related process. this method use as a thread"""
    while 1:
        # create a new process list name with no value as current_procs
        current_procs = {name: set() for name in CAPTURE_NAME}	

        # add a process into categories if it is part of CAPTURE_NAME
        for p in psutil.process_iter():
            try:
                cmd = p.cmdline	
                for name in CAPTURE_NAME:
                    if any(name in s for s in cmd):
                        current_procs[name].add(p) 
                        break
            except psutil.NoSuchProcess:
                pass

        # initate monitoring thread if there is new process
        for k in procs.iterkeys():
            new_process = list(current_procs[k] - procs[k])
            for p in new_process:
                t = threading.Thread(target=monitoring, args=(k,p,results))
                t.daemon = True
                t.start()

        # update the process list
        procs = current_procs

        # sleep for some time
        time.sleep(CHECKING_PROCESS_INTERVAL)
        
class profiler(Daemon):
    
    def __init__(self, args, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        Daemon.__init__(self, pidfile, stdin, stdout, stderr)
        self.args = args
    def run(self):
        
        # Initate variables
        procs = {name : set() for name in CAPTURE_NAME}
        results = {}
    
        # Run thread
        t = threading.Thread(target=sensingProcess, name='sensingProcess',
                             args=(procs,results))
        t.daemon = True
        t.start()
    
        t0 = time.time()
        while time.time()-t0 < self.args.duration:
            if time.time()-t0 < self.args.warmup_time:
                time.sleep(0.5)
            else:
                logging(results,self.args.file)
            
def main():
    
    # Get command arguments
    try:
        args = get_args()
    except IOError as (errno,strerror):
        return "IOError({0}): {1}".format(errno,strerror)
    
    import sys
    daemon = profiler(args,'/tmp/CPUMEMprofile.pid', stdout=sys.stdout, stderr="MemCPUprofiler.log")
    if 'start' == args.mode:
        print 'started'
        daemon.start()
    elif 'stop' == args.mode:
        daemon.stop()
        print 'stopped'
    elif 'restart' == args.mode:
        daemon.restart()
    else:
        pass

if __name__=="__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        pass




