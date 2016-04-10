""" A profiler receiver.

A module contains a class used for 
receiving the profile information and collect it 
then write into a file afterward.

@author: Misbah Uddin
"""

import time
import sys
import argparse
import logging
from collections import defaultdict
from itertools import izip_longest
from threading import Thread
import csv
import zmq

def get_args():
    """ None -> dict
    
    Argument parsing"""
    
    parser = argparse.ArgumentParser(description="A profile receiver for collecting a profile information")
    parser.add_argument('-warmup_time', type=int, default=30, 
                                help='A initial time that the receiver will not collect the information,\
                                      due to warm up period of the system (second)(default = 30)')    
    parser.add_argument('-end_time', type=int, default=300, 
                                help='A time lapsed before writing into a file (second)(default = 300)\
                                      Note that the record time = (end_time - warmup_time)')
    parser.add_argument('-output', type=str, default="output.out", 
                                help='A file name of reported histrogram (default = output.out)')    
    return parser.parse_args()


class ProfilerReceiver(Thread):
    """ This is a thread class that acts as a server to receive
    the profiling (latency) information and collects it in form of a dictionary of lists.
    Then, save to a csv file when the time ends."""
    
    # a dictionary where a key is a profile name and a value is list of latencies
    collection = defaultdict(list)
    
    def __init__(self,args):
        super(ProfilerReceiver,self).__init__()
        self.args = args
    
    def run(self):
        """ This method is called when ProfileReceiver is started. 
        It collects profile information. """
        
        logging.info("="*20)
        logging.info("Profile receiver module started. ")
        logging.info("="*20)
        
        # setup a server socket 
        self.receiver = zmq.Context().socket(zmq.PULL)
        self.receiver.bind("ipc:///tmp/profile" )  # ipc: local inter-process communication
        logging.info("ZMQ server socket is established.")
        
        # setting a receiving thread and start listening
        t = Thread(target=self.receiver_thread)
        t.daemon = True
        t.start()
        logging.info("Start listening profile information.")
                
        # sleep for the warm-up time
        time.sleep(self.args.warmup_time)
        
        # clean up a collection for removing information that we receive in warm-up period
        self.collection = defaultdict(list)
        logging.info("End of a warm-up period. ")
        
        # sleep for the time
        time.sleep(self.args.end_time-self.args.warmup_time)
        
        # Then, write to file
        with open(str(sys.path[0])+'/'+self.args.output,'w') as f:

            sorted_name_space = sorted(self.collection.keys())
            # create a csv native writer
            writer = csv.writer(f)
            # write header
            writer.writerow(sorted_name_space)
            # write contents (note: get a generator of list of values a in sequence of sorted_name_space,
            #                 then unpack it with *, then use zip function to transpose the list, finally
            #                 use writerows to write all rows)
            writer.writerows(izip_longest(*(self.collection[key] for key in sorted_name_space)))
            logging.info("Finish writing a file.")
            
        # The server is terminated
        logging.info("Profile receiver module ended.")
       
    def receiver_thread(self):
        """ a function thread that keep receiving profile information 
        and put it in a collection"""
        
        while 1:
            # receive profile information
            name,value = self.receiver.recv_multipart()
            
            # collect it 
            try:
                self.collection[name].append(float(value))
            except (TypeError, ValueError):
                logging.warning("Cannot collect profile name=%s value=%s, value must be of a number type." % (name,value))

def main():
    # Read command arguments
    try:
        args = get_args()
    except IOError as (errno, strerror):
        print "IOError({0}): {1}".format(errno,strerror)
        
    # setup a logging
    logging.basicConfig(filename=str(sys.path[0])+'/ProfileReceiver.log',
                    level=logging.DEBUG ,format='%(asctime)s %(levelname)s: %(module)s: %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')
    
    # start it
    ProfilerReceiver(args).start()

if __name__ == "__main__":
    exit(main())

        