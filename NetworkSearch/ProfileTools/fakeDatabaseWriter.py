import argparse
import time
import threading
import sys
import pymongo
import random
import copy
from collections import deque
from math import log

#below configuration for start/stop service
from NetworkSearch2.util.daemon import Daemon

def get_args():
    parser = argparse.ArgumentParser(description = "fake database writer module")
    parser.add_argument('-host', type=str, default="localhost", help='A database host IPaddress')
    parser.add_argument('-port', type=int, default=27017, help='A database host port')
    parser.add_argument('-db1', type=str, default="index", help='A database 1 name')
    parser.add_argument('-coll1',  type=str, default="termdoc", help='A database 1 collection')
    parser.add_argument('-db2', type=str, default="sensor", help='A database 2 name')
    parser.add_argument('-coll2',  type=str, default="objects", help='A database 2 collection')
    parser.add_argument("-disable1", action='store_true', default=False,
                        help='disable fake write on database 1 (index)')    
    parser.add_argument("-disable2", action='store_true', default=False,
                        help='disable fake write on database 2 (sensor)')
    parser.add_argument('-affected', type=float, default=1.0, help='ratio of affected \
                      index_objectsts over alindex_objectsts (0.0, 1.0] (default 0.1)')
    parser.add_argument('-addrate', type=float, default=1.0, help='add index and object rate (Poisson) (default 1)')
    parser.add_argument('-delrate', type=float, default=1.0, help='delete index and object rate (Poisson) (default 1)')
    parser.add_argument('-updaterate', type=float, default=1.0, help='update index and object rate (Poisson) (default 1)')
#     parser.add_argument("-usebatch", action='store_true', default=False, help='use batch write instead of poisson')
#     parser.add_argument("-batchinterval", type=int, default=1, help='an interval for a batch performs the write (default 1 sec)')
    parser.add_argument("mode", choices=['start','stop','restart'],
                        help='to start/stop/restart the fake database writer module')
    
    return parser.parse_args()


