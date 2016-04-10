from threading import Thread
import argparse
import sys
import time
import random
from collections import defaultdict
from math import log

import zmq
from daemon import Daemon

MASTER_PORT = 7730
PULL_PORT = 7731
# FLOW_LIFETIME = [5,10,20]
# HIGH_DATA_LENGTH = 100000
# LOW_DATA_LENGTH = 500
# NEW_FLOW_INTERVAL = 10
HEARTBEAT_INTERVAL = 10

def get_args():
    parser = argparse.ArgumentParser(description = "Flow simulator module")
    parser.add_argument('-mip','--masterIP', type=str, default=None, 
                        help='the manager IP address for the client to connect first to distribute list of IP address')
    parser.add_argument('-tr','--trafficRate', type=int, default=500, 
                        help='the traffic rate (Bytes per second)')
    parser.add_argument('-si','--sendInterval', type=float, default=0.5, 
                        help='the sending interval (second). This with trafficRate help to calculate message size')
    parser.add_argument('-flowgen','--flowGenerateRate', type=int, default=2, 
                        help='the rate in which the new flow is generated based on Poisson process (flow/min)')
    parser.add_argument('-flowlife','--flowLifeTime', type=int, default=4, 
                        help='the lifetime of the flow (seconds)')   
    parser.add_argument('-ctr','--ctrafficRate', type=int, default=500, 
                        help='the traffic rate (to client)(Bytes per second)')
    parser.add_argument('-csi','--csendInterval', type=float, default=0.5, 
                        help='the sending interval (to client) (second). This with trafficRate help to calculate message size')
    parser.add_argument('-cflowgen','--cflowGenerateRate', type=int, default=2, 
                        help='the rate in which the new flow is generated based on Poisson process (to client) (flow/min)')
    parser.add_argument('-cflowlife','--cflowLifeTime', type=int, default=4, 
                        help='the lifetime of the flow (to client) (seconds)')       
    parser.add_argument("mode", choices=['start','stop','restart'],
                        help='to start/stop/restart the Network Search module')
    parser.add_argument("type", choices=['master','server','client','eveClient'],
                        help='to specify the role of an application')

    return parser.parse_args()


class flowSimulator(Daemon):
    
    clients_dict = defaultdict(set)
    
    def __init__(self,args ,pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        super(flowSimulator,self).__init__(pidfile,stdin, stdout, stderr)
        self.args = args
        self.context = zmq.Context()
        
    # overwrite Daemon class. This method will be called when the daemon started    
    def run(self):
        self.sent_to_all_flag = False       
        if self.args.type == 'master':
            self.manager_server()
        elif self.args.type == 'server':
            self.client() # acting the same as client just some higher value parameters
        elif self.args.type == 'client':
            self.client()
        elif self.args.type == 'eveClient':
            self.sent_to_all_flag = True
            self.client()
        
    def manager_server(self):
        """ the server task is to receive a client IP and type and reply with a set of client IPs and types."""
        # create server sock
        sock = self.context.socket(zmq.REP)
        sock.bind("tcp://*:%s" % MASTER_PORT)
        
        while 1:
            #  Wait for next request from client
            client_IP,type = sock.recv_multipart()
            # add to a set
            self.clients_dict[type].add(client_IP)
            # send back the set
            sock.send_pyobj(self.clients_dict)
        
    def client(self):
        """ the client task is to inform (heartbeating) the manager server
        and issue sending something to a random other client"""
        
        # start a heart beat thread to the manager server
        t = Thread(target=self.heart_beat_thread)
        t.daemon = True
        t.start()
        
        # start a receiving thread
        t = Thread(target=self.receiving_thread)
        t.daemon = True
        t.start()
        
        # start flow gen thread tp servers
        t = Thread(target=self.flow_gen_thread , args=('server',))
        t.daemon = True
        t.start()       
        
        if self.args.type != 'server':
            # start flow gen thread to other clients
            t = Thread(target=self.flow_gen_thread , args=('client',))
            t.daemon = True
            t.start()
                 
        t.join()
        
    def  flow_gen_thread(self,dest_type):
        """ A creating flow Thread. """
        
        if dest_type == 'client':
            new_flow_rate = self.args.cflowGenerateRate/60.0
        else:
            new_flow_rate = self.args.flowGenerateRate/60.0
            
            
        sent_to_all_flag = self.sent_to_all_flag
        
        while 1:
            # Poisson process wait time 
            nextTime = -log(1.0-random.random())/new_flow_rate
            
            if sent_to_all_flag and dest_type =='server' :
                for IP in self.clients_dict[dest_type]:
                    Thread(target=self.sending_thread, args=(IP,dest_type)).start()
            else:  
                # random the parameter
                try:
                    randomIP = random.sample(self.clients_dict[dest_type], 1)[0]
                except ValueError:
                    time.sleep(nextTime)
                    continue
                # start a sending thread 
                Thread(target=self.sending_thread, args=(randomIP,dest_type)).start()
            
            # wait for sometime base on poisson process
            time.sleep(nextTime)

        
        
    def heart_beat_thread(self):
        """ A heart beat signal from the client to the server"""
        sock = self.context.socket(zmq.REQ)
        sock.connect ("tcp://{0}:{1}".format(self.args.masterIP,MASTER_PORT))
        
        interval = HEARTBEAT_INTERVAL
        thistype = self.args.type
        # get IP address
        import commands
        myIP = commands.getoutput("/sbin/ifconfig").split("\n")[1].split()[1][5:]
        while 1:
            sock.send_multipart([myIP,thistype])
            self.clients_dict = sock.recv_pyobj()
            time.sleep(interval)
            print self.clients_dict
    
    def receiving_thread(self):
        """ A receiving thread that receive the data and do nothing else"""
        sock = self.context.socket(zmq.PULL)
        sock.bind("tcp://*:"+str(PULL_PORT))
        
        while 1:
            # receive what ever sending to it
            sock.recv()
    
    def sending_thread(self,IP,dest_type):
        
        sock = self.context.socket(zmq.PUSH)
        sock.connect ("tcp://{0}:{1}".format(IP,PULL_PORT))
        
        if dest_type == 'client':
            # set up the variables
            interval = self.args.csendInterval
            data_length = self.args.ctrafficRate/float(self.args.csendInterval)
            # use normal distribution for flow life time
            flow_life_time = random.normalvariate(self.args.cflowLifeTime,self.args.cflowLifeTime*0.1)
        else:
            # set up the variables
            interval = self.args.sendInterval
            data_length = self.args.trafficRate/float(self.args.sendInterval)
            # use normal distribution for flow life time
            flow_life_time = random.normalvariate(self.args.flowLifeTime,self.args.flowLifeTime*0.1)
            
        start_time = time.time()
        
        while (time.time()-start_time) < flow_life_time:
            # use normal distribution for number of bytes send
            sock.send("a"*int(random.normalvariate(data_length,data_length*0.1)))
            time.sleep(interval)
    
def main():
    
    # Read command arguments
    try:
        args = get_args()
        print `args`
    except IOError as (errno, strerror):
        print "IOError({0}): {1}".format(errno,strerror)
        
    if args.type == 'master':
        pid = '/tmp/Flowsimulator-S.pid'
    else:
        pid = '/tmp/Flowsimulator-C.pid'
    # setup a daemon
    daemon = flowSimulator(args, pid, stdout=sys.stdout, stderr='Flowsimulator.log')
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
    
if __name__ == "__main__" :
    exit(main())
    