class fakeDatabaseWriter(Daemon):
    #overwrite __init__()
    def __init__(self, args, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.args = args
        Daemon.__init__(self, pidfile, stdin, stdout, stderr)
        self.mongo_connection = pymongo.MongoClient(self.args.host,self.args.port)
        self.db_collection_1 = self.mongo_connection[self.args.db1][self.args.coll1]
        self.db_collection_2 = self.mongo_connection[self.args.db2][self.args.coll2]
        
    # overwrite Daemon class. This method will be called when the daemon started
    def run(self):
        
        # index_objects that we can 
        total_objects = self.db_collection_1.count() 
        self.index_objects =list(self.db_collection_1.find({},limit=int(self.args.affected*total_objects)))
        self.new_index_objects=[]
        total_objects = self.db_collection_2.count() 
        self.objects =list(self.db_collection_2.find({},limit=int(self.args.affected*total_objects)))
        self.new_objects=[]
                
#         if self.args.usebatch:
#             self.addQ = deque()
#             self.delQ = deque()
#             self.updateQ = deque()
#             threading.Thread(target=self.batch_perform,args=(self.args.batchinterval,)).start()
#         
#         threading.Thread(target=self.add_index_object,args=(self.args.addrate,self.args.usebatch)).start()
#         threading.Thread(target=self.delete_index_object,args=(self.args.delrate,self.args.usebatch)).start()
#         threading.Thread(target=self.update_index_object,args=(self.args.updaterate,self.args.usebatch)).start()
        # index object
        if not self.args.disable1:
            threading.Thread(target=self.add_index_object,args=(self.db_collection_1,self.index_objects,self.new_index_objects,self.args.addrate,False)).start()
            threading.Thread(target=self.delete_index_object,args=(self.db_collection_1,self.index_objects,self.new_index_objects,self.args.delrate,False)).start()
            threading.Thread(target=self.update_index_object,args=(self.db_collection_1,self.index_objects,self.new_index_objects,self.args.updaterate,False)).start()
        # object
        if not self.args.disable2:
            threading.Thread(target=self.add_index_object,args=(self.db_collection_2,self.objects,self.new_objects,self.args.addrate,False)).start()
            threading.Thread(target=self.delete_index_object,args=(self.db_collection_2,self.objects,self.new_objects,self.args.delrate,False)).start()
            threading.Thread(target=self.update_index_object,args=(self.db_collection_2,self.objects,self.new_objects,self.args.updaterate,False)).start()
   
    def add_index_object(self,collection,objects,temp_objects,rate,isbatch):
        """ (int,) -> None
        
        A thread that add new index_objects into the database, using Poisson process with a given rate"""
        
        while 1:
            t0 = time.time()
            
            random_index = random.randint(0, len(objects))
            
            # get random object
            try:
                obj = copy.deepcopy(objects[random_index])
            except IndexError:
                obj = copy.deepcopy(objects[0])
                
            obj["keyword"] = random.randint(0,100000000)
            obj["writeFake"] = 1
            del obj["_id"]
            
            if isbatch:
                self.addQ.append(obj)
            else:
                # insert the random object into database
                try:
                    obj["_id"] = collection.insert(obj)
                except pymongo.errors.DuplicateKeyError:
                    continue
            
                # add to the list for future use
                temp_objects.append(obj)
            
            # Poisson process wait time 
            nextTime = -log(1.0-random.random())/rate
            try:
                time.sleep((t0 + nextTime)-time.time())
            except IOError:
                # in case we have negative value in sleep parameter
                pass
            
    
    def delete_index_object(self,collection,objects,temp_objects,rate,isbatch):
        """ (int,) -> None
        
        A thread that delete index_objects from the database, using Poisson process with a given rate"""
        
        while 1:
            t0 = time.time()
            
            if len(temp_objects)==0:
                time.sleep(1/float(rate)/10)
                continue

            random_index = random.randint(0, len(temp_objects))

            # get random object
            try:
                obj = temp_objects[random_index]
                # remove it from the list
                del temp_objects[random_index]
            except IndexError:
                obj = temp_objects[0]
                del temp_objects[0]
            
            if isbatch:
                self.delQ.append(obj)
            else:
                # delete the random object from database
                collection.remove({"_id":obj["_id"]})
            
            # Poisson process wait time 
            nextTime = -log(1.0-random.random())/rate
            try:
                time.sleep((t0 + nextTime)-time.time())
            except IOError:
                # in case we have negative value in sleep parameter
                pass
            
    
    def update_index_object(self,collection,objects,temp_objects,rate,isbatch):
        """ (int,) -> None
        
        A thread that update attribute(s) in index_objects, using Poisson process with a given rate"""
        while 1:
            t0 = time.time()
            
            size = len(objects)
            # get random object
            try:
                obj = objects[random.randint(0,size)]
            except IndexError:
                obj = objects[0]
            obj["writeFake"] = 1
            obj["randomFake"] = random.randint(0,100000)
            
            if isbatch:
                self.updateQ.append(obj)
            else:
                # insert the random object into database
                collection.update({"_id":obj["_id"]},{"$set": {"randomFake": obj["randomFake"] ,"writeFake":obj["writeFake"]}})
            
            # Poisson process wait time 
            nextTime = -log(1.0-random.random())/rate
            try:
                time.sleep((t0 + nextTime)-time.time())
            except IOError:
                # in case we have negative value in sleep parameter
                pass
            
#     def batch_perform(self,interval):
#         """ (int,) -> None
#         
#         if useBatch is true all reads, writes, and updates are performed in batch with given interval"""
#         while 1:
#             # insertion
#             addlist = [self.addQ.popleft() for _ in xrange(0,len(self.addQ))]
#             if len(addlist)>0:
#                 for obj in addlist:
#                     obj['_id']=self.db_collection_1.insert(obj)
#                     self.index_objects.append(obj)
#             
#             #deletion
#             dellist = [{"_id":self.delQ.popleft()["_id"]} for _ in xrange(0,len(self.delQ))]
#             if len(dellist)>0:
#                 for obj in addlist:
#                     self.db_collection_1.remove(obj)
#             
#             #update
#             for _ in xrange(0,len(self.updateQ)):
#                 obj = self.updateQ.popleft()
#                 self.db_collection_1.update({"_id":obj["_id"]},{"$set": {"randomFake": obj["randomFake"] ,"writeFake":obj["writeFake"]}})
#             time.sleep(interval)
            
        
def main():
    # Read command arguments
    try:
        args = get_args()
    except IOError as (errno, strerror):
        print "IOError({0}): {1}".format(errno,strerror)
                
    # setup a daemon
    daemon = fakeDatabaseWriter(args,'/tmp/fakeDatabaseWriter.pid', stdout=sys.stdout, stderr='FakeDatabaseWriter.log')
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
